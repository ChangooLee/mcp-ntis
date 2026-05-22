"""NTIS MCP FastMCP 서버.

mcp-opendart 패턴을 차용: NTISContext + global ctx fallback + Tool Registry.
"""

from __future__ import annotations

import json
import logging
import sys
import threading
from dataclasses import dataclass
from typing import Any, Optional

from fastmcp import FastMCP
from mcp.types import TextContent

from .client import NTISClient
from .config import MCPConfig, NTISConfig
from .registry.initialize_registry import initialize_registry

mcp_config = MCPConfig.from_env()
logging.basicConfig(
    level=getattr(logging, mcp_config.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("mcp-ntis")


# ---------------------------------------------------------------------------
# NTISContext + Global Context (lifespan/HTTP fallback)
# ---------------------------------------------------------------------------


@dataclass
class NTISContext:
    """Lifespan에서 생성·공유되는 NTIS MCP 컨텍스트."""

    client: NTISClient


_global_context: Optional[NTISContext] = None
_context_lock = threading.Lock()


def set_global_context(ctx: NTISContext) -> None:
    global _global_context
    with _context_lock:
        _global_context = ctx
        logger.info("✅ Global NTISContext 저장됨")


def get_global_context() -> Optional[NTISContext]:
    with _context_lock:
        return _global_context


# Backward-compat: 기존 도구가 사용하던 헬퍼
def get_client() -> NTISClient:
    ctx = get_global_context()
    if ctx is None:
        raise RuntimeError("NTISClient not initialized (lifespan not started)")
    return ctx.client


def set_client(client: NTISClient) -> None:
    """기존 호환을 위해 client 객체만 받아 NTISContext로 래핑."""
    set_global_context(NTISContext(client=client))


# ---------------------------------------------------------------------------
# JSON TextContent 헬퍼 (server.py에서도 노출 — 기존 import 호환)
# ---------------------------------------------------------------------------


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
    # 도구 응답에 transform_response가 적용된 뒤에도 _compact 처리로
    # LLM 컨텍스트 토큰을 절약
    if isinstance(payload, (dict, list)):
        txt = json.dumps(_compact(payload), ensure_ascii=False, separators=(",", ":"))
    elif isinstance(payload, str):
        txt = payload
    else:
        txt = json.dumps(str(payload), ensure_ascii=False)
    return TextContent(type="text", text=txt)


# ---------------------------------------------------------------------------
# 모듈 레벨 초기화 — NTIS 클라이언트와 컨텍스트
# ---------------------------------------------------------------------------


def _bootstrap_context() -> None:
    """모듈 로드 시 NTIS 클라이언트와 전역 컨텍스트를 즉시 초기화한다.

    FastMCP 3.x의 lifespan은 stdio 통신에서 list_tools 응답 직후
    조기 종료되는 케이스가 있어, 안정적인 동작을 위해 모듈 로드 시점에
    초기화한다.
    """
    if get_global_context() is not None:
        return
    try:
        ntis_config = NTISConfig.from_env()
        client = NTISClient(ntis_config)
        set_global_context(NTISContext(client=client))
        logger.info("NTIS 클라이언트 초기화 완료")
    except Exception as exc:
        logger.error(f"NTIS 클라이언트 초기화 실패: {exc}", exc_info=True)
        raise


# ---------------------------------------------------------------------------
# Tool Registry (메타 도구가 참조)
# ---------------------------------------------------------------------------

tool_registry = initialize_registry()


# ---------------------------------------------------------------------------
# FastMCP 인스턴스 + Instructions
# ---------------------------------------------------------------------------


mcp = FastMCP(
    "NTIS MCP",
    instructions=(
        "국가과학기술지식정보서비스(NTIS) 도구 모음. 총 16개 도구 (메타 도구 1개 포함).\n\n"
        "【도구 선택 가이드】 어떤 도구를 사용할지 모르겠으면 먼저 "
        "`get_ntis_tool_info()`를 호출해 카테고리별 전체 목록을 확인하거나 "
        "`get_ntis_tool_info(tool_name='...')`로 특정 도구의 활용 패턴·연관 도구를 조회.\n\n"

        "▸ R&D 과제 검색 → search_rnd_projects (예산·분류·기간 등 가장 풍부)\n"
        "▸ 논문/특허/보고서/장비 각각 → 전용 도구 (search_research_papers 등)\n"
        "▸ 여러 유형 동시 탐색 → search_unified(collection='rpaper,rpatent')\n"
        "▸ 위탁·공동연구 기관 목록 → get_consignment_research(project_id=...)\n"
        "▸ 기관 R&D 역량 → get_org_rnd_status (auto_resolve=True)\n"
        "▸ 트렌드 파악 → search_rnd_issues\n"
        "▸ 용어 정의 → search_terminology\n"
        "▸ 분류코드 계층 → get_classification_codes\n"
        "▸ 유사 과제 추천 → get_related_content (project만 지원)\n\n"

        "【분류 추천】\n"
        "▸ 일반 R&D → recommend_std_classification\n"
        "▸ 보건의료 → recommend_ht_classification (질환·연구행위·산업기술 3종)\n"
        "▸ 산업기술 → recommend_it_classification\n"
        "▸ 부처 불분명 → 세 도구 모두 호출 비교\n\n"

        "【핵심 검색 팁】\n"
        "▸ 기관명: search_field='OG', query='한국전자통신연구원'\n"
        "▸ 책임자: search_field='AU', query='홍길동'\n"
        "▸ 기관+키워드 조합: search_field='BI', query='AI', add_query='OG=KAIST&PY=2024/SAME'\n"
        "▸ 정량 분석(예산 합산·통계): fetch_all=True 필수\n"
        "  - 100건 상한 → fetch_all=False면 부정확한 집계가 됨"
    ),
)


# ---------------------------------------------------------------------------
# 도구 모듈 자동 import + 컨텍스트 부트스트랩
# ---------------------------------------------------------------------------


import importlib

for _mod in [
    "search_tools",
    "project_tools",
    "classification_tools",
    "extra_tools",
    "meta_tools",
]:
    importlib.import_module(f"mcp_ntis.tools.{_mod}")

# ScienceON (KISTI ScienceON OpenAPI) — SCIENCEON_* 환경변수 설정 시에만 활성
import os as _os

if _os.getenv("SCIENCEON_CLIENT_ID") and _os.getenv("SCIENCEON_API_KEY"):
    try:
        importlib.import_module("mcp_ntis.scienceon.tools")
        logger.info("ScienceON 도구 17개 활성화 (공식 카탈로그 1:1 매핑)")
    except Exception as _exc:
        logger.warning(f"ScienceON 도구 로드 실패: {_exc}")


# 모듈 로드 직후 NTIS 클라이언트 즉시 초기화
_bootstrap_context()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    logger.info("NTIS MCP 서버 시작")
    if mcp_config.transport == "http":
        logger.info(f"HTTP 모드: http://{mcp_config.host}:{mcp_config.port}")
        mcp.run(transport="streamable-http", host=mcp_config.host, port=mcp_config.port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
