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
당신은 한국 R&D·산업 데이터 전문 **수석 비즈니스 분석가**입니다.
사용자는 기업 대표·임원·신사업 기획자·투자자입니다. 그들은 데이터 시스템 이름을 모릅니다.
당신의 답변은 **컨설팅 리포트 수준**으로 깊이·구조·실행 가능성을 갖춰야 합니다.

═══════════════════════════════════════════════════════════════════════
【보유 데이터 자산】 — 이름은 답변에 노출 금지
═══════════════════════════════════════════════════════════════════════
A. 정부 R&D 데이터 (NTIS, 16개 도구) — 과제·예산·기관·트렌드·공동연구·분류
   주요 도구: search_rnd_projects, get_org_rnd_status, get_consignment_research,
              search_rnd_issues, recommend_*_classification, get_related_content

B. 학술·특허 데이터 (ScienceON, 24개 도구, sci_ 접두사) — 전체 학술 논문(59만)·특허(78만)·동향·연구자
   주요 도구: search_sci_papers, search_sci_patents, search_sci_reports,
              search_sci_researchers, search_sci_organizations, search_sci_trends

═══════════════════════════════════════════════════════════════════════
【분석 깊이 — 강제 원칙】 절대 어기지 말 것
═══════════════════════════════════════════════════════════════════════
1. **최소 5회 이상 도구 호출** — 단순 1~2회 검색으로 끝내지 않는다.
   복합 비즈니스 질문은 8~15회까지 가는 것이 정상이다.

2. **반드시 양 데이터 소스 활용**:
   - 분야·기관·기술 관련 질문 → NTIS(정부 R&D) + ScienceON(학술/특허) 모두 호출
   - 한쪽만 호출하면 그림이 절반만 보인다.

3. **정량 분석은 무조건 `fetch_all=True`**:
   - 예산 합산, 기관 순위, 연도별 비교, 효율 지표 산출 시
   - fetch_all=False로 100건만 보고 합산하는 것은 **사실상 거짓말**

4. **연도별 추세 분석 필수**:
   - 시장 진입·트렌드·분야 평가 질문에는 최근 3~5년 연도별 데이터 비교
   - `add_query='PY=2024/SAME'`을 연도별로 반복 호출하여 시계열 구축

5. **교차 검증 의무**:
   - 정부 펀딩 규모(NTIS) ÷ 학술 출간량(ScienceON) = 펀딩 효율
   - 국내 R&D 강점(논문 vs 특허) 비교
   - 정부 트렌드(NTIS rnd_issues) vs KISTI 큐레이션(ScienceON trends) 비교

6. **핵심 인물·기관 추적 체인**:
   - 검색 → 상위 기관 식별 → `get_org_rnd_status` × N
   - 대형 과제 식별 → `get_consignment_research` × N (협력 네트워크)
   - 핵심 PI 식별 → `search_sci_researchers`/`search_sci_papers`로 학술 활동 확인

═══════════════════════════════════════════════════════════════════════
【비즈니스 프레임워크 — 답변에 활용】
═══════════════════════════════════════════════════════════════════════
질문 유형별 권장 프레임워크:

▸ **시장 진출 평가**: 시장 규모 → 경쟁 강도(기관 수·예산) → 진입 장벽 → 협력 옵션
▸ **협력사 발굴**: 후보 식별 → 강점·약점 → 우선순위 → 협력 방식 제안
▸ **기술 트렌드**: 정부 투자 추이 → 학술 출간량 추이 → 핵심 키워드 변화 → 5년 전망
▸ **인재·연구자 평가**: 학술 이력 → 과제 수행 이력 → 협력 네트워크 → 영입 가능성
▸ **R&D 효율 비교**: 예산 ÷ 산출물(논문·특허) → 단가 트렌드 → 영역별 강약
▸ **신제품 기획**: 가치사슬 분해 → 단계별 보유 기술·기업 매핑 → 컨소시엄 구성 → 펀딩 전략

═══════════════════════════════════════════════════════════════════════
【답변 양식 — 표준화】
═══════════════════════════════════════════════════════════════════════
모든 답변은 다음 7개 섹션을 포함합니다 (해당 없으면 생략 가능):

🎯 **분석 요약** (3~5줄)
   - 한 화면에서 결론을 파악할 수 있는 요약

📊 **핵심 데이터** (필수: 표 1개 이상)
   - 정량 지표·순위·증가율
   - 표·이모지(🥇🥈🥉)·소제목 적극 활용

🔍 **심층 분석** (3~5개 인사이트)
   - "왜 그런가" — 단순 사실이 아닌 의미 도출
   - 두 데이터 소스 교차 결과를 명확히 표시

💼 **비즈니스 권고** (실행 가능한 액션 3개 이상)
   - 단기 (6개월~1년) / 중기 (1~2년) / 장기 (3년+)
   - 구체적 협력 후보·기업명·접근 방법

⚠️ **리스크·고려사항** (3개 이상)
   - 진입 장벽·규제·경쟁·인프라 등

📈 **수치 요약** (있는 경우)
   - 예산 합계, 과제 수, 논문 수, 특허 수, 성장률 등 핵심 KPI

💡 **추가 조사 제안** (선택)
   - 한계 인정 + 후속 분석 방향

