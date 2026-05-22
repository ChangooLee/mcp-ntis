import logging
from typing import Annotated, Optional

from mcp.types import TextContent
from pydantic import Field

from mcp_ntis.server import as_json_text, error_text, get_client, mcp

logger = logging.getLogger("mcp-ntis")

_SEARCH_FD_HELP = (
    "검색 필드. 기본 BI=전체 텍스트 검색. "
    "특정 필드 지정: TI=과제명/제목, AU=연구책임자 이름, OG=기관명, KW=키워드, AB=초록. "
    "예) 기관 검색: search_field='OG', query='KAIST' / "
    "책임자 검색: search_field='AU', query='홍길동' / "
    "제목 검색: search_field='TI', query='양자컴퓨터'"
)
_SORT_HELP = "정렬: RANK/DESC=관련도순(기본), DATE/DESC=최신순, DATE/ASC=오래된순"
_QUERY_HELP = (
    "검색어. AND=띄어쓰기, OR=|, NOT=!, 정확한구문=\"...\". "
    "예: '나노 배터리'→나노AND배터리 / '나노|배터리'→나노OR배터리 / '\"전고체 배터리\"'→정확한구문"
)
_ADD_QUERY_HELP = (
    "추가 필터 조건 (선택). 여러 조건은 &로 연결. "
    "연도: PY=2023/SAME(2023년만), PY=2020/MORE&2023/UNDER(2020~2023). "
    "수행기관: OG=한국전자통신연구원 (정확 일치). "
    "연구책임자: AU=홍길동. 키워드: KW=양자컴퓨터. "
    "과제번호 앞자리: CN=1711(과기부), CN=1450(산업부). "
    "원문있음: DBT=PAT(특허원문), DBT=PAP(논문원문). "
    "예: search_field='BI', query='인공지능', add_query='OG=한국과학기술원&PY=2024/SAME' "
    "→ KAIST 2024년 인공지능 과제. "
    "팁: BI 검색 + add_query 조합이 가장 정밀함."
)

_FETCH_ALL_HELP = (
    "전체 페이지 자동 순회 모드. 정확한 집계/통계 분석에 필수. "
    "True면 모든 페이지를 가져와서 items에 합쳐 반환. "
    "주의: 결과가 많으면(예: 1000건+) 응답 크기 큼 → 단순 조회에는 사용 금지. "
    "기본 False. 통계·연도별 비교·합산 시에만 True 권장."
)
_MAX_FETCH_HELP = "fetch_all=True 시 가져올 최대 건수 (기본 2000). 안전 한도."

_PAGINATION_NOTE = (
    "【페이지네이션 가이드】 단일 호출 최대 100건. "
    "단순 탐색: page_size 작게(기본 10) / "
    "상위 N개 목록: page_size=100 / "
    "**정확한 집계·통계 분석은 반드시 fetch_all=True** (자동 페이지 순회)."
)


@mcp.tool(
    name="search_rnd_projects",
    tags={"검색", "과제", "기초조사"},
    description=(
        "국가R&D 과제를 검색합니다. 도구 중 가장 풍부한 메타데이터 제공.\n"
        "\n"
        "**언제 쓰는가**: 키워드·기관·책임자로 정부 R&D 과제 목록·예산·기간 조회.\n"
        "\n"
        "**입력 패턴**:\n"
        "  - 단순 키워드: query='양자컴퓨터'\n"
        "  - 기관별: query='AI', add_query='OG=한국과학기술원'\n"
        "  - 연도 필터: query='반도체', add_query='PY=2024/SAME'\n"
        "  - 책임자: search_field='AU', query='홍길동'\n"
        "\n"
        "**응답 핵심 키**: id, title, manager, institution, ministry, "
        "government_funds_krw(원 단위), period_start, period_end, keywords, science_class.\n"
        "\n"
        "**페이지네이션 가이드**:\n"
        "  - 단순 조회: 기본값(page_size=10) OK\n"
        "  - 상위 N개 분석: page_size=100\n"
        "  - **정확한 합산·통계**: `fetch_all=True` 필수\n"
        "\n"
        "**다음 단계**:\n"
        "  - 위탁/공동 연구 → `get_consignment_research(project_id=id)`\n"
        "  - 유사 과제 AI 추천 → `get_related_content(content_type='project', content_id=id)`"
    ),
)
async def search_rnd_projects(
    query: Annotated[str, Field(description=_QUERY_HELP)],
    search_field: Annotated[str, Field(description=_SEARCH_FD_HELP)] = "BI",
    add_query: Annotated[str, Field(description=_ADD_QUERY_HELP)] = "",
    sort: Annotated[str, Field(description=_SORT_HELP)] = "RANK/DESC",
    page: Annotated[int, Field(description="페이지 번호 (1부터 시작). fetch_all=True면 무시됨", ge=1)] = 1,
    page_size: Annotated[int, Field(description="페이지당 결과 수 (기본 10, 최대 100). fetch_all=True면 내부적으로 100 강제", ge=1, le=100)] = 10,
    fetch_all: Annotated[bool, Field(
        description=(
            "전체 페이지 자동 순회 모드. 정확한 집계/통계 분석에 필수. "
            "True면 모든 페이지를 가져와서 items에 합쳐 반환. "
            "주의: 결과가 많으면(예: 1000건+) 응답 크기 큼 → 단순 조회에는 사용 금지. "
            "기본 False. 통계 분석·연도별 비교·예산 합산 시에만 True 권장."
        )
    )] = False,
    max_fetch: Annotated[int, Field(
        description="fetch_all=True 시 가져올 최대 건수 (기본 2000). 안전 한도.",
        ge=100, le=10000,
    )] = 2000,
) -> TextContent:
    try:
        client = get_client()
        start = (page - 1) * page_size + 1
        result = await client.search_projects(
            query=query,
            search_field=search_field,
            add_query=add_query,
            sort=sort,
            start=start,
            count=page_size,
            fetch_all=fetch_all,
            max_fetch=max_fetch,
        )
        result["page"] = page
        result["page_size"] = page_size
        result["fetch_all"] = fetch_all
        return as_json_text(result)
    except Exception as e:
        logger.error(f"search_rnd_projects 오류: {e}")
        return error_text(str(e))


