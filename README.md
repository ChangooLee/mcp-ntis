# mcp-ntis

국가과학기술지식정보서비스(NTIS) 데이터를 LLM에 연결하는 **MCP(Model Context Protocol) 서버**와, 그 위에 얹은 **Streamlit + LangChain DeepAgent 챗봇**.

- 🔬 **16개 MCP 도구**로 NTIS의 R&D 과제·논문·특허·보고서·연구장비·트렌드·분류 추천을 LLM에 직접 노출
- 🤖 **DeepAgent + Claude** 기반 챗봇 UI로 "어떤 도구를 어떻게 쓸지"를 자체적으로 판단해 분석
- 📊 **생각 과정·도구 호출·도구 응답·최종 답변**을 한 화면에서 실시간으로 시각화

---

## 빠른 시작

```bash
git clone https://github.com/ChangooLee/mcp-ntis
cd mcp-ntis

# 1) 가상환경 + 의존성
uv venv && source .venv/bin/activate
uv pip install -e .[chatbot]

# 2) 환경변수 설정 (.env)
cp .env.example .env
# .env 파일에서 NTIS_API_KEY, ANTHROPIC_API_KEY 입력

# 3) MCP 서버만 단독 실행 (Claude Desktop 등에 연결 시)
mcp-ntis

# 4) Streamlit 챗봇 실행
streamlit run chatbot/app.py
```

기동 후 브라우저로 `http://localhost:8501` 접속.

---

## 두 가지 사용 방법

### A. MCP 서버로 — Claude Desktop·Cursor·Codex 등에서 직접 사용

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

Claude Desktop 재시작 후 NTIS의 16개 도구가 활성화됩니다.

### B. Streamlit 챗봇으로 — 즉시 사용 가능한 대화형 분석가

```bash
streamlit run chatbot/app.py
```

화면 구성:
- **사이드바**: 16개 도구 목록 + 도구별 설명 + 6개 예시 질문 + 대화 초기화
- **메인 영역**: 사용자 질문 → 에이전트 분석 단계(🛠️ 도구 호출, 📥 도구 응답) → 🔬 최종 답변

내부적으로:
1. 사용자가 질문 입력
2. LangChain `DeepAgent`가 Claude를 호출해 어떤 도구를 사용할지 판단
3. NTIS 도구(in-process)가 NTIS OpenAPI를 호출해 결과 반환
4. 에이전트가 결과를 종합해 한국어로 최종 답변 작성
5. 모든 단계를 Streamlit이 실시간 시각화

---

## 제공 도구 (16개)

### 검색 도구 (6개)

| 도구 | 설명 |
|---|---|
| `search_rnd_projects` | 국가R&D 과제 검색. 가장 풍부한 메타데이터 (예산·분류·기간·기관). 연도별 중복 자동 제거. `fetch_all=True`로 전체 페이지 순회 가능. |
| `search_research_papers` | 국가R&D 연계 논문 (~19만 건). SCI/SCIE 구분, 학술지·저자·연계과제 포함. |
| `search_patents` | 국가R&D 연계 특허 (~38만 건). 출원/등록, 국내외 구분. |
| `search_research_reports` | 국가R&D 최종·중간 연구보고서. 원문 보유 여부 포함. |
| `search_research_equipment` | 연구장비 검색. 장비명·모델·제조사·구매가·공동활용 가능 여부 등. |
| `search_unified` | 여러 컬렉션 동시 검색. `collection='project,rpaper,rpatent'` 등. |

### 과제 상세 도구 (2개)

| 도구 | 설명 |
|---|---|
| `get_consignment_research` | 과제의 위탁·공동연구 기관과 분담 연구비. |
| `get_org_rnd_status` | 기관 R&D 포트폴리오 (연도별 과제 수·연구비·논문·특허). 동명이기관 자동 해결. |

### 분류 추천 도구 (3개)

| 도구 | 설명 |
|---|---|
| `recommend_std_classification` | 과학기술표준분류 추천 (과기부·교육부 계열). |
| `recommend_ht_classification` | 보건의료기술분류 추천 (질환·연구행위·산업기술 3종 동시). |
| `recommend_it_classification` | 산업기술분류 추천 (산업부·중기부 계열). |

