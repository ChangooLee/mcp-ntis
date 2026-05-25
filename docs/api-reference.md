# NTIS API Reference

국가과학기술지식정보서비스(NTIS) Open API 엔드포인트 및 파라미터 참조.

## 인증

모든 API 요청에 `apprvKey` 파라미터 필수 (String 64).

```
apprvKey=lg814619kv046cp808fk
```

---

## 1. 과제 검색 (pjtSearch)

**URL:** `GET https://www.ntis.go.kr/rndopen/openApi/pjtSearch/project`

| 파라미터 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `apprvKey` | String | Y | 인증키 |
| `SRWR` | String | Y | 검색어 |
| `collection` | String | Y | 고정값: `project` |
| `searchFd` | String | N | 검색 필드 코드 (기본: `BI`) |
| `addQuery` | String | N | 추가 필터 (`PY=2022/SAME` 등) |
| `searchRnkn` | String | N | 정렬 (`RANK/DESC`, `DATE/DESC`) |
| `startPosition` | Integer | N | 시작 위치 (기본: 1) |
| `displayCnt` | Integer | N | 결과 수 (기본: 10, 최대: 100) |

### searchFd 코드 (과제)

| 코드 | 설명 |
|---|---|
| `BI` | 기본정보 (제목+초록, 기본값) |
| `TI` | 과제명 |
| `KW` | 키워드 |
| `RN` | 연구자명 |
| `OA` | 수행기관 |
| `MA` | 주관기관 |

### 응답 XML 구조 (핵심 필드)

```xml
<RESULT>
  <TOTALHITS>1234</TOTALHITS>
  <HITS>10</HITS>
  <STARTPOSITION>1</STARTPOSITION>
  <HIT>
    <ProjectNumber>1415140010</ProjectNumber>
    <ProjectTitle>
      <Korean>나노소재 개발</Korean>
      <English>Nano material development</English>
    </ProjectTitle>
    <ProjectYear>2022</ProjectYear>
    <Goal><Teaser>고성능 나노소재...</Teaser></Goal>
    <Abstract><Teaser>나노소재를 이용한...</Teaser></Abstract>
    <Effect><Teaser>산업 적용 가능...</Teaser></Effect>
    <Keyword>
      <Korean>나노, 소재</Korean>
      <English>nano, material</English>
    </Keyword>
    <Manager><Name>홍길동</Name></Manager>
    <Ministry code="1345">과학기술정보통신부</Ministry>
    <GovernmentFunds>500000</GovernmentFunds>
    <TotalFunds>750000</TotalFunds>
    <ProjectPeriod>
      <Start>2020</Start>
      <End>2024</End>
    </ProjectPeriod>
    <ScienceClass>
      <Large code="AA">자연과학</Large>
      <Medium code="AA01">수학</Medium>
      <Small code="AA0101">대수학</Small>
    </ScienceClass>
  </HIT>
</RESULT>
```

---

## 2. 성과 검색 (natRnDSearch)

**URL:** `GET https://www.ntis.go.kr/rndopen/openApi/natRnDSearch`

| 파라미터 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `apprvKey` | String | Y | 인증키 |
| `collection` | String | Y | `rpaper` / `rpatent` / `rresearch` / `requip` |
| `SRWR` | String | Y | 검색어 |
| `searchFd` | String | N | 검색 필드 코드 |
| `addQuery` | String | N | 추가 필터 |
| `searchRnkn` | String | N | 정렬 |
| `startPosition` | Integer | N | 시작 위치 |
| `displayCnt` | Integer | N | 결과 수 |

### Collection별 searchFd 코드

**rpaper (논문):**

| 코드 | 설명 |
|---|---|
| `BI` | 기본 (제목+초록) |
| `TI` | 논문제목 |
| `AU` | 저자 |
| `JN` | 저널명 |

**rpatent (특허):**

| 코드 | 설명 |
|---|---|
| `BI` | 기본 |
| `TI` | 특허명 |
| `INV` | 발명자 |
| `AP` | 출원인 |

**rresearch (연구보고서):**

| 코드 | 설명 |
|---|---|
| `BI` | 기본 |
| `TI` | 보고서명 |
| `AU` | 저자 |

**requip (연구장비):**

| 코드 | 설명 |
|---|---|
| `BI` | 기본 |
| `TI` | 장비명 |
| `OA` | 보유기관 |

### addQuery 필터 예시

```
PY=2022/SAME    # 특정 연도
PY=2020/MORE    # 연도 이상
PY=2022/LESS    # 연도 이하
```

---

## 3. 통합 검색 (totalRstSearch)

**URL:** `GET https://www.ntis.go.kr/rndopen/openApi/totalRstSearch`

