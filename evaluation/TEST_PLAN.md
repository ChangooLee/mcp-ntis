# NTIS MCP 심층 평가 — 테스트 계획서

> **목적**: NTIS MCP 서버의 15개 도구를 LLM 사용자 관점에서 비판적·보수적으로 평가한다.
> **평가일**: 2026-05-20
> **평가 환경**: NTIS_API_KEY 활성 (lg814619kv046cp808fk + 신규 키 9wp7g775409672d5hiv7)

## 1. 평가 철학

LLM이 NTIS MCP를 호출할 때, **도구 설명(description)과 응답 데이터만으로** 다음을 판단할 수 있어야 한다:
1. 사용자 질문에 어떤 도구를 사용해야 하는지
2. 어떤 파라미터를 어떤 값으로 넣어야 하는지
3. 응답을 받은 뒤 추가 호출이 필요한지, 어느 필드를 다음 호출에 써야 하는지
4. 최종 답변에 충분한 정보가 모였는지

이 4가지를 흐름 없이 수행할 수 있어야 "잘 설계된 MCP"라 평가한다.

## 2. 평가 대상 도구 매핑 (description 기준)

| 카테고리 | 도구 | LLM 추정 역할 |
|---|---|---|
| **검색** | `search_rnd_projects` | 과제 검색 (가장 풍부한 메타데이터, 연계 도구의 출발점) |
| | `search_research_papers` | 논문 검색 (커버리지 한계: 19만 건) |
| | `search_patents` | 특허 검색 (커버리지 한계: 38만 건) |
| | `search_research_reports` | 연구보고서 검색 |
| | `search_research_equipment` | 연구장비 검색 |
| | `search_unified` | 다중 컬렉션 동시 검색 |
| **상세** | `get_consignment_research` | 과제 id로 위탁/공동연구 조회 |
| | `get_org_rnd_status` | 기관 R&D 포트폴리오 (동명이기관 disambiguation 처리) |
| **분류** | `recommend_std_classification` | 과학기술표준분류 (과기부 계열) |
| | `recommend_ht_classification` | 보건의료기술분류 (질환/연구행위/산업기술 3종) |
| | `recommend_it_classification` | 산업기술분류 (산업부/중기부) |
| | `get_classification_codes` | 분류 코드 계층 탐색 (22개 최상위 대분류) |
| **부가** | `search_rnd_issues` | NTIS 선정 최신 트렌드 이슈 |
| | `search_terminology` | 국가R&D 표준 용어사전 |
| | `get_related_content` | AI 기반 유사 콘텐츠 추천 |

## 3. 10개 모의 질문

각 질문은 **(A) 도구 2개 이상**, 또는 **(B) 같은 도구의 파라미터 변형 반복 호출**을 강제하도록 설계되었다.

### Q1. 기관별 mRNA 백신 연구 추세 비교
> "최근 5년간 mRNA 백신 연구를 가장 활발히 한 국내 기관 3곳을 찾고, 각 기관의 연도별 R&D 성장 추세를 비교해줘."

- **예상 호출**: `search_rnd_projects(KW=mRNA, PY=2021-2025)` → 기관 빈도 집계 → `get_org_rnd_status × 3` → 연도별 추세 비교
- **난이도 핵심**: 결과 집계 + 동명이기관 disambiguation

### Q2. 전고체 배터리 연구 생태계 지도
> "전고체 배터리 핵심 과제 하나를 찾고, 그 과제와 유사한 다른 과제들로 한국의 연구 생태계 지도를 그려줘."

- **예상 호출**: `search_rnd_projects(KW)` → 대표 과제 선택 → `get_related_content(project)` → 추가 `search_rnd_projects` (관련 키워드 기반)
- **난이도 핵심**: ID 체이닝, content_id 정확성

### Q3. 트렌드 이슈별 정부 투자 증가 추세
> "NTIS 최신 트렌드 이슈 5개 중 정부 투자가 가장 빠르게 늘고 있는 분야를 찾아줘. 각 이슈별 최근 2년간 연구비 추세를 비교해줘."

- **예상 호출**: `search_rnd_issues()` → 이슈명 × 연도 매트릭스로 `search_rnd_projects` 10회 호출 → 예산 집계
- **난이도 핵심**: 다중 반복 호출 + 응답 일관성 + 정량 분석

### Q4. ETRI 최대 예산 AI 과제의 공동연구 구조
> "ETRI(한국전자통신연구원)가 주관한 인공지능 과제 중 가장 큰 예산을 받은 과제의 모든 공동연구기관과 분담 연구비를 알려줘."

- **예상 호출**: `search_rnd_projects(OG=ETRI + KW=인공지능)` → 예산 정렬 → `get_consignment_research(project_id)`
- **난이도 핵심**: 다중 검색 필드 결합, 정렬, ID 추적