> **텍스트 요건**: 150자(450바이트) 이상, 연구목표·방법·효과 포함 권장. 짧으면 -1002 또는 -2002 오류 반환.

### 부가 도구 (4개)

| 도구 | 설명 |
|---|---|
| `search_rnd_issues` | NTIS 선정 최신 R&D 트렌드 이슈. |
| `search_terminology` | 국가R&D 표준 용어사전 (한·영 명칭, 약어, 정의). |
| `get_classification_codes` | 과학기술표준분류(NTIS001) / 국가중점기술(NTIS002) 코드 계층 조회. |
| `get_related_content` | AI 기반 유사 과제 추천 (project만 지원). |

### 메타 도구 (1개)

| 도구 | 설명 |
|---|---|
| `get_ntis_tool_info` | NTIS 도구 자체 탐색. LLM이 어떤 도구를 써야 할지 모를 때 먼저 호출. |

### ScienceON 도구 (24개, 선택)

NTIS와 다른 KISTI ScienceON OpenAPI Gateway 데이터(논문 ~59만/특허 ~78만/보고서/동향 등).
`SCIENCEON_CLIENT_ID`/`SCIENCEON_API_KEY`/`SCIENCEON_MAC` 환경변수가 설정되면 자동 활성화.

| 카테고리 | 도구 | 권한 (회귀 테스트 결과) |
|---|---|---|
| **논문** | `search_sci_papers` / `get_sci_paper` | ✅ |
| | `sci_resolver` (링크리졸버) | E4302 권한 필요 |
| | `sci_paper_toc` (권호 TOC) | E4302 권한 필요 |
| **특허** | `search_sci_patents` / `get_sci_patent` | ✅ |
| | `search_sci_applicant` (출원인 검색) | E4302 권한 필요 |
| **보고서** | `search_sci_reports` / `get_sci_report` | ✅ |
| **동향** | `search_sci_trends` / `get_sci_trend` | ✅ |
| | `search_sci_scent` / `get_sci_scent` (과학향기) | ✅ |
| **연구자·기관** | `search_sci_researchers` / `get_sci_researcher` | ✅ |
| | `search_sci_organizations` / `get_sci_organization` | ✅ |
| | `search_sci_authors` / `get_sci_author` (저자 전거) | E4302 권한 필요 |
| **지식인프라** | `search_sci_function` / `search_sci_service` | E4302 권한 필요 |
| | `search_sci_ddc` (주제분류) / `search_sci_education` | E4302 권한 필요 |
| | `recommend_sci_content` | E4302 권한 필요 |

> **E4302 안내**: ScienceON 인증키는 API 단위로 권한이 부여됩니다.
> 일부 도구는 KISTI에 별도 권한 신청이 필요합니다. helpdesk@kisti.re.kr 문의.

**자동 처리**:
- Access Token 만료 → Refresh Token으로 자동 재발급
- Refresh Token 만료 → 자동 재발급
- E4290 rate limit → 지수 백오프 자동 재시도 (1→2→4→8초)

---

## 환경 변수

`.env` 파일에 설정 (`.env.example` 참고):

