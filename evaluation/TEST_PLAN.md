# NTIS + ScienceON MCP 심층 평가 — 테스트 계획서 v2

> **목적**: NTIS MCP (정부 R&D) + ScienceON MCP (학술/특허 전체) 양쪽 도구를 융합 활용하여 LLM이 어떻게 종합 분석을 수행하는지 비판적·보수적으로 평가한다.
> **평가일**: 2026-05-22 (v2)
> **평가 환경**: NTIS 16개 + ScienceON 24개 = **40개 도구**

## 1. 평가 철학 (v2 확장)

v1에서는 NTIS 단일 데이터 소스로 평가했지만, NTIS는 **국가 R&D 연계 데이터만** 수록(논문 19만, 특허 38만)이므로 민간/순수 학문 영역의 사각지대가 존재했다. ScienceON 통합으로:

- **논문**: 19만 (NTIS) → **59만 (ScienceON)** = 3배 확장
- **특허**: 38만 (NTIS) → **78만 (ScienceON)** = 2배 확장
- **신규 카테고리**: 동향 보고서(KISTI 큐레이션), 과학향기, 연구자 전거, 인용 특허, 권호 TOC, 링크리졸버, 콘텐츠 추천

LLM이 두 데이터 소스의 차이를 인식하고 적절히 교차 검증/보완하는지가 핵심 평가 포인트다.

## 2. 도구 분류 (40개)

### NTIS (16개)
- 검색 6: search_rnd_projects, search_research_papers, search_patents, search_research_reports, search_research_equipment, search_unified
- 과제 상세 2: get_consignment_research, get_org_rnd_status
- 분류 추천 3: recommend_std/ht/it_classification
- 부가 4: search_rnd_issues, search_terminology, get_classification_codes, get_related_content
- 메타 1: get_ntis_tool_info

### ScienceON (24개) — `sci_` 접두사
- 논문 4: search_sci_papers, get_sci_paper, sci_resolver, sci_paper_toc
- 특허 3: search_sci_patents, get_sci_patent, search_sci_applicant
- 보고서 2: search_sci_reports, get_sci_report
- 동향 4: search_sci_trends, get_sci_trend, search_sci_scent, get_sci_scent
- 연구자·기관·저자 6: search_sci_researchers, get_sci_researcher, search_sci_organizations, get_sci_organization, search_sci_authors, get_sci_author
- 지식 인프라 5: search_sci_function, search_sci_service, search_sci_ddc, search_sci_education, recommend_sci_content

> **권한 안내**: ScienceON 일부 도구는 KISTI에서 API 단위로 권한을 부여합니다. 권한 없는 도구 호출 시 `E4302` 응답.
> **권한 확인됨 (200 OK)**: 논문/특허/보고서/동향/과학향기/연구자/연구기관 검색·상세 (14개)
> **E4302 (권한 신청 필요)**: APPLICANT/AUTHOR/FUNCTION/SERVICE/DDC/KACADEMY/RESOLVER/VOLUME/RECOMMEND (10개)

## 3. 10개 융합 시나리오 (v2)

각 질문은 **(A) NTIS + ScienceON 양쪽 도구 동시 활용**, **(B) 두 데이터 소스의 차이를 인사이트로 도출**, **(C) 정량 분석(`fetch_all=True` 또는 `rowCount` 다회 호출)을 강제**하도록 설계됨.

---

### Q1. mRNA 백신 — 정부 R&D vs 전체 학술 출간량 격차

> "최근 5년간 mRNA 백신 연구를 가장 활발히 한 국내 기관 3곳을 찾고, **NTIS의 정부지원 과제 수**와 **ScienceON의 실제 학술 논문 수**를 같은 기관 기준으로 비교해줘. 정부 펀딩과 실제 학술 출간량 사이의 비율로 어느 기관이 가장 펀딩 효율이 좋은지 평가해줘."

**예상 호출**
```
NTIS:    search_rnd_projects(query='mRNA 백신', fetch_all=True, PY=2021-2025) → 상위 3개 기관 추출
NTIS:    get_org_rnd_status × 3 (auto_resolve)
ScienceON: search_sci_papers({"BI": "mRNA", "AU": "<기관명>"}) × 3 → 학술 출간량
교차 집계: 정부지원금 / 논문 수 = "건당 펀딩 효율"
```

**핵심 평가**: ScienceON이 NTIS 대비 3배 큰 논문 모집단을 제공하므로 "정부 펀딩 → 실제 산출물" 효율 측정 가능. 단순 정부 펀딩만 보는 v1보다 한 단계 깊은 인사이트.

---

