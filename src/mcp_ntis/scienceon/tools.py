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

도구 설명 원칙:
  1. 한 줄 요약 (무엇을 하는가)
  2. 언제 쓰는가 (사용 시나리오)
  3. 입력 예시 (실제 값)
  4. 응답에서 사용 가능한 핵심 키
  5. 다음 단계 가이드
  6. 흔한 실수 회피 안내
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
        "국내·외 학술 논문을 검색합니다. KISTI가 수집한 전체 학술 DB(약 60만 건) 대상.\n"
        "\n"
        "**언제 쓰는가**: 특정 키워드·저자·연도의 학술 논문 목록을 얻고 싶을 때.\n"
        "\n"
        "**검색 필드**: BI(전체), TI(제목), AU(저자), AB(초록), KW(키워드), PY(발행년). "
        "예: {'BI':'양자컴퓨터'}, {'TI':'CRISPR','PY':'2024'}.\n"
        "\n"
        "**응답 핵심 키**: cn(논문ID), title, author, journal_name, pub_year, "
        "abstract, keywords, has_fulltext.\n"
        "\n"
        "**다음 단계**: 특정 논문 상세는 `get_sci_paper(cn=...)` 호출."
    ),
)
async def search_sci_papers(
    search_query: Annotated[
        dict[str, Any],
        Field(description=(
            "검색 조건 (dict). 지원 필드: BI/TI/AU/AB/KW/PY. "
            "예: {'BI':'양자컴퓨터'}, {'AU':'홍길동','PY':'2024'}."
        ))
    ] = {"BI": "AI"},
    cur_page: Annotated[int, Field(description="페이지 번호 (1부터 시작)", ge=1)] = 1,
    row_count: Annotated[int, Field(description="페이지당 결과 수 (1~100)", ge=1, le=100)] = 10,
) -> TextContent:
    return await _do_search("ARTI", search_query, cur_page, row_count)


@mcp.tool(
    name="get_sci_paper",
    tags={"ScienceON", "논문", "상세"},
    description=(
        "논문 1건의 전체 정보를 조회합니다 (초록·저널·연도·저자 등 전체 필드).\n"
        "\n"
        "**언제 쓰는가**: `search_sci_papers` 결과에서 특정 논문을 더 자세히 보고 싶을 때.\n"
        "\n"
        "**입력**: cn — 논문ID. 검색 결과의 `cn` 필드를 그대로 전달. "
        "예: 'JAKO202317141070190', 'ART003245282'.\n"
        "\n"
        "**응답**: 단일 `item` dict — title, author, abstract, journal_name, "
        "pub_year, has_fulltext, fulltext_url 등 전체 필드."
    ),
)
async def get_sci_paper(
    cn: Annotated[
        str,
        Field(description="논문 ID. 예: 'JAKO202317141070190', 'ART003245282'.")
    ],
) -> TextContent:
    return await _do_browse("ARTI", cn)


# =========================================================================
# 2. 특허 (PATENT) — 3개
# =========================================================================


@mcp.tool(
    name="search_sci_patents",
    tags={"ScienceON", "특허", "검색"},
    description=(
        "국내·해외(US/JP/EP/WO) 특허를 통합 검색합니다.\n"
        "\n"
        "**언제 쓰는가**: 키워드·출원인·IPC 기준 특허 목록, 출원·등록 일자 필터링.\n"
        "\n"
        "**검색 필드 (특허 전용)**: \n"
        "  - BI(전체), TI(발명명칭), PA(출원인), IN(발명자), AB(초록)\n"
        "  - AN(출원번호), RN(등록번호), CN(문헌번호)\n"
        "  - AD(출원일자 YYYYMMDD), RD(등록일자), UD(공개일자)\n"
        "  - IC(IPC 분류)\n"
        "  - ⚠️ PY(발행년)는 지원 안 됨 → 연도 필터는 AD/RD 사용\n"
        "\n"
        "**입력 예시**: {'BI':'전고체'}, {'PA':'KAIST'}, {'BI':'AI','AD':'20240101'}.\n"
        "\n"
        "**응답 핵심 키**: cn, title, applicants, appl_date, ipc, nation, patent_status.\n"
        "\n"
        "**다음 단계**: 특허 상세 → `get_sci_patent(cn)`. "
        "인용 관계 → `search_sci_citation_patents(cn)`."
    ),
)
async def search_sci_patents(
    search_query: Annotated[
        dict[str, Any],
        Field(description=(
            "검색 조건 (dict). 특허 전용 필드: BI/TI/PA/AN/AD/UN/UD/RN/RD/AB/IN/IC. "
            "예: {'BI':'전고체'}, {'PA':'KAIST'}."
        ))
    ] = {"BI": "battery"},
    cur_page: Annotated[int, Field(description="페이지 번호 (1부터)", ge=1)] = 1,
    row_count: Annotated[int, Field(description="페이지당 결과 수 (1~100)", ge=1, le=100)] = 10,
) -> TextContent:
    return await _do_search("PATENT", search_query, cur_page, row_count)


