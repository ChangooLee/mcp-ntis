"""DeepAgent + NTIS 도구 in-process 통합.

LangChain의 DeepAgent를 NTIS MCP 도구들과 직접 연결한다.
FastMCP stdio는 `tools/list` 응답에 도구가 누락되는 이슈가 있어,
in-process로 NTIS 도구 함수들을 직접 LangChain StructuredTool로 wrap한다.
Claude 모델을 백엔드로 사용.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import os
from pathlib import Path
from typing import Any, AsyncIterator, Callable

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field, create_model

from deepagents import create_deep_agent

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


# ---------------------------------------------------------------------------
# 시스템 프롬프트 — R&D 분석가 페르소나
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
당신은 한국 국가R&D 데이터(NTIS)에 능숙한 R&D 동향 분석가입니다.
사용자의 질문에 답하기 위해 NTIS 도구를 활용합니다.

【도구 활용 원칙】
- 어떤 도구를 써야 할지 모호하면 `get_ntis_tool_info()`를 먼저 호출해 카테고리·연관 도구를 확인합니다.
- 정량 분석(예산 합산, 연도별 비교, 통계)이 필요하면 검색 도구를 반드시 `fetch_all=True`로 호출합니다.
  fetch_all=False로 100건만 보고 합산하면 결과가 부정확합니다.
- 단순 탐색은 page_size 10~20이면 충분합니다.
- 결과 id 필드는 후속 도구(`get_consignment_research`, `get_related_content`)에 그대로 전달 가능합니다.
- 동명이기관은 `get_org_rnd_status(auto_resolve=True)`가 처리합니다.

【답변 작성 원칙】
- 단순 카운트 나열이 아닌 인사이트(왜 그런지, 무엇을 의미하는지)를 도출합니다.
- 표·순위·증가율 등 정량 지표를 적극 활용합니다.
- NTIS 커버리지 한계(국가R&D 연계만 수록, 민간 자체 R&D 미포함 등)를 필요 시 안내합니다.
- 외부 지식이 필요하면(글로벌 비교, 학술 정의 등) 보강합니다.

【커버리지 안내】
- 논문은 ~19만 건 (국가R&D 연계만). 전체 학술논문은 RISS·PubMed 안내.
- 특허는 ~38만 건 (국가R&D 연계만). 전체 특허는 KIPRIS 안내.
- 연구장비는 NTIS 등록분만 (~2,800대).

답변은 한국어로 작성합니다. 도구를 모두 호출한 뒤 마지막에 사용자가 이해하기 쉬운 형식으로 종합 답변을 작성하세요.
"""


# ---------------------------------------------------------------------------
# NTIS 도구를 LangChain StructuredTool로 직접 wrap
# ---------------------------------------------------------------------------


def _python_type_from_schema(schema: dict) -> Any:
    """JSON schema → Python type 매핑."""
    t = schema.get("type")
    if t == "string":
        return str
    if t == "integer":
        return int
    if t == "boolean":
        return bool
    if t == "number":
        return float
    if t == "array":
        return list
    if t == "object":
        return dict
    return Any


def _build_arg_model(name: str, parameters: dict) -> type[BaseModel]:
    """ToolMetadata.parameters JSON schema → pydantic BaseModel."""
    props = parameters.get("properties", {}) or {}
    required = set(parameters.get("required", []) or [])
    fields: dict[str, tuple] = {}
    for key, schema in props.items():
        py_type = _python_type_from_schema(schema)
        default = schema.get("default")
        desc = schema.get("description", "")
        if key in required:
            fields[key] = (py_type, Field(..., description=desc))
        else:
            fields[key] = (py_type, Field(default=default if default is not None else None, description=desc))
    if not fields:
        fields["_dummy"] = (str, Field(default="", description="unused"))
    return create_model(f"{name}_Args", **fields)  # type: ignore[call-overload]


async def _resolve_tool_fn(tool_name: str) -> Callable[..., Any]:
    """FastMCP에 등록된 도구 함수(원본 async/sync callable)를 가져온다."""
    from mcp_ntis.server import mcp

    tool_obj = await mcp.get_tool(tool_name)
    if tool_obj is None or not hasattr(tool_obj, "fn"):
        raise RuntimeError(f"Tool '{tool_name}' 함수 객체를 찾을 수 없습니다.")
    return tool_obj.fn


