# mcp-ntis

한국 R&D 공공 데이터(**NTIS · ScienceON · DataON**)를 LLM에 연결하는
**MCP(Model Context Protocol) 서버**, **Streamlit + LangChain DeepAgent 챗봇**,
그리고 한 줄 토큰으로 35개 도구를 공유할 수 있는 **REST 게이트웨이**.

- 🔬 **35개 MCP 도구** — NTIS(정부 R&D) 16 + ScienceON(학술·특허 DB) 17 + DataON(연구데이터) 2
- 🤖 **DeepAgent + Claude 챗봇** — 도구 선택·호출·종합을 자동 수행, 분석 과정 시각화
- 🌐 **REST 게이트웨이 모드** — 운영자가 키를 보유, 다른 사용자는 게이트웨이 URL+토큰만으로 35개 도구 사용

---

## 두 가지 운영 모드

`.env`에 `NTIS_GATEWAY_URL` 한 줄만으로 모드가 결정됩니다.

|  | **모드 A — 게이트웨이 사용자** | **모드 B — 게이트웨이 운영자 / 단독 사용** |
|---|---|---|
| 필요한 발급 키 | ❌ NTIS·ScienceON·DataON 모두 불필요 | ✅ 전부 직접 신청·보유 |
| `.env` 필수 변수 | `NTIS_GATEWAY_URL`<br>`NTIS_GATEWAY_API_KEY`<br>`ANTHROPIC_API_KEY` (챗봇 시) | `NTIS_API_KEY`<br>`SCIENCEON_*` (3개)<br>`DATAON_API_KEY`·`DATAON_DETAIL_API_KEY`<br>`ANTHROPIC_API_KEY` (챗봇 시)<br>`GATEWAY_API_KEY` (외부 노출 시) |
| 호출 경로 | 운영자 게이트웨이 → 각 KISTI API | 직접 NTIS/ScienceON/DataON 호출 |
| 부팅 분기 | `server.py`가 `NTIS_GATEWAY_URL` 감지 → 게이트웨이 프록시 모드 | `NTIS_GATEWAY_URL` 비어있음 → in-process 직접 호출 모드 |

운영자라면 [`gateway/README.md`](gateway/README.md)로 REST 게이트웨이를 띄워 사용자에게 URL+토큰을 배포할 수 있습니다.

---

## 빠른 시작 (모드 A — 게이트웨이 사용자)

게이트웨이 운영자에게 URL·토큰을 받았다는 전제로 시작.

```bash
git clone https://github.com/ChangooLee/mcp-ntis
cd mcp-ntis

# 1) 가상환경 + 의존성
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[chatbot]"

# 2) .env 작성 (세 줄로 끝)
cp .env.example .env
cat >> .env <<'EOF'
NTIS_GATEWAY_URL=<운영자에게 받은 URL>
NTIS_GATEWAY_API_KEY=<운영자에게 받은 토큰>
ANTHROPIC_API_KEY=sk-ant-...
EOF

# 3-a) MCP 서버로 사용 (Claude Desktop·Cursor 등 연결)
python -m mcp_ntis.server

# 3-b) 또는 Streamlit 챗봇 실행
streamlit run chatbot/app.py
```

NTIS·ScienceON·DataON 발급 키 일체 불필요. 게이트웨이가 KISTI 측 호출을 모두 대행합니다.

### Claude Desktop 연결 예시

```jsonc
{
  "mcpServers": {
    "ntis": {
      "command": "python",
      "args": ["-m", "mcp_ntis.server"],
      "cwd": "/path/to/mcp-ntis",
      "env": {
        "NTIS_GATEWAY_URL": "<운영자 URL>",
        "NTIS_GATEWAY_API_KEY": "<운영자 토큰>"
      }
    }
  }
}
```

---

## 빠른 시작 (모드 B — 직접 호출)

KISTI에서 직접 키를 발급받아 본인 머신에서 NTIS·ScienceON·DataON을 호출합니다.

```bash
git clone https://github.com/ChangooLee/mcp-ntis
cd mcp-ntis
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[chatbot]"

cp .env.example .env
# .env 편집:
#   NTIS_GATEWAY_URL=          ← 반드시 비워두기 (모드 분기)
#   NTIS_API_KEY=...           ← NTIS 발급 키
#   SCIENCEON_CLIENT_ID=...    ← ScienceON 발급 (3개)
#   SCIENCEON_API_KEY=...
#   SCIENCEON_MAC=...
#   DATAON_API_KEY=...         ← DataON 발급 (검색용)
#   DATAON_DETAIL_API_KEY=...  ← DataON 발급 (상세조회용)
#   ANTHROPIC_API_KEY=...

python -m mcp_ntis.server          # MCP stdio
# 또는
streamlit run chatbot/app.py        # 챗봇
```