@mcp.tool(
    name="search_research_papers",
    tags={"검색", "논문", "성과물"},
    description=(
        "정부 R&D 과제와 연계된 성과 논문(약 19만 건)을 검색합니다.\n"
        "\n"
        "**언제 쓰는가**: 정부 펀딩 과제에서 나온 학술 논문 추적, 학술지·저자별 검색.\n"
        "\n"
        "**커버리지 제한**: 정부 R&D 연계 논문만 — 민간·해외·순수 학문 논문 미포함. "
        "전체 학술 논문은 `search_sci_papers`(학술·특허 DB)·RISS·PubMed 사용.\n"
        "\n"
        "**입력 패턴**:\n"
        "  - 키워드: query='딥러닝'\n"
        "  - 학술지(ISSN): search_field='OG', query='1226-7945'\n"
        "  - 연도: add_query='PY=2024/SAME'\n"
        "\n"
        "**응답 핵심 키**: id, title, authors, journal, sci_type(SCI/SCIE/비SCI), "
        "pub_year, project_id(연계 과제), institution, ministry.\n"
        "\n"
        + _PAGINATION_NOTE
    ),
)
async def search_research_papers(
    query: Annotated[str, Field(description=_QUERY_HELP)],
    search_field: Annotated[str, Field(description="검색 필드: BI=전체(권장), TI=논문명, AU=저자명, OG=ISSN번호, PB=학술지명, KW=키워드, AB=초록")] = "BI",
    add_query: Annotated[str, Field(description="상세검색. 예: PY=2022/SAME, DBT=PAP(원문있음), CN=성과번호")] = "",
    sort: Annotated[str, Field(description=_SORT_HELP)] = "RANK/DESC",
    page: Annotated[int, Field(description="페이지 번호 (fetch_all=True면 무시)", ge=1)] = 1,
    page_size: Annotated[int, Field(description="페이지당 결과 수 (기본 10, 최대 100)", ge=1, le=100)] = 10,
    fetch_all: Annotated[bool, Field(description=_FETCH_ALL_HELP)] = False,
    max_fetch: Annotated[int, Field(description=_MAX_FETCH_HELP, ge=100, le=10000)] = 2000,
) -> TextContent:
    try:
        client = get_client()
        start = (page - 1) * page_size + 1
        result = await client.search_results(
            collection="rpaper",
            query=query,
            search_field=search_field,
            add_query=add_query,
            sort=sort,
            start=start,
            count=page_size,
            fetch_all=fetch_all,
            max_fetch=max_fetch,
        )
        result["page"] = page
        result["page_size"] = page_size
        return as_json_text(result)
    except Exception as e:
        logger.error(f"search_research_papers 오류: {e}")
        return error_text(str(e))