def _make_tool_callable(tool_name: str, tool_fn: Callable[..., Any]) -> Callable[..., Any]:
    """NTIS MCP 도구를 LangChain Tool에서 호출할 수 있는 async 함수로 wrap."""

    async def _call(**kwargs: Any) -> str:
        clean = {k: v for k, v in kwargs.items() if v is not None and k != "_dummy"}
        try:
            result = tool_fn(**clean)
            if inspect.iscoroutine(result):
                result = await result
            if hasattr(result, "text"):
                return result.text
            if isinstance(result, str):
                return result
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as exc:
            msg = str(exc) or exc.__class__.__name__
            return json.dumps(
                {"error": msg, "tool": tool_name, "hint": "NTIS API 응답 지연 또는 일시 오류. 잠시 뒤 재시도하거나 fetch_all=False로 시도하세요."},
                ensure_ascii=False,
            )

    return _call


async def build_langchain_tools() -> list[StructuredTool]:
    """NTIS 도구 16개를 LangChain StructuredTool로 변환."""
    from mcp_ntis.server import tool_registry

    tools: list[StructuredTool] = []
    for name, meta in tool_registry.tools.items():
        args_model = _build_arg_model(name, meta.parameters)
        tool_fn = await _resolve_tool_fn(name)
        coroutine = _make_tool_callable(name, tool_fn)
        description = meta.description
        if len(description) > 1024:
            description = description[:1020] + "..."
        tool = StructuredTool.from_function(
            coroutine=coroutine,
            name=name,
            description=description,
            args_schema=args_model,
        )
        tools.append(tool)
    return tools


# ---------------------------------------------------------------------------
# DeepAgent 빌더
# ---------------------------------------------------------------------------


async def build_agent() -> tuple[Any, list[Any]]:
    """NTIS 도구를 로드하고 DeepAgent를 생성한다."""
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY가 .env에 설정되지 않았습니다. "
            ".env.example을 참고하여 설정하세요."
        )

    model_name = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")

    # 도구 로드 (in-process)
    tools = await build_langchain_tools()

    # Claude 모델
    model = ChatAnthropic(
        model=model_name,
        api_key=anthropic_key,
        temperature=0.3,
        max_tokens=8192,
    )

    # DeepAgent 생성
    agent = create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )
    return agent, tools


# ---------------------------------------------------------------------------
# 스트리밍 실행
# ---------------------------------------------------------------------------


async def stream_agent_run(agent: Any, user_message: str) -> AsyncIterator[dict[str, Any]]:
    """에이전트 실행 — 각 단계(생각/도구호출/도구응답)를 yield."""
    inputs = {"messages": [{"role": "user", "content": user_message}]}

    async for event in agent.astream(inputs, stream_mode="updates"):
        if not isinstance(event, dict):
            continue
        for node, state in event.items():
            if not isinstance(state, dict):
                continue
            messages = state.get("messages") or []
            for msg in messages:
                kind = getattr(msg, "type", None) or msg.__class__.__name__.lower()
                if kind in ("ai", "aimessage"):
                    text = ""
                    if isinstance(msg.content, str):
                        text = msg.content
                    elif isinstance(msg.content, list):
                        for block in msg.content:
                            if isinstance(block, dict):
                                if block.get("type") == "text":
                                    text += block.get("text", "")
                                elif block.get("type") == "thinking":
                                    yield {"type": "thinking", "content": block.get("thinking", "")}
                            elif isinstance(block, str):
                                text += block
                    if text:
                        yield {"type": "ai_text", "content": text}
                    tool_calls = getattr(msg, "tool_calls", None) or []
                    for tc in tool_calls:
                        yield {
                            "type": "tool_call",
                            "content": {
                                "name": tc.get("name") if isinstance(tc, dict) else tc.name,
                                "args": tc.get("args") if isinstance(tc, dict) else tc.args,
                                "id": tc.get("id") if isinstance(tc, dict) else getattr(tc, "id", ""),
                            },
                        }
                elif kind in ("tool", "toolmessage"):
                    tool_name = getattr(msg, "name", "") or ""
                    content = msg.content if isinstance(msg.content, str) else str(msg.content)
                    yield {
                        "type": "tool_result",
                        "content": {"name": tool_name, "content": content},
                    }


async def run_agent_full(agent: Any, user_message: str) -> str:
    inputs = {"messages": [{"role": "user", "content": user_message}]}
    result = await agent.ainvoke(inputs)
    messages = result.get("messages") or []
    if not messages:
        return ""
    last = messages[-1]
    if isinstance(last.content, str):
        return last.content
    if isinstance(last.content, list):
        return "\n".join(
            b.get("text", "") if isinstance(b, dict) else str(b)
            for b in last.content
        )
    return str(last.content)
