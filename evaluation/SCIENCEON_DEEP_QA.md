# ScienceON 17개 도구 심층 파라미터 검증 보고서

> 각 도구를 다양한 파라미터(한글·영문, 다중 필드, 페이지, 잘못된 입력)로 실제 호출하여 검증.

## 0. 총괄

| 지표 | 결과 |
|---|---|
| 검증 케이스 | **34건** |
| 통과 | **34건** |
| 실패 | **0건** |
| 통과율 | **100%** |

검증 항목: 상태 정상화·인증 메타 미노출·KEY_MAPPING 적용·숫자 자동 변환·HTML 태그 제거·페이지네이션 힌트·에러 분기.

## 1. 도구별 검증 결과

| # | 도구 | 케이스 수 | 통과 |
|---|---|---|---|
| 1 | search_sci_papers | 4 (BI 영문, TI 한글, BI+PY, page=2) | 4/4 |
| 2 | get_sci_paper | 2 (정상 CN, 잘못된 CN) | 2/2 |
| 3 | search_sci_patents | 3 (BI 영문, BI 한글, BI+AD) | 3/3 |
| 4 | get_sci_patent | 1 (정상 CN) | 1/1 |
| 5 | search_sci_citation_patents | 3 (3개 특허 CN) | 3/3 |
| 6 | search_sci_reports | 2 (BI=AI, 한글) | 2/2 |
| 7 | get_sci_report | 1 (정상 CN) | 1/1 |
| 8 | search_sci_trends | 2 (BI=AI, 한글) | 2/2 |
| 9 | get_sci_trend | 1 (정상 CN) | 1/1 |
| 10 | search_sci_scent | 3 (PY=2024, PY=2023, **BI 에러 검증**) | 3/3 |
| 11 | get_sci_scent | 1 (정상 CN) | 1/1 |
| 12 | search_sci_researchers | 2 (deep learning, 한글 양자) | 2/2 |
| 13 | get_sci_researcher | 1 (정상 CN) | 1/1 |
| 14 | search_sci_organizations | 2 (university, research institute) | 2/2 |
| 15 | get_sci_organization | 1 (정상 CN) | 1/1 |
| 16 | search_sci_infra_trend | 2 (BI=AI, BI=6G) | 2/2 |
| 17 | search_sci_tech_news | 3 (RD=20231127, RD=20240301, **BI 에러 검증**) | 3/3 |

## 2. 발견된 KISTI API 스펙 — searchField 호환 매트릭스

도구별 실제 동작 가능 필드를 동적 호출로 매핑(E4007 회피용). description에 반영:

| 도구 (target) | 지원 필드 | 미지원 (에러) |
|---|---|---|
| ARTI (논문) | BI, TI, AU, AB, KW, **PY** | PA, RD, AD 등 |
| REPORT (보고서) | BI, TI, AU, AB, KW, **PY** | PA, RD, AD 등 |
| PATENT (특허) | BI, TI, **PA, AN, AD, RN, RD, AB, IN, IC, CN** | PY |
| ATT (동향) | BI, TI, AU, AB, KW | **PY 불가** |
| TREND (인프라 동향) | BI, TI, KW | AU, AB, PY |
| RESEARCHER | BI, TI 만 | AU, AB, KW, PY |
| ORGAN (연구기관) | BI, TI 만 | AU, AB, KW, PY |
| SCENT (과학향기) | **PY 전용** | BI/TI/AU 전부 |
| SNEWS (금주의 뉴스) | **RD 전용** | BI/TI/AU 전부 |
| CIPATENT | cn 인자만 (searchQuery 없음) | n/a |

⇒ 각 도구 description에 정확한 지원 필드 명시 → LLM이 E4007 회피 가능.

## 3. 응답 가공 품질 점검 (샘플)

### 3.1 논문 검색 — 키 변환·숫자 변환·HTML 제거

```json
{
  "target": "ARTI",
  "status": "ok",
  "total_count": 8021,
  "service_type": "논문",
  "page": 1, "page_size": 1, "returned": 1,
  "items": [{
    "rownum": 1,
    "cn": "JAKO202317141070190",
    "db_code": "JAKO",
    "title": "양자컴퓨터 플랫폼 동향",
    "author": "임세진;김현지;김덕영;...",
    "journal_name": "정보보호학회지",
    "pub_year": 2023,          // ← int 변환
    "issn": ";;",
    "language": "한국어",
    "abstract": "...",         // ← HTML 태그 제거됨
    "has_fulltext": "Y",       // ← FulltextFlag 매핑
    "fulltext_url": "...",
    "content_url": "..."
  }],
  "pagination_hint": "총 8,021건 중 1건 반환 — 남은 8,020건은 cur_page를 증가시켜 순회."
}
```

