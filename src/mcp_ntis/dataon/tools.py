"""DataON 도구 — KISTI 국가연구데이터플랫폼.

DataON 공식 OpenAPI는 현재 데이터셋 검색 1종.
"""

from __future__ import annotations

import logging
import threading
from typing import Annotated, Optional

from mcp.types import TextContent
from pydantic import Field

from mcp_ntis.server import as_json_text, error_text, mcp
from mcp_ntis.dataon.client import DataONClient

logger = logging.getLogger("mcp-ntis.dataon.tools")


# ---------------------------------------------------------------------------
# 클라이언트 싱글톤
# ---------------------------------------------------------------------------


_client: Optional[DataONClient] = None
_lock = threading.Lock()


def _get_client() -> DataONClient:
    global _client
    with _lock:
        if _client is None:
            _client = DataONClient()
        return _client


# ---------------------------------------------------------------------------
# 도구
# ---------------------------------------------------------------------------


@mcp.tool(
    name="search_dataon_datasets",
    tags={"DataON", "연구데이터", "검색"},
    description=(
        "국가 연구 데이터(공공·연구기관 공개 데이터셋)를 검색합니다.\n"
        "\n"
        "**언제 쓰는가**: 특정 주제의 실제 데이터셋(연구용 raw data·관측 데이터·"
        "센서 로그 등)을 찾을 때. 논문·특허와 달리 분석 가능한 데이터 자체.\n"
        "\n"
        "**입력**: \n"
        "  - query: 검색 키워드 (필수, 한·영 가능, 예: '배 수확', 'covid virus')\n"
        "  - from_: 페이지 시작 위치 (기본 0)\n"
        "  - size: 페이지당 결과 수 (기본 10, 권장 ≤ 50)\n"
        "  - sort_con: 'title' | 'date' | 'score' (기본 score, 정확도순)\n"
        "  - sort_arr: 'asc' | 'desc'\n"
        "\n"
        "**응답 핵심 키**: total_count, items[].title, description, keywords, "
        "doi, landing_url, access_type, catalog_type, repository, creator, publisher.\n"
        "\n"
        "**다음 단계**: 검색 결과의 doi 또는 id로 `get_dataon_dataset` 호출하여 상세 메타 조회."
    ),
)
async def search_dataon_datasets(
    query: Annotated[str, Field(description="검색 키워드. 예: '배 수확', 'covid virus'")],
    from_: Annotated[int, Field(description="페이지 시작 위치 (0부터)", ge=0)] = 0,
    size: Annotated[int, Field(description="페이지당 결과 수", ge=1, le=100)] = 10,
    sort_con: Annotated[
        str,
        Field(description="정렬 기준: title / date / score (기본 score)"),
    ] = "",
    sort_arr: Annotated[
        str,
        Field(description="정렬 순서: asc / desc"),
    ] = "",
) -> TextContent:
    try:
        client = _get_client()
        result = await client.search_datasets(
            query=query,
            from_=from_,
            size=size,
            sort_con=sort_con or None,
            sort_arr=sort_arr or None,
        )
        return as_json_text(result)
    except Exception as exc:
        logger.error(f"search_dataon_datasets 오류: {exc}")
        return error_text(str(exc))


@mcp.tool(
    name="get_dataon_dataset",
    tags={"DataON", "연구데이터", "상세"},
    description=(
        "연구 데이터셋 1건의 상세 메타정보를 조회합니다.\n"
        "\n"
        "**언제 쓰는가**: `search_dataon_datasets` 결과에서 특정 데이터셋의 "
        "전체 메타(저자·연도·DOI·접근경로·라이선스·repository 등)를 받고 싶을 때.\n"
        "\n"
        "**입력**:\n"
        "  - dataset_id: 검색 결과의 id 또는 doi\n"
        "  - query: 보조 검색어 (일부 환경에서 매칭에 도움)\n"
        "\n"
        "**응답**: items[0]에 단일 dataset의 정제된 메타 dict."
    ),
)
async def get_dataon_dataset(
    dataset_id: Annotated[str, Field(description="데이터셋 ID 또는 DOI")],
    query: Annotated[str, Field(description="보조 검색어 (선택)")] = "",
) -> TextContent:
    try:
        client = _get_client()
        result = await client.get_dataset_detail(
            dataset_id=dataset_id,
            query=query or None,
        )
        return as_json_text(result)
    except Exception as exc:
        logger.error(f"get_dataon_dataset 오류: {exc}")
        return error_text(str(exc))
