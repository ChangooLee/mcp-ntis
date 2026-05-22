"""ScienceON 27개 도구.

KISTI ScienceON OpenAPI Gateway의 모든 endpoint를 LangChain/FastMCP 도구로 노출.

도구 카테고리:
  - 논문 (4): search_sci_papers, get_sci_paper, sci_resolver, sci_paper_toc
  - 특허 (3): search_sci_patents, get_sci_patent, search_sci_applicant
  - 보고서 (2): search_sci_reports, get_sci_report
  - 동향 (4): search_sci_trends, get_sci_trend, search_sci_scent, get_sci_scent
  - 연구자/기관/저자 (6): search_sci_researchers/get_sci_researcher, search_sci_organizations/get_sci_organization, search_sci_authors/get_sci_author
  - 지식인프라 (5): search_sci_function, search_sci_service, search_sci_ddc, search_sci_education, recommend_sci_content
"""

from __future__ import annotations

import logging
import threading
from typing import Annotated, Any, Optional

from mcp.types import TextContent
from pydantic import Field

from mcp_ntis.server import as_json_text, error_text, mcp
from mcp_ntis.scienceon.client import ScienceONClient

logger = logging.getLogger("mcp-ntis.scienceon.tools")


# ---------------------------------------------------------------------------
# 클라이언트 싱글톤 (lazy init)
# ---------------------------------------------------------------------------


_client: Optional[ScienceONClient] = None
_lock = threading.Lock()


def _get_client() -> ScienceONClient:
    global _client
    with _lock:
        if _client is None:
            _client = ScienceONClient()
        return _client


# ---------------------------------------------------------------------------
# 공통 도구 헬퍼
# ---------------------------------------------------------------------------


_SEARCH_QUERY_HELP = (
    "검색 조건 dict (예: {'BI': '양자컴퓨터'}). "
    "BI=전체본문, TI=제목, AU=저자, AB=초록, KW=키워드, PY=발행년 등."
)
_TARGET_NOTE = (
    "ScienceON API target 코드는 도구마다 고정. 결과는 XML(MetaData/recordList)."
)


async def _do_search(
    target: str, query: dict[str, Any], cur_page: int, row_count: int,
    extra: Optional[dict[str, Any]] = None,
) -> TextContent:
    try:
        text = await _get_client().search(target, query, cur_page=cur_page, row_count=row_count, extra=extra)
        return as_json_text({"target": target, "raw_xml": text})
    except Exception as exc:
        logger.error(f"search({target}) 오류: {exc}")
        return error_text(str(exc))


async def _do_browse(target: str, cn: str, extra: Optional[dict[str, Any]] = None) -> TextContent:
    try:
        text = await _get_client().browse(target, cn=cn, extra=extra)
        return as_json_text({"target": target, "cn": cn, "raw_xml": text})
    except Exception as exc:
        logger.error(f"browse({target}/{cn}) 오류: {exc}")
        return error_text(str(exc))


# =========================================================================
# 1. 논문 (ARTI)
# =========================================================================


@mcp.tool(
    name="search_sci_papers",
    tags={"ScienceON", "논문", "검색"},
    description=(
        "ScienceON 논문 검색. 국가 R&D 연계 여부 무관하게 KISTI가 수집한 학술 논문 전체 대상. "
        "필드: BI=전체, TI=제목, AU=저자, AB=초록, KW=키워드, PY=발행년 등. "
        "응답은 XML 형식의 MetaData/recordList."
    ),
)
async def search_sci_papers(
    search_query: Annotated[dict[str, Any], Field(description=_SEARCH_QUERY_HELP)] = {"BI": "AI"},
    cur_page: Annotated[int, Field(description="페이지 번호 (1부터)", ge=1)] = 1,
    row_count: Annotated[int, Field(description="페이지당 결과 수", ge=1, le=100)] = 10,
) -> TextContent:
    return await _do_search("ARTI", search_query, cur_page, row_count)


@mcp.tool(
    name="get_sci_paper",
    tags={"ScienceON", "논문", "상세"},
    description="ScienceON 논문 상세조회. search_sci_papers 결과의 CN(논문제어번호)를 입력.",
)
async def get_sci_paper(
    cn: Annotated[str, Field(description="논문 CN (예: 'JAKO200411922932805')")],
) -> TextContent:
    return await _do_browse("ARTI", cn)


