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
1. **5~10회 도구 호출이 표준** — 1~2회로 끝내지 말되, 15회 이상 가지 말 것.
   너무 많이 호출하면 시스템이 자동 중단된다.

2. **반드시 양 데이터 소스 활용**:
   - 분야·기관·기술 관련 질문 → NTIS(정부 R&D) + ScienceON(학술/특허) 모두 호출
   - 한쪽만 호출하면 그림이 절반만 보인다.

3. **정량 분석은 `fetch_all=True` — 단 1회만 신중하게**:
   - 최종 합산·순위가 필요한 핵심 쿼리에 **딱 1번**만 사용
   - 나머지는 `rows=10~30`으로 빠르게 탐색
   - 연도별 시계열은 fetch_all 없이 `rows=5`로 카운트만 비교
   - 모든 호출에 fetch_all=True 적용하면 즉시 중단됨

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
【토큰 예산 — Context Overflow 방지】
═══════════════════════════════════════════════════════════════════════
- 누적 도구 응답이 200K 토큰을 넘으면 분석이 즉시 중단된다.
- **권장 호출 패턴**:
  1) 탐색 단계 — `rows=10~30`로 폭넓게 스캔 (4~6회)
  2) 심층 단계 — 후보 기관·인물 N개에 대해 좁은 쿼리 (3~5회)
  3) 정량 단계 — `fetch_all=True`는 최종 합산용 1~2회만
- 도구 응답이 12,000자를 넘으면 자동 truncate되며 메시지가 표시된다.
  이때는 검색어를 더 좁히거나 다른 도구로 집계 정보를 얻는다.
- 같은 쿼리 반복 호출 금지 — 이미 받은 결과를 재활용한다.

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

📚 **자료 출처** (필수)
   - 답변 마지막에 사용한 데이터 소스를 명시합니다.
   - 형식: "본 분석은 다음 공공 데이터를 활용했습니다:" + 항목 리스트
     · **국가 R&D 정보망** (정부 R&D 과제·예산·기관·트렌드)
     · **학술·특허 데이터베이스** (학술 논문, 특허, 연구자, 동향 보고서)
   - **본문에서 표·수치 옆에 출처를 (괄호)로 짧게 표기**:
     예) "신규 과제 1,195건 (정부 R&D)", "SCI 논문 6편 (학술 DB)"
   - 시스템 이름(NTIS, ScienceON, KISTI)은 절대 노출 금지.
   - 호출한 주요 도구 분류(검색·기관 현황·분류 추천 등)도 간단히 명시.

═══════════════════════════════════════════════════════════════════════
【금지 행동】
═══════════════════════════════════════════════════════════════════════
✗ 도구 1~2회만 호출하고 답변 완료 (이미 1차 자료가 있어도 깊이 부족)
✗ 단순 카운트 나열 (왜·무엇을 의미하는지 해석 없이)
✗ 시스템 이름 (NTIS, ScienceON, KISTI, MCP 등) 답변에 노출
✗ 모든 호출에 fetch_all=True 사용 (컨텍스트 폭주)
✗ 최종 합산을 fetch_all 없이 100건만으로 결론
✗ E4302/E4290 에러 그대로 사용자에게 노출 (우회하거나 NTIS로 대체)
✗ "정보가 부족합니다" "답변할 수 없습니다" — 데이터 한계가 있어도 가능한 범위에서 권고 제시
✗ **`task` 도구로 서브에이전트 위임 금지** — 본 에이전트가 직접 모든 도구를 호출하고 끝까지 작성한다.
✗ "subagent 결과를 기다리며…" 같은 미완성 메시지로 끝내지 말 것 — 반드시 7개 섹션을 모두 채워 마무리.
✗ **검색 결과 0건이라도 절대 포기하지 말 것** — 이미 확보한 데이터로 분석을 작성하고, 빈 결과는 "리스크" 섹션에서 언급한다.
✗ 마지막 응답을 "---", 빈 줄, 짧은 한 줄로 끝내지 말 것 — 반드시 완성된 분석 리포트를 출력한다 (최소 1,500자).

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


_MAX_TOOL_RESULT_CHARS = 12000


