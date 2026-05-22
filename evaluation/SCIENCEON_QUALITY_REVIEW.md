# ScienceON 17개 도구 품질 검토

> 비교 기준: 동일 저자의 `mcp-opendart`(금융감독원 OpenDART 통합) 및 `mcp-kr-legislation`(국가법령정보 통합) 도구 패턴.

## 1. 17개 도구 동작 검증 결과

```
종합: ok 17 / skip 0 / fail 0
```

| # | 도구 | 카테고리 | target | total_count(샘플) | 상태 |
|---|---|---|---|---|---|
| 1 | search_sci_papers | 논문 | ARTI | 428,323 | ok |
| 2 | get_sci_paper | 논문 상세 | ARTI(browse) | 단건 | ok |
| 3 | search_sci_patents | 특허 | PATENT | 110,908 | ok |
| 4 | get_sci_patent | 특허 상세 | PATENT(browse) | 단건 | ok |
| 5 | search_sci_citation_patents | 인용/피인용 특허 | PATENT(citation) | 0~N | ok |
| 6 | search_sci_reports | 보고서 | REPORT | 7,526 | ok |
| 7 | get_sci_report | 보고서 상세 | REPORT(browse) | 단건 | ok |
| 8 | search_sci_trends | 동향 | ATT | 2,480 | ok |
| 9 | get_sci_trend | 동향 상세 | ATT(browse) | 단건 | ok |
| 10 | search_sci_scent | 과학향기 | SCENT (PY 필드만) | 259 | ok |
| 11 | get_sci_scent | 과학향기 상세 | SCENT(browse) | 단건 | ok |
| 12 | search_sci_researchers | 연구자 | RESEARCHER | 764 | ok |
| 13 | get_sci_researcher | 연구자 상세 | RESEARCHER(browse) | 단건 | ok |
| 14 | search_sci_organizations | 연구기관 | ORGAN | 2,090 | ok |
| 15 | get_sci_organization | 연구기관 상세 | ORGAN(browse) | 단건 | ok |
| 16 | search_sci_infra_trend | 인프라 동향 | TREND(infra) | 22 | ok |
| 17 | search_sci_tech_news | 금주의 과학기술뉴스 | SNEWS (RD 필드만) | 0~N | ok |

⇒ 사용자께서 명시하신 **17개 공식 카탈로그와 1:1 매핑**. deprecated 9개(APPLICANT/AUTHOR/FUNCTION/SERVICE/DDC/KACADEMY/RESOLVER/VOLUME/RECOMMEND) 완전 제거.

## 2. 응답 가공 품질 — mcp-opendart 패턴 적용

### Before (이전 raw_xml 그대로)
```json
{
  "target": "ARTI",
  "raw_xml": "<MetaData><resultSummary>...<client_id>...</client_id>...</MetaData>"
}
```
⇒ 12,000자 가까운 XML 본문, 인증 토큰 노출, 키 가독성 ✗.

### After (정제된 dict)
```json
{
  "target": "ARTI",
  "status": "ok",
  "total_count": 428323,
  "service_type": "논문",
  "page": 1,
  "page_size": 2,
  "returned": 2,
  "pagination_hint": "총 428,323건 중 2건 반환 — 남은 428,321건은 cur_page를 증가시켜 순회.",
  "items": [
    {
      "rownum": 1,
      "cn": "ART002574280",
      "db_code": "JAKO",
      "publisher": "...",
      "journal_name": "Journal of Multimedia Information System",
      "issn": ";;",
      "volume_no": "...",
      "pub_year": 2020,
      "language": "영어",
      "article_id": "ART002574280",
      "title": "A Comparison of Deep Reinforcement Learning and Deep learning for Complex Image Analysis",
      "abstract": "...",
      "author": "...",
      "content_url": "...",
      "...": "..."
    }
  ]
}
```

### 적용된 변환 (mcp-opendart `transform_keys` 등가)

| 변환 | 설명 |
|---|---|
| **인증 메타 제거** | `client_id`, `token`, `session_id`, `parameterData` 본문 비노출 |
| **key 매핑** | `Pubyear` → `pub_year`, `JournalName` → `journal_name`, `ArticleCnt` → `paper_count` 등 — 약 70개 metaCode 매핑 |
| **숫자 변환** | `pub_year`, `paper_count`, `patent_count`, `report_count`, `rownum` 등 정수 변환 |
| **HTML 태그 제거** | `abstract`, `title`, `keywords`, `content` 등에서 `<span>` `<div>` 잔재 제거 |
| **CDATA 풀이** | XML CDATA 본문을 일반 string으로 |
| **중첩 그룹 정제** | `CallAPIInfo` → `linked_apis` 리스트로 평탄화 |
| **상태 표준화** | `status_code=200` → `status="ok"`, errorDetail → `error: {code, message}` |
| **페이지네이션 힌트** | `total > returned`일 때 남은 건수·순회 방법 안내 |

## 3. 항목별 품질 비교 (vs mcp-opendart / mcp-kr-legislation)

