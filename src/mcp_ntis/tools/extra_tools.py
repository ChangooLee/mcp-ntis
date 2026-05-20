import logging
from typing import Annotated

from mcp.types import TextContent
from pydantic import Field

from mcp_ntis.server import as_json_text, error_text, get_client, mcp

logger = logging.getLogger("mcp-ntis")


@mcp.tool(
    name="get_org_rnd_status",
    tags={"기관분석", "기관현황", "포트폴리오"},
    description=(
        "수행기관의 국가R&D 현황을 조회합니다. "
        "연도별 과제 수, 연구비(정부/민간, 원 단위), 논문·특허·보고서 건수, 대표 한글/영문 키워드, 주요 연구분야 제공. "
        "기관명(org_name) 또는 사업자등록번호(org_bno) 중 하나는 필수. "
        "동명이기관 처리: NTIS API는 부분 일치만 지원하므로 '한국과학기술원' 입력 시 부설기관도 함께 매칭됨. "
        "auto_resolve=true(기본): R&D 데이터가 있는 첫 후보를 자동 선택하고 auto_resolved 메타 포함. "
        "auto_resolve=false: disambiguation=true와 matching_org_names 목록 반환. "
        "정확한 단일 기관 조회는 사업자등록번호(org_bno) 사용 권장."
    ),
)
async def get_org_rnd_status(
    org_name: Annotated[str, Field(description="기관명 (키워드 검색). 예: '한국전자통신연구원', 'KAIST'")] = "",
    org_bno: Annotated[str, Field(description="사업자등록번호 10자리 (xxx-xx-xxxxx 또는 숫자만). 예: '1248602918'")] = "",
    auto_resolve: Annotated[bool, Field(description="동명이기관 자동 해결 (기본 True). False면 disambiguation 후보를 그대로 반환")] = True,
) -> TextContent:
    if not org_name and not org_bno:
        return as_json_text({"error": "org_name 또는 org_bno 중 하나는 필수입니다."})
    try:
        client = get_client()
        result = await client.get_org_rnd_status(org_name=org_name, org_bno=org_bno, auto_resolve=auto_resolve)
        return as_json_text(result)
    except Exception as e:
        logger.error(f"get_org_rnd_status 오류: {e}")
        return error_text(str(e))


@mcp.tool(
    name="search_rnd_issues",
    tags={"트렌드", "이슈", "탐색시작점"},
    description=(
        "NTIS가 선정한 국가R&D 최신 트렌드 이슈를 조회합니다. "
        "이슈별로 연관 R&D 과제 수, 추출 날짜, 연관 키워드를 제공. "
        "query 없이 호출하면 최신 5개 이슈 반환. query 입력 시 해당 키워드 관련 이슈 검색. "
        "결과의 이슈명으로 search_rnd_projects를 재호출하면 연관 과제를 탐색할 수 있음. "
        "사용 시점: 특정 주제를 모를 때 최신 R&D 트렌드 파악 또는 연구 동향 파악."
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
    tags={"용어", "표준화", "사전"},
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
    tags={"분류코드", "계층탐색"},
    description=(
        "과학기술표준분류코드 또는 국가중점기술코드를 조회합니다. "
        "code_type='NTIS001' → 과학기술표준분류코드 (대/중/소 3계층, ~3000개). "
        "code_type='NTIS002' → 국가중점기술코드. "
        "search_code 없이 호출하면 22개 최상위 대분류 목록 반환. "
        "search_code 입력 시 해당 코드의 직접 하위 분류만 반환. "
        "코드 계층 규칙 (NTIS001): "
        "  - 대분류(large): 2자리 영문 (예: 'NA'=수학) "
        "  - 중분류(medium): 4자리 영문+숫자 (예: 'NA01'=대수학) "
        "  - 소분류(small): 6자리 영문+숫자 (예: 'NA0101'=선형대수) "
        "  - 부모 코드 추출: small[:4]=medium, medium[:2]=large "
        "예: search_code='NA' → 수학의 중분류, search_code='NA01' → 대수학의 소분류. "
        "분류 추천(recommend_*) 결과의 코드 검증 및 계층 탐색에 활용."
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
    tags={"AI추천", "유사검색", "확장탐색"},
    description=(
        "특정 R&D 과제와 유사한 과제를 AI 기반으로 추천합니다 (similarity_score 포함). "
        "현재 NTIS ConnectionContent API는 'project'(과제)만 지원. "
        "paper/patent/researchreport 요청 시 명확한 안내 메시지와 빈 결과 반환. "
        "content_id는 search_rnd_projects 결과의 'id' 필드 사용 (예: '1711190129'). "
        "응답에 source_title(원본 과제명), items(유사 과제 목록 with similarity_score) 포함. "
        "사용 패턴: search_rnd_projects → 관심 과제 id 추출 → get_related_content로 유사 과제 확장. "
        "주의: NTIS AI 추천 DB에 등록되지 않은 ID는 exist=false로 빈 결과 반환됨."
    ),
)
async def get_related_content(
    content_type: Annotated[str, Field(description="콘텐츠 유형 (현재 'project'만 지원). paper/patent/researchreport 요청 시 안내 메시지 반환")],
    content_id: Annotated[str, Field(
        description=(
            "콘텐츠 고유번호. "
            "project: search_rnd_projects 결과의 id 필드 (예: '1711190129'). "
            "NTIS AI 추천 DB에 등록된 과제만 결과 반환됨."
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
