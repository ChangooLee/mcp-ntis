# NTIS · ScienceON 통합 REST API 게이트웨이

`mcp-ntis`의 33개 MCP 도구(NTIS 16개 + ScienceON 17개)를 **REST API**로 노출합니다.

다른 사용자가 본인의 MCP 클라이언트 · LangChain · LLM 워크플로에 바로 wrap해서 쓰도록
서버는 **API 라우터 역할만** 수행합니다.

---

## 빠른 시작

### 서버 측 (lchangoo@192.168.219.119)

```bash
cd ~/mcp-ntis
source .venv/bin/activate
uvicorn gateway.main:app --host 0.0.0.0 --port 8090
```

또는 user systemd로 영속:

```bash
systemctl --user status mcp-gateway.service
systemctl --user restart mcp-gateway.service
```

로그: `~/mcp-ntis/gateway.log`

### 클라이언트 측

```bash
# 헬스체크
curl http://192.168.219.119:8090/health

# 도구 목록 (33개)
curl http://192.168.219.119:8090/tools

# 특정 도구 메타
curl http://192.168.219.119:8090/tools/search_rnd_projects

# 도구 실행
curl -X POST http://192.168.219.119:8090/api/search_rnd_projects \
  -H "Content-Type: application/json" \
  -d '{"query": "배 수확", "page_size": 5}'
```

OpenAPI 문서: <http://192.168.219.119:8090/docs>

---

## 엔드포인트

| 메소드 | 경로 | 설명 |
|---|---|---|
| `GET` | `/` | 게이트웨이 상태·등록 도구 수 |
| `GET` | `/health` | 헬스체크 (`{status:"ok"}`) |
| `GET` | `/tools` | 33개 도구 목록 (이름·설명·태그·파라미터 키) |
| `GET` | `/tools/{name}` | 도구 전체 메타 (description·parameter schema) |
| `POST` | `/api/{name}` | 도구 실행 — body는 파라미터 dict |
| `GET` | `/docs` | Swagger UI |
| `GET` | `/openapi.json` | OpenAPI 스펙 |

---

## 33개 도구 카탈로그

### NTIS (국가 R&D 정보망) — 16개

| 카테고리 | 도구 |
|---|---|
| 검색 (5) | `search_rnd_projects`, `search_research_papers`, `search_patents`, `search_research_reports`, `search_research_equipment` |
| 통합·과제·기관 (3) | `search_unified`, `get_consignment_research`, `get_org_rnd_status` |
| 분류 추천·코드 (4) | `recommend_std_classification`, `recommend_ht_classification`, `recommend_it_classification`, `get_classification_codes` |
| 기타 (4) | `search_rnd_issues`, `search_terminology`, `get_related_content`, `get_ntis_tool_info` |

### ScienceON (학술·특허 DB) — 17개

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
curl -X POST http://192.168.219.119:8090/api/search_rnd_projects \
  -H "Content-Type: application/json" \
  -d '{
    "query": "배 적숙기 판정",
    "page_size": 5
  }'
```

응답 (요약):
```json
{
  "total_hits": 6,
  "items": [
    {
      "id": "...",
      "title": "재배지 환경에 따른 과실 품질 변화 및 적숙기 판정 기술 개발",
      "institution": "전북대학교",
      "year": "2013",
      "government_funds_krw": 30000000
    }
  ]
}
```

### ScienceON — 학술 논문 검색 (search_query는 KISTI 명세)

```bash
curl -X POST http://192.168.219.119:8090/api/search_sci_papers \
  -H "Content-Type: application/json" \
  -d '{
    "search_query": {"BI": "pear harvest timing"},
    "row_count": 5
  }'
```

응답 (요약):
```json
{
  "status": "ok",
  "total_count": 20,
  "items": [
    {
      "cn": "...",
      "title": "초기 생장 기반 프로테오믹스와 기상 변수를 통한 '신고' 배 세포벽 구성 성분 변화 예측",
      "pub_year": 2026
    }
  ]
}
```

### 정량 합산 — fetch_all

```bash
curl -X POST http://192.168.219.119:8090/api/search_rnd_projects \
  -H "Content-Type: application/json" \
  -d '{
    "query": "스마트 변기",
    "fetch_all": true,
    "max_fetch": 500
  }'
```

---

## 인증 (선택)

서버의 `.env` 또는 systemd `EnvironmentFile`에 `GATEWAY_API_KEY=...`를 설정하면 모든 요청에 `X-API-Key` 헤더가 필요합니다.

```bash
curl -X POST http://192.168.219.119:8090/api/search_rnd_projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: 발급받은-키" \
  -d '{"query": "AI 신약"}'
```

값이 비어 있으면 인증 비활성화(개발용).

---

## MCP 클라이언트로 wrap 하기 (활용 예)

이 게이트웨이는 **REST**라서 MCP가 아닙니다. 본인이 사용하는 MCP 클라이언트에 wrap하려면 두 가지 방법:

### 방법 1 — REST → MCP 어댑터 한 줄

```python
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-ntis-proxy")
GATEWAY = "http://192.168.219.119:8090"


@mcp.tool()
async def search_rnd_projects(query: str, page_size: int = 10) -> dict:
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{GATEWAY}/api/search_rnd_projects",
                         json={"query": query, "page_size": page_size})
        return r.json()
```

원하는 도구만 골라 wrap하면 됨.

### 방법 2 — LangChain Tool

```python
from langchain_core.tools import StructuredTool
import httpx

def search_papers(query: str, row_count: int = 10):
    r = httpx.post("http://192.168.219.119:8090/api/search_sci_papers",
                   json={"search_query": {"BI": query}, "row_count": row_count})
    return r.json()

tool = StructuredTool.from_function(
    name="search_sci_papers",
    description="ScienceON 학술 논문 검색",
    func=search_papers,
)
```

### 방법 3 — `/tools` 자동 동기화

`GET /tools` + `GET /tools/{name}`으로 메타를 받아 클라이언트에서 동적으로 33개 모두 자동 등록.

---

## systemd 서비스 관리 (서버 측)

```bash
# 상태
systemctl --user status mcp-gateway.service

# 재시작
systemctl --user restart mcp-gateway.service

# 로그 (실시간)
tail -f ~/mcp-ntis/gateway.log

# 비활성화
systemctl --user disable --now mcp-gateway.service
```

**재부팅 후에도 살아있게 하려면** (sudo 1회 필요):
```bash
sudo loginctl enable-linger lchangoo
```

---

## 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| `Address already in use` | 8090 점유 | `ss -tlnp` 로 확인 후 unit의 포트 변경 |
| NTIS 응답 `"코드 3 접근 허용 IP 아님"` | 노트북·다른 IP에서 호출 | 서버에서 호출 (서버 IP가 화이트리스트 등록된 경우만) |
| ScienceON `E4302` | 권한 미부여 도구 | 17개 공식 카탈로그만 노출 — 이전 deprecated 9개는 제거됨 |
| ScienceON `E4007 searchField` | 잘못된 검색 필드 | `GET /tools/{name}`으로 지원 필드 확인 (SCENT는 PY만, SNEWS는 RD만 등) |

---

## 보안 주의

- `.env` 파일에는 NTIS·ScienceON 발급 키가 포함됩니다. **절대 git에 커밋·외부 공유 금지**.
- 외부 인터넷에 노출할 경우 반드시 `GATEWAY_API_KEY`와 HTTPS(리버스 프록시) 적용.
- 본 게이트웨이는 LAN 내부 사용을 가정합니다.