| 항목 | mcp-opendart | mcp-kr-legislation | **mcp-ntis (ScienceON 17)** | 비고 |
|---|---|---|---|---|
| 도구당 응답 표준 스키마 | ✅ (status/message/list) | ✅ | ✅ **정제된 dict** | parser.py 통일 |
| 인증 메타 제거 | ✅ | ✅ | ✅ | client_id·token 비노출 |
| 약자 키 → 명료 영문 | ✅ `KEY_MAPPING` 60개+ | ✅ | ✅ **약 70개 매핑** | 신규 적용 |
| 숫자 필드 자동 변환 | ✅ `AMOUNT_FIELDS` | ✅ | ✅ **카운트·연도** | 신규 적용 |
| HTML 태그 제거 | n/a (DART는 JSON) | ✅ (법령 본문) | ✅ | _strip_html() |
| 페이지네이션 힌트 | ✅ `page_no` | ✅ | ✅ `pagination_hint` | total 대비 안내 |
| 에러 코드 정제 | ✅ `status`+`message` | ✅ | ✅ `error.code`+`message` | E4002·E4007 등 정확 매핑 |
| 토큰 자동 재발급 | n/a (DART는 API 키) | n/a | ✅ **AES-256-CBC + refresh** | E4103 자동 |
| Rate limit 백오프 | ✅ | ✅ | ✅ E4290 1→2→4→8s | client.py |
| 도구 메타 (linked_tools) | ✅ registry 기반 | ✅ | ⚠️ tags만 — registry 없음 | 차후 보강 가능 |
| 한글 도구 별칭 | ✅ `korean_name` | ✅ | ⚠️ description에 한글 | 동등하지만 별 필드 없음 |
| 자기 소개 도구 | ✅ `get_opendart_tool_info` | ✅ | ✅ `get_ntis_tool_info` (NTIS 측) | ScienceON 전용 도구도 추후 가능 |
| 도구 카테고리화 | ✅ ds001~ds006 | ✅ apis/ | ✅ 7개 카테고리 docstring | tools.py 한 파일로 통일 |
| 파라미터 검증 | ✅ Pydantic Field | ✅ Pydantic | ✅ Pydantic | 동등 |
| 응답 캐싱 | n/a | ⚠️ | ⚠️ NTIS 측만 (Sci 캐시 없음) | NTIS와 별개 캐시 도입 가능 |

## 4. 갭 분석

### 적용 완료 (이번 작업)
1. ✅ 24개 → 17개 정리 (deprecated 9개 제거 + 신규 3개 추가)
2. ✅ XML → 정제된 dict 파서 (`parser.py`)
3. ✅ KEY_MAPPING(70개) + 숫자 변환 + HTML 제거
4. ✅ 에러 코드(E4002/E4007/E4290/E4103/E4302) 자동 분기
5. ✅ 페이지네이션 힌트
6. ✅ 17개 모두 회귀 테스트 통과

### 잔여 갭 (차후 보강 가능)
1. **registry 기반 linked_tools 메타** — opendart의 `get_opendart_tool_info` 패턴.
   - 현재 `get_ntis_tool_info`는 NTIS 16개만 노출. ScienceON 17개도 같은 메타 인덱스에 합쳐야 함.
   - 작업량: tool_registry에 ScienceON 도구 17개 등록 + linked_tools(예: `search_sci_papers` → `get_sci_paper`, `search_sci_researchers`).

2. **결과 캐싱** — NTIS는 `cache.py`(MD5 키, TTL 24h)가 있는데 ScienceON은 없음.
   - 작업량: `cache.py`를 import해 search/browse 결과 캐시. 토큰 만료 후 캐시 잔존 처리 필요.

3. **fetch_all 패턴** — NTIS 도구는 `fetch_all=True`로 자동 페이지 순회.
   - ScienceON은 도구당 1회 호출만 — `curPage × rowCount`가 10,000건 미만 제약 있어 직접 구현 가능.

4. **응답 토큰 절약** — `Abstract`/`Content` 전체 본문은 한 record당 수천 자.
   - opendart는 핵심 필드만 반환. ScienceON도 `abstract_teaser=True` 옵션으로 250자 잘림 가능.

## 5. 결론

- **17개 도구 모두 실 API에 정상 호출**되어 `status="ok"` 반환.
- 응답 가공·에러 처리·페이지네이션은 **mcp-opendart와 동등 수준**으로 정비됨.
- 토큰 자동 재발급·AES-256-CBC 암호화 등 ScienceON 고유 인증 로직은 안정적으로 동작.
- 잔여 갭(registry 메타, 캐싱, fetch_all)은 핵심 기능에 영향 없는 부가 사항으로, 필요 시 후속 작업으로 분리 가능.

## 6. 파일 변경 요약

| 파일 | 변경 |
|---|---|
| `src/mcp_ntis/scienceon/tools.py` | 24개 → **17개 도구**로 재구성, 3개 신규(인용·infra TREND·SNEWS) |
| `src/mcp_ntis/scienceon/parser.py` | **신규** — XML→정제된 dict, KEY_MAPPING 70개, 숫자 변환, HTML 제거, 에러 분기 |
| `src/mcp_ntis/server.py` | 활성화 로그 메시지 17개로 수정 |
| `evaluation/SCIENCEON_QUALITY_REVIEW.md` | **신규** — 본 검토 보고서 |
