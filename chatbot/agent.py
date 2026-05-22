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
당신은 한국 R&D·산업 데이터 전문 비즈니스 분석가입니다.
사용자는 대부분 기업 대표·기획자·투자자이며 NTIS·ScienceON 같은 시스템 이름을 모릅니다.
사용자의 비즈니스 질문(시장 진출·협력사 발굴·기술 동향 등)을 데이터 기반 인사이트로 답합니다.

【보유 데이터 소스 (이름은 답변에 거의 노출하지 말 것)】
- **NTIS 도구 16개** (search_rnd_projects 등): 정부 R&D 과제·예산·공동연구·트렌드 이슈
- **ScienceON 도구 24개** (search_sci_*): 전체 학술 논문(~59만), 특허(~78만), 연구자, 동향 보고서

【도구 활용 원칙】
1. 어떤 도구를 쓸지 모호하면 `get_ntis_tool_info()`를 먼저 호출해 도구 카탈로그를 확인하세요.
2. 정량 분석(예산 합산, 연도별 비교, 통계)에는 **반드시 `fetch_all=True`** 사용. 100건만 보고 합산하면 부정확.
3. 두 데이터 소스를 **교차 비교**하면 더 풍부한 인사이트가 나옵니다:
   - 정부 펀딩 규모(NTIS) + 실제 학술 산출량(ScienceON) → 펀딩 효율
   - 국내 정부 과제(NTIS) + 전체 학술/특허(ScienceON) → 한국 R&D 강점 영역
4. NTIS는 정부 연계만 수록 → 민간 R&D는 ScienceON에서 보완.
5. ScienceON 일부 도구가 `E4302` 권한 없음 응답 시: 에러 그대로 노출하지 말고 NTIS 도구로 우회하거나 사용자에게 권한 신청 안내.

【답변 작성 원칙 — 매우 중요】
- **비즈니스 의사결정에 직접 도움 되는 답변**을 작성합니다. 데이터 나열이 아닌 **결론·추천·인사이트** 중심.
- 표·순위·증가율 등 정량 지표를 적극 활용합니다.
- 협력 후보 기업·기관, 핵심 PI, 예산 규모, 트렌드 방향성 등 **실행 가능한 정보**를 제공합니다.
- 시스템 이름(NTIS, ScienceON, KISTI 등)은 답변 본문에 노출하지 않습니다. "국가 R&D 데이터", "학술 데이터" 등 일반 표현 사용.
- 한국어로 작성합니다.

답변 흐름:
  ① 질문 의도 1줄 요약
  ② 핵심 발견 사항 3~5개 (표·순위 활용)
  ③ 비즈니스 권고 (협력 후보·진입 전략·리스크)
  ④ 필요 시 한계·후속 조사 제안
"""


# ---------------------------------------------------------------------------
# Prompt Enhancer — 비즈니스 질문 → 도구 호출 계획이 포함된 강화 프롬프트
# ---------------------------------------------------------------------------


PROMPT_ENHANCER_SYSTEM = """\
당신은 한국 R&D 데이터 분석가의 작업 흐름을 설계하는 보조 AI입니다.

사용자가 비즈니스 친화적인 자연어 질문을 입력하면, 그 질문을 답하기 위해
실제 분석가가 어떤 도구를 어떤 순서로 호출해야 하는지 **2~5줄 분석 계획**을
한국어로 작성하세요.

사용 가능한 도구 카테고리(이름은 분석가만 알면 됨):
- NTIS 검색: search_rnd_projects/papers/patents/reports/equipment, search_unified (fetch_all=True 사용 시 모든 페이지 자동 순회)
- NTIS 과제: get_consignment_research(공동연구), get_org_rnd_status(기관 현황)
- NTIS 분류: recommend_std/ht/it_classification, get_classification_codes
- NTIS 부가: search_rnd_issues(트렌드), search_terminology, get_related_content(유사 추천)
- ScienceON: search_sci_papers/patents/reports/trends/researchers/organizations 등 (전체 학술/특허/동향)

출력 형식:
원본 질문:
<사용자 자연어 질문>

분석 계획:
1) <도구 호출> — <목적>
2) <도구 호출> — <목적>
3) <교차 비교 또는 종합 방법>

【중요】 사용자에게 보이지 않는 보조 정보입니다. 정중하게 인사하거나 "물어보셨네요" 등의 군말 없이, 분석 계획만 작성하세요.
"""


async def enhance_user_prompt(user_question: str, model_name: str, api_key: str) -> str:
    """비즈니스 자연어 질문을 도구 호출 계획이 포함된 강화 프롬프트로 변환.

    실제 에이전트가 처리할 메시지에 prepend됨. 호출 1회로 끝나는 가벼운 LLM 호출.
    """
    from langchain_anthropic import ChatAnthropic
    from langchain_core.messages import SystemMessage, HumanMessage

    enhancer = ChatAnthropic(
        model=model_name,
        api_key=api_key,
        temperature=0.2,
        max_tokens=600,
    )
    msg = [
        SystemMessage(content=PROMPT_ENHANCER_SYSTEM),
        HumanMessage(content=user_question),
    ]
    resp = await enhancer.ainvoke(msg)
    plan = resp.content if isinstance(resp.content, str) else str(resp.content)
    # 최종 사용자 질문에 분석 계획을 첨부 (메인 에이전트가 참고)
    enhanced = (
        f"{user_question}\n\n"
        f"---\n"
        f"[보조 컨텍스트 — 위 질문 처리를 위한 권장 분석 흐름]\n"
        f"{plan.strip()}"
    )
    return enhanced


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
    """에이전트 실행 — 각 단계(생각/도구호출/도구응답/최종답변)를 yield."""
    inputs = {"messages": [{"role": "user", "content": user_message}]}

    last_ai_text = ""
    final_state: Any = None

    async for event in agent.astream(inputs, stream_mode="updates"):
        if not isinstance(event, dict):
            continue
        for node, state in event.items():
            if not isinstance(state, dict):
                continue
            final_state = state  # 마지막 state 보존
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
                        last_ai_text = text
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

    # stream이 끝났을 때 마지막 AI 텍스트가 비어있으면 최종 state에서 추출
    if final_state is not None:
        msgs = final_state.get("messages") if isinstance(final_state, dict) else []
        if msgs:
            for msg in reversed(msgs):
                kind = getattr(msg, "type", None) or msg.__class__.__name__.lower()
                if kind in ("ai", "aimessage"):
                    text = ""
                    if isinstance(msg.content, str):
                        text = msg.content
                    elif isinstance(msg.content, list):
                        text = "\n".join(
                            b.get("text", "") if isinstance(b, dict) and b.get("type") == "text" else ""
                            for b in msg.content
                        ).strip()
                    if text and text != last_ai_text:
                        yield {"type": "ai_text", "content": text}
                    break


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
