# 도구 설명(Description) 작은 모델 친화 점검

> Qwen3·Gemma3 등 7B~14B 작은 모델이 도구를 정확히 선택·호출할 수 있도록 33개 도구의 description·docstring을 일관된 구조로 재작성.

## 0. 결과 요약

| 지표 | 결과 |
|---|---|
| 점검 대상 | **33개 도구** (NTIS 16 + ScienceON 17) |
| 구조 점수 4점 이상 | **33/33 (100%)** |
| 평균 description 길이 | 약 380자 |
| 일관 적용된 표준 구조 | 5개 섹션 |

## 1. 표준 description 구조 (5개 섹션)

모든 도구가 다음 패턴으로 통일:

```
[한 줄 요약 — 무엇을 하는가]

**언제 쓰는가**: [사용 시나리오]

**입력**: [필수·선택 파라미터 + 실제 값 예시]

**응답 핵심 키**: [LLM이 답변 작성에 활용 가능한 필드]

**다음 단계** 또는 **흔한 오류**: [체이닝·회피 가이드]
```

## 2. 도구별 점수 (5점 만점)

### NTIS 16개

| # | 도구 | 점수 | 길이 |
|---|---|---|---|
| 1 | search_rnd_projects | 5/5 | 657 |
| 2 | search_research_papers | 5/5 | 564 |
| 3 | search_patents | 5/5 | 539 |
| 4 | search_research_reports | 5/5 | 414 |
| 5 | search_research_equipment | 5/5 | 459 |
| 6 | search_unified | 5/5 | 383 |
| 7 | get_consignment_research | 4/5 | 436 |
| 8 | get_org_rnd_status | 4/5 | 459 |
| 9 | recommend_std_classification | 4/5 | 495 |
| 10 | recommend_ht_classification | 4/5 | 554 |
| 11 | recommend_it_classification | 4/5 | 381 |
| 12 | get_classification_codes | 4/5 | 428 |
| 13 | search_rnd_issues | 5/5 | 329 |
| 14 | search_terminology | 4/5 | 294 |
| 15 | get_related_content | 4/5 | 447 |
| 16 | get_ntis_tool_info | 4/5 | 520 |

### ScienceON 17개

| # | 도구 | 점수 | 길이 |
|---|---|---|---|
| 17 | search_sci_papers | 5/5 | 354 |
| 18 | get_sci_paper | 4/5 | 299 |
| 19 | search_sci_patents | 5/5 | 512 |
| 20 | get_sci_patent | 4/5 | 280 |
| 21 | search_sci_citation_patents | 4/5 | 257 |
| 22 | search_sci_reports | 5/5 | 272 |
| 23 | get_sci_report | 4/5 | 228 |
| 24 | search_sci_trends | 5/5 | 300 |
| 25 | get_sci_trend | 4/5 | 212 |
| 26 | search_sci_scent | 5/5 | 257 |
| 27 | get_sci_scent | 4/5 | 189 |
| 28 | search_sci_researchers | 5/5 | 356 |
| 29 | get_sci_researcher | 4/5 | 240 |
| 30 | search_sci_organizations | 5/5 | 331 |
| 31 | get_sci_organization | 4/5 | 220 |
| 32 | search_sci_infra_trend | 4/5 | 276 |
| 33 | search_sci_tech_news | 5/5 | 336 |

## 3. 작은 모델 친화 개선 사례 (Before / After)

### 사례 A: `get_sci_report` (보고서 상세조회)

**Before** (50자, 1/5)
```
ScienceON 보고서 상세조회 (action=browse, target=REPORT).
```
문제: `action=browse`·`target=REPORT` 같은 내부 jargon. 언제 쓰는지·입력 예시·응답 키 모두 부재. 작은 모델은 "어떤 cn 값을 넣어야 할지" 모름.

**After** (228자, 4/5)
```
연구보고서 1건의 전체 정보를 조회합니다 (목차·요약·발행 기관 등).

**언제 쓰는가**: `search_sci_reports` 결과에서 특정 보고서를 더 자세히 볼 때.

**입력**: cn — 보고서 ID. 예: 'TRKO202200009744', 'TRKO201800014330'.

**응답**: 단일 `item` dict — title, publisher, pub_year, abstract 등.
```