### Q2. 전고체 배터리 — 한국 연구의 글로벌 영향력

> "전고체 배터리 분야에서 한국이 글로벌 영향력을 가진 정도를 평가해줘. NTIS 과제로 정부 투자 규모, ScienceON 논문 검색으로 한국 학자의 학술 출간량, ScienceON 특허 검색으로 출원 활동을 종합 비교해줘. 한국이 더 강한 영역(특허 vs 논문)이 어느 쪽인지 결론을 내려줘."

**예상 호출**
```
NTIS:    search_rnd_projects(query='전고체 배터리', fetch_all=True) — 정부 투자
ScienceON: search_sci_papers({"BI": "solid-state battery"}, rowCount=100) — 학술 논문
ScienceON: search_sci_patents({"BI": "solid-state battery"}, rowCount=100) — 특허
ScienceON: search_sci_trends({"BI": "전고체"}) — KISTI 큐레이션 동향 보고서
NTIS:    get_related_content(project) — 추가 유사 과제
```

**핵심 평가**: 특허·논문 출간량의 균형을 보고 한국 R&D의 "응용 vs 기초" 강점을 도출하는지. NTIS만으로는 불가능.

---

### Q3. 트렌드 이슈 융합 분석 (정부 큐레이션 + KISTI 큐레이션)

> "NTIS가 선정한 최신 R&D 이슈와 ScienceON이 큐레이션한 산업기술 동향(TREND/ATT)을 함께 분석해줘. 두 큐레이션이 일치하는 분야와 불일치하는 분야를 식별하고, 각 이슈에 대한 학술적 뒷받침(논문 출간량)이 충분한지 평가해줘."

**예상 호출**
```
NTIS:    search_rnd_issues() — 정부 선정 5개 이슈
ScienceON: search_sci_trends({"BI": "AI"}, rowCount=20) — KISTI 큐레이션 동향
교차 매칭: 두 큐레이션 비교
ScienceON: search_sci_papers({"BI": "<이슈명>"}) × 5 — 학술 뒷받침
NTIS:    search_rnd_projects × 5 (이슈명, fetch_all=True) — 정부 펀딩 규모
```

**핵심 평가**: 정부와 KISTI가 동일 트렌드를 다르게 식별하는지, 학술 뒷받침이 정책 우선순위와 일치하는지.

---

### Q4. ETRI AI — 핵심 인력 식별 (정부 과제 + 학술 출간)

> "ETRI(한국전자통신연구원)가 주관한 AI 과제 중 가장 큰 예산 과제의 공동연구기관과 분담 연구비를 보여주고, **ScienceON 연구자 검색**으로 그 과제에 참여한 핵심 PI들의 학술 출간 이력을 추적해줘. 어떤 PI가 가장 활발한 학술 활동을 하고 있는지 식별해줘."

**예상 호출**
```
NTIS:    search_rnd_projects(query='AI', OG=ETRI, fetch_all=True) → 최대 예산 과제
NTIS:    get_consignment_research(pjt_id) → 공동연구기관 + PI 이름
ScienceON: search_sci_researchers({"BI": "<PI name>"}) × N → 핵심 PI 검색
ScienceON: get_sci_researcher(cn) — 각 PI 상세
ScienceON: search_sci_papers({"AU": "<PI name>"}) × N → 학술 출간
```

**핵심 평가**: 정부 과제 데이터(NTIS) → 실제 연구자(ScienceON RESEARCHER) → 학술 산출물(ScienceON ARTI) 3단 체인 추적 능력.

---

### Q5. CRISPR — 분류 추천과 실제 학술 분포의 일치도

> "'CRISPR-Cas9 기반 유전자 편집으로 희귀질환 치료' 연구의 NTIS 분류(표준/보건의료/산업기술 3종)를 추천받고, **ScienceON DDC 주제분류**로도 동일 텍스트를 분류해줘. 두 분류 체계가 동일 연구를 어떻게 다르게 매핑하는지 비교하고, 실제 ScienceON 논문 검색 결과의 분류 분포와 일치도를 평가해줘."

**예상 호출**
```
NTIS:    recommend_std_classification + recommend_ht_classification + recommend_it_classification
NTIS:    get_classification_codes(NTIS001, search_code=top_medium) — 계층 탐색
ScienceON: search_sci_ddc(subject="CRISPR") — DDC 주제 분류 (E4302 권한 신청 필요)
ScienceON: search_sci_papers({"BI": "CRISPR Cas9"}, rowCount=100) — 실제 분포
교차 분석: NTIS LA0306 vs ScienceON DDC 코드
```