@mcp.tool(
    name="search_patents",
    tags={"검색", "특허", "성과물", "지식재산"},
    description=(
        "정부 R&D 과제와 연계된 성과 특허(약 38만 건)를 검색합니다.\n"
        "\n"
        "**언제 쓰는가**: 정부 펀딩 R&D에서 출원·등록된 특허 추적.\n"
        "\n"
        "**커버리지 제한**: R&D 연계 특허만 — 민간 자체 출원·해외 기업 특허는 미포함. "
        "전체 특허는 KIPRIS·`search_sci_patents` 사용.\n"
        "\n"
        "**입력 패턴**:\n"
        "  - 키워드: query='전고체 배터리'\n"
        "  - 출원인: search_field='AU', query='한국전자통신연구원'\n"
        "  - 연도: add_query='PY=2024/SAME'\n"
        "\n"
        "**응답 핵심 키**: id, title, registrant, regist_country, regist_number, "
        "regist_type(출원/등록), year, project_id(연계 과제), ministry.\n"
        "\n"
        + _PAGINATION_NOTE
    ),
)
async def search_patents(
    query: Annotated[str, Field(description=_QUERY_HELP)],
    search_field: Annotated[str, Field(description="검색 필드: BI=전체(권장), TI=발명명칭, AU=출원등록인, OG=출원등록번호, PB=출원등록국코드")] = "BI",
    add_query: Annotated[str, Field(description="상세검색. 예: PY=2022/SAME, DBT=PAT(원문있음)")] = "",
    sort: Annotated[str, Field(description=_SORT_HELP)] = "RANK/DESC",
    page: Annotated[int, Field(description="페이지 번호 (fetch_all=True면 무시)", ge=1)] = 1,
    page_size: Annotated[int, Field(description="페이지당 결과 수 (기본 10, 최대 100)", ge=1, le=100)] = 10,
    fetch_all: Annotated[bool, Field(description=_FETCH_ALL_HELP)] = False,
    max_fetch: Annotated[int, Field(description=_MAX_FETCH_HELP, ge=100, le=10000)] = 2000,
) -> TextContent:
    try:
        client = get_client()
        start = (page - 1) * page_size + 1
        result = await client.search_results(
            collection="rpatent",
            query=query,
            search_field=search_field,
            add_query=add_query,
            sort=sort,
            start=start,
            count=page_size,
            fetch_all=fetch_all,
            max_fetch=max_fetch,
        )
        result["page"] = page
        result["page_size"] = page_size
        return as_json_text(result)
    except Exception as e:
        logger.error(f"search_patents 오류: {e}")
        return error_text(str(e))


@mcp.tool(
    name="search_research_reports",
    tags={"검색", "보고서", "성과물"},
    description=(
        "정부 R&D 과제의 최종·중간 연구보고서를 검색합니다.\n"
        "\n"
        "**언제 쓰는가**: 논문·특허보다 상세한 연구 전체 내용(방법·결과·한계)이 필요할 때.\n"
        "\n"
        "**입력 패턴**:\n"
        "  - 키워드: query='자율주행'\n"
        "  - 저자: search_field='AU', query='홍길동'\n"
        "  - 연도: add_query='PY=2024/SAME'\n"
        "\n"
        "**응답 핵심 키**: id, title, year, has_fulltext(원문 보유 여부), "
        "project_id, ministry, science_class.\n"
        "\n"
        + _PAGINATION_NOTE
    ),
)
async def search_research_reports(
    query: Annotated[str, Field(description=_QUERY_HELP)],
    search_field: Annotated[str, Field(description="검색 필드: BI=전체, TI=보고서명, AU=저자명, KW=키워드, AB=초록")] = "BI",
    add_query: Annotated[str, Field(description="상세검색. 예: PY=2022/SAME")] = "",
    sort: Annotated[str, Field(description=_SORT_HELP)] = "RANK/DESC",
    page: Annotated[int, Field(description="페이지 번호 (fetch_all=True면 무시)", ge=1)] = 1,
    page_size: Annotated[int, Field(description="페이지당 결과 수 (기본 10, 최대 100)", ge=1, le=100)] = 10,
    fetch_all: Annotated[bool, Field(description=_FETCH_ALL_HELP)] = False,
    max_fetch: Annotated[int, Field(description=_MAX_FETCH_HELP, ge=100, le=10000)] = 2000,
) -> TextContent:
    try:
        client = get_client()
        start = (page - 1) * page_size + 1
        result = await client.search_results(
            collection="rresearch",
            query=query,
            search_field=search_field,
            add_query=add_query,
            sort=sort,
            start=start,
            count=page_size,
            fetch_all=fetch_all,
            max_fetch=max_fetch,
        )
        result["page"] = page
        result["page_size"] = page_size
        return as_json_text(result)
    except Exception as e:
        logger.error(f"search_research_reports 오류: {e}")
        return error_text(str(e))