| 변수 | 필수 | 설명 |
|---|---|---|
| `NTIS_API_KEY` | **Y** | NTIS 승인 인증키 ([NTIS 포털](https://www.ntis.go.kr)에서 신청) |
| `ANTHROPIC_API_KEY` | **Y (챗봇 사용 시)** | Claude API 키 |
| `ANTHROPIC_MODEL` | N | Claude 모델명 (기본 `claude-sonnet-4-5-20250929`) |
| `NTIS_NEW_API_KEY` | N | 신규 API용 (이슈·용어·분류코드) |
| `NTIS_ORG_CD` | N | 기관약어 |
| `NTIS_USER_ID` | N | 사용자 ID |
| `NTIS_CACHE_TTL_HOURS` | N | 응답 캐시 TTL (기본 24시간) |
| `LOG_LEVEL` | N | 로그 레벨 (기본 INFO) |
| `TRANSPORT` | N | `stdio` 또는 `http` (기본 stdio) |

> ⚠️ **보안**: `.env`는 `.gitignore`에 등록되어 있어 커밋되지 않습니다. API 키를 직접 입력하세요.

---

## 챗봇 사용 예시

### 1) 도구 자체 탐색

> **사용자**: "get_ntis_tool_info를 호출해서 사용 가능한 도구 카테고리만 알려줘."

DeepAgent가 `get_ntis_tool_info()`를 호출 → 9개 카테고리로 정리된 16개 도구 목록 반환 → Claude가 사용자에게 한국어 요약 답변.

### 2) 트렌드 분석

> **사용자**: "NTIS 최신 트렌드 이슈 5개 중 정부 투자가 가장 빠르게 늘고 있는 분야를 찾아줘."

DeepAgent가:
1. `search_rnd_issues()`로 5개 이슈 발견
2. 각 이슈명으로 `search_rnd_projects(fetch_all=True, add_query='PY=2021/SAME')` × 5년 = 25회 호출
3. 정부지원금 합산해 증가율 계산
4. "소형언어모델 5년 +1,218%" 같은 결론 도출

### 3) 제품 기획

> **사용자**: "스마트 토일렛 헬스케어 제품을 만들고 싶어. 어떤 기술이 필요하고 어떤 기업과 협력할 수 있을지 알려줘."

DeepAgent가 7~10회의 도구 호출로:
- "스마트 토일렛" 직접 매칭 196건 과제 발견
- 가스센서·영상AI·소변광학 기술 영역별 한국 R&D 사례 매핑
- (주)쉬즈엠·(주)이엘티센서·(주)랩스피너 등 협력 후보 식별
- 정부 펀딩 사업 5단계 로드맵 제안

자세한 답변 예시: `evaluation/QA_SHOWCASE.md`, `evaluation/SMART_TOILET_PLAN.md`.

---

## 프로젝트 구조

```
mcp-ntis/
├── src/mcp_ntis/             # MCP 서버 핵심
│   ├── server.py             # FastMCP 인스턴스, lifespan, 컨텍스트
│   ├── config.py             # 환경변수 로드 (NTISConfig, MCPConfig)
│   ├── client.py             # NTIS OpenAPI 비동기 클라이언트 (httpx)
│   ├── cache.py              # 파일 캐시 (~/.cache/mcp-ntis/, 24h TTL)
│   ├── registry/             # 도구 메타데이터 (korean_name, tags, linked_tools)
│   │   ├── tool_registry.py
│   │   └── initialize_registry.py
│   ├── utils/                # 공용 헬퍼
│   │   └── ctx_helper.py     # transform_response, KEY_MAPPING 등
│   └── tools/                # @mcp.tool 데코레이터 함수들
│       ├── search_tools.py
│       ├── project_tools.py
│       ├── classification_tools.py
│       ├── extra_tools.py
│       └── meta_tools.py     # get_ntis_tool_info
│
├── chatbot/                  # Streamlit 챗봇
│   ├── app.py                # Streamlit UI
│   └── agent.py              # DeepAgent + LangChain 통합
│
├── skills/                   # 개발자 가이드 문서
│   ├── tool-development.md
│   ├── api-integration.md
│   ├── pagination-strategy.md
│   ├── response-transformation.md
│   └── llm-workflow.md
│
├── evaluation/               # 평가·예시 답변 문서
│   ├── TEST_PLAN.md
│   ├── TEST_RESULTS.md
│   ├── IMPROVEMENTS.md
│   ├── QA_SHOWCASE.md
│   └── SMART_TOILET_PLAN.md
│
├── .env.example              # 환경변수 템플릿
├── .env                      # 실제 키 (gitignored)
├── pyproject.toml
└── README.md
```

---

## 기술 스택

| 영역 | 기술 |
|---|---|
| **MCP 서버** | FastMCP 3.2.4, mcp 1.x |
| **HTTP 클라이언트** | httpx (비동기, 60초 timeout) |
| **응답 캐시** | 파일 기반 MD5 키 + 24시간 TTL |
| **챗봇 LLM** | Anthropic Claude Sonnet 4.5 |
| **AI 에이전트** | LangChain DeepAgent 0.6.2 |
| **LLM Tool 통합** | LangChain StructuredTool (in-process wrapper) |
| **UI** | Streamlit 1.57 |
| **Python** | 3.10+ |

### 챗봇 아키텍처

```
┌────────────────────────────────────────────────────────────┐
│                   Streamlit UI (chatbot/app.py)            │
│  - 사용자 입력 / 도구 호출 시각화 / 최종 답변 표시            │
└─────────────────────────┬──────────────────────────────────┘
                          │ stream_agent_run() (async iter)
                          ▼
┌────────────────────────────────────────────────────────────┐
│          DeepAgent (chatbot/agent.py)                      │
│  - LangChain create_deep_agent()                           │
│  - SYSTEM_PROMPT: NTIS 분석가 페르소나                       │
│  - 모델: Claude Sonnet 4.5                                  │
│  - tools: StructuredTool × 16 (NTIS 도구 in-process wrap)  │
└─────────────────────────┬──────────────────────────────────┘
                          │ 도구 호출 (Python 직접 invoke)
                          ▼
┌────────────────────────────────────────────────────────────┐
│       NTIS MCP 서버 (src/mcp_ntis/)                        │
│  - @mcp.tool 함수들 (FastMCP 등록)                          │
│  - NTISClient → httpx → NTIS OpenAPI                       │
│  - 파일 캐시 (~/.cache/mcp-ntis/)                           │
└────────────────────────────────────────────────────────────┘
```

FastMCP 3.x의 stdio 모드와 langchain-mcp-adapters 호환 이슈로,
챗봇은 NTIS 도구 함수를 **in-process로 직접 wrap**해 사용합니다.
순수 MCP stdio 서버는 별개로 정상 작동하며 Claude Desktop 등에서 사용 가능.

---

## 검색 연산자

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

## 페이지네이션 가이드

NTIS 검색 API는 단일 호출당 최대 100건. 시나리오별 권장 패턴:

| 시나리오 | 설정 |
|---|---|
| 단순 탐색 | `page_size=10~20` |
| 상위 N개 목록 | `page_size=100`, 1페이지로 충분 |
| **정량 집계** (예산 합산, 통계) | **`fetch_all=True`** 필수 |
| 매우 큰 결과셋 | `fetch_all=True, max_fetch=5000` |

자세히는 `skills/pagination-strategy.md` 참조.

---

## 캐시

응답은 `~/.cache/mcp-ntis/`에 24시간 캐시 (`NTIS_CACHE_TTL_HOURS`로 조정). 동일 파라미터 재호출은 즉시 응답.

---

## 부록 — ScienceON API 토큰 발급 (참고)

KISTI ScienceON OpenAPI도 같은 NTIS 생태계 데이터(논문·특허·보고서·동향·연구자·기관 등)를
제공하므로, 향후 통합을 위해 토큰 발급 절차를 기록합니다. **NTIS와는 별개의 API이며 별도
인증키가 필요**합니다.

### 토큰 발급 정확한 스펙

ScienceON 토큰 발급은 AES 암호화를 거쳐야 하는데, **공식 가이드 페이지의 텍스트만으로는
스펙이 명확하지 않아 KISTI 헬프데스크가 GitHub 샘플 코드를 보라고 안내**합니다
(자료실: [API 활용 예제 코드(PYTHON)](https://scienceon.kisti.re.kr/apigateway/api/material/pdsList.do)).

샘플 코드에서 확인된 정확한 스펙:

| 항목 | 값 |
|---|---|
| 엔드포인트 | `https://apigateway.kisti.re.kr/tokenrequest.do` |
| 알고리즘 | **AES-256-CBC** (ECB 아님) |
| IV (고정) | **`jvHJ1EFA0IXBrxxz`** (16바이트 UTF-8) |
| 키 | 발급 인증키 32자 문자열 그대로 UTF-8 (hex 변환 금지) |
| 패딩 | PKCS7 (`chr(pad_n) * pad_n`) |
| Base64 | **`base64.urlsafe_b64encode`** (일반 base64 아님) |
| JSON 페이로드 | `{"datetime":"YYYYMMDDHHmmss","mac_address":"AA-BB-CC-DD-EE-FF"}` (공백 제거) |
| datetime 포맷 | `strftime('%Y-%m-%d %H:%M:%S')`에서 숫자만 추출 |
| MAC 포맷 | 대문자 + 하이픈 (예: `5C-E9-1E-8C-9F-7E`) |

### 검증된 Python 클라이언트

```python
import json, base64, datetime, re, httpx
from urllib import parse
from Crypto.Cipher import AES

MAC_ADDRESS = "5C-E9-1E-8C-9F-7E"        # 등록 MAC
CLIENT_ID   = "<발급받은 client_id>"
KEY         = "<발급받은 32자 인증키>"

IV = b"jvHJ1EFA0IXBrxxz"
BLOCK = 16

def _pkcs7(s: str) -> bytes:
    n = BLOCK - len(s) % BLOCK
    return (s + chr(n) * n).encode("utf-8")

def create_token() -> dict:
    time_s = "".join(re.findall(r"\d", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    plain = json.dumps({"datetime": time_s, "mac_address": MAC_ADDRESS}).replace(" ", "")
    cipher = AES.new(KEY.encode("utf-8"), AES.MODE_CBC, IV)
    accounts = base64.urlsafe_b64encode(cipher.encrypt(_pkcs7(plain))).decode("utf-8")
    url = f"https://apigateway.kisti.re.kr/tokenrequest.do?client_id={CLIENT_ID}&accounts={accounts}"
    return httpx.get(url, timeout=15).json()

def search_paper(access_token: str, keyword: str) -> str:
    q = parse.quote(json.dumps({"BI": keyword}))
    url = ("https://apigateway.kisti.re.kr/openapicall.do?"
           f"client_id={CLIENT_ID}&token={access_token}&version=1.0"
           f"&action=search&target=ARTI&searchQuery={q}&curPage=1&rowCount=10")
    return httpx.get(url, timeout=20).text

if __name__ == "__main__":
    tk = create_token()
    print(tk["access_token"])
    print(search_paper(tk["access_token"], "양자컴퓨터"))
```

### 응답 예시

```json
{
  "access_token":  "0a583bb6ed7d2f535719ac23999bbe2f...",
  "refresh_token": "c877261643542220ec7636154be88b60...",
  "access_token_expire":  "2026-05-22 12:44:24.873",   // 2시간 유효
  "refresh_token_expire": "2026-06-05 10:44:24.873",   // 2주 유효
  "issued_at":            "2026-05-22 10:44:24.000873",
  "client_id":            "<요청 client_id>"
}
```

### 토큰 재발급 (Refresh Token 사용)

```python
url = f"https://apigateway.kisti.re.kr/tokenrequest.do?refreshToken={refresh_token}&client_id={CLIENT_ID}"
new = httpx.get(url, timeout=15).json()  # 새 access_token 발급
```

### 흔한 오류

| 코드 | 원인 | 해결 |
|---|---|---|
| `E4006` | 암호화 방식 불일치 (가장 흔함) | AES-256-CBC + 고정 IV + urlsafe_b64encode 사용 |
| `E4103` | Access Token 만료 | Refresh Token으로 재발급 |
| `E4106` | Refresh Token 만료 | createToken으로 처음부터 |

> ⚠️ **MAC 주소는 신청 시 등록한 값과 정확히 일치**해야 합니다. (대문자/소문자, 콜론/하이픈 포함). 변경이 필요하면 ScienceON 포털에서 수정 후 사용하세요.

---

## 데이터 출처

[국가과학기술지식정보서비스(NTIS)](https://www.ntis.go.kr) — 한국과학기술정보연구원(KISTI) 제공.

---

## 라이선스

[LICENSE](LICENSE) 참조.
