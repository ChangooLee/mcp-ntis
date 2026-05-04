import logging
from typing import Annotated

from mcp.types import TextContent
from pydantic import Field

from mcp_ntis.server import as_json_text, error_text, get_client, mcp

logger = logging.getLogger("mcp-ntis")


@mcp.tool(
    name="get_consignment_research",
    description=(
        "주관/협동 과제의 위탁/공동연구 정보를 조회합니다. "
        "과제고유번호(ProjectNumber)로 해당 과제에 속한 위탁·공동연구기관, "
        "연구비, 참여기간, 연구책임자 정보를 확인할 수 있습니다. "
        "과제고유번호는 search_rnd_projects 결과의 'id' 필드에서 얻을 수 있습니다."
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