| 파라미터 | 타입 | 설명 |
|---|---|---|
| `collection` | String | 콤마 구분 복수 지정 가능: `rpaper,rpatent,rresearch,requip` |
| 나머지 | | 위와 동일 |

응답에 `COLCOUNT` 요소로 컬렉션별 건수 포함.

---

## 4. 위탁/공동연구 조회 (projectuOrg)

**URL:** `GET https://www.ntis.go.kr/rndopen/openApi/projectuOrg`

| 파라미터 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `apprvKey` | String | Y | 인증키 |
| `pjtId` | String | Y | 과제고유번호 (ProjectNumber) |

### 응답 XML 구조

```xml
<HIT NO="1">
  <ProjectNumber>1415140010</ProjectNumber>
  <CommissionNumber>3415140010-01</CommissionNumber>
  <ProjectTitle>
    <Korean>위탁과제 제목</Korean>
    <Commission>위탁과제명</Commission>
  </ProjectTitle>
  <Manager><Name>홍길동</Name></Manager>
  <ProjectPeriod>
    <Start>2022</Start>
    <End>2024</End>
  </ProjectPeriod>
  <CollaborativeResearchFunds>100000</CollaborativeResearchFunds>
  <ConsignmentProjectResearchFunds>50000</ConsignmentProjectResearchFunds>
  <CommissionType>위탁</CommissionType>
</HIT>
```

---

## 5. 분류 추천 (rcmncls)

**URL:** `GET https://www.ntis.go.kr/rndopen/openApi/rcmncls`

### 단순 모드

| 파라미터 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `apprvKey` | String | Y | 인증키 |
| `collection` | String | Y | `rcmncls` (표준) / `rcmnhtcls` (보건) / `rcmnitcls` (산업) |
| `rqstDes` | String | Y | 분류 추천 텍스트 (UTF-8, 300바이트 이상, 30KB 이하) |
| `orgCd` | String | N | 기관코드 |

### 상세 모드

| 파라미터 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `collection` | String | Y | `rcmnclsdtl` / `rcmnhtclsdtl` / `rcmnitclsdtl` |
| `rschGoalAbstract` | String | Y | 연구목표 요약 |
| `rschAbstract` | String | Y | 연구내용 요약 |
| `expEfctAbstract` | String | N | 기대효과 요약 |
| `korKywd` | String | N | 국문 핵심어 |
| `engKywd` | String | N | 영문 핵심어 |

> **주의:** 단순/상세 모드 모두 텍스트 합산 300바이트 이상이어야 합니다.

### 응답 XML (표준분류)

```xml
<response>
  <STATUS>
    <ResultCode>200</ResultCode>
    <ResultMsg>정상처리</ResultMsg>
  </STATUS>
  <RESULT>
    <Result_1 LCLS_CD="AA" LCLS_NM="자연과학"
              MCLS_CD="AA01" MCLS_NM="수학"
              SCLS_CD="AA0101" SCLS_NM="대수학"
              SCLS_WEIGHT="85.2"/>
    <Result_2 .../>
  </RESULT>
</response>
```

### 응답 XML (보건의료기술분류)

```xml
<RESULT>
  <MOHWD>  <!-- 질환별분류 -->
    <Result_1 LCLS_CD="D01" LCLS_NM="암"
              MCLS_CD="D0101" MCLS_NM="폐암"
              MCLS_WEIGHT="90.0"/>
  </MOHWD>
  <MOHWR>  <!-- 연구행위및산출물분류 -->
    <Result_1 LCLS_CD="R01" LCLS_NM="기초연구"
              MCLS_CD="R0101" MCLS_NM="분자생물학"
              MCLS_WEIGHT="88.5"/>
  </MOHWR>
</RESULT>
```

---

## 오류 응답

NTIS API 오류 시 XML에 `<ERROR>` 요소 포함:

```xml
<ERROR>
  <CODE>3</CODE>
  <MESSAGE>접근 허용 IP가 아닙니다.</MESSAGE>
</ERROR>
```

| 코드 | 설명 |
|---|---|
| 1 | 인증키 오류 |
| 2 | 만료된 인증키 |
| 3 | IP 접근 제한 |
| 4 | 요청 파라미터 오류 |

> **IP 제한:** NTIS API는 등록된 IP에서만 접근 가능합니다. 서버는 반드시 NTIS에 등록된 IP에서 실행해야 합니다.

---

## 검색어 연산자

| 연산자 | 예시 | 의미 |
|---|---|---|
| 띄어쓰기 | `나노 기술` | AND |
| `\|` | `나노\|기술` | OR |
| `!` | `!나노` | NOT |
| `"..."` | `"나노 기술"` | 정확한 구문 |
