# NTIS MCP 개선 사항 — 적용 완료

> **작성 일자**: 2026-05-20 (1차)
> **완료 일자**: 2026-05-20 (2차 — 모든 항목 적용 완료)
> **최종 회귀 테스트**: 10/10 통과 (100%)

---

## 작업 요약

| 우선순위 | 식별 건수 | 완료 건수 | 상태 |
|---|---|---|---|
| Critical | 5 | 5 | ✅ |
| High | 5 | 5 | ✅ |
| Medium | 4 | 4 | ✅ |
| Low | 3 | 3 | ✅ |
| **합계** | **17** | **17** | **100%** |

---

## Critical — 완료

### ✅ C1. `search_unified` 검색어 미전달

**원인**: `totalRstSearch` 엔드포인트는 `query` 파라미터를 사용 (다른 검색 API는 `SRWR`)

**수정** (`client.py:search_unified`)
```python
params = {
    **self._base_params(),
    "collection": collection,
    "query": query,        # ← SRWR → query로 변경
    "searchFd": search_field,
    ...
}
```

**추가 수정**: SITID 매핑 (`PJK`=project, `EQU`=equipment, `RFR`/`RES`=report)

**검증**: 다양한 query로 호출 시 서로 다른 결과 반환, items의 title이 정상 채워짐.

---

### ✅ C2. `search_research_equipment` 파서 재작성

**원인**: requip은 다른 도구와 완전히 다른 XML 구조

**수정** (`client.py:_parse_equip_hit` — 전면 재작성)
- 응답 필드 13개 신설: `equip_no`, `title`, `title_eng`, `model`, `manufacturer`, `institution`, `install_location`, `feature`, `buy_date`, `year`, `price_krw`, `acquisition_method`, `use_scope`, `use_type`, `equipment_class`, `project_id`, `project_title`, `ministry`, `science_class`

**검증**: 모든 필드 정상 채워짐 (예: 한국원자력연구원의 Philips XL-30 차폐형 전자현미경, 419,741,218원).

---

### ✅ C3. `recommend_it_classification` MOTIE 래퍼

**원인**: IT 분류는 `<RESULT><MOTIE><Result_*/></MOTIE></RESULT>` 구조 (다른 분류는 `<RESULT><Result_*/></RESULT>`)

**수정** (`client.py:_parse_classification_result`)
```python
container = result_elem.find("MOTIE")
if container is None:
    container = result_elem
# 동일 코드 중복 자동 제거
seen_codes = set()
for child in container:
    if child.tag.startswith("Result_"):
        small_code = child.get("SCLS_CD", "")
        if small_code and small_code in seen_codes:
            continue
        if small_code:
            seen_codes.add(small_code)
        ...
```

**검증**: IT 분류 5개 추천 정상 반환.

---

### ✅ C4. `get_related_content` 모든 ID 0건 반환

**원인**: ConnectionContent API는 `pjtId` 파라미터 사용 (우리는 `id`로 호출), project만 지원

**수정** (`client.py:get_related_content`)
- `id` → `pjtId` 파라미터로 변경
- `project` 외 컨텐츠 타입에 대한 명확한 안내 메시지 반환
- 응답 정규화: `id`, `title`, `similarity_score`, `institution`, `year`
- 미존재 ID는 `note` 메시지로 안내

**검증**: 정상 ID로 10개 유사 과제 반환 (similarity_score 포함).

---

### ✅ C5. 페이지네이션 경고 메타

**수정** (`client.py`의 모든 검색 메서드)
```python
total = meta.get("total_hits", 0)
if total > start - 1 + len(items):
    remaining = total - (start - 1 + len(items))
    meta["pagination_warning"] = (
        f"총 {total}건 중 {len(items)}건만 반환됨 (남은 {remaining}건). "
        f"정확한 집계가 필요하면 start={start + count}부터 추가 호출하세요. "
        f"최대 page_size=100."
    )
```

**검증**: 1045건 중 50건 반환 시 `pagination_warning` 자동 포함.

---

## High — 완료

### ✅ H1. `search_terminology` 인증 오류

**원인**: ntisDic API는 신규 API 키를 `apprvKey`로 받음 (기존 키 + `userKey` 조합은 미지원)

**수정** (`client.py:search_terminology`)
```python
key = self.config.new_api_key or self.config.api_key
params = {"apprvKey": key, ...}  # userKey 제거
```

**검증**: "양자" 검색 시 409건 정상 반환.

---

### ✅ H2. `get_org_rnd_status` disambiguation 자동 처리

