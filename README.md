# mcp-ntis

국가과학기술지식정보서비스(NTIS) API를 위한 MCP(Model Context Protocol) 서버.

국가R&D 과제, 논문, 특허, 연구보고서, 연구장비를 검색하고 과학기술 분류를 추천받을 수 있습니다.

## 제공 도구 (15개)

### 검색 도구

| 도구 | 설명 |
|---|---|
| `search_rnd_projects` | 국가R&D 과제 검색 (연구목표, 내용, 기대효과, 예산, 분류 포함) |
| `search_research_papers` | 국가R&D 논문 검색 (SCI/비SCI, 국내/국외, 연계과제 포함) |
| `search_patents` | 국가R&D 특허 검색 (국내외 출원·등록, 연계과제 포함) |
| `search_research_reports` | 국가R&D 연구보고서 검색 |
| `search_research_equipment` | 국가R&D 연구시설장비 검색 |
| `search_unified` | 통합검색 (여러 컬렉션 동시 조회) |

### 과제 상세 도구

| 도구 | 설명 |
|---|---|
| `get_consignment_research` | 과제의 위탁/공동연구 기관 및 연구비 조회 |
| `get_org_rnd_status` | 수행기관의 국가R&D 현황 조회 (연도별 과제 수, 연구비, 성과) |

### 분류 추천 도구

| 도구 | 설명 |
|---|---|
| `recommend_std_classification` | 국가과학기술표준분류 추천 (과기부·교육부 등) |
| `recommend_ht_classification` | 보건의료기술분류 추천 (보건복지부·질병청) |
| `recommend_it_classification` | 산업기술분류 추천 (산업부·중기부) |

### 부가 정보 도구

| 도구 | 설명 |
|---|---|
| `search_rnd_issues` | 이슈로 보는 국가R&D 조회 (최신 트렌드 이슈, 연관 과제 수) |
| `search_terminology` | 국가R&D 용어사전 검색 (한글/영문 표준 용어, 약어) |
| `get_classification_codes` | 과학기술표준분류 또는 국가중점기술 코드 계층 조회 |
| `get_related_content` | AI 기반 유사 과제·논문·특허·보고서 추천 |

## 설치

```bash
git clone https://github.com/ChangooLee/mcp-ntis
cd mcp-ntis
uv venv && source .venv/bin/activate
uv pip install -e .
```

## 환경변수 설정

```bash
cp .env.example .env
# .env 파일에서 NTIS_API_KEY 설정
```

| 변수 | 필수 | 설명 |
|---|---|---|
| `NTIS_API_KEY` | **Y** | NTIS 승인 인증키 ([NTIS 포털](https://www.ntis.go.kr) 에서 신청) |
| `NTIS_ORG_CD` | N | 기관약어 (분류추천 API 정확도 향상) |
| `NTIS_USER_ID` | N | 사용자 ID |
| `NTIS_CACHE_TTL_HOURS` | N | 캐시 TTL 시간 (기본 24) |
| `LOG_LEVEL` | N | 로그 레벨 (기본 INFO) |
| `TRANSPORT` | N | `stdio` 또는 `http` (기본 stdio) |

## Claude Desktop 설정

`~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ntis": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/mcp-ntis", "mcp-ntis"],
      "env": {
        "NTIS_API_KEY": "your_api_key"
      }
    }
  }
}
```

## 사용 예시

```python
# 과제 검색 (키워드)
search_rnd_projects(query="나노소재", search_field="KW", page_size=5)

# 기관 검색
search_rnd_projects(query="KAIST", search_field="OG")

# 연구책임자 검색
search_rnd_projects(query="홍길동", search_field="AU")

# 연도 범위 필터
search_rnd_projects(query="양자컴퓨터", add_query="PY=2021/MORE&2023/UNDER")

# 위탁연구 조회 (search_rnd_projects 결과의 id 필드 사용)
get_consignment_research(project_id="1415140010")

# 기관 R&D 역량 분석
get_org_rnd_status(org_name="한국전자통신연구원")

# 표준분류 추천 (단순모드)
recommend_std_classification(text="나노복합재료 합성 및 제조기술...")

# 표준분류 추천 (상세모드)
recommend_std_classification(
    detailed=True,
    goal="나노복합재료의 물성 향상을 위한 연구",
    abstract="고강도 나노복합재료를 제조하는 공정 개발",
    kor_keywords="나노복합재, 고분자복합체"
)

# 용어 검색
search_terminology(query="나노소재")

# 유사 과제 추천
get_related_content(content_type="project", content_id="1415140010")

# 최신 R&D 트렌드 이슈
search_rnd_issues()
```

## 검색어 연산자

| 연산자 | 예시 | 의미 |
|---|---|---|
| 띄어쓰기 | `나노 기술` | AND |
| `\|` | `나노\|기술` | OR |
| `!` | `!나노` | NOT |
| `"..."` | `"나노 기술"` | 정확한 구문 |

## 캐시

응답은 `~/.cache/mcp-ntis/`에 24시간 캐시됩니다 (`NTIS_CACHE_TTL_HOURS`로 조정 가능).

## 데이터 출처

[국가과학기술지식정보서비스(NTIS)](https://www.ntis.go.kr) — 한국과학기술정보연구원(KISTI) 제공

## 라이선스

[LICENSE](LICENSE) 참조.
