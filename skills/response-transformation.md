---
name: response-transformation
description: NTIS 응답을 LLM이 이해하기 쉬운 형태로 정규화하는 방법
---

# 응답 변환 가이드

NTIS API의 원본 응답은 XML과 약어 필드가 섞여있어 LLM이 직접 다루기 어렵다. `utils/ctx_helper.py`의 `transform_response()` + `_compact()`가 이를 정규화한다.

## 1. 변환 파이프라인

```
NTIS XML → ET parsing → _parse_*_hit() → transform_response() → _compact() → JSON TextContent
                          (client.py)       (ctx_helper)         (server.py)
```

각 단계의 역할:

| 단계 | 처리 |
|---|---|
| `_parse_*_hit()` | XML → dict, 정규화된 필드명 (id, title, institution 등) |
| `transform_response()` | 잔여 약어 키 휴먼리더블화 + 금액 숫자화 + null 정리 |
| `_compact()` | 빈 문자열·빈 컬렉션 재귀 제거로 토큰 절약 |
| `as_json_text()` | 최종 JSON TextContent 생성 (ensure_ascii=False) |

## 2. KEY_MAPPING 추가

새로운 NTIS API를 통합할 때 응답에 약어 필드가 있으면 `ctx_helper.py:KEY_MAPPING`에 추가:

```python
KEY_MAPPING = {
    "rcept_no": "receipt_number",
    "PJT_ID": "project_id",
    # ...
}
```

규칙:
- 영문 약어 → snake_case 영문 풀네임 또는 한국어 의역
- camelCase 한국어 → snake_case 한국어 ("topicNm" → "issue_name")
- 단위가 명확한 금액은 접미사 추가 ("amount" → "amount_krw")

## 3. AMOUNT_FIELDS

금액으로 자동 변환할 필드명을 등록:

```python
AMOUNT_FIELDS = {
    "government_funds_krw",
    "total_funds_krw",
    "consignment_project_funds_krw",
    "price_krw",
    "rnd_budget_krw",
}
```

- `"1,250,000,000"` → `1250000000` (int)
- `"-"`, `""`, `"null"` → `0`
- `"(100)"` → `-100` (회계 음수 표기)
- 변환 실패 시 원본 문자열 반환

## 4. null 정규화

`"null"`, `"NULL"`, `"None"` 문자열은 모두 빈 문자열로 변환. `_compact()`가 빈 문자열을 제거하므로 최종 응답에서는 노이즈 없음.

## 5. 텍스트 정리

`client.py`의 `_clean_text()`가 추가로 처리:

- `<span class="search_word">` 하이라이트 태그 제거
- `_x005F_`, `_x000D_` 등 XML escape 아티팩트 제거
- 앞쪽 `"..."` 마커 제거 (NTIS가 truncated 표시로 사용)
- 연속 공백 → 단일 공백

날짜는 `_clean_date()`로 `"2024-07-01 00:00:00.0"` → `"2024-07-01"` 처리.

## 6. 변환 검증

```python
from mcp_ntis.utils.ctx_helper import transform_response

raw = {"PJT_ID": "1711190129", "topicNm": "AI", "amount": "1,000,000"}
result = transform_response(raw)
# {'project_id': '1711190129', 'issue_name': 'AI', 'amount': '1,000,000'}
# amount는 AMOUNT_FIELDS에 없어서 그대로
```

AMOUNT_FIELDS에 등록되지 않은 필드는 문자열로 유지된다. 자주 쓰는 금액 필드는 반드시 등록할 것.

## 7. Idempotent 보장

`transform_response()`는 한 번 변환된 데이터를 다시 통과시켜도 안전. 이미 휴먼리더블 키는 KEY_MAPPING에 없으므로 그대로 통과. 이중 호출이 발생해도 결과가 변하지 않는다.