### 3.2 연구기관 — 카운트 숫자 변환

```json
{
  "target": "ORGAN", "status": "ok", "total_count": 251,
  "items": [{
    "cn": "34717",
    "org_name_kr": "주식회사 연우이앤티",
    "org_name_en": "...",
    "paper_count": 0,        // ← int 변환
    "patent_count": 5,        // ← int 변환
    "report_count": 0
  }]
}
```

### 3.3 에러 분기 (SCENT를 BI로 호출)

```json
{
  "target": "SCENT", "status": "error", "total_count": 0,
  "items": [],
  "error": {
    "code": "E4007",
    "message": "searchField 값 오류",
    "status_message": "Bad Request"
  }
}
```

### 3.4 인증 메타 누출 점검

| 검사 키워드 | 응답 내 발견 |
|---|---|
| `client_id` | ❌ 없음 |
| `"token"` | ❌ 없음 |
| `session_id` | ❌ 없음 |
| client_id 값 (`46744…`) | ❌ 없음 |

## 4. 품질 등급 평가

| 항목 | 등급 | 근거 |
|---|---|---|
| 17개 도구 동작 안정성 | **A** | 34/34 통과 (100%) |
| 응답 정제 (KEY_MAPPING) | **A** | 약 80개 metaCode → 명료 영문 |
| 숫자 자동 변환 | **A** | pub_year/paper_count/patent_count 모두 int |
| HTML/CDATA 정제 | **A** | abstract·title·content 모두 깨끗 |
| 인증 메타 보안 | **A** | client_id/token/session_id 노출 없음 |
| 에러 분기 정확도 | **A** | E4007 등 KISTI 에러 코드 그대로 전달 |
| 페이지네이션 안내 | **A** | 남은 건수·순회 방법 자동 출력 |
| 도구 description 정확도 | **A** | 지원 필드를 도구별로 명시 (E4007 회피) |
| 토큰 자동 재발급 | **A** | E4103 자동, refresh 만료 시 재발급 |
| Rate limit 대응 | **A** | E4290 1→2→4→8s 지수 백오프 |

## 5. mcp-opendart / mcp-kr-legislation 대비 동등성

| 영역 | 상태 |
|---|---|
| 응답 표준 스키마(status·items·error) | ✅ 동등 |
| key 약자 → 명료 영문 변환 | ✅ 동등 (약 80개 매핑) |
| 숫자 필드 자동 변환 | ✅ 동등 |
| 페이지네이션 메타 | ✅ 동등 (`pagination_hint`) |
| 에러 코드 정제 | ✅ 동등 |
| 도구당 description·tags | ✅ 동등 |
| linked_tools/registry 메타 | ⚠️ NTIS 16개만 보유, ScienceON 17개는 미등록 (차후 보강) |
| 결과 캐싱 | ⚠️ NTIS 측만, ScienceON은 미적용 (차후 보강) |

## 6. 결론

- **17개 도구 전부, 다양한 입력(한글/영문, 단일·다중 필드, 페이지, 에러 케이스)에서 정상 동작**.
- 응답은 mcp-opendart 수준의 정제된 dict이며 인증 메타 비공개·HTML 정제·숫자 변환이 일관 적용됨.
- KISTI 측 API 스펙 차이(도구별 검색 필드 호환성)는 description에 명시되어 LLM이 잘못된 필드 사용을 회피할 수 있음.
- 잔여 갭(registry 메타, 캐싱)은 핵심 기능과 별개로 후속 작업으로 분리 가능.

## 7. 파일 변경

| 파일 | 변경 |
|---|---|
| `src/mcp_ntis/scienceon/tools.py` | 도구별 description에 정확한 지원 필드 명시 (E4007 회피) |
| `src/mcp_ntis/scienceon/parser.py` | KEY_MAPPING에 논문 부가 필드 6개 추가 (FulltextFlag → has_fulltext 등) |
| `evaluation/SCIENCEON_DEEP_QA.md` | **신규** — 본 보고서 |
