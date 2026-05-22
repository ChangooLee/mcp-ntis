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
        "특정 기관의 정부 R&D 포트폴리오 요약을 조회합니다.\n"
        "\n"
        "**언제 쓰는가**: 협력 후보 기관 실사, 특정 기관의 연도별 R&D 규모·분야 정량 평가.\n"
        "\n"
        "**입력**: org_name(기관명) 또는 org_bno(사업자등록번호 10자리) 중 하나 필수.\n"
        "  - 예: org_name='한국전자통신연구원' / org_name='KAIST' / org_bno='1248602918'\n"
        "\n"
        "**동명이기관 처리**:\n"
        "  - auto_resolve=True(기본): R&D 데이터가 있는 첫 후보 자동 선택\n"
        "  - auto_resolve=False: 후보 목록만 반환 (matching_org_names)\n"
        "  - 정확한 단일 기관: 사업자등록번호(org_bno) 사용 권장\n"
        "\n"
        "**응답 핵심 키**: org_name, year_stats(연도별 과제·예산), keywords_kr, "
        "keywords_en, research_fields."
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
        "정부가 선정한 R&D 최신 트렌드 이슈를 조회합니다.\n"
        "\n"
        "**언제 쓰는가**: 무엇이 핫한지 모를 때 시작점으로 사용. "
        "정책 키워드·연관 과제 수로 정부 우선순위 분야 파악.\n"
        "\n"
        "**입력**: \n"
        "  - query 빈 값: 최신 이슈 5개\n"
        "  - query 입력: 키워드 관련 이슈 (예: query='6G', query='AI 신약')\n"
        "\n"
        "**응답 핵심 키**: id, name(이슈명), date, related_project_count, related_keywords.\n"
        "\n"
        "**다음 단계**: 이슈 키워드로 `search_rnd_projects(query=...)` 호출하여 연관 과제 탐색."
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
        "정부 R&D 표준 용어사전을 검색합니다 (한·영 명칭·약어·정의).\n"
        "\n"
        "**언제 쓰는가**: 표준 용어 확인, 약어 풀이, 보고서 용어 표준화.\n"
        "\n"
        "**입력**: query — 한글·영문 검색어.\n"
        "  - 예: query='인공지능 신약 개발' / query='AI'\n"
        "  - search_field='TI': 용어명만 매칭\n"
        "  - search_field='AB': 약어로 검색\n"
        "\n"
        "**응답 핵심 키**: id, korean(한글명), english(영문명), "
        "standard_class(표준 분류), term_class(용어 등급)."
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
        "과학기술표준분류·국가중점기술의 분류 코드 트리를 조회합니다.\n"
        "\n"
        "**언제 쓰는가**: 분류 추천(`recommend_*`) 결과 코드 검증, 분류 트리 계층 탐색.\n"
        "\n"
        "**입력**:\n"
        "  - code_type='NTIS001': 과학기술표준분류 (대/중/소 3계층, 약 3,000개)\n"
        "  - code_type='NTIS002': 국가중점기술\n"
        "  - search_code 빈 값: 22개 최상위 대분류 반환\n"
        "  - search_code='NA': 'NA(수학)'의 하위 중분류 반환\n"
        "  - search_code='NA01': 'NA01(대수학)'의 하위 소분류 반환\n"
        "\n"
        "**코드 계층 규칙 (NTIS001)**: 대=2자리 / 중=4자리 / 소=6자리.\n"
        "\n"
        "**응답 핵심 키**: items (code, name, name_eng, parent_code, kind_code)."
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
        "특정 R&D 과제와 유사한 과제를 AI로 추천합니다 (similarity_score 포함).\n"
        "\n"
        "**언제 쓰는가**: 관심 과제와 비슷한 다른 과제 발굴, 분야별 R&D 확장 탐색.\n"
        "\n"
        "**입력**:\n"
        "  - content_type: 현재 'project'만 지원 (paper/patent/researchreport는 안내만 반환)\n"
        "  - content_id: `search_rnd_projects` 결과의 id (예: '1711190129')\n"
        "\n"
        "**응답 핵심 키**: source_title(원본 과제명), items[]: id, title, similarity_score.\n"
        "\n"
        "**사용 패턴**: `search_rnd_projects` → 관심 과제 id → `get_related_content` 유사 확장.\n"
        "\n"
        "**참고**: AI 추천 DB에 등록되지 않은 과제는 exist=false 빈 결과 반환."
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