@mcp.tool(
    name="get_sci_patent",
    tags={"ScienceON", "특허", "상세"},
    description=(
        "특허 1건의 전체 정보를 조회합니다 (청구항·IPC·출원인·국가 등).\n"
        "\n"
        "**언제 쓰는가**: `search_sci_patents` 결과에서 특정 특허를 더 자세히 분석할 때.\n"
        "\n"
        "**입력**: cn — 특허 ID. 예: 'USP20240311942597', 'JPA2019110194154', 'KOR3020040010708'.\n"
        "\n"
        "**응답**: 단일 `item` dict — title, applicants, appl_date, ipc, nation, "
        "patent_status, 청구항 등 전체 필드."
    ),
)
async def get_sci_patent(
    cn: Annotated[
        str,
        Field(description="특허 ID. 예: 'USP20240311942597', 'KOR3020040010708'.")
    ],
) -> TextContent:
    return await _do_browse("PATENT", cn)


@mcp.tool(
    name="search_sci_citation_patents",
    tags={"ScienceON", "특허", "인용", "피인용"},
    description=(
        "특정 특허의 인용/피인용 관계를 조회합니다 (기술 영향력 분석용).\n"
        "\n"
        "**언제 쓰는가**: \n"
        "  - 핵심 특허의 후속 출원·기술 파급력 분석\n"
        "  - 경쟁 기업의 기술 추적 (누가 이 특허를 인용했는가)\n"
        "\n"
        "**입력**: cn — 기준 특허 ID. 먼저 `search_sci_patents`로 ID를 식별.\n"
        "\n"
        "**응답**: 기준 특허를 인용한·인용 당한 특허 목록.\n"
        "\n"
        "**참고**: 인용 데이터가 없는 특허도 많음 (total_count=0이면 인용 기록 없음)."
    ),
)
async def search_sci_citation_patents(
    cn: Annotated[str, Field(description="기준 특허 ID. 예: 'USP20240311942597'.")],
    cur_page: Annotated[int, Field(description="페이지 번호 (1부터)", ge=1)] = 1,
    row_count: Annotated[int, Field(description="페이지당 결과 수 (1~100)", ge=1, le=100)] = 10,
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
        "국가 R&D 최종·중간 연구보고서를 검색합니다 (KISTI 수집).\n"
        "\n"
        "**언제 쓰는가**: 특정 분야의 연구 전체 내용(방법·결과·한계)을 보고 싶을 때. "
        "논문·특허보다 상세함.\n"
        "\n"
        "**검색 필드**: BI/TI/AU/AB/KW/PY. "
        "예: {'BI':'자율주행'}, {'BI':'AI','PY':'2024'}.\n"
        "\n"
        "**응답 핵심 키**: cn, title, publisher, pub_year, abstract.\n"
        "\n"
        "**다음 단계**: 보고서 상세 → `get_sci_report(cn)`."
    ),
)
async def search_sci_reports(
    search_query: Annotated[
        dict[str, Any],
        Field(description=(
            "검색 조건 (dict). 지원 필드: BI/TI/AU/AB/KW/PY. "
            "예: {'BI':'자율주행','PY':'2024'}."
        ))
    ] = {"BI": "AI"},
    cur_page: Annotated[int, Field(description="페이지 번호 (1부터)", ge=1)] = 1,
    row_count: Annotated[int, Field(description="페이지당 결과 수 (1~100)", ge=1, le=100)] = 10,
) -> TextContent:
    return await _do_search("REPORT", search_query, cur_page, row_count)