각 발급처:
- **NTIS**: <https://www.ntis.go.kr> (가입 → 마이페이지 → 인증키 신청)
- **ScienceON**: <https://scienceon.kisti.re.kr/apigateway/main/mainForm.do>
- **DataON**: <https://dataon.gitbook.io/dataon-user-guide/sharing/openapi> (KISTI 헬프데스크 안내)

---

## 제공 도구 (35개)

### NTIS — 정부 R&D 정보망 (16개)

| 카테고리 | 도구 | 설명 |
|---|---|---|
| **검색 (6)** | `search_rnd_projects` | 국가R&D 과제 — 가장 풍부한 메타(예산·분류·기간·기관). `fetch_all=True` 지원 |
|  | `search_research_papers` | R&D 연계 논문 (~19만) — SCI 구분, 학술지, 연계과제 |
|  | `search_patents` | R&D 연계 특허 (~38만) — 출원/등록, 국내·해외 |
|  | `search_research_reports` | 최종·중간 연구보고서 — 원문 보유 여부 포함 |
|  | `search_research_equipment` | 연구장비 — 장비명·제조사·구매가·공동활용 가능 여부 |
|  | `search_unified` | 다중 컬렉션 동시 검색 (project/rpaper/rpatent/rresearch/requip) |
| **과제 상세 (2)** | `get_consignment_research` | 위탁·공동연구 기관·분담금 |
|  | `get_org_rnd_status` | 기관 R&D 포트폴리오, 동명이기관 auto_resolve |
| **분류 추천 (3)** | `recommend_std_classification` | 과학기술표준분류 (과기부·교육부 계열) |
|  | `recommend_ht_classification` | 보건의료기술분류 (질환·연구행위·산업기술) |
|  | `recommend_it_classification` | 산업기술분류 (산업부·중기부 계열) |
| **부가 (4)** | `search_rnd_issues` | NTIS 선정 최신 R&D 트렌드 이슈 |
|  | `search_terminology` | 표준 용어사전 (한·영·정의·약어) |
|  | `get_classification_codes` | 표준분류 코드 계층 조회 |
|  | `get_related_content` | AI 기반 유사 과제 추천 |
| **메타 (1)** | `get_ntis_tool_info` | NTIS 16개 도구 카탈로그 자체 탐색 |

> 분류 추천: 본문 150자(450바이트) 이상, 연구목표·방법·효과 포함 권장.

### ScienceON — KISTI 학술·특허 데이터베이스 (17개)

KISTI 공식 카탈로그(`scienceon.kisti.re.kr/apigateway/api/way/service/...`)와 1:1 매핑.

| 카테고리 | 도구 |
|---|---|
| **논문 (2)** | `search_sci_papers`, `get_sci_paper` |
| **특허 (3)** | `search_sci_patents`, `get_sci_patent`, `search_sci_citation_patents` |
| **보고서 (2)** | `search_sci_reports`, `get_sci_report` |
| **동향·과학향기 (4)** | `search_sci_trends`, `get_sci_trend`, `search_sci_scent`, `get_sci_scent` |
| **연구자·연구기관 (4)** | `search_sci_researchers`, `get_sci_researcher`, `search_sci_organizations`, `get_sci_organization` |
| **TREND·뉴스 (2)** | `search_sci_infra_trend`, `search_sci_tech_news` |

자동 처리: Access Token 만료 → Refresh, Refresh 만료 → 재발급, E4290 rate limit → 지수 백오프(1→2→4→8s).

도구별 검색 필드 제약은 도구 description에 명시 (예: SCENT는 PY만, SNEWS는 RD만, RESEARCHER/ORGAN은 BI/TI만).

### DataON — 국가연구데이터플랫폼 (2개)

| 도구 | 설명 |
|---|---|
| `search_dataon_datasets` | 연구 데이터셋 검색 (영문 키워드 효율적) |
| `get_dataon_dataset` | 데이터셋 메타 상세 조회 (svc_id 기반) |

응답 핵심 키: `total_count`, `items[]: title, description, doi, landing_url, repository, catalog_type, access_type` 등.

---

## 환경 변수

