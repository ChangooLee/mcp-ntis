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
    "과제번호 앞자리: CN=1711(과기부), CN=1450(산업부). "
    "원문있음: DBT=PAT(특허원문), DBT=PAP(논문원문). "
    "예: 최근 3년 과기부 과제 → add_query='PY=2021/MORE&2023/UNDER&CN=1711'"
)


@mcp.tool(
    name="search_rnd_projects",
    description=(
        "국가R&D 과제를 검색합니다. 15개 도구 중 과제 정보가 가장 풍부: "
        "연구목표·내용·기대효과 요약, 예산(정부·민간), 국가과학기술표준분류(대/중/소), "
        "수행기관, 사업명, 연구기간, 6T분류, 연구개발단계 포함. "
        "결과의 id 필드(예: '1711198200')를 get_consignment_research에 전달하면 "
        "위탁·공동연구 기관과 연구비 배분을 조회할 수 있음. "
        "기관 검색 시 search_field='OG', 책임자 검색 시 search_field='AU' 사용."
    ),
)
async def search_rnd_projects(
    query: Annotated[str, Field(description=_QUERY_HELP)],
    search_field: Annotated[str, Field(description=_SEARCH_FD_HELP)] = "BI",
    add_query: Annotated[str, Field(description=_ADD_QUERY_HELP)] = "",
    sort: Annotated[str, Field(description=_SORT_HELP)] = "RANK/DESC",
    page: Annotated[int, Field(description="페이지 번호 (1부터 시작)", ge=1)] = 1,
    page_size: Annotated[int, Field(description="페이지당 결과 수 (기본 10, 최대 100)", ge=1, le=100)] = 10,
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
        )
        result["page"] = page
        result["page_size"] = page_size
        return as_json_text(result)
    except Exception as e:
        logger.error(f"search_rnd_projects 오류: {e}")
        return error_text(str(e))


@mcp.tool(
    name="search_research_papers",
    description=(
        "국가R&D 논문을 검색합니다. 학술지명(OG), 저자(AU), 키워드(KW), 초록(AB) 등으로 필터링. "
        "SCI/비SCI 구분, 국내/국외 구분, 논문구분(학술지/학술대회) 확인 가능. "
        "결과에는 논문명, 저자, 학술지, 초록, 키워드, 연계과제 포함."
    ),
)
async def search_research_papers(
    query: Annotated[str, Field(description=_QUERY_HELP)],
    search_field: Annotated[str, Field(description="검색 필드: BI=전체, TI=논문명/과제고유번호, AU=저자명, OG=ISSN번호, PB=학술지명, KW=키워드, AB=초록")] = "BI",
    add_query: Annotated[str, Field(description="상세검색. 예: PY=2022/SAME, DBT=PAP(원문있음), CN=성과번호")] = "",
    sort: Annotated[str, Field(description=_SORT_HELP)] = "RANK/DESC",
    page: Annotated[int, Field(description="페이지 번호", ge=1)] = 1,
    page_size: Annotated[int, Field(description="페이지당 결과 수 (기본 10, 최대 100)", ge=1, le=100)] = 10,
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
        )
        result["page"] = page
        result["page_size"] = page_size
        return as_json_text(result)
    except Exception as e:
        logger.error(f"search_research_papers 오류: {e}")
        return error_text(str(e))