@mcp.tool(
    name="get_sci_report",
    tags={"ScienceON", "보고서", "상세"},
    description=(
        "연구보고서 1건의 전체 정보를 조회합니다 (목차·요약·발행 기관 등).\n"
        "\n"
        "**언제 쓰는가**: `search_sci_reports` 결과에서 특정 보고서를 더 자세히 볼 때.\n"
        "\n"
        "**입력**: cn — 보고서 ID. 예: 'TRKO202200009744', 'TRKO201800014330'.\n"
        "\n"
        "**응답**: 단일 `item` dict — title, publisher, pub_year, abstract 등."
    ),
)
async def get_sci_report(
    cn: Annotated[str, Field(description="보고서 ID. 예: 'TRKO202200009744'.")],
) -> TextContent:
    return await _do_browse("REPORT", cn)


# =========================================================================
# 4. 동향·과학향기 (ATT/SCENT) — 4개
# =========================================================================


@mcp.tool(
    name="search_sci_trends",
    tags={"ScienceON", "동향", "검색"},
    description=(
        "산업·기술 동향 분석 보고서를 검색합니다 (KISTI 큐레이션).\n"
        "\n"
        "**언제 쓰는가**: 특정 산업 분야의 시장·기술 동향, 글로벌 트렌드 파악.\n"
        "\n"
        "**검색 필드**: BI/TI/AU/AB/KW (⚠️ PY는 미지원). "
        "예: {'BI':'반도체'}, {'KW':'AI'}.\n"
        "\n"
        "**응답 핵심 키**: cn, title, publisher, pub_year, abstract.\n"
        "\n"
        "**다음 단계**: 동향 상세 → `get_sci_trend(cn)`.\n"
        "\n"
        "**참고**: 인프라 동향(별도 도구) → `search_sci_infra_trend`."
    ),
)
async def search_sci_trends(
    search_query: Annotated[
        dict[str, Any],
        Field(description=(
            "검색 조건 (dict). 지원 필드: BI/TI/AU/AB/KW (PY 불가). "
            "예: {'BI':'반도체 동향'}."
        ))
    ] = {"BI": "AI"},
    cur_page: Annotated[int, Field(description="페이지 번호 (1부터)", ge=1)] = 1,
    row_count: Annotated[int, Field(description="페이지당 결과 수 (1~100)", ge=1, le=100)] = 10,
) -> TextContent:
    return await _do_search("ATT", search_query, cur_page, row_count)


@mcp.tool(
    name="get_sci_trend",
    tags={"ScienceON", "동향", "상세"},
    description=(
        "동향 보고서 1건의 전체 본문·메타데이터를 조회합니다.\n"
        "\n"
        "**언제 쓰는가**: `search_sci_trends` 결과의 특정 동향을 더 자세히 볼 때.\n"
        "\n"
        "**입력**: cn — 동향 보고서 ID. 예: 'IWT201811007', 'GTB2020005723'.\n"
        "\n"
        "**응답**: 단일 `item` dict — title, abstract, publisher, pub_year 등."
    ),
)
async def get_sci_trend(
    cn: Annotated[str, Field(description="동향 보고서 ID. 예: 'IWT201811007'.")],
) -> TextContent:
    return await _do_browse("ATT", cn)


@mcp.tool(
    name="search_sci_scent",
    tags={"ScienceON", "과학향기", "검색"},
    description=(
        "과학향기 콘텐츠(일반인 대상 과학 칼럼·뉴스)를 검색합니다.\n"
        "\n"
        "**언제 쓰는가**: 대중 친화적 과학 콘텐츠, 교양 과학 글 검색.\n"
        "\n"
        "**검색 필드**: ⚠️ **PY(발행년도) 한 필드만** 지원 — BI/TI 등은 에러(E4007). "
        "예: {'PY':'2024'}, {'PY':'2023'}.\n"
        "\n"
        "**응답 핵심 키**: cn, title, content, register_date.\n"
        "\n"
        "**다음 단계**: 과학향기 상세 → `get_sci_scent(cn)`."
    ),
)
async def search_sci_scent(
    search_query: Annotated[
        dict[str, Any],
        Field(description=(
            "검색 조건 (dict). PY(발행년도)만 지원. "
            "예: {'PY':'2024'}. 다른 필드는 E4007 에러."
        ))
    ] = {"PY": "2024"},
    cur_page: Annotated[int, Field(description="페이지 번호 (1부터)", ge=1)] = 1,
    row_count: Annotated[int, Field(description="페이지당 결과 수 (1~100)", ge=1, le=100)] = 10,
) -> TextContent:
    return await _do_search("SCENT", search_query, cur_page, row_count)


