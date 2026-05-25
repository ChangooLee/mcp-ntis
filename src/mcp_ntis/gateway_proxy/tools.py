"""게이트웨이 프록시 도구 — 원격 게이트웨이의 N개 도구를 in-process로 wrap.

작동:
  1. 시작 시 GET /tools 로 도구 목록과 description·tags 수신
  2. 각 도구별 GET /tools/{name} 으로 입력 schema 수신
  3. 동적으로 @mcp.tool 등록 (함수 시그니처는 schema 기반 pydantic BaseModel)
  4. 호출 시 POST /api/{name} 으로 게이트웨이에 위임 후 응답 그대로 반환
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx
from mcp.types import TextContent

from mcp_ntis.server import as_json_text, error_text, mcp

logger = logging.getLogger("mcp-ntis.gateway_proxy")


# ---------------------------------------------------------------------------
# 게이트웨이 설정
# ---------------------------------------------------------------------------


GATEWAY_URL = os.getenv("NTIS_GATEWAY_URL", "").rstrip("/")
GATEWAY_KEY = os.getenv("NTIS_GATEWAY_API_KEY", "").strip()
TIMEOUT = float(os.getenv("NTIS_GATEWAY_TIMEOUT", "120"))


def _headers() -> dict[str, str]:
    h = {"Content-Type": "application/json"}
    if GATEWAY_KEY:
        h["X-API-Key"] = GATEWAY_KEY
    return h


# ---------------------------------------------------------------------------
# JSON Schema → pydantic 타입 매핑 (단순 케이스만)
# ---------------------------------------------------------------------------


_TYPE_NAME = {
    "string": "str",
    "integer": "int",
    "boolean": "bool",
    "number": "float",
    "array": "list",
    "object": "dict",
}


# ---------------------------------------------------------------------------
# 도구 호출 — 게이트웨이에 POST
# ---------------------------------------------------------------------------


async def _call_gateway(tool_name: str, kwargs: dict[str, Any]) -> TextContent:
    clean = {k: v for k, v in kwargs.items() if v is not None}
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(
                f"{GATEWAY_URL}/api/{tool_name}",
                headers=_headers(),
                json=clean,
            )
        try:
            data = resp.json()
        except Exception:
            data = {"raw": resp.text[:2000]}
        return as_json_text(data)
    except httpx.TimeoutException:
        return error_text(f"게이트웨이 타임아웃 ({TIMEOUT}s): {tool_name}")
    except httpx.RequestError as e:
        return error_text(f"게이트웨이 네트워크 오류: {e}")
    except Exception as e:
        return error_text(f"{type(e).__name__}: {e}")


def _make_proxy_fn(tool_name: str, parameters: dict[str, Any]):
    """schema에서 명시적 시그니처를 가진 async 함수를 동적 생성.

    FastMCP는 **kwargs 함수를 거부하므로 각 파라미터를 정식 인자로 노출.
    """
    props = (parameters or {}).get("properties") or {}
    required = set((parameters or {}).get("required") or [])

    sig_parts: list[str] = []
    arg_names: list[str] = []
    for key, schema in props.items():
        if not isinstance(schema, dict):
            continue
        if not key.isidentifier():
            continue  # 비-식별자 키는 skip
        py_t = _TYPE_NAME.get(schema.get("type"), "Any")
        if key in required:
            sig_parts.append(f"{key}: {py_t}")
        else:
            sig_parts.append(f"{key}: {py_t} = None")
        arg_names.append(key)

    sig = ", ".join(sig_parts) if sig_parts else ""
    args_dict = "{" + ", ".join(f"'{n}': {n}" for n in arg_names) + "}"

    code = (
        f"async def {tool_name}({sig}):\n"
        f"    return await _call_gateway({tool_name!r}, {args_dict})\n"
    )
    ns: dict[str, Any] = {"_call_gateway": _call_gateway, "Any": Any}
    exec(code, ns)
    return ns[tool_name]


# ---------------------------------------------------------------------------
# 부트스트랩 — 시작 시 1회 게이트웨이 메타 수집·등록
# ---------------------------------------------------------------------------


def _fetch_gateway_tools() -> list[dict[str, Any]]:
    """동기 httpx로 게이트웨이 /tools + /tools/{name} 조회.

    server.py 모듈 import 시점에 동기적으로 호출되므로 asyncio 안 씀.
    """
    with httpx.Client(timeout=30.0) as c:
        list_resp = c.get(f"{GATEWAY_URL}/tools", headers=_headers())
        list_resp.raise_for_status()
        tools_meta = list_resp.json().get("tools", [])
        full = []
        for entry in tools_meta:
            name = entry["name"]
            r = c.get(f"{GATEWAY_URL}/tools/{name}", headers=_headers())
            r.raise_for_status()
            full.append(r.json())
        return full


def register_proxy_tools() -> int:
    """게이트웨이의 모든 도구를 @mcp.tool로 동적 등록. 등록 개수 반환."""
    if not GATEWAY_URL:
        return 0

    try:
        tools_meta = _fetch_gateway_tools()
    except Exception as exc:
        logger.error(f"게이트웨이 메타 수집 실패: {exc}")
        raise

    count = 0
    for meta in tools_meta:
        name = meta["name"]
        description = (meta.get("description") or "").strip()
        if len(description) > 1024:
            description = description[:1020] + "..."
        parameters = meta.get("parameters") or {}
        tags = set(meta.get("tags") or [])

        proxy_fn = _make_proxy_fn(name, parameters)

        # FastMCP 데코레이터를 직접 호출하여 등록
        decorator = mcp.tool(name=name, description=description, tags=tags)
        decorator(proxy_fn)
        count += 1

    return count


# 모듈 import 시 자동 등록
_REGISTERED = register_proxy_tools()
logger.info(
    f"게이트웨이 프록시 모드 — {_REGISTERED}개 도구 등록 ({GATEWAY_URL})"
)
