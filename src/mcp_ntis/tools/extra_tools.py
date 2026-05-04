import logging
from typing import Annotated

from mcp.types import TextContent
from pydantic import Field

from mcp_ntis.server import as_json_text, error_text, get_client, mcp

logger = logging.getLogger("mcp-ntis")


@mcp.tool(
    name="get_org_rnd_status",
    description=(
        "수행기관의 국가R&D 현황을 조회합니다. "
        "연도별 과제 수, 연구비(정부/민간), 논문·특허·보고서 건수, 대표 키워드·연구분야 제공. "
        "기관명(org_name) 또는 사업자등록번호(org_bno) 중 하나는 필수. "
        "특정 기관의 R&D 역량·포트폴리오 분석에 활용."
    ),
)
async def get_org_rnd_status(
    org_name: Annotated[str, Field(description="기관명 (키워드 검색). 예: '한국전자통신연구원', 'KAIST'")] = "",
    org_bno: Annotated[str, Field(description="사업자등록번호 10자리 (xxx-xx-xxxxx 또는 숫자만). 예: '1248602918'")] = "",
) -> TextContent:
    if not org_name and not org_bno:
        return as_json_text({"error": "org_name 또는 org_bno 중 하나는 필수입니다."})
    try:
        client = get_client()
        result = await client.get_org_rnd_status(org_name=org_name, org_bno=org_bno)
        return as_json_text(result)
    except Exception as e:
        logger.error(f"get_org_rnd_status 오류: {e}")
        return error_text(str(e))


@mcp.tool(
    name="search_rnd_issues",
    description=(
        "이슈로 보는 국가R&D를 조회합니다. "
        "과학기술 트렌드 이슈와 연관 R&D 과제 현황 파악에 활용. "
        "query 없이 호출하면 최신 5개 이슈를 반환. "
        "query 입력 시 해당 키워드 관련 이슈 검색. "
        "결과에는 이슈명, 추출일자, 연관 과제 수, 연관 키워드 포함."
    ),
)
async def search_rnd_issues(
    query: Annotated[str, Field(description="검색 키워드 (한글/영문). 빈 값이면 최신 이슈 5개 반환")] = "",
) -> TextContent:
    try:
        client = get_client()
        result = await client.search_rnd_issues(query=query)
        return as_json_text(result)
    except Exception as e:
        logger.error(f"search_rnd_issues 오류: {e}")
        return error_text(str(e))


@mcp.tool(
    name="search_terminology",
    description=(
        "국가R&D 용어사전을 검색합니다. "
        "과학기술 표준 용어의 한글명·영문명·약어·정의·관련어 제공. "
        "연구 보고서 작성 시 표준 용어 확인이나 약어 풀이에 활용. "
        "검색 필드: BI=전체(기본), TI=용어명(한글/영문), AB=약어."
    ),
)
async def search_terminology(
    query: Annotated[str, Field(description="검색어. 예: '나노소재', 'nano', 'AI'")],
    search_field: Annotated[str, Field(description="검색 필드: BI=전체(기본), TI=용어명, AB=약어")] = "BI",
    add_query: Annotated[str, Field(description="상세검색. 예: PY=2020/SAME(등록연도), TI01=한글용어, TI02=영문용어")] = "",
    page: Annotated[int, Field(description="페이지 번호 (1부터)", ge=1)] = 1,
    page_size: Annotated[int, Field(description="페이지당 결과 수 (기본 10, 최대 100)", ge=1, le=100)] = 10,
) -> TextContent:
    try:
        client = get_client()
        start = (page - 1) * page_size + 1
        result = await client.search_terminology(
            query=query,
            search_field=search_field,
            add_query=add_query,
            start=start,
            count=page_size,
        )
        result["page"] = page
        result["page_size"] = page_size
        return as_json_text(result)
    except Exception as e:
        logger.error(f"search_terminology 오류: {e}")
        return error_text(str(e))


@mcp.tool(
    name="get_classification_codes",
    description=(
        "과학기술표준분류코드 또는 국가중점기술코드를 조회합니다. "
        "code_type='NTIS001' → 과학기술표준분류코드 (대/중/소 계층 구조). "
        "code_type='NTIS002' → 국가중점기술코드. "
        "search_code 없이 호출하면 최상위 분류 전체 목록 반환. "
        "search_code 입력 시 해당 코드의 하위 분류 반환. "
        "분류 추천 결과의 코드 검증이나 계층 탐색에 활용."
    ),
)
async def get_classification_codes(
    code_type: Annotated[str, Field(description="코드 유형: 'NTIS001'=과학기술표준분류코드, 'NTIS002'=국가중점기술코드")],
    search_code: Annotated[str, Field(description="조회할 분류 코드 (선택). 예: '060200' → 해당 코드 하위 분류 반환")] = "",
) -> TextContent:
    if code_type not in ("NTIS001", "NTIS002"):
        return as_json_text({"error": "code_type은 'NTIS001' 또는 'NTIS002'여야 합니다."})
    try:
        client = get_client()
        result = await client.get_classification_codes(code_type=code_type, search_code=search_code)
        return as_json_text(result)
    except Exception as e:
        logger.error(f"get_classification_codes 오류: {e}")
        return error_text(str(e))


@mcp.tool(
    name="get_related_content",
    description=(
        "특정 R&D 콘텐츠와 연관된 유사 콘텐츠를 AI 기반으로 추천합니다. "
        "content_type: 'project'=과제, 'paper'=논문, 'patent'=특허, 'researchreport'=보고서. "
        "content_id는 각 콘텐츠의 고유번호 (search_rnd_projects의 id 필드 등). "
        "유사 연구 탐색이나 관련 성과 파악에 활용."
    ),
)
async def get_related_content(
    content_type: Annotated[str, Field(description="콘텐츠 유형: 'project'(과제), 'paper'(논문), 'patent'(특허), 'researchreport'(보고서)")],
    content_id: Annotated[str, Field(
        description=(
            "콘텐츠 고유번호. "
            "project: search_rnd_projects 결과의 id 필드. "
            "paper/patent/researchreport: 각 검색 결과의 id 필드(ResultID). "
            "예: project → '1415140010', paper → 'PAP-2023-001234'"
        )
    )],
) -> TextContent:
    if content_type not in ("project", "paper", "patent", "researchreport"):
        return as_json_text({"error": "content_type은 'project', 'paper', 'patent', 'researchreport' 중 하나여야 합니다."})
    try:
        client = get_client()
        result = await client.get_related_content(content_type=content_type, content_id=content_id)
        return as_json_text(result)
    except Exception as e:
        logger.error(f"get_related_content 오류: {e}")
        return error_text(str(e))
