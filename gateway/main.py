"""NTIS · ScienceON 통합 REST API 게이트웨이.

mcp-ntis의 33개 MCP 도구를 REST 엔드포인트로 자동 노출한다.
다른 사용자가 본인의 MCP 클라이언트·LangChain·LLM에 wrap해서 쓸 수 있도록
서버는 API 라우터 역할만 수행.

기동:
    uvicorn gateway.main:app --host 0.0.0.0 --port 8080

엔드포인트:
    GET  /             - 게이트웨이 상태·등록 도구 수
    GET  /health       - 단순 헬스체크
    GET  /tools        - 33개 도구 메타 목록 (이름·설명·파라미터 스키마)
    GET  /tools/{name} - 특정 도구 메타 상세
    POST /api/{name}   - 도구 실행 (body=파라미터 dict)

인증 (선택):
    환경변수 `GATEWAY_API_KEY`가 설정되면 모든 요청에 `X-API-Key` 헤더 필요.
    빈 값이면 인증 없이 동작 (개발용).
"""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
import os
import time
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# mcp-ntis 패키지 import
import mcp_ntis.server  # noqa: F401 (도구 등록 트리거)
from mcp_ntis.server import mcp, tool_registry

logger = logging.getLogger("gateway")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


# ---------------------------------------------------------------------------
# 인증
# ---------------------------------------------------------------------------


def _check_api_key(request: Request) -> None:
    expected = os.getenv("GATEWAY_API_KEY", "").strip()
    if not expected:
        return  # 인증 비활성화
    received = request.headers.get("x-api-key", "").strip()
    if received != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key 헤더가 누락되었거나 일치하지 않습니다.",
        )


# ---------------------------------------------------------------------------
# FastAPI 앱
# ---------------------------------------------------------------------------


app = FastAPI(
    title="NTIS · ScienceON 통합 REST 게이트웨이",
    description=(
        "한국 정부 R&D 정보망(NTIS)과 학술·특허 데이터베이스(ScienceON)의 "
        "33개 도구를 REST API로 노출합니다.\n\n"
        "각 도구는 `POST /api/{tool_name}`으로 호출하며, body에 파라미터 dict를 전달합니다.\n\n"
        "도구 목록은 `GET /tools`로 조회하세요."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 필요 시 도메인 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# 도구 호출 헬퍼
# ---------------------------------------------------------------------------


async def _invoke_tool(tool_name: str, params: dict[str, Any]) -> Any:
    """MCP 도구를 호출하고 정제된 결과를 반환."""
    tool = await mcp.get_tool(tool_name)
    if tool is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"도구 '{tool_name}'을(를) 찾을 수 없습니다. /tools 로 도구 목록을 확인하세요.",
        )

    fn = getattr(tool, "fn", None)
    if fn is None:
        raise HTTPException(status_code=500, detail=f"도구 '{tool_name}'에 fn 핸들러가 없습니다.")

    # 빈 dict / None 처리
    params = params or {}

    try:
        result = fn(**params)
        if inspect.iscoroutine(result):
            result = await result
    except TypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"파라미터 오류: {exc}. /tools/{tool_name} 으로 스키마를 확인하세요.",
        )
    except Exception as exc:
        logger.exception(f"tool {tool_name} 실행 오류")
        raise HTTPException(
            status_code=500,
            detail=f"도구 실행 오류: {type(exc).__name__}: {exc}",
        )

    # TextContent → text → JSON 파싱
    if hasattr(result, "text"):
        text = result.text
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return {"raw": text}
    if isinstance(result, str):
        try:
            return json.loads(result)
        except (json.JSONDecodeError, TypeError):
            return {"raw": result}
    return result


# ---------------------------------------------------------------------------
# 메타 엔드포인트
# ---------------------------------------------------------------------------