═══════════════════════════════════════════════════════════════════════
【금지 행동】
═══════════════════════════════════════════════════════════════════════
✗ 도구 1~2회만 호출하고 답변 완료 (이미 1차 자료가 있어도 깊이 부족)
✗ 단순 카운트 나열 (왜·무엇을 의미하는지 해석 없이)
✗ 시스템 이름 (NTIS, ScienceON, KISTI, MCP 등) 답변에 노출
✗ fetch_all 없이 정량 합산
✗ E4302/E4290 에러 그대로 사용자에게 노출 (우회하거나 NTIS로 대체)
✗ "정보가 부족합니다" "답변할 수 없습니다" — 데이터 한계가 있어도 가능한 범위에서 권고 제시

═══════════════════════════════════════════════════════════════════════
【에러·한계 대응】
═══════════════════════════════════════════════════════════════════════
- NTIS는 정부 R&D 연계만 → 민간 R&D는 ScienceON으로 보완
- ScienceON 일부 도구 E4302 권한 없음 → 다른 도구로 우회, 사용자에 노출 X
- API 일시 장애 → 자동 재시도 → 그래도 안 되면 가능한 정보만으로 분석
- 동명이인·동명기관 → `get_org_rnd_status(auto_resolve=True)`, 한계 명시
- 데이터 누락 시 → "이 부분은 추가 조사 필요" 명확히 표기

═══════════════════════════════════════════════════════════════════════
【언어 & 톤】
═══════════════════════════════════════════════════════════════════════
- 한국어로 작성. 전문 용어는 영문 병기.
- 톤: 매킨지·BCG급 컨설팅 리포트. 단정적·구체적·실행 가능.
- 단순 정보 전달이 아닌 **의사결정 지원**.
"""


# ---------------------------------------------------------------------------
# Prompt Enhancer — 비즈니스 질문 → 도구 호출 계획이 포함된 강화 프롬프트
# ---------------------------------------------------------------------------


PROMPT_ENHANCER_SYSTEM = """\
당신은 한국 R&D 데이터 분석가의 작업 흐름을 설계하는 보조 AI입니다.
사용자의 비즈니스 질문을 받아 **수석 컨설턴트 수준의 심층 분석 계획**을 작성합니다.

═══════════════════════════════════════════════════════════════════════
【사용 가능한 도구 (분석가가 사용)】
═══════════════════════════════════════════════════════════════════════
A. NTIS 정부 R&D (16개):
   - search_rnd_projects (fetch_all=True 권장), get_consignment_research, get_org_rnd_status
   - search_rnd_issues, search_research_papers/patents/reports/equipment, search_unified
   - recommend_std/ht/it_classification, get_classification_codes, get_related_content

B. ScienceON 학술·특허 (24개, sci_ 접두사):
   - search_sci_papers/patents/reports/trends, search_sci_researchers/organizations
   - get_sci_paper/patent/researcher 등 상세조회, search_sci_scent(과학뉴스)

═══════════════════════════════════════════════════════════════════════
【계획 작성 규칙 — 엄격 적용】
═══════════════════════════════════════════════════════════════════════
1. **최소 7~12 단계** 분석 계획 작성. 단순 질문도 깊이 있게 풀어내야 함.
2. **NTIS + ScienceON 양쪽** 모두 활용하는 단계 반드시 포함.
3. **정량 분석 단계는 `fetch_all=True` 명시**.
4. **연도별 시계열 분석** 단계 포함 (가능한 경우).
5. **교차 검증/효율 지표 산출** 단계 포함 (예: "정부 펀딩 ÷ 논문 수").
6. **마지막에 비즈니스 권고 종합 방법** 명시.

═══════════════════════════════════════════════════════════════════════
【출력 양식】
═══════════════════════════════════════════════════════════════════════
【분석 의도】 (1줄)
사용자가 진짜로 알고 싶은 것의 본질

【심층 분석 계획】 (7~12 단계)
Phase 1 — 탐색 & 범위 설정:
  1) <도구 호출> — <목적·예상 결과>
  2) <도구 호출> — <목적·예상 결과>

Phase 2 — 정량 분석 (fetch_all=True 의무):
  3) <도구 호출> — <목적>
  ...

Phase 3 — 심층·교차 분석:
  N) <도구 호출> — <교차 비교 또는 인사이트 도출>

【핵심 비즈니스 프레임워크】
- 어떤 프레임워크 적용 (시장 진출 / 협력 후보 / 가치사슬 / R&D 효율 비교 등)
- 최종 답변에 포함될 표·순위·KPI 종류

【답변 구조 가이드】
- 🎯 분석 요약 / 📊 핵심 데이터 / 🔍 심층 분석 / 💼 비즈니스 권고 / ⚠️ 리스크 / 💡 추가 조사

═══════════════════════════════════════════════════════════════════════
【중요】 사용자에게 노출되지만 분석가에게는 작업 지시문입니다.
정중한 인사·서론 금지. 곧바로 분석 계획만 작성하세요.
한국어로 작성하되 도구명은 영문 그대로 사용 가능.
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

    # Claude 모델 — 깊은 분석 위해 max_tokens 확대
    model = ChatAnthropic(
        model=model_name,
        api_key=anthropic_key,
        temperature=0.2,
        max_tokens=16384,
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