| 변수 | 모드 A | 모드 B | 설명 |
|---|---|---|---|
| `NTIS_GATEWAY_URL` | **필수** | 비움 | 운영자에게 받은 게이트웨이 URL — 이게 모드 스위치 |
| `NTIS_GATEWAY_API_KEY` | **필수** | 비움 | 게이트웨이 토큰 |
| `ANTHROPIC_API_KEY` | 챗봇 사용 시 | 챗봇 사용 시 | Claude API 키 |
| `ANTHROPIC_MODEL` | 선택 | 선택 | 기본 `claude-sonnet-4-5-20250929` |
| `NTIS_API_KEY` | — | **필수** | NTIS 발급 인증키 |
| `NTIS_NEW_API_KEY` | — | 선택 | 이슈·용어·분류코드용 |
| `SCIENCEON_CLIENT_ID` / `SCIENCEON_API_KEY` / `SCIENCEON_MAC` | — | 선택 (3개 모두 있을 때 활성) | ScienceON 17개 도구 활성화 |
| `DATAON_API_KEY` | — | 선택 | DataON 검색 도구 활성화 |
| `DATAON_DETAIL_API_KEY` | — | 선택 | DataON 상세 도구 활성화 |
| `GATEWAY_API_KEY` | — | 게이트웨이 외부 노출 시 | 자체 인증 토큰 (`openssl rand -hex 32`) |
| `LOG_LEVEL` | 선택 | 선택 | 기본 `INFO` |
| `TRANSPORT` | 선택 | 선택 | `stdio` / `http` (기본 stdio) |

> ⚠️ **보안**: `.env`는 `.gitignore`에 등록되어 절대 커밋되지 않습니다.
> 모든 발급 키와 게이트웨이 토큰은 `.env`에만 보관하세요.

---

## 챗봇 사용 예시

### 1) 도구 자체 탐색

> **사용자**: "사용 가능한 도구 카테고리를 알려줘."

DeepAgent → `get_ntis_tool_info()` → 카테고리별 35개 도구 목록 → Claude 한국어 요약.

### 2) 트렌드 분석

> **사용자**: "NTIS 최신 트렌드 이슈 5개 중 정부 투자가 가장 빠르게 늘고 있는 분야는?"

DeepAgent가:
1. `search_rnd_issues()`로 5개 이슈 발견
2. 각 이슈 키워드로 `search_rnd_projects(fetch_all=True, add_query='PY=...')` 5년 시계열 수집
3. 정부지원금 합산해 증가율 계산
4. 결론 도출

### 3) 제품 기획 (3 도메인 통합)

> **사용자**: "스마트 토일렛 헬스케어 제품을 만들고 싶어. 어떤 기술이 필요하고 어떤 기업과 협력할 수 있을지 알려줘."

DeepAgent가 7~10회 도구 호출로:
- `search_rnd_projects` — 정부 R&D에서 스마트 변기 직접 매칭 사례
- `search_sci_papers` / `search_sci_patents` — 글로벌 학술·특허 동향
- `search_dataon_datasets` — 관련 공개 데이터셋
- `recommend_ht_classification` + `recommend_it_classification` — 부처 매칭 (다부처 사업 후보)
- `get_org_rnd_status` — 협력 후보 기관 R&D 역량

자세한 답변 예시: `evaluation/scenarios/05_SMART_TOILET_HEALTHCARE.md`.

---

## 프로젝트 구조

```
mcp-ntis/
├── src/mcp_ntis/
│   ├── server.py             # FastMCP 인스턴스 + 모드 분기 (게이트웨이 vs 직접)
│   ├── config.py             # 환경변수 로드
│   ├── client.py             # NTIS 비동기 클라이언트 (httpx)
│   ├── cache.py              # 파일 캐시
│   ├── registry/             # 도구 메타데이터
│   ├── utils/                # 공용 헬퍼
│   ├── tools/                # NTIS 16개 (in-process 모드용)
│   ├── scienceon/            # ScienceON 17개 (in-process 모드용)
│   ├── dataon/               # DataON 2개 (in-process 모드용)
│   └── gateway_proxy/        # 모드 A — 원격 게이트웨이 메타로 도구 동적 등록
│       └── tools.py
│
├── chatbot/                  # Streamlit + DeepAgent 챗봇
│   ├── app.py
│   └── agent.py
│
├── gateway/                  # FastAPI REST 게이트웨이 (모드 B 운영자용)
│   ├── main.py
│   ├── mcp-gateway.service   # systemd 유닛 템플릿
│   └── README.md
│
├── skills/                   # 개발자 가이드
├── evaluation/               # 평가·시나리오·테스트 결과
├── .env.example
├── pyproject.toml
└── README.md
```

---

## 기술 스택