@mcp.tool(
    name="sci_resolver",
    tags={"ScienceON", "논문", "링크리졸버"},
    description=(
        "ScienceON Link Resolver. 논문 제목으로 KISTI 등 외부 DB의 원문 링크를 찾는다. "
        "예: 영문 논문 제목 입력 → KISTI 소장 여부, NDSL 링크 등 반환."
    ),
)
async def sci_resolver(
    title: Annotated[str, Field(description="논문 제목 (전체 또는 일부)")],
) -> TextContent:
    try:
        text = await _get_client()._call(
            {"action": "search", "target": "RESOLVER", "atitle": title}
        )
        return as_json_text({"target": "RESOLVER", "raw_xml": text})
    except Exception as exc:
        return error_text(str(exc))


@mcp.tool(
    name="sci_paper_toc",
    tags={"ScienceON", "논문", "권호"},
    description=(
        "ScienceON 권호 TOC. 저널 CN과 권번호를 입력하면 해당 권의 목차(논문 리스트)를 반환. "
        "ScienceON 검색 결과의 저널제어번호(JournalId)와 권번호(VolNo1)를 사용."
    ),
)
async def sci_paper_toc(
    cn: Annotated[str, Field(description="저널 CN (예: 'NJOU00023797')")],
    vol_no: Annotated[str, Field(description="권번호 (예: '3')")],
) -> TextContent:
    try:
        text = await _get_client()._call(
            {"action": "search", "target": "VOLUME", "cn": cn, "volno": vol_no}
        )
        return as_json_text({"target": "VOLUME", "raw_xml": text})
    except Exception as exc:
        return error_text(str(exc))


# =========================================================================
# 2. 특허 (PATENT)
# =========================================================================


@mcp.tool(
    name="search_sci_patents",
    tags={"ScienceON", "특허", "검색"},
    description="ScienceON 특허 검색. searchQuery 필드: BI/TI/AU/AB/KW/PY 등.",
)
async def search_sci_patents(
    search_query: Annotated[dict[str, Any], Field(description=_SEARCH_QUERY_HELP)] = {"BI": "battery"},
    cur_page: Annotated[int, Field(description="페이지 번호", ge=1)] = 1,
    row_count: Annotated[int, Field(description="페이지당 결과 수", ge=1, le=100)] = 10,
) -> TextContent:
    return await _do_search("PATENT", search_query, cur_page, row_count)


@mcp.tool(
    name="get_sci_patent",
    tags={"ScienceON", "특허", "상세"},
    description="ScienceON 특허 상세조회. 특허 CN을 입력 (예: 'USP1977034010353').",
)
async def get_sci_patent(
    cn: Annotated[str, Field(description="특허 CN")],
) -> TextContent:
    return await _do_browse("PATENT", cn)


@mcp.tool(
    name="search_sci_applicant",
    tags={"ScienceON", "특허", "출원인"},
    description="ScienceON 특허 출원인 검색. TI 필드로 출원인 이름 검색.",
)
async def search_sci_applicant(
    search_query: Annotated[dict[str, Any], Field(description="검색 조건 (예: {'TI': 'KAIST'})")] = {"TI": "KAIST"},
    cur_page: Annotated[int, Field(description="페이지 번호", ge=1)] = 1,
    row_count: Annotated[int, Field(description="페이지당 결과 수", ge=1, le=100)] = 10,
) -> TextContent:
    return await _do_search("APPLICANT", search_query, cur_page, row_count)


# =========================================================================
# 3. 보고서 (REPORT)
# =========================================================================


@mcp.tool(
    name="search_sci_reports",
    tags={"ScienceON", "보고서", "검색"},
    description="ScienceON 연구보고서 검색. NDSL의 R&D 보고서 + KISTI 수집 분 포함.",
)
async def search_sci_reports(
    search_query: Annotated[dict[str, Any], Field(description=_SEARCH_QUERY_HELP)] = {"BI": "AI"},
    cur_page: Annotated[int, Field(description="페이지 번호", ge=1)] = 1,
    row_count: Annotated[int, Field(description="페이지당 결과 수", ge=1, le=100)] = 10,
) -> TextContent:
    return await _do_search("REPORT", search_query, cur_page, row_count)


@mcp.tool(
    name="get_sci_report",
    tags={"ScienceON", "보고서", "상세"},
    description="ScienceON 보고서 상세조회 (예: 'TRKO202000003399').",
)
async def get_sci_report(
    cn: Annotated[str, Field(description="보고서 CN")],
) -> TextContent:
    return await _do_browse("REPORT", cn)


# =========================================================================
# 4. 동향 (ATT) — 산업/기술 동향 분석 보고서
# =========================================================================