@mcp.tool(
    name="get_sci_scent",
    tags={"ScienceON", "과학향기", "상세"},
    description=(
        "과학향기 콘텐츠 1건의 전체 본문을 조회합니다.\n"
        "\n"
        "**언제 쓰는가**: `search_sci_scent` 결과에서 특정 콘텐츠 전체 본문이 필요할 때.\n"
        "\n"
        "**입력**: cn — 과학향기 ID. 예: '6863', '6864'.\n"
        "\n"
        "**응답**: 단일 `item` dict — title, content(본문), register_date 등."
    ),
)
async def get_sci_scent(
    cn: Annotated[str, Field(description="과학향기 콘텐츠 ID. 예: '6863'.")],
) -> TextContent:
    return await _do_browse("SCENT", cn)


# =========================================================================
# 5. 연구자·연구기관 — 4개
# =========================================================================


@mcp.tool(
    name="search_sci_researchers",
    tags={"ScienceON", "연구자", "검색"},
    description=(
        "연구자(개인)를 검색합니다. 이름·소속·키워드로 식별.\n"
        "\n"
        "**언제 쓰는가**: 특정 분야 전문가 풀 도출, 영입 후보 검토, 협력자 매핑.\n"
        "\n"
        "**검색 필드**: ⚠️ **BI/TI 두 필드만** 지원 — AU/KW 등은 에러(E4007). "
        "예: {'BI':'deep learning'}, {'BI':'양자컴퓨터'}.\n"
        "\n"
        "**응답 핵심 키**: cn, author_name_kr, author_name_en, author_inst_kr, "
        "author_inst_en, keywords, paper_count, patent_count, report_count.\n"
        "\n"
        "**다음 단계**: 연구자 상세 → `get_sci_researcher(cn)`."
    ),
)
async def search_sci_researchers(
    search_query: Annotated[
        dict[str, Any],
        Field(description=(
            "검색 조건 (dict). BI/TI 만 지원. "
            "예: {'BI':'양자컴퓨터'}, {'TI':'홍길동'}."
        ))
    ] = {"BI": "kim"},
    cur_page: Annotated[int, Field(description="페이지 번호 (1부터)", ge=1)] = 1,
    row_count: Annotated[int, Field(description="페이지당 결과 수 (1~100)", ge=1, le=100)] = 10,
) -> TextContent:
    return await _do_search("RESEARCHER", search_query, cur_page, row_count)


@mcp.tool(
    name="get_sci_researcher",
    tags={"ScienceON", "연구자", "상세"},
    description=(
        "연구자 1명의 상세 정보를 조회합니다 (논문·특허·보고서 누적 카운트 포함).\n"
        "\n"
        "**언제 쓰는가**: 특정 연구자의 학술 활동 규모·전문 분야 정량 평가.\n"
        "\n"
        "**입력**: cn — 연구자 ID. 예: '263087', '132709'.\n"
        "\n"
        "**응답**: 단일 `item` dict — author_name_kr, author_inst_kr, keywords, "
        "paper_count, patent_count, report_count."
    ),
)
async def get_sci_researcher(
    cn: Annotated[str, Field(description="연구자 ID. 예: '263087'.")],
) -> TextContent:
    return await _do_browse("RESEARCHER", cn)


@mcp.tool(
    name="search_sci_organizations",
    tags={"ScienceON", "연구기관", "검색"},
    description=(
        "연구기관(대학·출연연·기업)을 검색합니다.\n"
        "\n"
        "**언제 쓰는가**: 협력 후보 기관 발굴, 분야별 선도 기관 식별, 컨소시엄 구성.\n"
        "\n"
        "**검색 필드**: ⚠️ **BI/TI 두 필드만** 지원. "
        "예: {'BI':'university'}, {'TI':'KAIST'}, {'BI':'Electronics Telecommunications'}.\n"
        "\n"
        "**응답 핵심 키**: cn, org_name_kr, org_name_en, keywords, "
        "paper_count, patent_count, report_count.\n"
        "\n"
        "**다음 단계**: 기관 상세 → `get_sci_organization(cn)`."
    ),
)
async def search_sci_organizations(
    search_query: Annotated[
        dict[str, Any],
        Field(description=(
            "검색 조건 (dict). BI/TI 만 지원. "
            "예: {'BI':'Electronics Telecommunications'} (ETRI 검색)."
        ))
    ] = {"BI": "korea"},
    cur_page: Annotated[int, Field(description="페이지 번호 (1부터)", ge=1)] = 1,
    row_count: Annotated[int, Field(description="페이지당 결과 수 (1~100)", ge=1, le=100)] = 10,
) -> TextContent:
    return await _do_search("ORGAN", search_query, cur_page, row_count)