| 영역 | 기술 |
|---|---|
| MCP 서버 | FastMCP 3.x, mcp 1.x |
| HTTP 클라이언트 | httpx (비동기) |
| 응답 캐시 | 파일 기반 MD5 키 + TTL (기본 24h) |
| 챗봇 LLM | Anthropic Claude Sonnet 4.5 |
| AI 에이전트 | LangChain DeepAgent |
| UI | Streamlit |
| 게이트웨이 (선택) | FastAPI + uvicorn |
| Python | 3.10+ |

### 모드 A 아키텍처 (게이트웨이 사용자)

```
┌─────────────────────────────────────────────────────────────┐
│  Streamlit 챗봇 / Claude Desktop / Cursor                    │
└──────────────────────┬──────────────────────────────────────┘
                       │ MCP stdio / in-process tool call
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  mcp_ntis.server (게이트웨이 프록시 모드)                       │
│  - NTIS_GATEWAY_URL 감지 → gateway_proxy.tools 로드             │
│  - /tools 메타로 35개 도구 동적 등록                            │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS + X-API-Key
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  운영자 게이트웨이 (FastAPI)                                   │
│  - .env에 NTIS/ScienceON/DataON 발급 키 보유                   │
│  - 사용자별 GATEWAY_API_KEY로 인증                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
       ┌───────────────┼───────────────┐
       ▼               ▼               ▼
    NTIS API     ScienceON API     DataON API
```

### 모드 B 아키텍처 (직접 호출)

```
┌─────────────────────────────────────────────────────────────┐
│  Streamlit 챗봇 / Claude Desktop                             │
└──────────────────────┬──────────────────────────────────────┘
                       │ in-process tool call
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  mcp_ntis.server (직접 호출 모드)                              │
│  - tools/ + scienceon/ + dataon/ 모듈 로드                     │
└─┬───────────────┬───────────────┬───────────────────────────┘
  ▼               ▼               ▼
NTIS API     ScienceON API    DataON API   ← 발급 키 직접 사용
```

---

## 검색 연산자 (NTIS)

| 연산자 | 예시 | 의미 |
|---|---|---|
| 띄어쓰기 | `나노 기술` | AND |
| `\|` | `나노\|기술` | OR |
| `!` | `!나노` | NOT |
| `"..."` | `"나노 기술"` | 정확한 구문 |
| `add_query='PY=2024/SAME'` | | 2024년 과제만 |
| `add_query='PY=2020/MORE&2023/UNDER'` | | 2020~2023 범위 |
| `add_query='OG=한국전자통신연구원'` | | 특정 수행기관 |
| `add_query='AU=홍길동'` | | 특정 연구책임자 |

---

## 페이지네이션

NTIS 단일 호출 최대 100건. 시나리오별 권장:

| 시나리오 | 설정 |
|---|---|
| 단순 탐색 | `page_size=10~20` |
| 상위 N개 목록 | `page_size=100`, 1페이지로 충분 |
| **정량 집계** (예산 합산·통계) | **`fetch_all=True`** 필수 |
| 매우 큰 결과셋 | `fetch_all=True, max_fetch=5000` |

ScienceON·DataON도 각 도구의 `row_count`·`size` / `cur_page`·`from_`로 페이지네이션. `pagination_hint` 응답 필드로 남은 건수·다음 호출 위치 자동 안내.

---

## 캐시

응답은 `~/.cache/mcp-ntis/`에 기본 24시간 캐시. 동일 파라미터 재호출은 즉시 응답.
`.env`의 `NTIS_CACHE_TTL_HOURS`로 TTL 조정.

> 모드 A에서는 게이트웨이가 KISTI 호출을 처리하므로 클라이언트 측 캐시는 없습니다.

---

## 게이트웨이 직접 운영하기

[gateway/README.md](gateway/README.md) 참조 — FastAPI 게이트웨이를 본인 호스트에 띄워 사용자에게 URL+토큰 배포하는 절차.

요약:
1. 모드 B로 `.env` 구성 (NTIS·ScienceON·DataON 발급 키)
2. `GATEWAY_API_KEY=$(openssl rand -hex 32)`
3. `pip install -e ".[gateway]"`
4. `uvicorn gateway.main:app --host 0.0.0.0 --port <PORT>` (또는 systemd 유닛 활용)
5. nginx + Let's Encrypt로 HTTPS 노출
6. 사용자에게 URL과 `GATEWAY_API_KEY` 배포

---

## 데이터 출처

- [국가과학기술지식정보서비스 (NTIS)](https://www.ntis.go.kr) — KISTI
- [KISTI ScienceON OpenAPI Gateway](https://scienceon.kisti.re.kr)
- [국가연구데이터플랫폼 (DataON)](https://dataon.kisti.re.kr)

---

## 라이선스

[LICENSE](LICENSE) 참조.
