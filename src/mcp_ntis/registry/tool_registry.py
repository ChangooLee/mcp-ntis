"""NTIS MCP 도구 메타데이터 레지스트리.

mcp-opendart 패턴을 차용하여 도구의 한국어 이름·태그·연관 도구 관계를
체계적으로 관리한다. `get_ntis_tool_info` 메타 도구가 이 레지스트리를
참조해 LLM에게 풍부한 컨텍스트를 제공한다.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Set

logger = logging.getLogger("mcp-ntis")


class ToolMetadata:
    """단일 MCP 도구의 메타데이터 (이름, 설명, 파라미터, 연관 도구, 태그)."""

    def __init__(
        self,
        name: str,
        description: str,
        parameters: dict,
        korean_name: Optional[str] = None,
        linked_tools: Optional[List[str]] = None,
        tags: Optional[Set[str]] = None,
        usage_pattern: Optional[str] = None,
    ) -> None:
        self.name = name
        self.korean_name = korean_name
        self.description = description
        self.parameters = parameters
        self.linked_tools = linked_tools or []
        self.tags = tags or set()
        self.usage_pattern = usage_pattern or ""

    def rich_description(self) -> str:
        """LLM이 도구의 목적·파라미터·연관 흐름을 한눈에 볼 수 있는 형식."""
        lines: List[str] = []
        if self.korean_name:
            lines.append(f"[도구] {self.name} — {self.korean_name}")
        lines.append(f"[설명] {self.description}")

        if self.tags:
            lines.append(f"[태그] {', '.join(sorted(self.tags))}")

        props = self.parameters.get("properties", {})
        required = set(self.parameters.get("required", []))
        if props:
            lines.append("[입력 파라미터]")
            for key, schema in props.items():
                desc = schema.get("description", "")
                mark = " (필수)" if key in required else ""
                default = schema.get("default")
                default_note = f" [기본값: {default}]" if default is not None else ""
                lines.append(f"  - {key}: {desc}{mark}{default_note}")

        if self.linked_tools:
            lines.append(f"[연관 도구] {', '.join(self.linked_tools)}")

        if self.usage_pattern:
            lines.append(f"[활용 패턴]\n{self.usage_pattern}")

        return "\n".join(lines)

    def brief_summary(self) -> str:
        kor = f" ({self.korean_name})" if self.korean_name else ""
        return f"- {self.name}{kor}: {self.description[:80]}"


class ToolRegistry:
    """도구 메타데이터 전체 컬렉션."""

    def __init__(self) -> None:
        self.tools: Dict[str, ToolMetadata] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: dict,
        korean_name: Optional[str] = None,
        linked_tools: Optional[List[str]] = None,
        tags: Optional[Set[str]] = None,
        usage_pattern: Optional[str] = None,
    ) -> None:
        self.tools[name] = ToolMetadata(
            name=name,
            description=description,
            parameters=parameters,
            korean_name=korean_name,
            linked_tools=linked_tools,
            tags=tags,
            usage_pattern=usage_pattern,
        )

    def get(self, name: str) -> Optional[ToolMetadata]:
        return self.tools.get(name)

    def search_by_tag(self, tag: str) -> List[ToolMetadata]:
        return [t for t in self.tools.values() if tag in t.tags]

    def list_all_briefs(self) -> str:
        return "\n".join(t.brief_summary() for t in self.tools.values())

    def list_by_category(self) -> Dict[str, List[ToolMetadata]]:
        """카테고리별 도구 목록. 1순위 태그를 카테고리로 사용."""
        category_priority = [
            "검색",
            "과제상세",
            "기관분석",
            "분류추천",
            "분류코드",
            "트렌드",
            "용어",
            "AI추천",
            "메타",
        ]
        categories: Dict[str, List[ToolMetadata]] = {c: [] for c in category_priority}
        for tool in self.tools.values():
            assigned = False
            for cat in category_priority:
                if cat in tool.tags:
                    categories[cat].append(tool)
                    assigned = True
                    break
            if not assigned:
                categories.setdefault("기타", []).append(tool)
        return {k: v for k, v in categories.items() if v}
