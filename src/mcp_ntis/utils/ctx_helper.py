"""NTIS MCP 응답 변환·컨텍스트 헬퍼.

mcp-opendart의 ctx_helper 패턴을 차용하여:
- API 응답의 약어 필드를 human-readable한 이름으로 변환
- 금액 문자열을 숫자형으로 변환
- 비어있거나 'null' 문자열을 정규화
- with_context() 로 lifespan/global ctx 양방향 fallback
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, Dict, List, Optional

from mcp.types import TextContent

logger = logging.getLogger("mcp-ntis")


# ---------------------------------------------------------------------------
# JSON TextContent 변환
# ---------------------------------------------------------------------------

def as_json_text(payload: Any) -> TextContent:
    """다양한 타입의 데이터를 JSON TextContent로 변환."""
    if isinstance(payload, (dict, list)):
        txt = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    elif isinstance(payload, str):
        try:
            json.loads(payload)
            txt = payload
        except json.JSONDecodeError:
            txt = json.dumps({"raw": payload}, ensure_ascii=False)
    else:
        def _default(o: Any) -> Any:
            if isinstance(o, bytes):
                try:
                    return o.decode("utf-8")
                except UnicodeDecodeError:
                    return f"<bytes: {len(o)} bytes>"
            try:
                return o.model_dump()
            except Exception:
                return str(o)
        txt = json.dumps(payload, ensure_ascii=False, default=_default, separators=(",", ":"))
    return TextContent(type="text", text=txt)


def error_text(msg: str) -> TextContent:
    return as_json_text({"error": msg})


# ---------------------------------------------------------------------------
# 응답 키 한글/영문 매핑
# 우리 client.py가 이미 휴먼리더블 키를 쓰지만, 일부 NTIS 원본 약어가
# 응답에 그대로 노출되는 경우가 있어 안전망으로 변환한다.
# ---------------------------------------------------------------------------

KEY_MAPPING: Dict[str, str] = {
    # NTIS 검색 응답
    "rcept_no": "receipt_number",
    "ProjectNumber": "project_id",
    "ProjectYear": "project_year",
    "ResultID": "result_id",
    "ResultTitle": "result_title",
    "BudgetProject": "budget_project",
    "BudgetProjectNumber": "budget_project_id",
    "MinistryName": "ministry_name",
    "PerformAgency": "perform_agency",
    "PerformAgent": "perform_agent_type",
    "ResearchAgency": "research_agency",
    # 위탁/공동연구 NTIS 원본명
    "CommissionNumber": "commission_number",
    "CommissionType": "commission_type",
    "CommissionLeadAgency": "commission_lead_agency",
    "ConsignmentProjectResearchFunds": "consignment_project_funds_krw",
    "CollaborativeResearchFunds": "collaborative_research_funds_krw",
    # 분류 응답
    "LCLS_CD": "large_code",
    "LCLS_NM": "large_name",
    "MCLS_CD": "medium_code",
    "MCLS_NM": "medium_name",
    "SCLS_CD": "small_code",
    "SCLS_NM": "small_name",
    "SCLS_WEIGHT": "accuracy",
    "MCLS_WEIGHT": "accuracy",
    "DCLS_CD": "disease_code",
    "DCLS_NM": "disease_name",
    "DCLS_WEIGHT": "accuracy",
    # 이슈 응답
    "topicNo": "issue_id",
    "topicNm": "issue_name",
    "extrDt": "extract_date",
    "rltdPjtCnt": "related_project_count",
    "rltdKywdList": "related_keywords",
    # 기관 응답
    "reqOrgNm": "org_name",
    "reqOrgBno": "org_bno",
    "orgName": "org_name",
    "numOfList": "number_of_matches",
    "rndStatusList": "rnd_status",
    "pjtCnt": "project_count",
    "rndBudget": "rnd_budget_krw",
    "govBudget": "gov_budget_krw",
    "paperCnt": "paper_count",
    "patentCnt": "patent_count",
    "reportCnt": "report_count",
    # ConnectionContent JSON 원본 키
    "PJT_ID": "project_id",
    "KOR_PJT_NM": "project_title_kor",
    "ENG_PJT_NM": "project_title_eng",
    "RSCH_AGNC_NM": "research_agency_name",
    "PJT_YR": "project_year",
    "similarity_score": "similarity_score",
}


# 금액으로 강제 정수 변환할 필드 (값이 문자열 숫자인 경우)
AMOUNT_FIELDS = {
    "government_funds_krw",
    "total_funds_krw",
    "consignment_project_funds_krw",
    "collaborative_research_funds_krw",
    "price_krw",
    "rnd_budget_krw",
    "gov_budget_krw",
}


def _convert_amount(value: Any) -> Any:
    """문자열 금액을 int로 변환. 실패 시 원본 반환."""
    if isinstance(value, (int, float)):
        return value
    if not isinstance(value, str):
        return value
    cleaned = value.replace(",", "").replace(" ", "").strip()
    if not cleaned or cleaned in {"-", "null", "NULL", "None"}:
        return 0
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = "-" + cleaned[1:-1]
    try:
        return float(cleaned) if "." in cleaned else int(cleaned)
    except (ValueError, TypeError):
        return value


def _normalize_value(value: Any) -> Any:
    """문자열 'null'/'NULL'을 빈 문자열로, 좌우 공백 제거."""
    if isinstance(value, str):
        stripped = value.strip()
        if stripped in {"null", "NULL", "None", "none"}:
            return ""
        return stripped
    return value


def transform_response(data: Any) -> Any:
    """딕셔너리 키를 휴먼리더블로 변환 + 금액 필드 숫자화 + null 정규화.

    이미 변환된 데이터(LLM이 이해하기 쉬운 키)는 그대로 통과.
    """
    if isinstance(data, dict):
        out: Dict[str, Any] = {}
        for k, v in data.items():
            new_key = KEY_MAPPING.get(k, k)
            new_value = transform_response(v)
            if new_key in AMOUNT_FIELDS:
                new_value = _convert_amount(new_value)
            else:
                new_value = _normalize_value(new_value)
            out[new_key] = new_value
        return out
    if isinstance(data, list):
        return [transform_response(item) for item in data]
    return _normalize_value(data)


# ---------------------------------------------------------------------------
# Context fallback 헬퍼 — 일관된 API 호출 패턴
# ---------------------------------------------------------------------------


def _get_lifespan_context(ctx: Any) -> Optional[Any]:
    """MCP context → NTISContext 추출 (lifespan)."""
    if ctx is None:
        return None
    try:
        if hasattr(ctx, "request_context"):
            req = ctx.request_context
            if hasattr(req, "lifespan_context"):
                lc = req.lifespan_context
                if isinstance(lc, dict):
                    for key in ("app_lifespan_context", "lifespan_context", "context", "ctx"):
                        if key in lc:
                            return lc[key]
                    if "client" in lc:
                        return lc
                return lc
    except Exception as exc:
        logger.debug(f"context 추출 실패: {exc}")
    return None


async def with_context_async(
    ctx: Optional[Any],
    tool_name: str,
    fn: Callable[[Any], Any],
    transform: bool = True,
) -> Any:
    """비동기 도구 본체를 fn에 람다로 감싸고, lifespan ctx 우선 + global ctx fallback.

    Args:
        ctx: MCP 호출 시점의 Context (있으면 lifespan 사용)
        tool_name: 로깅용
        fn: `lambda context: await client.search_projects(...)` 형태의 async 작업
        transform: True 시 응답을 transform_response()로 정규화
    """
    logger.info(f"📌 Tool 호출: {tool_name}")

    ntis_ctx = _get_lifespan_context(ctx)
    if ntis_ctx is None:
        # 전역 컨텍스트 fallback
        try:
            from mcp_ntis.server import get_global_context  # type: ignore[import-untyped]
            ntis_ctx = get_global_context()
        except Exception as exc:
            logger.error(f"전역 컨텍스트 접근 실패: {exc}")

    if ntis_ctx is None:
        raise ValueError("NTIS context not available. Lifespan not initialized.")

    result = await fn(ntis_ctx)
    return transform_response(result) if transform else result