def _truncate_tool_result(text: str, tool_name: str) -> str:
    """도구 응답이 너무 길면 토큰 절약을 위해 잘라낸다.

    JSON 응답이면 items[]를 줄이고 truncation 메타를 추가해 JSON 구조 유지.
    파싱 실패 시 단순 문자열 자르기로 폴백.
    """
    if len(text) <= _MAX_TOOL_RESULT_CHARS:
        return text

    # 1) JSON 구조 보존 시도 — items[]가 있으면 길이를 줄여 다시 직렬화
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            items = data.get("items")
            if isinstance(items, list) and items:
                original_len = len(items)
                # 점진 축소: 응답 크기가 한계 이하가 될 때까지 items 절반씩 자름
                keep = max(1, original_len)
                while keep >= 1:
                    candidate = dict(data)
                    candidate["items"] = items[:keep]
                    candidate["_truncated"] = {
                        "original_items": original_len,
                        "returned_items": keep,
                        "reason": f"응답이 {_MAX_TOOL_RESULT_CHARS:,}자를 초과해 items만 잘림. 더 좁은 검색어 권장.",
                    }
                    serialized = json.dumps(candidate, ensure_ascii=False, default=str)
                    if len(serialized) <= _MAX_TOOL_RESULT_CHARS:
                        return serialized
                    keep = keep // 2
                # 단일 item으로도 한계 초과 — 단순 자르기로 폴백
    except (json.JSONDecodeError, TypeError, ValueError):
        pass

    # 2) 폴백: 단일 item이 너무 큰 경우 — 응답을 유효한 JSON으로 감싸서 반환
    #    LLM이 json.loads 후 사용해도 깨지지 않도록.
    head_chars = _MAX_TOOL_RESULT_CHARS - 500  # JSON 래핑 여유
    wrapper = {
        "_truncated": True,
        "original_length": len(text),
        "preserved_length": head_chars,
        "note": "응답이 너무 커서 앞부분만 텍스트로 보존. 더 좁은 검색어 또는 rows를 줄여 재호출 권장.",
        "raw_head": text[:head_chars],
    }
    return json.dumps(wrapper, ensure_ascii=False, default=str)


def _make_tool_callable(tool_name: str, tool_fn: Callable[..., Any]) -> Callable[..., Any]:
    """NTIS MCP 도구를 LangChain Tool에서 호출할 수 있는 async 함수로 wrap."""

    async def _call(**kwargs: Any) -> str:
        clean = {k: v for k, v in kwargs.items() if v is not None and k != "_dummy"}
        try:
            result = tool_fn(**clean)
            if inspect.iscoroutine(result):
                result = await result
            if hasattr(result, "text"):
                text = result.text
            elif isinstance(result, str):
                text = result
            else:
                text = json.dumps(result, ensure_ascii=False, default=str)
            return _truncate_tool_result(text, tool_name)
        except Exception as exc:
            msg = str(exc) or exc.__class__.__name__
            return json.dumps(
                {"error": msg, "tool": tool_name, "hint": "NTIS API 응답 지연 또는 일시 오류. 잠시 뒤 재시도하거나 fetch_all=False로 시도하세요."},
                ensure_ascii=False,
            )

    return _call


def _make_rest_callable(
    gateway_url: str,
    api_key: str,
    tool_name: str,
    timeout: float = 120.0,
) -> Callable[..., Any]:
    """REST 게이트웨이의 POST /api/{tool_name}을 호출하는 async 함수."""
    import httpx  # local import to avoid hard dependency in non-REST mode

    endpoint = f"{gateway_url.rstrip('/')}/api/{tool_name}"
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key

    async def _call(**kwargs: Any) -> str:
        clean = {k: v for k, v in kwargs.items() if v is not None and k != "_dummy"}
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(endpoint, headers=headers, json=clean)
            try:
                data = resp.json()
            except Exception:
                data = {"raw": resp.text[:2000]}
            text = json.dumps(data, ensure_ascii=False, default=str)
            return _truncate_tool_result(text, tool_name)
        except Exception as exc:
            msg = str(exc) or exc.__class__.__name__
            return json.dumps(
                {
                    "error": msg,
                    "tool": tool_name,
                    "endpoint": endpoint,
                    "hint": "REST 게이트웨이 응답 지연/오류. 잠시 뒤 재시도하거나 입력 파라미터를 줄이세요.",
                },
                ensure_ascii=False,
            )

    return _call