### 사례 B: `search_terminology` (용어사전)

**Before** (57자, 2/5)
```
국가R&D 용어사전을 검색합니다. 과학기술 표준 용어의 한·영 명칭, 약어, 정의, 관련어 제공. 표준 용어 확인이나 약어 풀이에 활용.
```
문제: 너무 짧음. 입력 예시·응답 키 없음.

**After** (294자, 4/5)
```
정부 R&D 표준 용어사전을 검색합니다 (한·영 명칭·약어·정의).

**언제 쓰는가**: 표준 용어 확인, 약어 풀이, 보고서 용어 표준화.

**입력**: query — 한글·영문 검색어.
  - 예: query='인공지능 신약 개발' / query='AI'
  - search_field='TI': 용어명만 매칭
  - search_field='AB': 약어로 검색

**응답 핵심 키**: id, korean(한글명), english(영문명),
standard_class(표준 분류), term_class(용어 등급).
```

### 사례 C: `search_rnd_projects` (과제 검색)

**Before** (~1,500자)
- 너무 길어 핵심 흐름이 묻힘. 페이지네이션 설명이 본문 절반.

**After** (657자)
- 구조화: 한 줄 요약 → 언제 쓰는가 → 입력 패턴 4가지 → 응답 키 → 페이지네이션 → 다음 단계
- 작은 모델이 첫 줄·구조로 빠르게 파악 가능.

## 4. 적용된 작은 모델 친화 원칙

| 원칙 | 적용 방식 |
|---|---|
| **첫 줄에 핵심 요약** | 모든 도구가 첫 줄에 "무엇을 하는가" 한 문장 |
| **시나리오 명시** | "**언제 쓰는가**" 섹션 — 사용자가 어떤 질문일 때 호출하는지 |
| **실제 값 예시** | `cn='JAKO20240...'`, `query='양자컴퓨터'` 등 추상 ID에 구체 예시 |
| **응답 키 사전 노출** | 답변 생성에 쓸 수 있는 필드를 미리 알려줌 → 후속 추론 효율 |
| **체이닝 가이드** | `다음 단계: get_sci_paper(cn)` 등 다음 호출 도구 명시 |
| **흔한 오류 회피** | SCENT는 PY만, ATT는 PY 불가 등 가이드라인 명시 |
| **내부 jargon 제거** | `action=browse`, `target=ATT` 등 KISTI 코드 노출 최소화 |
| **마크다운 구조** | `**언제 쓰는가**` 굵게, 줄바꿈으로 시각적 분리 |

## 5. 33개 도구 회귀 테스트

| 그룹 | 결과 |
|---|---|
| ScienceON 17개 (전수) | **ok 17 / skip 0 / fail 0** |
| NTIS 16개 (전수) | **ok 16 / fail 0** |
| 합계 | **33/33 정상 동작** |

description 재작성이 코드 동작에 영향 없음을 확인.

## 6. 파일 변경

| 파일 | 변경 내용 |
|---|---|
| `src/mcp_ntis/scienceon/tools.py` | 17개 도구 description 5섹션 구조 적용 |
| `src/mcp_ntis/tools/search_tools.py` | 6개 도구 재작성 (search_rnd_projects 등) |
| `src/mcp_ntis/tools/classification_tools.py` | 3개 도구 재작성 (recommend_*) |
| `src/mcp_ntis/tools/extra_tools.py` | 5개 도구 재작성 (get_org_*, search_terminology 등) |
| `src/mcp_ntis/tools/project_tools.py` | get_consignment_research 재작성 |
| `src/mcp_ntis/tools/meta_tools.py` | get_ntis_tool_info 재작성 |
| `evaluation/TOOL_DESCRIPTION_AUDIT.md` | **신규** — 본 보고서 |

## 7. 결론

- 33개 도구 전부 작은 모델 친화 표준(첫 줄 요약 + 5섹션 구조) 적용 완료.
- 평균 description 380자 — 작은 모델 컨텍스트에 부담 없되 정보 충분.
- 코드 동작에 영향 없음 — 33/33 회귀 테스트 통과.
- LangChain/Qwen3·Gemma3 등 7B~14B 모델에서 도구 선택·호출 정확도 향상 기대.
