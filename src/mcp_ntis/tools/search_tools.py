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
        "국가R&D 과제를 검색합니다. 15개 도구 중 과제 정보가 가장 풍부: "
        "연구목표·내용·기대효과 요약, 예산(정부·민간, 원 단위), 국가과학기술표준분류(대/중/소), "
        "수행기관명, 사업명, 연구기간(연도별·총괄), 6T분류, 연구개발단계 포함. "
        "같은 과제의 연도별 중복 레코드는 자동으로 제거되고 최신 연도만 반환됨. "
        "\n\n"
        "【중요: 페이지네이션 사용 가이드】"
        "\n"
        "단일 호출은 최대 100건까지만 반환됩니다. 사용 시나리오별 권장 패턴: "
        "\n"
        " • **단순 조회/탐색** (상위 몇 건만 보면 충분): page_size=10~20, 기본값 OK. "
        "\n"
        " • **목록 분석** (상위 N개 기관·키워드 추출): page_size=100 후 1페이지로 충분. "
        "\n"
        " • **정확한 집계** (총 예산 합산, 분야 통계, 연도별 비교 등 정량 분석): "
        "**반드시 fetch_all=True 사용** — 한 번의 호출로 모든 페이지를 자동 순회. "
        "fetch_all=False로 100건만 보고 정량 분석하면 결과가 부정확 (전체의 일부만 합산). "
        "\n"
        " • **수동 페이지 순회**: page를 1, 2, 3, … 증가시켜 호출. "
        "응답에 total_hits 대비 반환이 적으면 pagination_warning 메타가 자동 안내. "
        "\n\n"
        "결과의 id 필드(예: '1711198200')를 get_consignment_research에 전달하면 "
        "위탁·공동연구 기관과 연구비 배분을 조회 가능. "
        "get_related_content(content_type='project', content_id=id)로 유사 과제 AI 추천 가능. "
        "팁: 기관+키워드 동시 검색은 search_field='BI'와 add_query='OG=기관명' 조합이 가장 정확."
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
        "국가R&D 과제의 성과 논문을 검색합니다. "
        "[커버리지 제한] 정부지원 국가R&D 과제와 연계된 논문만 수록 (~19만 건). "
        "민간기업 자체 연구, 기초학문 논문, 해외 연구는 포함되지 않음. "
        "전체 학술논문 검색이 필요하면 RISS·DBpia·PubMed·Google Scholar 안내. "
        "결과에는 논문명, 저자, 학술지(SCI/SCIE/비SCI 구분), 초록, 키워드, 연계과제(project_id) 포함. "
        "특정 project_id로 연계 논문 역추적은 NTIS 검색 필드로 지원되지 않음 → "
        "키워드/제목 검색 후 결과의 project_id 필드를 클라이언트에서 매칭. "
        "학술지(OG=ISSN), 저자(AU), 키워드(KW), 초록(AB) 등으로 필터링 가능. "
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
        "국가R&D 과제의 성과 특허를 검색합니다. "
        "[커버리지 제한] 정부지원 국가R&D 과제와 연계된 특허만 수록 (~38만 건). "
        "민간기업 자체 특허, 해외 기업 특허, R&D 과제 미연계 특허는 포함되지 않음. "
        "전체 특허 검색이 필요하면 KIPRIS(kipris.or.kr) 또는 특허청 DB 안내. "
        "결과에는 발명명칭, 출원인, 등록국가·번호, 출원/등록 구분, 연계과제 포함. "
        "출원인(AU), 출원등록번호(OG), 발명명칭(TI) 등으로 필터링 가능. "
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
        "국가R&D 과제의 최종·중간 연구보고서를 검색합니다. "
        "논문·특허와 달리 연구 결과 전체를 서술한 보고서로, 개발 방법·실험 결과·한계 등이 포함됨. "
        "결과에는 보고서명, 저자, 초록(요약), 키워드, 원문 보유 여부, 연계과제 포함. "
        "has_fulltext=true인 경우 NTIS에서 원문 열람 가능. "
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
        "국가R&D 연구시설장비를 검색합니다. "
        "장비명(국문/영문), 모델, 제조사, 보유기관, 설치위치, 구매가(원 단위), 구매일자, "
        "활용범위(공동활용허용가능 여부), 장비 특징(상세 설명) 포함. "
        "검색 필드: BI=전체, TI=장비명, OG=보유기관. "
        "공동활용 가능 장비 검색·기관별 인프라 매핑에 유용. "
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
        "한 번의 호출로 여러 R&D 성과 유형을 동시에 검색합니다. "
        "응답에 collection_counts(컬렉션별 매칭 건수)가 포함되어 전체 분포 파악에 유용. "
        "사용 시점: 주제를 처음 탐색할 때 어느 유형에 데이터가 풍부한지 한눈에 보고 싶을 때. "
        "이미 유형을 알고 있다면 전용 도구(search_rnd_projects 등)가 초록·분류·예산 등 더 많은 필드 반환. "
        "[커버리지 참고] 논문/특허는 국가R&D 과제 연계 성과만 수록 (전체 DB의 일부)."
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