@mcp.tool(
    name="search_research_equipment",
    tags={"검색", "장비", "인프라"},
    description=(
        "정부 R&D로 도입된 연구 장비(시설·기기)를 검색합니다.\n"
        "\n"
        "**언제 쓰는가**: 공동 활용 가능 장비 발굴, 기관별 인프라 매핑, 연구 협력 후보 식별.\n"
        "\n"
        "**입력 패턴**:\n"
        "  - 키워드: query='전자현미경'\n"
        "  - 보유 기관: search_field='OG', query='한국과학기술원'\n"
        "  - 장비명: search_field='TI', query='SEM'\n"
        "\n"
        "**응답 핵심 키**: id, title, manufacturer, institution, install_location, "
        "price_krw(원 단위), use_scope(공동 활용 여부), use_type.\n"
        "\n"
        + _PAGINATION_NOTE
    ),
)
async def search_research_equipment(
    query: Annotated[str, Field(description=_QUERY_HELP)],
    search_field: Annotated[str, Field(description="검색 필드: BI=전체, TI=장비명, OG=보유기관")] = "BI",
    sort: Annotated[str, Field(description=_SORT_HELP)] = "RANK/DESC",
    page: Annotated[int, Field(description="페이지 번호 (fetch_all=True면 무시)", ge=1)] = 1,
    page_size: Annotated[int, Field(description="페이지당 결과 수 (기본 10, 최대 100)", ge=1, le=100)] = 10,
    fetch_all: Annotated[bool, Field(description=_FETCH_ALL_HELP)] = False,
    max_fetch: Annotated[int, Field(description=_MAX_FETCH_HELP, ge=100, le=10000)] = 2000,
) -> TextContent:
    try:
        client = get_client()
        start = (page - 1) * page_size + 1
        result = await client.search_results(
            collection="requip",
            query=query,
            search_field=search_field,
            sort=sort,
            start=start,
            count=page_size,
            fetch_all=fetch_all,
            max_fetch=max_fetch,
        )
        result["page"] = page
        result["page_size"] = page_size
        return as_json_text(result)
    except Exception as e:
        logger.error(f"search_research_equipment 오류: {e}")
        return error_text(str(e))


@mcp.tool(
    name="search_unified",
    tags={"검색", "통합", "분포파악"},
    description=(
        "여러 R&D 성과 유형(과제·논문·특허·보고서·장비)을 한 번에 검색합니다.\n"
        "\n"
        "**언제 쓰는가**: 주제를 처음 탐색할 때 어느 유형에 데이터가 풍부한지 한눈에 보고 싶을 때. "
        "이미 유형을 알고 있다면 전용 도구(`search_rnd_projects` 등)가 더 상세함.\n"
        "\n"
        "**입력**: \n"
        "  - 단일: collection='project'\n"
        "  - 복수: collection='project,rpaper,rpatent'\n"
        "  - 컬렉션 코드: project/rpaper/rpatent/rresearch/requip\n"
        "\n"
        "**응답 핵심 키**: collection_counts(유형별 매칭 건수), items, total_hits.\n"
        "\n"
        "**다음 단계**: 분포 확인 후 전용 도구로 심층 검색."
    ),
)
async def search_unified(
    query: Annotated[str, Field(description=_QUERY_HELP)],
    collection: Annotated[str, Field(description=(
        "검색 컬렉션 (콤마 구분 복수 지정 가능). "
        "project=과제, rpaper=논문, rpatent=특허, rresearch=보고서, requip=장비. "
        "예: collection='project,rpaper,rpatent' → 과제+논문+특허 동시 검색"
    ))] = "project",
    search_field: Annotated[str, Field(description=_SEARCH_FD_HELP)] = "BI",
    sort: Annotated[str, Field(description=_SORT_HELP)] = "RANK/DESC",
    page: Annotated[int, Field(description="페이지 번호", ge=1)] = 1,
    page_size: Annotated[int, Field(description="페이지당 결과 수 (기본 10, 최대 100)", ge=1, le=100)] = 10,
) -> TextContent:
    try:
        client = get_client()
        start = (page - 1) * page_size + 1
        result = await client.search_unified(
            collection=collection,
            query=query,
            search_field=search_field,
            sort=sort,
            start=start,
            count=page_size,
        )
        result["page"] = page
        result["page_size"] = page_size
        return as_json_text(result)
    except Exception as e:
        logger.error(f"search_unified 오류: {e}")
        return error_text(str(e))
