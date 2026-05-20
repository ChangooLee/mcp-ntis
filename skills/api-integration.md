---
name: api-integration
description: NTIS OpenAPI 엔드포인트 통합 및 인증 방식
---

# NTIS API 통합 가이드

## 1. 인증 키 체계

NTIS는 두 가지 백엔드를 운영하며 키가 분리되어 있다.

| 키 | 변수 | 사용 엔드포인트 |
|---|---|---|
| 기본 승인키 | `NTIS_API_KEY` | 검색·과제·기관·분류추천 등 대부분 |
| 신규 승인키 | `NTIS_NEW_API_KEY` | 이슈로보는R&D, 분류코드(targetSearch), 용어사전(ntisDic) |

`client.py`의 `_base_params()` / `_new_params()`가 이 분리를 처리한다.

## 2. 엔드포인트 목록

| 기능 | URL | 파라미터 | 인증 |
|---|---|---|---|
| 과제 검색 | `/openApi/pjtSearch/project` | SRWR, searchFd, searchRnkn | apprvKey (기본) |
| 성과 검색 | `/openApi/natRnDSearch` | SRWR, searchFd, collection | apprvKey (기본) |
| 통합 검색 | `/openApi/totalRstSearch` | **query** (SRWR 아님!), searchFd | apprvKey (기본) |
| 위탁/공동 | `/openApi/projectuOrg` | pjtId | apprvKey (기본) |
| 분류 추천 | `/openApi/rcmncls` | collection, rqstDes | apprvKey (기본) |
| 기관현황 | `/openApi/orgRndInfo` | reqOrgNm, reqOrgBno | apprvKey (기본) |
| 이슈 | `/openApi/issue` | SRWR | apprvKey (**신규**) |
| 용어사전 | `/openApi/ntisDic` | query, searchField | apprvKey (**신규**) |
| 분류코드 | `/openApi/targetSearch` | rqstSlctCd | apprvKey (**신규**) |
| 유사추천 | `/openApi/ConnectionContent` | collection, **pjtId** | apprvKey (기본) |

## 3. 알려진 함정

### 3.1 totalRstSearch는 SRWR이 아닌 `query`

다른 검색 API는 모두 `SRWR` 파라미터인데, 통합검색만 `query`를 받음. SRWR로 호출하면 검색어를 무시하고 전체 결과를 반환.

### 3.2 ConnectionContent는 project만 지원

`content_type='paper'` 등 다른 컨텐츠는 모두 빈 결과. project + `pjtId` 조합만 정상 작동.

### 3.3 SITID 매핑

`totalRstSearch` 응답의 SITID는 일반 검색 API와 다름:
- `PJK` = project (다른 API는 `project`)
- `PAP` = paper
- `PAT` = patent
- `EQU` = equipment
- `RFR`, `RES` = research report

### 3.4 분류 응답 XML 구조

- 표준분류 (`rcmncls`): `<RESULT><Result_1 ... /></RESULT>`
- 보건의료 (`rcmnhtcls`): `<RESULT><MOHWD>...</MOHWD><MOHWR>...</MOHWR><MOTIE>...</MOTIE></RESULT>`
- 산업기술 (`rcmnitcls`): `<RESULT><MOTIE><Result_1 ... /></MOTIE></RESULT>`

파서가 `MOTIE` 래퍼를 처리하도록 `_parse_classification_result()`에 분기.

### 3.5 연구장비 XML 구조

다른 검색과 완전히 다른 필드:
- `EquipID` (≠ ResultID)
- `Title/Korean`, `Title/English`
- `KeepOrganization/Name`
- `Feature/Full`, `Feature/Teaser`
- `Manufacturer`, `Model`, `Price`, `InstallLocation`, `UseScope`, `BuyDate`

`_parse_equip_hit()` 전용 파서 필요.

### 3.6 HTML 잔재 제거

검색 결과에 `<span class="search_word">` 하이라이트 태그가 섞여있음. `_strip_html()`로 제거. 텍스트 추출은 `elem.text`가 아닌 `itertext()` 사용 (NTIS는 하이라이트를 실제 자식 요소로 반환).

### 3.7 XML 이스케이프 아티팩트

`_x005F_`, `_x000D_` 등의 escape 시퀀스가 응답에 그대로 노출. `XML_ESCAPE_RE`로 제거.

## 4. Rate Limit

- 검색 계열: 30 tps
- 분류 추천: 100 tps

캐시(`~/.cache/mcp-ntis/`, TTL 24h)가 동일 파라미터 호출을 흡수.

## 5. 새 API 추가 절차

1. `client.py`에 엔드포인트 URL 상수 추가
2. 파라미터 처리 메서드 작성 (필요 시 `_new_params()` 사용)
3. 응답 파서 추가 (`_parse_xxx_hit()` 패턴)
4. `tools/`에 도구 등록
5. `registry/initialize_registry.py`에 메타데이터 등록
6. `skills/api-integration.md` 본 문서에 함정 추가
