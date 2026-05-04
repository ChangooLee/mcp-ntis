import json
import logging
import sys
import threading
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncIterator, Optional

from fastmcp import FastMCP
from mcp.types import TextContent

from .client import NTISClient
from .config import MCPConfig, NTISConfig

mcp_config = MCPConfig.from_env()
logging.basicConfig(
    level=getattr(logging, mcp_config.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("mcp-ntis")

_global_client: Optional[NTISClient] = None
_lock = threading.Lock()


def get_client() -> NTISClient:
    global _global_client
    with _lock:
        if _global_client is None:
            raise RuntimeError("NTISClient not initialized")
        return _global_client


def set_client(client: NTISClient) -> None:
    global _global_client
    with _lock:
        _global_client = client


def error_text(msg: str) -> TextContent:
    return as_json_text({"error": msg})


def _compact(obj: Any) -> Any:
    """빈 문자열·빈 컬렉션을 재귀적으로 제거해 컨텍스트 노이즈를 줄인다."""
    if isinstance(obj, dict):
        cleaned = {k: _compact(v) for k, v in obj.items()}
        return {k: v for k, v in cleaned.items() if v not in ("", [], {}, None)}
    if isinstance(obj, list):
        return [_compact(v) for v in obj]
    return obj


def as_json_text(payload: Any) -> TextContent:
    if isinstance(payload, (dict, list)):
        txt = json.dumps(_compact(payload), ensure_ascii=False, separators=(",", ":"))
    elif isinstance(payload, str):
        txt = payload
    else:
        txt = json.dumps(str(payload), ensure_ascii=False)
    return TextContent(type="text", text=txt)


@dataclass
class NTISContext:
    client: NTISClient


@asynccontextmanager
async def ntis_lifespan(app: FastMCP) -> AsyncIterator[NTISContext]:
    logger.info("NTIS MCP 서버 초기화 중...")
    try:
        config = NTISConfig.from_env()
        client = NTISClient(config)
        set_client(client)
        ctx = NTISContext(client=client)
        logger.info("NTIS 클라이언트 초기화 완료")
        yield ctx
    except Exception as e:
        logger.error(f"초기화 실패: {e}", exc_info=True)
        raise
    finally:
        global _global_client
        if _global_client:
            await _global_client.close()
        with _lock:
            _global_client = None
        logger.info("NTIS MCP 서버 종료")


mcp = FastMCP(
    "NTIS MCP",
    instructions=(
        "국가과학기술지식정보서비스(NTIS) 도구 모음. 총 15개 도구.\n\n"

        "【도구 선택 규칙】\n"
        "▸ R&D 과제 검색 → search_rnd_projects (예산·분류·기간 등 가장 풍부)\n"
        "▸ 논문/특허/보고서/장비 각각 → 전용 도구 사용 (search_research_papers 등)\n"
        "▸ 여러 유형 동시 탐색 → search_unified(collection='rpaper,rpatent')\n"
        "▸ 위탁·공동연구 기관 목록 → get_consignment_research(project_id=search_rnd_projects 결과의 id)\n"
        "▸ 기관 R&D 역량·연도별 추이 → get_org_rnd_status\n"
        "▸ 과학기술 트렌드 파악 → search_rnd_issues\n"
        "▸ 용어 정의·약어 확인 → search_terminology\n"
        "▸ 분류코드 계층 탐색 → get_classification_codes\n"
        "▸ 유사 과제/논문/특허 발굴 → get_related_content\n\n"

        "【분류 추천 도구 선택】\n"
        "▸ 과기부·교육부·환경부 등 일반 R&D → recommend_std_classification\n"
        "▸ 보건복지부·질병청·국립암센터 → recommend_ht_classification\n"
        "▸ 산업통상자원부·중소벤처기업부 → recommend_it_classification\n"
        "▸ 부처가 불분명하면 세 도구 모두 호출해 비교\n\n"

        "【검색 팁】\n"
        "▸ 기관명 검색: search_field='OG', query='삼성전자'\n"
        "▸ 연구책임자 검색: search_field='AU', query='홍길동'\n"
        "▸ 특정 연도 과제: add_query='PY=2023/SAME'\n"
        "▸ 연도 범위: add_query='PY=2020/MORE&2023/UNDER'\n"
        "▸ 복수 조건: add_query='PY=2022/SAME&CN=1711'\n"
        "▸ page_size=3~5면 개요 파악에 충분, 10은 상세 목록용"
    ),
    lifespan=ntis_lifespan,
)

import importlib
for _mod in ["search_tools", "project_tools", "classification_tools", "extra_tools"]:
    importlib.import_module(f"mcp_ntis.tools.{_mod}")


def main() -> None:
    logger.info("NTIS MCP 서버 시작")
    if mcp_config.transport == "http":
        logger.info(f"HTTP 모드: http://{mcp_config.host}:{mcp_config.port}")
        mcp.run(transport="streamable-http", host=mcp_config.host, port=mcp_config.port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