**수정** (`client.py:get_org_rnd_status`)
- `auto_resolve` 파라미터 추가 (기본 True)
- 후보 점수 함수 (입력 정확 일치 > 본원 추정 > 짧은 이름)
- R&D 데이터가 있는 첫 후보 우선 선택
- 모든 후보 시도 후 데이터 없으면 명확한 안내 메시지

**도구 description 업데이트** (`extra_tools.py:get_org_rnd_status`)
- `auto_resolve` 파라미터 노출

---

### ✅ H3. `add_query`의 OG/AU 필터 안내

**수정** (`search_tools.py:_ADD_QUERY_HELP`)
```
수행기관: OG=한국전자통신연구원 (정확 일치).
연구책임자: AU=홍길동. 키워드: KW=양자컴퓨터.
예: search_field='BI', query='인공지능', add_query='OG=한국과학기술원&PY=2024/SAME'
   → KAIST 2024년 인공지능 과제.
팁: BI 검색 + add_query 조합이 가장 정밀함.
```

---

### ✅ H4. `search_field=TI/CN` 정확화

**수정** (`search_tools.py`)
- 논문 search_field에서 "/과제고유번호" 제거
- 특허 search_field에서 "/과제고유번호" 제거
- 도구 description에 "project_id 역추적 불가, 클라이언트 매칭 필요" 명시

---

### ✅ H5. 분류 추천 중복 항목 제거

**수정** (`client.py:_parse_classification_result`, `_parse_ht_classification_result`)
- STD/IT: `small_code` 기반 중복 제거
- HT 질환분류: `disease_code` 기반
- HT 연구행위분류: `medium_code` 기반
- HT 산업기술분류: `small_code` 기반

**검증**: CRISPR 질환분류에서 "눈 및 눈 부속기의 질환" 중복 제거됨.

---

## Medium — 완료

### ✅ M1. 코드 계층 추출 안내

**수정** (`extra_tools.py:get_classification_codes`)
- 대분류(2자)/중분류(4자)/소분류(6자) 구조 명시
- `small[:4]=medium`, `medium[:2]=large` 추출 규칙 명시

### ✅ M2. 분류 추천 error_type enum

**수정** (`client.py:_parse_classification_result`)
- `result_code='-1002'` → `error_type='text_too_short'`
- `result_code='-2002'` → `error_type='insufficient_terms'`

### ✅ M3. `search_unified` collection 안내

**수정** (`search_tools.py:search_unified`)
- 컬렉션 단축어 전체 명시 (project, rpaper, rpatent, rresearch, requip)
- 예시 강화

### ✅ M4. `get_consignment_research` 분담금 안내

**수정** (`project_tools.py`)
- `consignment_project_funds_krw` vs `collaborative_research_funds_krw` 구분 안내
- 공동연구는 0으로 기록될 수 있음 명시

---

## Low — 완료

### ✅ L1. 분류 코드 응답 효율

**현황**: `get_classification_codes`는 캐싱(24시간)으로 첫 호출 외 효율적. 응답에 `total` 필드 포함하여 LLM이 전체 규모 인지 가능.

### ✅ L2. 응답 메타 일관성

**수정** (`client.py`)
- 모든 도구가 `meta`(`total_hits`, `hits`, `search_time`, `note`, `pagination_warning`, `deduplicated`, `auto_resolved`) 구조를 일관되게 사용

### ✅ L3. `search_time` 활용

**현황**: 모든 검색 응답에 `search_time` 필드가 포함되어 LLM이 후속 호출 빈도를 조절할 수 있음 (예시: `search_time=0.03s` → 안전한 다회 호출)

---

## 회귀 테스트 결과

`evaluation/TEST_RESULTS.md` 참조.

```
[Q1~Q10] 모두 PASS (10/10)
```

전체 회귀 테스트 스크립트: `/tmp/regression_test.py`

```bash
find ~/.cache/mcp-ntis -name '*.json' -delete
python /tmp/regression_test.py
```

---

## 변경 파일 요약

| 파일 | 변경 | 라인 수 추이 |
|---|---|---|
| `src/mcp_ntis/client.py` | 핵심 파서/엔드포인트/메타 수정 | +120 |
| `src/mcp_ntis/tools/search_tools.py` | description 개선 | +30 |
| `src/mcp_ntis/tools/extra_tools.py` | get_org_rnd_status 파라미터 추가, description | +20 |
| `src/mcp_ntis/tools/project_tools.py` | description 개선 | +5 |
| `src/mcp_ntis/tools/classification_tools.py` | (이미 충분히 개선됨) | 0 |
