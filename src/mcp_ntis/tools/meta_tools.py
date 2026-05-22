"""NTIS MCP 메타 도구 — 도구 자체 탐색·도움말 제공.

LLM이 어떤 도구를 사용할지 모를 때 가장 먼저 호출하는 도구.
"""

from __future__ import annotations

import logging
from typing import Annotated

from mcp.types import TextContent
from pydantic import Field

from mcp_ntis.server import as_json_text, error_text, mcp, tool_registry

logger = logging.getLogger("mcp-ntis")


@mcp.tool(
    name="get_ntis_tool_info",
    tags={"메타", "도구탐색", "도움말"},
    description=(
        "정부 R&D 도구(NTIS 16개) 카탈로그를 탐색합니다 — 어떤 도구를 써야 할지 모를 때 사용.\n"
        "\n"
        "**언제 쓰는가**: 작업 시작 전 어느 도구가 필요한지 파악, 도구 간 연결 관계 확인.\n"
        "\n"
        "**입력 패턴**:\n"
        "  - 인자 없음: 카테고리별 전체 16개 도구 목록\n"
        "  - tool_name='search_rnd_projects': 해당 도구의 상세(파라미터·연관 도구·활용 예시)\n"
        "  - tag='검색': 태그로 필터링된 도구 목록\n"
        "\n"
        "**응답 핵심 키**: \n"
        "  - 목록: categories(검색/과제상세/기관분석/분류추천/...), total_tools\n"
        "  - 상세: tool_name, korean_name, parameters, linked_tools, usage_pattern\n"
        "\n"
        "**활용 예**: 사용자 질문 → tag='검색' 호출 → 도구 선택 → tool_name=... 으로 상세 확인.\n"
        "\n"
        "**참고**: 학술·특허 DB 도구(ScienceON 17개)는 별도 카탈로그 — `search_sci_*` 직접 호출."
    ),
)
async def get_ntis_tool_info(
    tool_name: Annotated[
        str,
        Field(description="조회할 도구의 영문명 (예: 'search_rnd_projects'). 빈 값이면 전체 목록 반환"),
    ] = "",
    tag: Annotated[
        str,
        Field(description="태그로 필터링 (예: '검색', '분류추천', '기관분석'). 빈 값이면 무시"),
    ] = "",
) -> TextContent:
    try:
        # 1) 특정 도구 상세 조회
        if tool_name:
            tool = tool_registry.get(tool_name)
            if tool is None:
                available = list(tool_registry.tools.keys())
                return as_json_text({
                    "error": f"'{tool_name}' 도구를 찾을 수 없습니다.",
                    "available_tools": available,
                    "hint": "tool_name 없이 호출하면 전체 카테고리별 목록을 볼 수 있습니다.",
                })

            return as_json_text({
                "tool_name": tool.name,
                "korean_name": tool.korean_name,
                "description": tool.description,
                "tags": sorted(list(tool.tags)),
                "parameters": tool.parameters,
                "linked_tools": tool.linked_tools,
                "usage_pattern": tool.usage_pattern,
                "rich_description": tool.rich_description(),
            })

        # 2) 태그 필터링
        if tag:
            matched = tool_registry.search_by_tag(tag)
            if not matched:
                all_tags = set()
                for t in tool_registry.tools.values():
                    all_tags |= t.tags
                return as_json_text({
                    "error": f"태그 '{tag}'에 해당하는 도구가 없습니다.",
                    "available_tags": sorted(all_tags),
                })
            return as_json_text({
                "tag": tag,
                "matched_count": len(matched),
                "tools": [
                    {
                        "name": t.name,
                        "korean_name": t.korean_name,
                        "description": t.description,
                        "tags": sorted(list(t.tags)),
                        "linked_tools": t.linked_tools,
                    }
                    for t in matched
                ],
            })

        # 3) 카테고리별 전체 목록
        categories = tool_registry.list_by_category()
        result = {
            "total_tools": len(tool_registry.tools),
            "categories": {
                cat: [
                    {
                        "name": t.name,
                        "korean_name": t.korean_name,
                        "description": t.description[:120] + ("..." if len(t.description) > 120 else ""),
                        "tags": sorted(list(t.tags)),
                    }
                    for t in tools
                ]
                for cat, tools in categories.items()
            },
            "hint": (
                "각 도구의 상세 사용법·파라미터·연관 도구·활용 패턴은 "
                "get_ntis_tool_info(tool_name='<이름>')로 조회하세요."
            ),
        }
        return as_json_text(result)

    except Exception as e:
        logger.error(f"get_ntis_tool_info 오류: {e}")
        return error_text(str(e))