@mcp.tool(
    name="get_sci_organization",
    tags={"ScienceON", "연구기관", "상세"},
    description=(
        "연구기관 1곳의 R&D 산출 누적(논문·특허·보고서 카운트)을 조회합니다.\n"
        "\n"
        "**언제 쓰는가**: 특정 기관의 학술·특허 활동 규모 정량 평가, 파트너 실사.\n"
        "\n"
        "**입력**: cn — 기관 ID. 예: '90' (한국전자통신연구원).\n"
        "\n"
        "**응답**: 단일 `item` dict — org_name_kr, paper_count, patent_count, report_count, keywords."
    ),
)
async def get_sci_organization(
    cn: Annotated[str, Field(description="기관 ID. 예: '90' (ETRI), '34717'.")],
) -> TextContent:
    return await _do_browse("ORGAN", cn)


# =========================================================================
# 6. TREND (지식 인프라 동향) — 1개
# =========================================================================


@mcp.tool(
    name="search_sci_infra_trend",
    tags={"ScienceON", "동향", "지식인프라"},
    description=(
        "지식 인프라 기반 트렌드 콘텐츠를 검색합니다 (`search_sci_trends`와 다른 데이터).\n"
        "\n"
        "**언제 쓰는가**: KISTI 지식 인프라가 가공한 별도 트렌드 콘텐츠가 필요할 때. "
        "건수가 적은 편(수십~수백건).\n"
        "\n"
        "**검색 필드**: BI/TI/KW 만 지원. "
        "예: {'BI':'AI'}, {'KW':'6G'}.\n"
        "\n"
        "**응답 핵심 키**: cn, title, abstract, pub_year.\n"
        "\n"
        "**참고**: 일반 산업 동향은 `search_sci_trends`(ATT)를 우선 사용."
    ),
)
async def search_sci_infra_trend(
    search_query: Annotated[
        dict[str, Any],
        Field(description=(
            "검색 조건 (dict). BI/TI/KW 만 지원. "
            "예: {'BI':'6G'}, {'KW':'AI'}."
        ))
    ] = {"BI": "AI"},
    cur_page: Annotated[int, Field(description="페이지 번호 (1부터)", ge=1)] = 1,
    row_count: Annotated[int, Field(description="페이지당 결과 수 (1~100)", ge=1, le=100)] = 10,
) -> TextContent:
    return await _do_search("TREND", search_query, cur_page, row_count)


# =========================================================================
# 7. 금주의 과학기술뉴스 (PTPM) — 1개
# =========================================================================


@mcp.tool(
    name="search_sci_tech_news",
    tags={"ScienceON", "뉴스", "주간"},
    description=(
        "금주의 과학기술뉴스(주간 큐레이션 콘텐츠)를 검색합니다.\n"
        "\n"
        "**언제 쓰는가**: 특정 등록일의 과학기술 뉴스 모음, 12대 국가전략기술 분류별 뉴스.\n"
        "\n"
        "**검색 필드**: ⚠️ **RD(등록일자) 한 필드만** 지원 (YYYYMMDD 형식). "
        "예: {'RD':'20231127'}, {'RD':'20240301'}. BI/TI는 E4007 에러.\n"
        "\n"
        "**응답 핵심 키**: order(순서), title, content, strategic_tech_name(12대 국가전략기술), "
        "origin_url, register_date.\n"
        "\n"
        "**참고**: 데이터가 적은 분야 — 등록 일자에 따라 결과 없음 가능."
    ),
)
async def search_sci_tech_news(
    search_query: Annotated[
        dict[str, Any],
        Field(description=(
            "검색 조건 (dict). RD(등록일자 YYYYMMDD)만 지원. "
            "예: {'RD':'20231127'}."
        ))
    ] = {"RD": "20240301"},
    cur_page: Annotated[int, Field(description="페이지 번호 (1부터)", ge=1)] = 1,
    row_count: Annotated[int, Field(description="페이지당 결과 수 (1~100)", ge=1, le=100)] = 10,
) -> TextContent:
    return await _do_search("SNEWS", search_query, cur_page, row_count)
