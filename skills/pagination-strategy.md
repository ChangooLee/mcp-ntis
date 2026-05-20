---
name: pagination-strategy
description: NTIS 검색 도구의 페이지네이션 전략 — 정확한 집계를 위한 표준 패턴
---

# 페이지네이션 전략

NTIS 검색 API는 단일 호출당 **최대 100건**까지만 반환한다. LLM이 정확한 집계를 하려면 모든 페이지를 순회해야 한다.

## 1. 시나리오별 권장 패턴

| 시나리오 | 권장 설정 |
|---|---|
| 단순 탐색 (예: "Top 3만 보면 충분") | `page_size=10~20`, 기본값 |
| 상위 N개 목록·기관 추출 | `page_size=100`, 1페이지로 충분 |
| 정량 집계 (예산 합산, 통계 비교) | **`fetch_all=True`** 필수 |
| 매우 큰 결과셋 (10,000+) | `fetch_all=True, max_fetch=5000` 등 한도 조정 |

## 2. `fetch_all` 사용법

```python
result = await client.search_projects(
    query="치매 신약",
    search_field="BI",
    add_query="PY=2024/SAME",
    fetch_all=True,        # 전체 페이지 자동 순회
    max_fetch=2000,        # 안전 한도 (기본 2000)
)
# result["items"]에 모든 페이지 결과가 합쳐져 있음
# total_hits와 len(items)가 일치하면 완전 순회
```

내부 동작:
1. 첫 페이지 가져오기
2. `total_hits` 확인
3. `min(total_hits, max_fetch)`까지 다음 페이지 반복
4. `max_fetch` 한도에 걸리면 `fetch_all_truncated` 메타 추가

## 3. 응답 메타 필드

| 필드 | 의미 |
|---|---|
| `total_hits` | NTIS DB의 전체 매칭 건수 |
| `len(items)` | 실제 반환된 건수 |
| `pagination_warning` | total_hits > items 일 때 자동 추가 (fetch_all=False일 때만) |
| `fetch_all_truncated` | fetch_all=True인데 max_fetch에 걸렸을 때 추가 |

LLM은 이 메타를 보고 추가 호출이 필요한지 판단해야 한다.

## 4. 흔한 실수

### ❌ 잘못된 패턴

```python
# 1045건 중 100건만 합산 → 부정확
r = await client.search_projects(query="항암", count=100)
total_budget = sum(p["government_funds_krw"] for p in r["items"])
```

### ✅ 올바른 패턴

```python
r = await client.search_projects(query="항암", fetch_all=True)
total_budget = sum(p["government_funds_krw"] for p in r["items"])
# 응답에 pagination_warning이 없거나 fetch_all_truncated가 없으면 정확
```

## 5. max_fetch 가이드

| 데이터 규모 | 권장 max_fetch | 비고 |
|---|---|---|
| ~500건 | 1000 (기본) | 5초 내 완료 |
| ~2,000건 | 2000 (기본) | 10초 내 완료 |
| ~5,000건 | 5000 | 30초 내 완료 |
| 10,000건 이상 | 10000 (상한) | 응답 크기 매우 큼, 별도 분석 권장 |

응답이 너무 크면 LLM 컨텍스트 윈도우를 초과할 수 있다. 정량 분석만 필요하면 client.py 레벨에서 합산 후 요약만 반환하는 별도 도구를 만드는 것이 효율적.

## 6. 캐시 활용

`~/.cache/mcp-ntis/`에 24시간 캐시. 같은 파라미터 호출은 즉시 응답. 정량 분석 시 `fetch_all=True`로 한 번 호출하면 모든 페이지가 캐시되어 이후 부분 페이지 호출도 빠름.