@mcp.tool(
    name="search_patents",
    description=(
        "국가R&D 특허를 검색합니다. 출원인(AU), 출원등록국(OG), 발명의 명칭(TI) 등으로 필터링. "
        "국내/해외 특허, 출원/등록 구분, 지적재산권 종류 확인 가능. "
        "결과에는 발명명칭, 출원인, 등록국가, 등록번호, 연계과제 포함."
    ),
)
async def search_patents(
    query: Annotated[str, Field(description=_QUERY_HELP)],
    search_field: Annotated[str, Field(description="검색 필드: BI=전체, TI=출원등록명/과제고유번호, AU=출원등록인, OG=출원등록번호, PB=출원등록국코드")] = "BI",
    add_query: Annotated[str, Field(description="상세검색. 예: PY=2022/SAME, DBT=PAT(원문있음)")] = "",
    sort: Annotated[str, Field(description=_SORT_HELP)] = "RANK/DESC",
    page: Annotated[int, Field(description="페이지 번호", ge=1)] = 1,
    page_size: Annotated[int, Field(description="페이지당 결과 수 (기본 10, 최대 100)", ge=1, le=100)] = 10,
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
        )
        result["page"] = page
        result["page_size"] = page_size
        return as_json_text(result)
    except Exception as e:
        logger.error(f"search_patents 오류: {e}")
        return error_text(str(e))


@mcp.tool(
    name="search_research_reports",
    description=(
        "국가R&D 연구보고서를 검색합니다. 보고서명, 저자, 키워드, 초록 등으로 검색. "
        "원문 보유 여부, 연계과제 정보 확인 가능. "
        "결과에는 보고서명, 저자, 초록, 키워드, 연계과제 포함."
    ),
)
async def search_research_reports(
    query: Annotated[str, Field(description=_QUERY_HELP)],
    search_field: Annotated[str, Field(description="검색 필드: BI=전체, TI=보고서명, AU=저자명, KW=키워드, AB=초록")] = "BI",
    add_query: Annotated[str, Field(description="상세검색. 예: PY=2022/SAME")] = "",
    sort: Annotated[str, Field(description=_SORT_HELP)] = "RANK/DESC",
    page: Annotated[int, Field(description="페이지 번호", ge=1)] = 1,
    page_size: Annotated[int, Field(description="페이지당 결과 수 (기본 10, 최대 100)", ge=1, le=100)] = 10,
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
        )
        result["page"] = page
        result["page_size"] = page_size
        return as_json_text(result)
    except Exception as e:
        logger.error(f"search_research_reports 오류: {e}")
        return error_text(str(e))


@mcp.tool(
    name="search_research_equipment",
    description=(
        "국가R&D 연구시설장비를 검색합니다. 장비명, 보유기관 등으로 검색. "
        "연구에 활용 가능한 장비 현황 파악에 유용. "
        "결과에는 장비명, 보유기관, 연계과제 포함."
    ),
)
async def search_research_equipment(
    query: Annotated[str, Field(description=_QUERY_HELP)],
    search_field: Annotated[str, Field(description="검색 필드: BI=전체, TI=장비명, OG=보유기관")] = "BI",
    sort: Annotated[str, Field(description=_SORT_HELP)] = "RANK/DESC",
    page: Annotated[int, Field(description="페이지 번호", ge=1)] = 1,
    page_size: Annotated[int, Field(description="페이지당 결과 수 (기본 10, 최대 100)", ge=1, le=100)] = 10,
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
        )
        result["page"] = page
        result["page_size"] = page_size
        return as_json_text(result)
    except Exception as e:
        logger.error(f"search_research_equipment 오류: {e}")
        return error_text(str(e))


@mcp.tool(
    name="search_unified",
    description=(
        "한 번의 호출로 여러 R&D 성과 유형을 동시에 검색합니다. "
        "collection 예: 'rpaper,rpatent'=논문+특허 동시, 'project,rpaper,rpatent'=과제+논문+특허. "
        "사용 시점: 주제를 처음 탐색할 때 여러 유형에 걸쳐 어느 분야인지 감잡기 위함. "
        "이미 유형을 알고 있다면 search_rnd_projects/search_research_papers 등 전용 도구가 "
        "더 많은 필드(초록·분류·예산 등)를 반환하므로 전용 도구를 사용할 것."
    ),
)
async def search_unified(
    query: Annotated[str, Field(description=_QUERY_HELP)],
    collection: Annotated[str, Field(description="검색 컬렉션 (콤마 구분 복수 가능). project=과제, rpaper=논문, rpatent=특허, rresearch=보고서, requip=장비. 예: 'rpaper,rpatent'")] = "project",
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
