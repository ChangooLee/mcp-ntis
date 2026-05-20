---
name: tool-development
description: NTIS MCP에 새로운 도구를 추가하고 등록하는 표준 패턴
---

# Tool 개발 가이드

NTIS MCP에 새 도구를 추가할 때 따라야 할 표준 패턴.

## 1. 파일 위치 결정

| 도구 유형 | 위치 |
|---|---|
| 검색 (R&D 과제·논문·특허·보고서·장비) | `tools/search_tools.py` |
| 과제 상세 조회 | `tools/project_tools.py` |
| 분류 추천 (표준·보건의료·산업기술) | `tools/classification_tools.py` |
| 부가 도구 (트렌드·용어·분류코드·유사추천) | `tools/extra_tools.py` |
| 메타 도구 (도구 자체 탐색) | `tools/meta_tools.py` |

새 카테고리가 필요하면 `tools/new_category.py` 생성 후 `server.py`의 importlib 루프에 추가.

## 2. 표준 도구 시그니처

```python
from typing import Annotated
from mcp.types import TextContent
from pydantic import Field

from mcp_ntis.server import as_json_text, error_text, get_client, mcp
from mcp_ntis.utils.ctx_helper import transform_response


@mcp.tool(
    name="tool_name",
    tags={"카테고리1", "카테고리2"},   # registry와 일치시킬 것
    description=(
        "도구의 한 줄 설명. "
        "다음 줄에 활용 예시·연관 도구·페이지네이션 가이드 등 풍부히 기술."
    ),
)
async def tool_name(
    required_param: Annotated[str, Field(description="필수 파라미터 설명")],
    optional_param: Annotated[int, Field(description="기본값 있는 파라미터")] = 10,
) -> TextContent:
    try:
        client = get_client()
        raw = await client.some_api_call(required_param, optional_param)
        # 응답 정규화 (KEY_MAPPING + 금액 숫자화 + null 정리)
        result = transform_response(raw)
        return as_json_text(result)
    except Exception as exc:
        return error_text(str(exc))
```

## 3. Registry 등록

도구를 추가하면 `registry/initialize_registry.py`에도 등록:

```python
registry.register(
    name="tool_name",
    korean_name="한국어 이름",
    description="설명",
    parameters={ ... JSON Schema ... },
    tags={"카테고리1", "카테고리2"},
    linked_tools=["연관도구1", "연관도구2"],
    usage_pattern="활용 패턴 다중라인 텍스트",
)
```

레지스트리에 등록하지 않으면 `get_ntis_tool_info`가 도구를 찾지 못한다.

## 4. 페이지네이션 지원

검색형 도구는 반드시 `fetch_all` + `max_fetch` 파라미터 지원:

```python
fetch_all: Annotated[bool, Field(description="전체 페이지 자동 순회")] = False,
max_fetch: Annotated[int, Field(description="fetch_all 시 최대 건수", ge=100, le=10000)] = 2000,
```

`client.py`의 호출에 `fetch_all=fetch_all, max_fetch=max_fetch` 전달.

## 5. 응답 변환

모든 응답은 `transform_response()`를 통과시켜:
- NTIS 약어 키 (`pjt_id`, `corp_name` 등)를 휴먼리더블 키로 변환
- 금액 문자열을 int/float로 자동 변환
- `"null"` 문자열을 빈 문자열로 정규화

직접 변환된 객체를 반환하면 transform_response는 idempotent하므로 안전.

## 6. 에러 처리

- API 호출 실패 → `error_text(str(exc))` 반환
- 도메인 검증 실패 → `as_json_text({"error": "...", "hint": "..."})` 반환
- 빈 결과는 에러가 아닌 정상 응답으로 처리

## 7. 체크리스트

- [ ] `@mcp.tool`에 `name`, `tags`, `description` 모두 지정
- [ ] 모든 파라미터에 `Annotated[Type, Field(description=...)]`
- [ ] `transform_response()` 적용
- [ ] `registry/initialize_registry.py`에도 등록 (메타 도구 노출 위해)
- [ ] 검색형이면 `fetch_all` + `max_fetch` 지원
- [ ] `server.py`의 importlib 루프에 모듈 포함