@app.get("/", tags=["meta"])
async def root() -> dict[str, Any]:
    """게이트웨이 상태·등록 도구 수."""
    tool_names = await _list_tool_names()
    return {
        "service": "NTIS · ScienceON 통합 REST 게이트웨이",
        "version": "1.0.0",
        "tool_count": len(tool_names),
        "endpoints": {
            "tools_list": "/tools",
            "tool_meta": "/tools/{name}",
            "tool_invoke": "POST /api/{name}",
            "docs": "/docs",
            "openapi": "/openapi.json",
        },
        "auth": "X-API-Key 헤더 필요" if os.getenv("GATEWAY_API_KEY") else "비활성화 (개발용)",
    }


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok", "ts": str(int(time.time()))}


async def _list_tool_names() -> list[str]:
    """FastMCP에 등록된 도구 이름 목록."""
    # FastMCP 버전별 호환
    if hasattr(mcp, "list_tools"):
        tools = await mcp.list_tools()
        return [t.name if hasattr(t, "name") else t for t in tools]
    if hasattr(mcp, "_tool_manager"):
        return list(mcp._tool_manager._tools.keys())
    # tool_registry fallback (mcp_ntis 자체 registry)
    return list(tool_registry.tools.keys())


@app.get("/tools", tags=["meta"], dependencies=[Depends(_check_api_key)])
async def list_tools() -> dict[str, Any]:
    """등록된 모든 도구의 메타 (이름·설명·태그·파라미터 스키마)."""
    items = []
    for name in sorted(await _list_tool_names()):
        tool = await mcp.get_tool(name)
        if tool is None:
            continue
        desc = (getattr(tool, "description", "") or "").strip()
        tags = sorted(list(getattr(tool, "tags", []) or []))
        # 파라미터 스키마: FastMCP는 parameters 또는 input_schema
        params = getattr(tool, "parameters", None) or getattr(tool, "input_schema", None) or {}
        items.append(
            {
                "name": name,
                "description_head": desc.split("\n")[0][:200],
                "tags": tags,
                "parameter_keys": list((params.get("properties") or {}).keys()),
            }
        )
    return {"count": len(items), "tools": items}


@app.get("/tools/{name}", tags=["meta"], dependencies=[Depends(_check_api_key)])
async def get_tool_meta(name: str) -> dict[str, Any]:
    """특정 도구의 전체 메타 (description·파라미터 스키마 포함)."""
    tool = await mcp.get_tool(name)
    if tool is None:
        raise HTTPException(status_code=404, detail=f"도구 '{name}' 없음")
    return {
        "name": name,
        "description": (getattr(tool, "description", "") or "").strip(),
        "tags": sorted(list(getattr(tool, "tags", []) or [])),
        "parameters": getattr(tool, "parameters", None) or getattr(tool, "input_schema", None) or {},
    }


# ---------------------------------------------------------------------------
# 도구 실행 엔드포인트
# ---------------------------------------------------------------------------


@app.post("/api/{name}", tags=["invoke"], dependencies=[Depends(_check_api_key)])
async def invoke_tool(name: str, payload: dict[str, Any] | None = None) -> Any:
    """도구 실행. body에 파라미터 dict를 전달.

    예시:
        POST /api/search_rnd_projects
        {
          "query": "배 수확",
          "page_size": 5
        }

    예시 (학술 DB — searchQuery dict 필드):
        POST /api/search_sci_papers
        {
          "search_query": {"BI": "pear harvest"},
          "row_count": 3
        }
    """
    params = payload or {}
    return await _invoke_tool(name, params)


# ---------------------------------------------------------------------------
# 에러 핸들러 — 일관된 JSON
# ---------------------------------------------------------------------------


@app.exception_handler(HTTPException)
async def http_exc_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "path": str(request.url.path)},
    )


# ---------------------------------------------------------------------------
# 시작 로그
# ---------------------------------------------------------------------------


@app.on_event("startup")
async def _startup() -> None:
    names = await _list_tool_names()
    logger.info(f"게이트웨이 시작 — {len(names)}개 도구 등록")
    auth_state = "활성화" if os.getenv("GATEWAY_API_KEY") else "비활성화 (개발용)"
    logger.info(f"인증: {auth_state}")