**핵심 평가**: NTIS·ScienceON 두 분류 체계의 차이를 LLM이 이해하는지. ScienceON DDC는 권한 필요 시 안내.

---

### Q6. 동명이인 disambiguation — 저자 전거 활용

> "한국에서 '김철수' 양자컴퓨터 연구자를 찾으려고 해. NTIS의 AU 검색만으로는 동명이인 분리가 어려우니, **ScienceON 저자 전거(AUTHOR) 검색**을 사용해서 표준화된 식별자 기반으로 정확히 분리해줘. 저자별 학술 출간 분야와 NTIS 과제 이력을 매칭해서 진짜 양자컴퓨터 연구자를 식별해줘."

**예상 호출**
```
NTIS:    search_rnd_projects(query='김철수', search_field='AU', fetch_all=True)
ScienceON: search_sci_authors({"BI": "Kim Chul-soo"}) — 저자 전거 (E4302 권한 필요)
ScienceON: get_sci_author(cn) × N — 각 저자 표준화 정보
ScienceON: search_sci_papers({"AU": "Kim Chul-soo"}) — 양자 키워드 매칭
교차 검증: AUTHOR CN ↔ ScienceON 논문 ↔ NTIS 과제
```

**핵심 평가**: NTIS의 동명이인 한계(v1에서 식별 실패)를 ScienceON 저자 전거로 극복할 수 있는지. 권한 미부여 시 한계 명시.

---

### Q7. KAIST mRNA — 정부 과제와 실제 SCI 논문 매핑

> "2024년 KAIST가 수행한 mRNA 관련 과제 3건의 책임자 이름을 NTIS에서 얻은 뒤, **ScienceON 논문 검색**으로 각 책임자의 최근 SCI 논문을 찾아 과제와의 연관성을 분석해줘. NTIS의 성과 매핑이 안 되는 케이스(project_id 역추적 불가)를 ScienceON으로 우회해줘."

**예상 호출**
```
NTIS:    search_rnd_projects(query='mRNA', OG=한국과학기술원, PY=2024) → PI 3명
ScienceON: search_sci_researchers({"BI": "<PI>"}) × 3 → 연구자 CN
ScienceON: search_sci_papers({"AU": "<PI>"}, rowCount=20) × 3 → SCI 논문
ScienceON: get_sci_paper(cn) × N — 각 논문 상세
연관성 분석: 논문 제목·초록 vs 과제 목표 매칭
```

**핵심 평가**: v1에서 NTIS만으로 실패한 "project_id → 논문" 매핑을 ScienceON으로 우회 성공할 수 있는지.

---

### Q8. 항암면역 vs 치매신약 — 정부 예산 + 학술 출간량 동시 비교

> "보건의료 분야에서 '항암 면역치료' vs '치매 신약' 정부 투자(NTIS, 5년)와 학술 출간량(ScienceON 논문, 같은 기간)을 동시 비교해줘. 정부 펀딩 1억원당 논문 수를 계산하여 어느 분야가 더 효율적인지 평가해줘."

**예상 호출**
```
NTIS:    search_rnd_projects × 2분야 × 5년 = 10회 (fetch_all=True) — 정부 예산
ScienceON: search_sci_papers × 2분야 × 5년 = 10회 — 학술 출간량
ScienceON: search_sci_trends × 2분야 — KISTI 동향 보고서 추가
계산: (정부지원 합계) / (논문 수) = 논문 1편당 정부 펀딩
```

**핵심 평가**: 두 분야의 R&D 효율을 정량적으로 평가. ScienceON 논문 데이터로 NTIS 펀딩의 산출물 측정 가능.

---

### Q9. 전자현미경 — 보유 기관의 연구 산출물 매핑

> "전자현미경을 가장 많이 보유한 기관 3곳(NTIS)을 찾고, **ScienceON 연구기관 검색**으로 각 기관의 학술 출간 활동을 조회해줘. 전자현미경을 활용했을 것으로 보이는 분야(전자/구조분석)의 논문 분포를 매핑해서 장비-성과 연계를 확인해줘."

**예상 호출**
```
NTIS:    search_research_equipment(query='전자현미경', fetch_all=True) → 상위 3개 기관
ScienceON: search_sci_organizations({"BI": "<기관명>"}) × 3 → 기관 CN
ScienceON: get_sci_organization(cn) × 3 → 기관 상세
ScienceON: search_sci_papers({"BI": "TEM 또는 cryo-EM"}, "AF": "<기관명>") × 3 → 장비 활용 논문
교차 분석: 장비 수 vs 논문 출간량
```

