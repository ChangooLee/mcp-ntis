"""ScienceON 17개 도구 — KISTI ScienceON OpenAPI Gateway 공식 카탈로그.

공식 가이드(`scienceon.kisti.re.kr/apigateway/api/way/service/...`)에 게재된
17개 API와 1:1 매핑. 응답은 XML이지만 parser.py가 정제된 dict로 변환.

카테고리:
  - 논문 (2): search_sci_papers, get_sci_paper
  - 특허 (3): search_sci_patents, get_sci_patent, search_sci_citation_patents
  - 보고서 (2): search_sci_reports, get_sci_report
  - 동향/과학향기 (4): search_sci_trends, get_sci_trend, search_sci_scent, get_sci_scent
  - 연구자/연구기관 (4): search_sci_researchers, get_sci_researcher,
                          search_sci_organizations, get_sci_organization
  - TREND (1): search_sci_infra_trend
  - 금주의 과학기술뉴스 (1): search_sci_tech_news

deprecated (KISTI가 공식 카탈로그에서 제거):
  APPLICANT / AUTHOR / FUNCTION / SERVICE / DDC / KACADEMY / RESOLVER / VOLUME / RECOMMEND.
"""

from __future__ import annotations

import logging
import threading
from typing import Annotated, Any, Optional

from mcp.types import TextContent
from pydantic import Field

from mcp_ntis.server import as_json_text, error_text, mcp
from mcp_ntis.scienceon.client import ScienceONClient
from mcp_ntis.scienceon.parser import parse_scienceon_xml

logger = logging.getLogger("mcp-ntis.scienceon.tools")


# ---------------------------------------------------------------------------
# 클라이언트 싱글톤
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
# 공통 헬퍼 — 검색·상세 호출 후 XML을 정제된 dict로 변환
# ---------------------------------------------------------------------------


_SEARCH_QUERY_HELP = (
    "검색 조건 dict. 도구별 지원 필드가 다름 (E4007 회피 위해 각 도구 description 참조). "
    "공통 필드: BI(전체본문), TI(제목). "
    "ARTI/REPORT: BI/TI/AU(저자)/AB(초록)/KW(키워드)/PY(발행년). "
    "ATT(동향): BI/TI/AU/AB/KW (PY 미지원). "
    "TREND(infra)/RESEARCHER/ORGAN: BI/TI/KW만. "
    "PATENT: BI/TI/PA(출원인)/AN/AD/RN/RD/AB/IN/IC. "
    "SCENT: PY 전용. SNEWS: RD 전용."
)


async def _do_search(
    target: str,
    query: dict[str, Any],
    cur_page: int,
    row_count: int,
    extra: Optional[dict[str, Any]] = None,
) -> TextContent:
    try:
        text = await _get_client().search(
            target, query, cur_page=cur_page, row_count=row_count, extra=extra
        )
        parsed = parse_scienceon_xml(text, target, page=cur_page, page_size=row_count)
        return as_json_text(parsed)
    except Exception as exc:
        logger.error(f"search({target}) 오류: {exc}")
        return error_text(str(exc))


async def _do_browse(
    target: str,
    cn: str,
    extra: Optional[dict[str, Any]] = None,
) -> TextContent:
    try:
        text = await _get_client().browse(target, cn=cn, extra=extra)
        parsed = parse_scienceon_xml(text, target, page=1, page_size=1)
        # 상세조회는 단일 record가 표준
        if parsed.get("items"):
            parsed["item"] = parsed["items"][0]
        parsed["cn"] = cn
        return as_json_text(parsed)
    except Exception as exc:
        logger.error(f"browse({target}/{cn}) 오류: {exc}")
        return error_text(str(exc))


# =========================================================================
# 1. 논문 (ARTI) — 2개
# =========================================================================