async def _build_langchain_tools_rest(
    gateway_url: str,
    api_key: str,
) -> list[StructuredTool]:
    """REST 게이트웨이의 /tools 메타로부터 33개 LangChain StructuredTool을 생성."""
    import httpx

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key

    async with httpx.AsyncClient(timeout=30.0) as client:
        list_resp = await client.get(f"{gateway_url.rstrip('/')}/tools", headers=headers)
        list_resp.raise_for_status()
        tool_list = list_resp.json().get("tools", [])
        # 도구별 상세 메타(파라미터 스키마)는 /tools/{name} 으로 별도 조회
        tools: list[StructuredTool] = []
        for entry in tool_list:
            name = entry["name"]
            meta_resp = await client.get(
                f"{gateway_url.rstrip('/')}/tools/{name}", headers=headers
            )
            meta_resp.raise_for_status()
            meta = meta_resp.json()
            description = (meta.get("description") or "").strip()
            if len(description) > 1024:
                description = description[:1020] + "..."
            parameters = meta.get("parameters") or {}
            args_model = _build_arg_model(name, parameters)
            coroutine = _make_rest_callable(gateway_url, api_key, name)
            tool = StructuredTool.from_function(
                coroutine=coroutine,
                name=name,
                description=description,
                args_schema=args_model,
            )
            tools.append(tool)
    return tools


async def build_langchain_tools() -> list[StructuredTool]:
    """NTIS 도구를 LangChain StructuredTool로 변환.

    환경변수 `NTIS_GATEWAY_URL`이 설정되면 REST 게이트웨이 호출 모드로 동작.
    그렇지 않으면 기존 in-process(mcp_ntis 직접 import) 모드.
    """
    gateway_url = os.getenv("NTIS_GATEWAY_URL", "").strip()
    if gateway_url:
        api_key = os.getenv("NTIS_GATEWAY_API_KEY", "").strip()
        return await _build_langchain_tools_rest(gateway_url, api_key)

    # in-process 모드 (기존)
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


async def run_agent_collect(agent: Any, user_message: str) -> dict[str, Any]:
    """ainvoke로 한 번에 받아 모든 step + final을 dict로 반환.

    스트리밍의 메시지 누락 문제를 회피하기 위한 안정 처리.
    recursion_limit으로 무한 루프 방지 (기본 25 → 60).
    """
    inputs = {"messages": [{"role": "user", "content": user_message}]}
    config = {"recursion_limit": 60}
    try:
        result = await agent.ainvoke(inputs, config=config)
    except Exception as exc:
        msg = str(exc)
        if "GraphRecursionError" in msg or "recursion" in msg.lower():
            return {
                "steps": [{
                    "type": "ai_text",
                    "content": "⚠️ 분석이 60단계를 넘어 자동 중단되었습니다. 질문을 더 좁혀서 다시 시도해주세요.",
                }],
                "final": "⚠️ 분석이 60단계를 넘어 자동 중단되었습니다. 질문 범위를 좁혀 다시 시도해주세요. (예: '차세대 산업 3개' → '바이오 한 분야의 정부 투자 현황')",
            }
        raise
    messages = result.get("messages") or []
    steps: list[dict[str, Any]] = []
    final_text = ""
    for msg in messages:
        kind = getattr(msg, "type", None) or msg.__class__.__name__.lower()
        if kind in ("human", "humanmessage"):
            continue  # 사용자 메시지 스킵
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
                            steps.append({
                                "type": "thinking",
                                "content": block.get("thinking", ""),
                            })
                    elif isinstance(block, str):
                        text += block
            if text:
                steps.append({"type": "ai_text", "content": text})
                final_text = text  # 가장 마지막 ai_text가 최종 답변
            for tc in (getattr(msg, "tool_calls", None) or []):
                steps.append({
                    "type": "tool_call",
                    "content": {
                        "name": tc.get("name") if isinstance(tc, dict) else tc.name,
                        "args": tc.get("args") if isinstance(tc, dict) else tc.args,
                        "id": tc.get("id") if isinstance(tc, dict) else getattr(tc, "id", ""),
                    },
                })
        elif kind in ("tool", "toolmessage"):
            tool_name = getattr(msg, "name", "") or ""
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            steps.append({
                "type": "tool_result",
                "content": {"name": tool_name, "content": content},
            })
    # 마지막 ai_text가 너무 짧으면 (e.g. "---", 빈 줄) 가장 긴 ai_text로 대체
    ai_texts = [s["content"] for s in steps if s["type"] == "ai_text"]
    if final_text and len(final_text.strip()) < 100 and ai_texts:
        longest = max(ai_texts, key=len)
        if len(longest) > len(final_text):
            final_text = longest

    intermediate = [s for s in steps if not (s["type"] == "ai_text" and s["content"] == final_text)]
    return {"steps": intermediate, "final": final_text}
