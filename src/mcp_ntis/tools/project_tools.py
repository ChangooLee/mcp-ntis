import logging
from typing import Annotated

from mcp.types import TextContent
from pydantic import Field

from mcp_ntis.server import as_json_text, error_text, get_client, mcp

logger = logging.getLogger("mcp-ntis")


@mcp.tool(
    name="get_consignment_research",
    tags={"과제상세", "협력", "위탁연구"},
    description=(
        "특정 R&D 과제의 위탁·공동연구 협력 정보를 조회합니다 (협력 기관 망 추적).\n"
        "\n"
        "**언제 쓰는가**: 대형 과제의 위탁·공동연구 기관 매핑, 컨소시엄 구조 분석.\n"
        "\n"
        "**입력**: project_id — `search_rnd_projects` 결과의 id 필드. "
        "예: '1415140010', '2410011917'.\n"
        "\n"
        "**응답 핵심 키**: items[]: lead_agency(주관), commission_lead_agency(위탁 수행), "
        "commission_type(공동연구/위탁), researcher_count, "
        "consignment_project_funds_krw(위탁 분담금), collaborative_research_funds_krw(공동 분담금).\n"
        "\n"
        "**참고**: 공동연구(commission_type='공동연구(국내)')는 분담금이 0으로 기록될 수 있음."
    ),
)
async def get_consignment_research(
    project_id: Annotated[
        str,
        Field(
            description=(
                "조회할 과제의 고유번호 또는 위탁과제번호. "
                "예: '1415140010' (search_rnd_projects 결과의 id 필드 값)"
            )
        ),
    ],
) -> TextContent:
    try:
        client = get_client()
        result = await client.get_consignment_research(pjt_id=project_id)
        return as_json_text(result)
    except Exception as e:
        logger.error(f"get_consignment_research 오류: {e}")
        return error_text(str(e))