@mcp.tool(
    name="search_sci_papers",
    tags={"ScienceON", "논문", "검색"},
    description=(
        "ScienceON 논문 검색. KISTI가 수집한 국내·외 학술 논문 전체 대상. "
        "지원 필드: **BI/TI/AU/AB/KW/PY**. "
        "응답 핵심 키: cn, title, author, journal_name, pub_year, abstract, keywords. "
        "다음 단계: get_sci_paper(cn)로 상세 조회."
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
    description=(
        "ScienceON 논문 상세 조회 (action=browse, target=ARTI). "
        "search_sci_papers 결과의 CN 필드를 그대로 전달."
    ),
)
async def get_sci_paper(
    cn: Annotated[str, Field(description="논문 CN (예: 'JAKO200411922932805', 'NPAP13299514')")],
) -> TextContent:
    return await _do_browse("ARTI", cn)


# =========================================================================
# 2. 특허 (PATENT) — 3개
# =========================================================================


@mcp.tool(
    name="search_sci_patents",
    tags={"ScienceON", "특허", "검색"},
    description=(
        "ScienceON 특허 검색. 국내·해외(US/JP/EP/WO) 특허 통합. "
        "**검색 필드는 특허 전용**: BI(전체), TI(발명명칭), PA(출원인), AN(출원번호), "
        "AD(출원일자 YYYYMMDD), UN(공개번호), UD(공개일자), RN(등록번호), RD(등록일자), "
        "AB(초록), IN(발명자), IC(IPC), CN(문헌번호). "
        "⚠️ PY(발행년)는 지원 안 됨 — 연도 필터는 AD/RD/UD 사용. "
        "응답 핵심: cn, title, applicants, appl_date, ipc, nation, patent_status."
    ),
)
async def search_sci_patents(
    search_query: Annotated[
        dict[str, Any],
        Field(description=(
            "검색 조건. 특허 전용 필드: BI/TI/PA/AN/AD/UN/UD/RN/RD/AB/IN/IC/CN. "
            "예: {'BI':'전고체'}, {'PA':'KAIST'}, {'BI':'AI','AD':'2024'}."
        ))
    ] = {"BI": "battery"},
    cur_page: Annotated[int, Field(description="페이지 번호", ge=1)] = 1,
    row_count: Annotated[int, Field(description="페이지당 결과 수", ge=1, le=100)] = 10,
) -> TextContent:
    return await _do_search("PATENT", search_query, cur_page, row_count)


@mcp.tool(
    name="get_sci_patent",
    tags={"ScienceON", "특허", "상세"},
    description="ScienceON 특허 상세조회 (action=browse, target=PATENT). 특허 CN을 입력.",
)
async def get_sci_patent(
    cn: Annotated[str, Field(description="특허 CN (예: 'USP20240311942597', 'WPA2024A30182496')")],
) -> TextContent:
    return await _do_browse("PATENT", cn)


@mcp.tool(
    name="search_sci_citation_patents",
    tags={"ScienceON", "특허", "인용", "피인용"},
    description=(
        "ScienceON 인용/피인용 특허 조회 (action=citation, target=PATENT). "
        "기준 특허의 인용 관계를 추적해 기술 영향력·후속 출원을 분석. "
        "search_sci_patents로 기준 특허 CN을 먼저 식별한 뒤 호출."
    ),
)
async def search_sci_citation_patents(
    cn: Annotated[str, Field(description="기준 특허 CN")],
    cur_page: Annotated[int, Field(description="페이지 번호", ge=1)] = 1,
    row_count: Annotated[int, Field(description="페이지당 결과 수", ge=1, le=100)] = 10,
) -> TextContent:
    """인용/피인용 특허는 action=citation, target=PATENT, cn 필수."""
    try:
        text = await _get_client()._call({
            "action": "citation",
            "target": "PATENT",
            "cn": cn,
            "curPage": cur_page,
            "rowCount": row_count,
        })
        parsed = parse_scienceon_xml(text, "PATENT_CITATION", page=cur_page, page_size=row_count)
        parsed["base_cn"] = cn
        return as_json_text(parsed)
    except Exception as exc:
        logger.error(f"search_sci_citation_patents({cn}) 오류: {exc}")
        return error_text(str(exc))


# =========================================================================
# 3. 보고서 (REPORT) — 2개
# =========================================================================


@mcp.tool(
    name="search_sci_reports",
    tags={"ScienceON", "보고서", "검색"},
    description=(
        "ScienceON 연구보고서 검색. NDSL의 R&D 최종·중간 보고서. "
        "지원 필드: **BI/TI/AU/AB/KW/PY**. "
        "응답 핵심 키: cn, title, publisher, pub_year, abstract."
    ),
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
    description="ScienceON 보고서 상세조회 (action=browse, target=REPORT).",
)
async def get_sci_report(
    cn: Annotated[str, Field(description="보고서 CN (예: 'TRKO202200009744')")],
) -> TextContent:
    return await _do_browse("REPORT", cn)


# =========================================================================
# 4. 동향·과학향기 (ATT/SCENT) — 4개
# =========================================================================


@mcp.tool(
    name="search_sci_trends",
    tags={"ScienceON", "동향", "검색"},
    description=(
        "ScienceON 동향 분석 보고서 검색 (target=ATT). "
        "KISTI가 큐레이션한 산업·기술 동향 — 정부 R&D 이슈와 별개 데이터. "
        "지원 필드: **BI/TI/AU/AB/KW** (⚠️ PY 미지원). "
        "참고: TREND(infra)는 별도의 검색 도구 search_sci_infra_trend."
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
    description="ScienceON 동향 보고서 상세 (action=browse, target=ATT).",
)
async def get_sci_trend(
    cn: Annotated[str, Field(description="동향 보고서 CN")],
) -> TextContent:
    return await _do_browse("ATT", cn)


@mcp.tool(
    name="search_sci_scent",
    tags={"ScienceON", "과학향기", "검색"},
    description=(
        "ScienceON 과학향기 검색 (target=SCENT). 일반 대중 대상 과학 칼럼·뉴스. "
        "검색 필드는 **PY(발행년도)만 허용** — 예: {'PY': '2024'}. "
        "다른 필드(BI/TI 등) 사용 시 E4007 에러."
    ),
)
async def search_sci_scent(
    search_query: Annotated[
        dict[str, Any],
        Field(description="검색 조건. SCENT는 PY(발행년도)만 지원. 예: {'PY': '2024'}")
    ] = {"PY": "2024"},
    cur_page: Annotated[int, Field(description="페이지 번호", ge=1)] = 1,
    row_count: Annotated[int, Field(description="페이지당 결과 수", ge=1, le=100)] = 10,
) -> TextContent:
    return await _do_search("SCENT", search_query, cur_page, row_count)


@mcp.tool(
    name="get_sci_scent",
    tags={"ScienceON", "과학향기", "상세"},
    description="ScienceON 과학향기 상세 (action=browse, target=SCENT).",
)
async def get_sci_scent(
    cn: Annotated[str, Field(description="과학향기 콘텐츠 CN (예: '6908')")],
) -> TextContent:
    return await _do_browse("SCENT", cn)


# =========================================================================
# 5. 연구자·연구기관 — 4개
# =========================================================================


@mcp.tool(
    name="search_sci_researchers",
    tags={"ScienceON", "연구자", "검색"},
    description=(
        "ScienceON 연구원 검색 (target=RESEARCHER). "
        "지원 필드: **BI/TI**만 (다른 필드는 E4007). "
        "응답 핵심: cn, author_name_kr, author_name_en, author_inst_kr, author_inst_en, "
        "keywords, paper_count, patent_count, report_count."
    ),
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
    description="ScienceON 연구자 상세 (action=browse, target=RESEARCHER).",
)
async def get_sci_researcher(
    cn: Annotated[str, Field(description="연구자 CN")],
) -> TextContent:
    return await _do_browse("RESEARCHER", cn)


@mcp.tool(
    name="search_sci_organizations",
    tags={"ScienceON", "연구기관", "검색"},
    description=(
        "ScienceON 연구기관 검색 (target=ORGAN). "
        "지원 필드: **BI/TI**만 (다른 필드는 E4007). "
        "응답 핵심: cn, org_name_kr, org_name_en, keywords, paper_count, patent_count, report_count."
    ),
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
    description="ScienceON 연구기관 상세 (action=browse, target=ORGAN).",
)
async def get_sci_organization(
    cn: Annotated[str, Field(description="연구기관 CN (예: '90'=한국전자통신연구원)")],
) -> TextContent:
    return await _do_browse("ORGAN", cn)


# =========================================================================
# 6. TREND (지식 인프라 동향) — 1개
# =========================================================================


@mcp.tool(
    name="search_sci_infra_trend",
    tags={"ScienceON", "동향", "지식인프라"},
    description=(
        "ScienceON 인프라 동향 검색 (target=TREND, infra). "
        "ATT 동향과 다른 데이터 — KISTI 지식 인프라 가공 트렌드 콘텐츠. "
        "지원 필드: **BI/TI/KW**만."
    ),
)
async def search_sci_infra_trend(
    search_query: Annotated[dict[str, Any], Field(description=_SEARCH_QUERY_HELP)] = {"BI": "AI"},
    cur_page: Annotated[int, Field(description="페이지 번호", ge=1)] = 1,
    row_count: Annotated[int, Field(description="페이지당 결과 수", ge=1, le=100)] = 10,
) -> TextContent:
    return await _do_search("TREND", search_query, cur_page, row_count)


# =========================================================================
# 7. 금주의 과학기술뉴스 (PTPM) — 1개
# =========================================================================


@mcp.tool(
    name="search_sci_tech_news",
    tags={"ScienceON", "뉴스", "주간"},
    description=(
        "ScienceON 금주의 과학기술뉴스 검색 (target=SNEWS, 가이드 경로 ptpm). "
        "주간 큐레이션된 과학기술 뉴스. **검색 필드는 RD(등록일자)만 허용** — "
        "예: {'RD': '20240301'}. 응답 필드: sj(제목), contents, cdNm(12대 국가전략기술), "
        "orginUrl, registDt(등록일자)."
    ),
)
async def search_sci_tech_news(
    search_query: Annotated[
        dict[str, Any],
        Field(description="검색 조건. SNEWS는 RD(등록일자 YYYYMMDD)만 지원. 예: {'RD': '20240301'}")
    ] = {"RD": "20240301"},
    cur_page: Annotated[int, Field(description="페이지 번호", ge=1)] = 1,
    row_count: Annotated[int, Field(description="페이지당 결과 수", ge=1, le=100)] = 10,
) -> TextContent:
    return await _do_search("SNEWS", search_query, cur_page, row_count)