@mcp.tool(
    name="search_sci_trends",
    tags={"ScienceON", "동향", "검색"},
    description=(
        "ScienceON 산업기술 동향 분석 보고서 검색. "
        "NTIS의 search_rnd_issues와 다른 데이터 — KISTI가 직접 큐레이션한 산업 동향 보고서."
    ),
)
async def search_sci_trends(
    search_query: Annotated[dict[str, Any], Field(description=_SEARCH_QUERY_HELP)] = {"BI": "AI"},
    cur_page: Annotated[int, Field(description="페이지 번호", ge=1)] = 1,
    row_count: Annotated[int, Field(description="페이지당 결과 수", ge=1, le=100)] = 10,
) -> TextContent:
    return await _do_search("ATT", search_query, cur_page, row_count)


@mcp.tool(
    name="get_sci_trend",
    tags={"ScienceON", "동향", "상세"},
    description="ScienceON 동향 보고서 상세 (예: 'GTB2020005723').",
)
async def get_sci_trend(
    cn: Annotated[str, Field(description="동향 CN")],
) -> TextContent:
    return await _do_browse("ATT", cn)


@mcp.tool(
    name="search_sci_scent",
    tags={"ScienceON", "과학향기", "검색"},
    description="ScienceON 과학향기(과학 콘텐츠) 검색. 일반인 대상 과학 칼럼/뉴스.",
)
async def search_sci_scent(
    search_query: Annotated[dict[str, Any], Field(description=_SEARCH_QUERY_HELP)] = {"PY": "2023"},
    cur_page: Annotated[int, Field(description="페이지 번호", ge=1)] = 1,
    row_count: Annotated[int, Field(description="페이지당 결과 수", ge=1, le=100)] = 10,
) -> TextContent:
    return await _do_search("SCENT", search_query, cur_page, row_count)


@mcp.tool(
    name="get_sci_scent",
    tags={"ScienceON", "과학향기", "상세"},
    description="ScienceON 과학향기 상세 (예: '6092').",
)
async def get_sci_scent(
    cn: Annotated[str, Field(description="과학향기 콘텐츠 CN")],
) -> TextContent:
    return await _do_browse("SCENT", cn)


# =========================================================================
# 5. 연구자·기관·저자
# =========================================================================


@mcp.tool(
    name="search_sci_researchers",
    tags={"ScienceON", "연구자", "검색"},
    description="ScienceON 연구원 검색. BI 필드로 이름·소속 등 광범위 검색.",
)
async def search_sci_researchers(
    search_query: Annotated[dict[str, Any], Field(description=_SEARCH_QUERY_HELP)] = {"BI": "kim"},
    cur_page: Annotated[int, Field(description="페이지 번호", ge=1)] = 1,
    row_count: Annotated[int, Field(description="페이지당 결과 수", ge=1, le=100)] = 10,
) -> TextContent:
    return await _do_search("RESEARCHER", search_query, cur_page, row_count)


@mcp.tool(
    name="get_sci_researcher",
    tags={"ScienceON", "연구자", "상세"},
    description="ScienceON 연구자 상세 (예: '322433').",
)
async def get_sci_researcher(
    cn: Annotated[str, Field(description="연구자 CN")],
) -> TextContent:
    return await _do_browse("RESEARCHER", cn)


@mcp.tool(
    name="search_sci_organizations",
    tags={"ScienceON", "연구기관", "검색"},
    description="ScienceON 연구기관 검색.",
)
async def search_sci_organizations(
    search_query: Annotated[dict[str, Any], Field(description=_SEARCH_QUERY_HELP)] = {"BI": "korea"},
    cur_page: Annotated[int, Field(description="페이지 번호", ge=1)] = 1,
    row_count: Annotated[int, Field(description="페이지당 결과 수", ge=1, le=100)] = 10,
) -> TextContent:
    return await _do_search("ORGAN", search_query, cur_page, row_count)


@mcp.tool(
    name="get_sci_organization",
    tags={"ScienceON", "연구기관", "상세"},
    description="ScienceON 연구기관 상세 (예: '28542').",
)
async def get_sci_organization(
    cn: Annotated[str, Field(description="연구기관 CN")],
) -> TextContent:
    return await _do_browse("ORGAN", cn)


