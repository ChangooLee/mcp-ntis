# NTIS · ScienceON 통합 REST API 게이트웨이

`mcp-ntis`의 MCP 도구들을 **REST API**로 노출하는 옵션 컴포넌트.

여러 사용자가 본인의 MCP 클라이언트 · LangChain · LLM 워크플로에 wrap해서 쓰도록 서버는 **API 라우터 역할만** 수행합니다.

게이트웨이를 직접 운영하면 NTIS·ScienceON 발급 키를 게이트웨이에만 두고, 클라이언트들은 게이트웨이 URL과 게이트웨이 자체 API key만으로 도구를 호출할 수 있습니다.

---

## 빠른 시작

### 1. 의존성 설치

```bash
cd <project-root>
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[gateway]"
```

### 2. 환경변수 설정

`.env` (또는 systemd `EnvironmentFile`)에 다음을 정의:

```bash
# 필수 — NTIS·ScienceON 발급 키 (게이트웨이만 보유)
NTIS_API_KEY=<발급키>
SCIENCEON_CLIENT_ID=<발급 client_id>
SCIENCEON_API_KEY=<발급 api key>
SCIENCEON_MAC=<신청 시 등록한 MAC>

# 인증 (강력 권장) — 빈 값이면 비활성화(개발용)
GATEWAY_API_KEY=<openssl rand -hex 32 등으로 발급>
```

### 3. 실행

```bash
uvicorn gateway.main:app --host 0.0.0.0 --port <PORT>
```

### 4. 호출 (클라이언트 측)

```bash
GATEWAY=https://<your-gateway-host>
API_KEY=<your-gateway-api-key>

curl $GATEWAY/health
curl -H "X-API-Key: $API_KEY" $GATEWAY/tools

curl -X POST $GATEWAY/api/search_rnd_projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"query": "<검색어>", "page_size": 5}'
```

OpenAPI 문서: `$GATEWAY/docs`

---

## 엔드포인트

| 메소드 | 경로 | 설명 |
|---|---|---|
| `GET` | `/` | 게이트웨이 상태·등록 도구 수 |
| `GET` | `/health` | 헬스체크 (`{status:"ok"}`) — 인증 면제 |
| `GET` | `/tools` | 등록된 도구 목록 (이름·설명 첫 줄·태그·파라미터 키) |
| `GET` | `/tools/{name}` | 도구 전체 메타 (description·parameter schema) |
| `POST` | `/api/{name}` | 도구 실행 — body는 파라미터 dict |
| `GET` | `/docs` | Swagger UI |
| `GET` | `/openapi.json` | OpenAPI 스펙 |

---

## 도구 카탈로그 (총 33개)

### NTIS — 16개

| 카테고리 | 도구 |
|---|---|
| 검색 (5) | `search_rnd_projects`, `search_research_papers`, `search_patents`, `search_research_reports`, `search_research_equipment` |
| 통합·과제·기관 (3) | `search_unified`, `get_consignment_research`, `get_org_rnd_status` |
| 분류 추천·코드 (4) | `recommend_std_classification`, `recommend_ht_classification`, `recommend_it_classification`, `get_classification_codes` |
| 기타 (4) | `search_rnd_issues`, `search_terminology`, `get_related_content`, `get_ntis_tool_info` |

### ScienceON — 17개

| 카테고리 | 도구 |
|---|---|
| 논문 (2) | `search_sci_papers`, `get_sci_paper` |
| 특허 (3) | `search_sci_patents`, `get_sci_patent`, `search_sci_citation_patents` |
| 보고서 (2) | `search_sci_reports`, `get_sci_report` |
| 동향·과학향기 (4) | `search_sci_trends`, `get_sci_trend`, `search_sci_scent`, `get_sci_scent` |
| 연구자·연구기관 (4) | `search_sci_researchers`, `get_sci_researcher`, `search_sci_organizations`, `get_sci_organization` |
| TREND·뉴스 (2) | `search_sci_infra_trend`, `search_sci_tech_news` |

---

## 호출 예시

### NTIS — 키워드로 R&D 과제 검색

```bash
curl -X POST $GATEWAY/api/search_rnd_projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "query": "<키워드>",
    "page_size": 5
  }'
```

### ScienceON — 학술 논문 검색 (search_query는 KISTI 명세)

```bash
curl -X POST $GATEWAY/api/search_sci_papers \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "search_query": {"BI": "<영문 키워드>"},
    "row_count": 5
  }'
```

### 정량 합산 — `fetch_all`

```bash
curl -X POST $GATEWAY/api/search_rnd_projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "query": "<키워드>",
    "fetch_all": true,
    "max_fetch": 500
  }'
```

---

## 인증

서버의 `.env` 또는 systemd `EnvironmentFile`에 `GATEWAY_API_KEY=...`를 설정하면 모든 요청에 `X-API-Key` 헤더가 필요합니다.

값이 비어 있으면 인증 비활성화 (개발 환경 전용).

`/health`만 인증 면제 (모니터링·로드밸런서 헬스체크용).

---