**핵심 평가**: 장비 인프라 → 학술 산출 연계 분석을 두 시스템 융합으로 수행.

---

### Q10. 양자 우월성 — 4중 검증

> "'양자 우월성(Quantum Supremacy)' 개념의 한국 R&D 활동을 4가지 데이터 소스로 교차 검증해줘:
> ① NTIS 통합검색(과제+논문+특허)
> ② ScienceON 논문 검색 (한국이 출간한 모든 학술 논문)
> ③ ScienceON 특허 검색 (전체 등록 특허)
> ④ ScienceON 동향 보고서 (KISTI 큐레이션)
>
> 네 데이터 소스에서 추출한 건수와 핵심 키워드를 비교해서 한국의 양자 R&D 강점(이론·하드웨어·응용 중 어느 영역)을 결론지어줘."

**예상 호출**
```
NTIS:    search_terminology({"BI": "양자"}) — 표준 용어 정의
NTIS:    search_unified(collection='project,rpaper,rpatent', query='양자 우월성')
ScienceON: search_sci_papers({"BI": "quantum supremacy"}, rowCount=50)
ScienceON: search_sci_patents({"BI": "quantum computing"}, rowCount=50)
ScienceON: search_sci_trends({"BI": "양자컴퓨터"})
4-way 비교: 건수·SCI 비율·키워드 클러스터
```

**핵심 평가**: 4개 데이터 소스 결과 융합으로 단순 "건수 합계"가 아닌 **카테고리별 한국 R&D 강약점 판별**.

---

## 4. 평가 프로토콜 (각 질문마다 6단계 — v2 확장)

| Step | 평가 항목 | 출력 |
|---|---|---|
| **A. 도구 선택** | NTIS 도구와 ScienceON 도구 중 적절히 선택하는가? | 명확 / 한쪽만 / 모호 |
| **B. 파라미터 결정** | description만으로 두 도구의 다른 파라미터(query JSON vs SRWR) 추론 가능한가? | 가능 / 추론 실패 |
| **C. 응답 데이터** | 두 도구의 다른 응답 형식(JSON vs XML)을 LLM이 동시 처리하는가? | 충분 / 누락 |
| **D. 체이닝 일관성** | NTIS id ↔ ScienceON CN 매칭 시도하는가? | 일치 / 불일치 |
| **E. 교차 검증** | 두 데이터 소스의 차이를 인사이트로 도출하는가? **(v2 신규)** | 도출 / 단순 합산 / 한쪽 무시 |
| **F. 최종 합성** | 사용자 질문에 답변 가능하며 정량 비교가 있는가? | 가능 / 부분 / 불가 |

## 5. ScienceON 권한 정책 영향

질문 처리 중 `E4302` 발생 시 LLM의 행동을 평가:
- ❌ 그대로 사용자에게 에러 노출
- ✅ "권한 미부여" 명시 + KISTI 헬프데스크 안내 + 대체 도구 활용
- ✅ NTIS 도구로 우회 가능 여부 판단

## 6. 평가 결과 분류 기준

| 우선순위 | 정의 |
|---|---|
| **Critical** | LLM이 도구를 잘못 선택, 두 시스템 차이를 무시, 호출 실패 빈번 |
| **High** | 응답 데이터 누락, 형식 불일치로 후속 호출 실패 |
| **Medium** | description 모호, 두 도구 비교 인사이트 부족 |
| **Low** | 토큰 효율성, 가독성 |

## 7. 산출물

| 파일 | 내용 |
|---|---|
| `evaluation/TEST_PLAN.md` | 본 문서 (v2) |
| `evaluation/TEST_RESULTS.md` | Q1~Q10 호출 내역 + 6단계 평가 |
| `evaluation/IMPROVEMENTS.md` | 개선 사항 분류 |
| `evaluation/QA_SHOWCASE.md` | LLM 답변 예시 (Streamlit 챗봇 실행) |

## 8. v1 → v2 변경 요약

| 항목 | v1 | v2 |
|---|---|---|
| 도구 수 | 16개 (NTIS only) | **40개 (NTIS 16 + ScienceON 24)** |
| 데이터 소스 | 정부 R&D 연계만 | 정부 R&D + KISTI 전체 학술/특허 |
| 논문 모집단 | 19만 | **59만** |
| 특허 모집단 | 38만 | **78만** |
| 동명이인 처리 | NTIS AU 매칭 한계 | **ScienceON AUTHOR 전거** 활용 (권한 필요) |
| 평가 단계 | 5단계 | 6단계 (교차검증 추가) |
| 정량 비교 | 단일 데이터 | **두 데이터 소스 교차** |
