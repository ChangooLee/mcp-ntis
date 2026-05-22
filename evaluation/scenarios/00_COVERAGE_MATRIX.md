# 시나리오 도구 커버리지 매트릭스

총 40개 도구(NTIS 16 + ScienceON 24)를 10개 시나리오에 걸쳐 한 번 이상 호출하도록 설계.

## 시나리오 개요

| # | 제목 | 비즈니스 의도 |
|---|---|---|
| 1 | AI 신약 개발 시장 진출 평가 | 정부 R&D 강도, 학술·특허 우위, 진입 전략 |
| 2 | 전고체 배터리 협력사 발굴 | 출연연·중소기업 매핑, 위탁 협력 망, 장비 확보 |
| 3 | mRNA 백신 R&D 생태계 분석 | 핵심 PI, 연도별 정부 펀딩, 학술 임팩트 |
| 4 | 양자컴퓨터 핵심 인재 영입 평가 | 연구자 학술 이력, 과제 수행, 영입 가능성 |
| 5 | 스마트 토일렛 헬스케어 컨소시엄 | 융합 기술 매핑, 컨소시엄 후보, 펀딩 경로 |
| 6 | CRISPR 신약 정부 분류·펀딩 | 표준 분류 추천, DDC 주제, 관련 과제 |
| 7 | 차세대 디스플레이 R&D 효율 비교 | 예산÷산출물, 출원인 순위, 산업 이전 |
| 8 | 자율주행 학술↔산업 연결 | 보고서·과학향기·추천 콘텐츠 종합 |
| 9 | 6G 통신 트렌드·정부 이슈 진단 | 동향, R&D 이슈, 권호 TOC, 링크 리졸버 |
| 10 | ETRI 파트너십 사전 실사 | 기관 R&D 현황, 협력 네트워크, 학술 산출 |

## NTIS 16개 도구 매핑

| 도구 | 시나리오 |
|---|---|
| search_rnd_projects | 1, 3, 6, 7 |
| search_research_papers | 1, 4, 7, 10 |
| search_patents | 1, 7, 10 |
| search_research_reports | 8 |
| search_research_equipment | 2, 5 |
| search_unified | 2, 5, 9 |
| get_consignment_research | 2, 10 |
| get_org_rnd_status | 2, 4, 10 |
| recommend_std_classification | 1, 6 |
| recommend_ht_classification | 5 |
| recommend_it_classification | 5 |
| get_classification_codes | 6 |
| get_related_content | 8 |
| search_rnd_issues | 3, 9 |
| search_terminology | 1 |
| get_ntis_tool_info | 9 |

## ScienceON 24개 도구 매핑

| 도구 | 시나리오 |
|---|---|
| search_sci_papers | 1, 3, 4, 5, 6, 7, 10 |
| get_sci_paper | 1, 3 |
| search_sci_patents | 1, 2, 5, 7 |
| get_sci_patent | 1 |
| search_sci_reports | 8 |
| get_sci_report | 8 |
| search_sci_trends | 1, 9 |
| get_sci_trend | 1, 9 |
| search_sci_scent | 8 |
| get_sci_scent | 8 |
| search_sci_researchers | 3, 4, 10 |
| get_sci_researcher | 3, 4 |
| search_sci_organizations | 2, 5 |
| get_sci_organization | 2, 10 |
| search_sci_authors (E4302) | 4 |
| get_sci_author (E4302) | 4 |
| search_sci_applicant (E4302) | 7 |
| search_sci_function (E4302) | 6 |
| search_sci_service (E4302) | 5 |
| search_sci_ddc (E4302) | 6 |
| search_sci_education (E4302) | 7 |
| sci_paper_toc (E4302) | 9 |
| sci_resolver (E4302) | 9 |
| recommend_sci_content (E4302) | 8 |

## 보고서 작성 원칙

1. **시스템 이름 노출 금지** — NTIS/ScienceON/KISTI 대신 "국가 R&D 정보망"·"학술·특허 데이터베이스"
2. **📚 자료 출처 섹션 필수** — 본문 표·수치 옆 (정부 R&D)·(학술 DB) 표기
3. **7개 표준 섹션** — 🎯요약, 📊데이터, 🔍심층, 💼권고, ⚠️리스크, 📈KPI, 💡추가조사
4. **E4302 도구** — 권한 미부여 시 "한계" 섹션에서 명시, 본문에 시스템 에러 노출 X
5. **실데이터 기반** — Python으로 도구 직접 호출, 결과를 보고서에 반영
