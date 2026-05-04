# CLAUDE.md — NTIS MCP 개발 가이드

## 프로젝트 개요

국가과학기술지식정보서비스(NTIS) API를 MCP(Model Context Protocol)로 래핑한 서버.
FastMCP 기반, Python 3.10+, 비동기 httpx 클라이언트, 파일 기반 캐시.

## 핵심 파일 구조

```
src/mcp_ntis/
├── server.py          # FastMCP 인스턴스, lifespan, as_json_text(), get_client()
├── config.py          # NTISConfig, MCPConfig (.env 로드)
├── client.py          # NTISClient (API 호출, XML 파싱, 캐시 통합)
├── cache.py           # 파일 기반 캐시 (~/.cache/mcp-ntis/, MD5 키, TTL)
└── tools/
    ├── search_tools.py        # search_rnd_projects, search_research_papers, search_patents,
    │                          #   search_research_reports, search_research_equipment, search_unified
    ├── project_tools.py       # get_consignment_research
    ├── classification_tools.py # recommend_std_classification, recommend_ht_classification,
    │                           #   recommend_it_classification
    └── extra_tools.py         # get_org_rnd_status, search_rnd_issues, search_terminology,
                               #   get_classification_codes, get_related_content
```

## 코딩 패턴

### 도구 등록
```python
from mcp_ntis.server import as_json_text, get_client, mcp
from mcp.types import TextContent
from typing import Annotated
from pydantic import Field

@mcp.tool(name="tool_name", description="도구 설명")
async def tool_name(
    param: Annotated[str, Field(description="파라미터 설명")],
) -> TextContent:
    client = get_client()
    result = await client.some_method(param)
    return as_json_text(result)
```

### 새 도구 모듈 추가
`server.py`의 importlib 루프에 모듈명 추가:
```python
for _mod in ["search_tools", "project_tools", "classification_tools", "new_module"]:
    importlib.import_module(f"mcp_ntis.tools.{_mod}")
```

### XML 파싱 패턴 (client.py)
- `_strip_html(text)`: span 하이라이트 태그 제거
- `_elem_text(elem)`: None-safe 텍스트 추출 — `itertext()` 사용 (NTIS가 `<Korean><span>나노</span>소재</Korean>` 형태로 span을 실제 XML 자식 요소로 반환하므로 `elem.text`로는 빈 문자열이 됨)
- `_child_text(parent, tag)`: 자식 태그 텍스트 추출
- `_parse_keyword(elem)`: 한글/영문 키워드 dict 반환
- **절대 `elem.text`나 `findtext()` 직접 사용 금지** → 항상 `_elem_text()` / `_child_text()` 사용

## API 엔드포인트

| 기능 | URL | 인증 |
|---|---|---|
| 과제검색 | `https://www.ntis.go.kr/rndopen/openApi/pjtSearch/project` | `apprvKey` |
| 성과검색 | `https://www.ntis.go.kr/rndopen/openApi/natRnDSearch` | `apprvKey` |
| 통합검색 | `https://www.ntis.go.kr/rndopen/openApi/totalRstSearch` | `apprvKey` |
| 위탁/공동 | `https://www.ntis.go.kr/rndopen/openApi/projectuOrg` | `apprvKey` |
| 분류추천 | `https://www.ntis.go.kr/rndopen/openApi/rcmncls` | `apprvKey` |
| 수행기관 R&D현황 | `https://www.ntis.go.kr/rndopen/openApi/orgRndInfo` | `apprvKey` |
| 이슈로보는R&D | `https://www.ntis.go.kr/rndopen/openApi/issue` | `apprvKey` |
| 용어사전 | `https://www.ntis.go.kr/rndopen/openApi/ntisDic` | `userKey` (=NTIS_API_KEY) |
| 분류코드 검색 | `https://www.ntis.go.kr/rndopen/openApi/targetSearch` | `apprvKey` |
| 연관콘텐츠 추천 | `https://www.ntis.go.kr/rndopen/openApi/ConnectionContent` | `apprvKey` |

- 모든 응답은 XML (UTF-8)
- Rate limit: 검색 30 tps, 분류추천 100 tps
- 검색 결과 `<span class="search_word">` 태그 포함 → 반드시 제거

## 환경변수

| 변수 | 필수 | 설명 |
|---|---|---|
| `NTIS_API_KEY` | Y | NTIS 승인 인증키 |
| `NTIS_ORG_CD` | N | 기관약어 (분류추천 필요) |
| `NTIS_USER_ID` | N | 로그인 사용자 ID |
| `NTIS_CACHE_TTL_HOURS` | N | 캐시 TTL 시간 (기본 24) |
| `LOG_LEVEL` | N | 로그 레벨 (기본 INFO) |
| `TRANSPORT` | N | stdio 또는 http (기본 stdio) |

## 설치 및 실행

```bash
cd /Users/changoo/Workspace/mcp-ntis
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

cp .env.example .env
# .env에 NTIS_API_KEY=lg814619kv046cp808fk 설정

# 테스트 실행
python -c "from mcp_ntis.server import mcp; print('OK')"

# MCP Inspector로 테스트
npx @modelcontextprotocol/inspector python -m mcp_ntis.server
```

## 품질 평가 기준

1. **API 정상 호출**: 모든 15개 도구가 실제 NTIS API 응답 반환
2. **LLM 도구 선택**: 검색 의도에 맞는 도구가 자동 선택
3. **정보 밀도**: 응답에 불필요한 HTML/XML 잔재 없음, 핵심 필드만 포함
4. **적정 도구 설계**: 유사 기능 중복 없음, 파라미터 명확

## 주의사항

- NAVIGATION 섹션(페이셋 데이터)은 응답에서 제외 (토큰 낭비)
- Abstract는 Full 대신 Teaser(250자) 사용 (토큰 절약)
- `pjtSearch` URL은 collection이 경로에 포함: `.../pjtSearch/project`
- 분류추천 API: `rqstDes` 최소 300byte, 최대 30KB
- 캐시 위치: `~/.cache/mcp-ntis/`