## 클라이언트가 MCP·LangChain에 wrap 하는 방법

이 게이트웨이는 REST라서 그대로는 MCP가 아닙니다. 사용 중인 MCP 클라이언트에 wrap하려면 다음 중 하나:

### 방법 1 — REST → MCP 어댑터

```python
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-ntis-proxy")
GATEWAY = "<your-gateway-url>"
API_KEY = "<your-gateway-api-key>"


@mcp.tool()
async def search_rnd_projects(query: str, page_size: int = 10) -> dict:
    async with httpx.AsyncClient() as c:
        r = await c.post(
            f"{GATEWAY}/api/search_rnd_projects",
            headers={"X-API-Key": API_KEY},
            json={"query": query, "page_size": page_size},
        )
        return r.json()
```

원하는 도구만 골라 wrap하면 됨.

### 방법 2 — LangChain Tool

```python
from langchain_core.tools import StructuredTool
import httpx

GATEWAY = "<your-gateway-url>"
API_KEY = "<your-gateway-api-key>"


def search_papers(query: str, row_count: int = 10):
    r = httpx.post(
        f"{GATEWAY}/api/search_sci_papers",
        headers={"X-API-Key": API_KEY},
        json={"search_query": {"BI": query}, "row_count": row_count},
    )
    return r.json()


tool = StructuredTool.from_function(
    name="search_sci_papers",
    description="ScienceON 학술 논문 검색",
    func=search_papers,
)
```

### 방법 3 — `/tools` 자동 동기화 (33개 일괄 등록)

`GET /tools` + `GET /tools/{name}`으로 메타를 받아 클라이언트에서 동적으로 33개 모두 자동 등록.

본 저장소의 `chatbot/agent.py`가 환경변수 `NTIS_GATEWAY_URL` + `NTIS_GATEWAY_API_KEY`만 설정해도 게이트웨이를 통해 33개 도구를 자동 로드하는 예시 구현을 포함합니다 (REST 모드).

---

## systemd 영속 실행 (Linux)

`gateway/mcp-gateway.service` 파일을 user systemd 또는 system systemd에 등록할 수 있습니다.

```bash
# user systemd
mkdir -p ~/.config/systemd/user
cp gateway/mcp-gateway.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now mcp-gateway.service

# 로그
tail -f ~/<project-root>/gateway.log
```

재부팅·로그아웃에도 살리려면 (sudo 1회 필요):

```bash
sudo loginctl enable-linger <user>
```

---

## nginx 리버스 프록시 (HTTPS·도메인 노출)

게이트웨이는 기본적으로 HTTP만 listen합니다. 외부 노출 시 nginx + Let's Encrypt 등을 통한 HTTPS·도메인 매핑을 권장합니다.

다음과 같은 location 블록을 본인의 HTTPS 가상 호스트에 추가:

```nginx
location ^~ /mcp-gateway/ {
    add_header X-Robots-Tag "noindex, nofollow" always;
    client_max_body_size 1m;
    access_log /var/log/nginx/mcp-gateway.access.log;
    error_log  /var/log/nginx/mcp-gateway.error.log warn;

    proxy_pass http://127.0.0.1:<게이트웨이 포트>/;
    proxy_http_version 1.1;
    proxy_set_header Host              $host;
    proxy_set_header X-Real-IP         $remote_addr;
    proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-API-Key         $http_x_api_key;
    proxy_set_header Connection        "";

    proxy_hide_header X-Powered-By;
    proxy_hide_header Server;

    proxy_buffering    off;
    proxy_read_timeout 120s;
    proxy_connect_timeout 30s;
    proxy_send_timeout 30s;
}

location = /mcp-gateway {
    return 301 /mcp-gateway/;
}
```

---

## 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| `Address already in use` | 게이트웨이 포트 점유 | `ss -tlnp` 로 확인 후 unit의 포트 변경 |
| NTIS 응답 `"코드 3 접근 허용 IP 아님"` | NTIS 화이트리스트 외 IP에서 호출 | 게이트웨이를 NTIS 화이트리스트 등록된 IP에서 운영 |
| ScienceON `E4302` | KISTI 권한 미부여 도구 | 17개 공식 카탈로그만 노출 |
| ScienceON `E4007 searchField` | 잘못된 검색 필드 | `GET /tools/{name}`으로 지원 필드 확인 (SCENT는 PY만, SNEWS는 RD만 등) |
| HTTP 401 | `X-API-Key` 헤더 누락·불일치 | 키 확인 |

---

## 보안 주의

- `.env` 파일에는 NTIS·ScienceON 발급 키와 `GATEWAY_API_KEY`가 포함됩니다. **절대 git에 커밋·외부 공유 금지** (저장소의 `.gitignore`에 등재 확인).
- 외부 인터넷에 노출할 경우 반드시 `GATEWAY_API_KEY`와 HTTPS(리버스 프록시) 적용.
- API key는 사용자별 별도 발급·rotate 권장.
- nginx 단의 access log와 별도 로그를 분리 운영하면 이상 트래픽 탐지가 용이.