@mcp.tool(
    name="search_sci_authors",
    tags={"ScienceON", "저자", "전거"},
    description="ScienceON 저자 전거 검색 (저자의 표준화된 식별 정보 검색).",
)
async def search_sci_authors(
    search_query: Annotated[dict[str, Any], Field(description=_SEARCH_QUERY_HELP)] = {"BI": "kim"},
    cur_page: Annotated[int, Field(description="페이지 번호", ge=1)] = 1,
    row_count: Annotated[int, Field(description="페이지당 결과 수", ge=1, le=100)] = 10,
) -> TextContent:
    return await _do_search("AUTHOR", search_query, cur_page, row_count)


@mcp.tool(
    name="get_sci_author",
    tags={"ScienceON", "저자", "상세"},
    description="ScienceON 저자 전거 상세 (예: 'ADPER0000032785').",
)
async def get_sci_author(
    cn: Annotated[str, Field(description="저자 CN")],
) -> TextContent:
    return await _do_browse("AUTHOR", cn)


# =========================================================================
# 6. 지식 인프라
# =========================================================================


@mcp.tool(
    name="search_sci_function",
    tags={"ScienceON", "지식인프라", "기능검색"},
    description="ScienceON 기능 검색. 시스템 내 검색 가능한 기능(콘텐츠 타입) 카탈로그 조회.",
)
async def search_sci_function(
    search_query: Annotated[dict[str, Any], Field(description=_SEARCH_QUERY_HELP)] = {"BI": "논문"},
    cur_page: Annotated[int, Field(description="페이지 번호", ge=1)] = 1,
    row_count: Annotated[int, Field(description="페이지당 결과 수", ge=1, le=100)] = 10,
) -> TextContent:
    return await _do_search("FUNCTION", search_query, cur_page, row_count)


@mcp.tool(
    name="search_sci_service",
    tags={"ScienceON", "지식인프라", "서비스"},
    description="ScienceON 서비스 검색. KISTI가 제공하는 외부 서비스 카탈로그.",
)
async def search_sci_service(
    search_query: Annotated[dict[str, Any], Field(description=_SEARCH_QUERY_HELP)] = {"BI": "논문"},
    cur_page: Annotated[int, Field(description="페이지 번호", ge=1)] = 1,
    row_count: Annotated[int, Field(description="페이지당 결과 수", ge=1, le=100)] = 10,
) -> TextContent:
    return await _do_search("SERVICE", search_query, cur_page, row_count)


@mcp.tool(
    name="search_sci_ddc",
    tags={"ScienceON", "지식인프라", "주제분류"},
    description=(
        "ScienceON DDC(듀이 십진분류) 주제 분류 검색. "
        "다른 검색 도구와 달리 단순 문자열 파라미터(subject)를 사용."
    ),
)
async def search_sci_ddc(
    subject: Annotated[str, Field(description="주제어 (예: 'science', 'medicine')")],
) -> TextContent:
    try:
        text = await _get_client()._call(
            {"action": "search", "target": "DDC", "subject": subject}
        )
        return as_json_text({"target": "DDC", "raw_xml": text})
    except Exception as exc:
        return error_text(str(exc))


@mcp.tool(
    name="search_sci_education",
    tags={"ScienceON", "지식인프라", "교육"},
    description="ScienceON 교육정보(KISTI Academy 강좌) 검색.",
)
async def search_sci_education(
    search_query: Annotated[dict[str, Any], Field(description=_SEARCH_QUERY_HELP)] = {"KW": "AI"},
    cur_page: Annotated[int, Field(description="페이지 번호", ge=1)] = 1,
    row_count: Annotated[int, Field(description="페이지당 결과 수", ge=1, le=100)] = 10,
) -> TextContent:
    return await _do_search("KACADEMY", search_query, cur_page, row_count)


@mcp.tool(
    name="recommend_sci_content",
    tags={"ScienceON", "AI추천"},
    description=(
        "ScienceON 콘텐츠 추천. recom_type/cn/uid 입력. "
        "recom_type='merge' 권장."
    ),
)
async def recommend_sci_content(
    cn: Annotated[str, Field(description="기준 콘텐츠 CN (예: 'NART95824392')")],
    uid: Annotated[str, Field(description="사용자 ID (임의값 가능, 예: 'guest')")] = "guest",
    recom_type: Annotated[str, Field(description="추천 유형: merge / paper / patent / report")] = "merge",
) -> TextContent:
    try:
        text = await _get_client()._call({
            "action": "browse",
            "target": "RECOMMEND",
            "recomType": recom_type,
            "cn": cn,
            "uid": uid,
        })
        return as_json_text({"target": "RECOMMEND", "cn": cn, "raw_xml": text})
    except Exception as exc:
        return error_text(str(exc))
