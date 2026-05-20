---
name: llm-workflow
description: LLM이 NTIS MCP를 활용해 복합 R&D 분석 질문에 답하는 표준 워크플로우
---

# LLM 워크플로우 가이드

NTIS MCP를 사용해 R&D 동향·기관·트렌드를 분석할 때 따라야 할 표준 단계.

## 1. 도구 발견 (Discovery)

질문을 받으면 먼저 어떤 도구를 쓸지 모를 수 있다. 다음 순서로 결정:

```
1. get_ntis_tool_info()          # 전체 카테고리 목록 — 큰 그림 파악
2. get_ntis_tool_info(tag='검색')  # 특정 카테고리만 필터
3. get_ntis_tool_info(tool_name='search_rnd_projects')  # 선택한 도구의 상세 활용 패턴 확인
```

linked_tools 필드를 통해 다음에 호출할 도구를 자연스럽게 발견.

## 2. 분석 패턴별 표준 워크플로우

### 2.1 기관 분석 (예: "ETRI의 AI 연구는?")

```
1) search_rnd_projects(query='인공지능', add_query='OG=한국전자통신연구원')
   → 결과의 id 추출
2) 결과 정렬·집계 (가장 큰 예산, 최근 연도 등)
3) 필요시 get_consignment_research(project_id=<id>) → 공동연구 구조
4) get_org_rnd_status(org_name='한국전자통신연구원', auto_resolve=True)
   → 기관 전체 R&D 포트폴리오
```

### 2.2 트렌드 분석 (예: "지금 가장 핫한 분야는?")

```
1) search_rnd_issues()  # 최신 5개 이슈
2) 각 이슈명으로 search_rnd_projects 호출 → 연도별 비교
3) 정량 비교 필요 시 fetch_all=True (페이지 순회)
```

### 2.3 분류 추천 (예: "이 연구는 어디로 분류되나?")

```
1) recommend_std_classification(text=<설명>)    # 일반 R&D
2) recommend_ht_classification(text=<설명>)     # 보건의료 시
3) recommend_it_classification(text=<설명>)     # 산업기술 시
4) get_classification_codes(code_type='NTIS001', search_code=<top_medium_code>)
   → 상위/하위 계층 확인
```

부처를 모르면 세 도구 모두 호출해서 정확도 비교.

### 2.4 정량 비교 (예: "분야 A vs B 5년간 정부 투자")

```
1) for year in years:
       search_rnd_projects(query=A, add_query=f'PY={year}/SAME', fetch_all=True)
2) for year in years:
       search_rnd_projects(query=B, add_query=f'PY={year}/SAME', fetch_all=True)
3) 페이지 순회 결과 합산 → 정확한 추세 비교
```

⚠️ fetch_all=False로 합산하면 100건 상한 때문에 부정확 → 반드시 fetch_all=True

### 2.5 유사 과제 확장 (예: "이 과제와 비슷한 것은?")

```
1) search_rnd_projects → 핵심 과제 id 식별
2) get_related_content(content_type='project', content_id=<id>)
   → similarity_score 기반 추천 10건
3) 추천 결과의 id로 추가 search_rnd_projects 호출 가능
```

## 3. 응답 메타 활용

LLM은 응답의 메타 필드를 반드시 확인:

| 메타 | 의미 | 대응 |
|---|---|---|
| `pagination_warning` | total 대비 일부만 반환됨 | fetch_all=True로 재호출 또는 페이지 추가 |
| `fetch_all_truncated` | max_fetch 한도 초과 | max_fetch 증가 또는 분석 방식 변경 |
| `deduplicated` | 연도별 중복 제거됨 | 정상 (참고용) |
| `auto_resolved` | 동명이기관 자동 선택됨 | warning 필드 확인하여 적합한지 판단 |
| `disambiguation: true` | 동명이기관 후보 다수 | matching_org_names 보고 사용자에게 확인 또는 org_bno 사용 |
| `error_type` | 분류 추천 실패 | text_too_short → 텍스트 보강 / insufficient_terms → 전문 용어 추가 |

## 4. 답변 작성 시 주의

- **단순 카운트 나열 금지**: 데이터의 의미를 분석 — "왜 이 분야가 1위인가?", "왜 단가가 변했나?"
- **정량 비교는 fetch_all 결과로**: 100건 상한 모르고 단순 합산하면 LLM 신뢰도 추락
- **MCP 메타 노출 자제**: 사용자에게 "pagination_warning이 있어서…"라고 말하지 말고, 데이터의 한계와 의미를 자연스럽게 설명
- **외부 지식과 결합**: NTIS는 한국 국가 R&D만 — 글로벌 비교나 학계 정의는 외부 지식 보강 필요

## 5. 일반적인 분석 결과 구조

좋은 분석 답변 템플릿:

```
1) 결과 요약 (핵심 수치 1~2개)
2) 표 또는 순위 (상위 3~5개)
3) 패턴/인사이트 (왜 그런가)
4) 한계 또는 보완 (NTIS 커버리지·동명이기관 등)
5) 후속 질문 제안 (선택)
```