### Q5. CRISPR 유전자 편집 연구 분류 통합 검증
> "'CRISPR-Cas9 기반 유전자 편집으로 희귀질환을 치료'하는 연구의 표준분류·보건의료기술분류·산업기술분류를 모두 추천받고, 정확도 1위 표준분류의 상위/하위 계층 코드를 보여줘."

- **예상 호출**: `recommend_std_classification` + `recommend_ht_classification` + `recommend_it_classification` (병렬) → `get_classification_codes(search_code=정확도1위 small_code 또는 그 parent)`
- **난이도 핵심**: 3종 통합 + 코드 계층 양방향 탐색 (상위/하위)

### Q6. 동명이인 연구자 disambiguation
> "한국에서 '김철수'라는 이름의 연구자가 양자컴퓨터 관련 과제를 수행한 사례를 모두 찾고, 동명이인 여부를 기관별로 그룹화해서 정리해줘."

- **예상 호출**: `search_rnd_projects(AU=김철수, KW=양자)` + 페이지 반복 → institution 클러스터링
- **난이도 핵심**: AU 동명이인 처리 한계, 페이지네이션

### Q7. 2024 KAIST mRNA 과제의 성과 연계
> "2024년 KAIST가 수행한 mRNA 관련 과제 중 실제 논문이나 특허가 도출된 것을 찾아 성과를 분석해줘."

- **예상 호출**: `search_rnd_projects(OG=KAIST + KW=mRNA + PY=2024)` → 각 project_id로 `search_research_papers(CN=)` + `search_patents(CN=)`
- **난이도 핵심**: project_id ↔ 성과 매핑, CN 검색 필드 사용법

### Q8. 항암면역 vs 치매신약 5년 투자 비교
> "보건의료 분야에서 '항암 면역치료' vs '치매 신약' 정부 투자를 5년간 연도별로 비교해줘."

- **예상 호출**: `search_rnd_projects` × 2 분야 × 5년 = 10회 + 예산 집계
- **난이도 핵심**: 다회 호출 + 정량 비교 + 자동 중복 제거 영향

### Q9. 전자현미경 보유 기관 매핑
> "전자현미경을 가장 많이 보유한 기관 3곳을 찾고, 그 기관들이 그 장비로 수행 중인 연구 분야를 매핑해줘."

- **예상 호출**: `search_research_equipment(query=전자현미경)` → 기관 빈도 집계 → `search_rnd_projects(OG)` × 3
- **난이도 핵심**: 장비-과제 연계, 기관별 분야 추출

### Q10. 양자 우월성 용어→연구 통합 조사
> "'양자 우월성(Quantum Supremacy)'의 표준 정의를 확인하고, 그 개념을 다루는 국내 과제·논문·특허를 통합적으로 조사해줘."

- **예상 호출**: `search_terminology(양자 우월성)` → 정의 확인 → `search_unified(project,rpaper,rpatent)` 또는 개별 검색 도구 호출
- **난이도 핵심**: 용어→실제 연구 연계, search_unified vs 개별 검색 선택

## 4. 평가 프로토콜 (각 질문마다 5단계 적용)

| Step | 평가 항목 | 출력 |
|---|---|---|
| **A. 도구 선택** | description만 보고 첫 호출 도구가 명확한가? | 명확 / 모호(이유) |
| **B. 파라미터 결정** | 파라미터 값을 description/docstring으로 추론 가능한가? | 가능 / 추론 실패(어느 필드) |
| **C. 응답 데이터** | 응답에 다음 단계 호출에 필요한 정보가 모두 있는가? | 충분 / 누락(어느 필드) |
| **D. 체이닝 일관성** | 도구 간 id/형식이 일치하는가? | 일치 / 불일치(예시) |
| **E. 최종 합성** | 사용자 질문에 답할 수 있는가? | 가능 / 부분 / 불가 |

## 5. 평가 결과 분류 기준

| 우선순위 | 정의 |
|---|---|
| **Critical** | LLM이 도구를 잘못 선택하거나 호출 실패가 빈번 → 즉시 수정 |
| **High** | 응답 데이터 누락/형식 불일치로 후속 호출 실패 → 다음 릴리스 |
| **Medium** | description 모호/예시 부족으로 추론 실패 → 문서 개선 |
| **Low** | 토큰 효율성, 가독성 등 미세 개선 |

## 6. 산출물

| 파일 | 내용 |
|---|---|
| `evaluation/TEST_PLAN.md` | 본 문서 |
| `evaluation/TEST_RESULTS.md` | Q1~Q10 호출 내역 + 5단계 평가 |
| `evaluation/IMPROVEMENTS.md` | Critical/High/Medium/Low 분류 개선 사항 |
