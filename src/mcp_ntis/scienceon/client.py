"""ScienceON API 클라이언트.

KISTI ScienceON OpenAPI 게이트웨이(apigateway.kisti.re.kr)와 통신.
- AES-256-CBC + 고정 IV + urlsafe base64 인코딩으로 토큰 발급
- 만료 시 refresh_token 자동 재발급
- 27개 ScienceON API 호출 통합

공식 샘플 코드(자료실 PYTHON 예제, 2021-11-22) 기준.
"""

from __future__ import annotations

import base64
import datetime
import json
import logging
import os
import re
import threading
import time as _time
from typing import Any, Dict, Optional
from urllib import parse

import httpx
from Crypto.Cipher import AES

logger = logging.getLogger("mcp-ntis.scienceon")


# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------

TOKEN_URL = "https://apigateway.kisti.re.kr/tokenrequest.do"
API_URL = "https://apigateway.kisti.re.kr/openapicall.do"

# 토큰 발급 AES-256-CBC 고정 IV (ScienceON 공식 샘플 기준)
_AES_IV = b"jvHJ1EFA0IXBrxxz"
_AES_BLOCK = 16


# ---------------------------------------------------------------------------
# 암호화 헬퍼
# ---------------------------------------------------------------------------


def _pkcs7_pad(text: str, block: int = _AES_BLOCK) -> bytes:
    n = block - len(text) % block
    return (text + chr(n) * n).encode("utf-8")


def _encrypt_accounts(key: str, mac_address: str) -> str:
    """ScienceON 토큰 요청용 `accounts` 파라미터를 생성한다."""
    time_str = "".join(
        re.findall(r"\d", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    plain = json.dumps({"datetime": time_str, "mac_address": mac_address}).replace(" ", "")
    cipher = AES.new(key.encode("utf-8"), AES.MODE_CBC, _AES_IV)
    encrypted = cipher.encrypt(_pkcs7_pad(plain))
    return base64.urlsafe_b64encode(encrypted).decode("utf-8")


# ---------------------------------------------------------------------------
# 토큰 관리
# ---------------------------------------------------------------------------


class TokenStore:
    """access_token + refresh_token + 만료 시각 저장."""

    def __init__(self) -> None:
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.access_expire_ts: float = 0.0  # epoch seconds
        self.refresh_expire_ts: float = 0.0
        self._lock = threading.Lock()

    def is_access_valid(self, safety_margin_sec: int = 60) -> bool:
        return bool(self.access_token) and (_time.time() + safety_margin_sec) < self.access_expire_ts

    def is_refresh_valid(self) -> bool:
        return bool(self.refresh_token) and _time.time() < self.refresh_expire_ts

    def update_from_response(self, data: Dict[str, Any]) -> None:
        with self._lock:
            if "access_token" in data:
                self.access_token = data["access_token"]
            if "refresh_token" in data:
                self.refresh_token = data["refresh_token"]
            if "access_token_expire" in data:
                self.access_expire_ts = self._parse_expire(data["access_token_expire"])
            if "refresh_token_expire" in data:
                self.refresh_expire_ts = self._parse_expire(data["refresh_token_expire"])

    @staticmethod
    def _parse_expire(s: str) -> float:
        # "2026-05-22 12:44:24.873"
        try:
            for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
                try:
                    dt = datetime.datetime.strptime(s, fmt)
                    return dt.timestamp()
                except ValueError:
                    continue
        except Exception:
            pass
        return _time.time() + 3600  # fallback 1h


# ---------------------------------------------------------------------------
# ScienceON 클라이언트
# ---------------------------------------------------------------------------


class ScienceONClient:
    """ScienceON API 통합 클라이언트.

    환경변수:
        SCIENCEON_CLIENT_ID — 발급받은 64자 client_id
        SCIENCEON_API_KEY   — 발급받은 32자 인증키 (AES 암호화 키로 사용)
        SCIENCEON_MAC       — 신청 시 등록한 MAC 주소 (대문자+하이픈)
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        api_key: Optional[str] = None,
        mac_address: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        self.client_id = client_id or os.getenv("SCIENCEON_CLIENT_ID", "")
        self.api_key = api_key or os.getenv("SCIENCEON_API_KEY", "")
        self.mac_address = mac_address or os.getenv("SCIENCEON_MAC", "")
        if not (self.client_id and self.api_key and self.mac_address):
            raise ValueError(
                "ScienceON 자격증명 누락: SCIENCEON_CLIENT_ID / SCIENCEON_API_KEY / SCIENCEON_MAC 환경변수를 설정하세요."
            )
        self.tokens = TokenStore()
        self._http: Optional[httpx.AsyncClient] = None
        self._timeout = timeout

    @property
    def http(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(timeout=self._timeout)
        return self._http

    async def close(self) -> None:
        if self._http and not self._http.is_closed:
            await self._http.aclose()

    # ------------------------------------------------------------------ 토큰

    async def _request_new_token(self) -> Dict[str, Any]:
        accounts = _encrypt_accounts(self.api_key, self.mac_address)
        url = f"{TOKEN_URL}?client_id={self.client_id}&accounts={accounts}"
        resp = await self.http.get(url)
        data = resp.json()
        if "errorCode" in data:
            raise RuntimeError(
                f"ScienceON 토큰 발급 실패 ({data.get('errorCode')}): "
                f"{data.get('errorMessage', data.get('message', ''))}. "
                "암호화 방식·키·MAC 주소 등록 상태 확인 필요."
            )
        self.tokens.update_from_response(data)
        return data

    async def _refresh_access_token(self) -> Dict[str, Any]:
        url = (
            f"{TOKEN_URL}?refreshToken={self.tokens.refresh_token}"
            f"&client_id={self.client_id}"
        )
        resp = await self.http.get(url)
        text = resp.text
        # 응답이 JSON일 수도, XML 에러일 수도 있음
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = {"errorMessage": text, "errorCode": "RefreshFailed"}
        if "errorCode" in data:
            logger.warning(f"refresh_token 만료/오류 → 토큰 재발급 시도: {data}")
            return await self._request_new_token()
        self.tokens.update_from_response(data)
        return data

    async def ensure_token(self) -> str:
        if self.tokens.is_access_valid():
            return self.tokens.access_token  # type: ignore[return-value]
        if self.tokens.is_refresh_valid():
            await self._refresh_access_token()
        else:
            await self._request_new_token()
        return self.tokens.access_token  # type: ignore[return-value]

    # ----------------------------------------------------------- 공통 호출

    async def _call(self, params: Dict[str, Any], _attempt: int = 0) -> str:
        """openapicall.do GET 호출. 토큰 만료/rate limit 시 자동 재시도."""
        token = await self.ensure_token()
        params = {
            "client_id": self.client_id,
            "token": token,
            "version": "1.0",
            **params,
        }
        resp = await self.http.get(API_URL, params=params)
        text = resp.text
        # 토큰 만료(E4103) 자동 처리
        if "E4103" in text:
            logger.info("Access Token 만료 감지 → 재발급 후 재시도")
            await self._refresh_access_token()
            params["token"] = self.tokens.access_token
            resp = await self.http.get(API_URL, params=params)
            text = resp.text
        # Rate limit (E4290) — 지수 백오프 재시도
        if "E4290" in text and _attempt < 4:
            import asyncio as _asyncio
            wait = 2 ** _attempt  # 1, 2, 4, 8초
            logger.warning(f"ScienceON rate limit (E4290), {wait}s 대기 후 재시도 [{_attempt+1}/4]")
            await _asyncio.sleep(wait)
            return await self._call(params, _attempt=_attempt + 1)
        return text

    async def search(
        self,
        target: str,
        search_query: Optional[Dict[str, Any]] = None,
        cur_page: int = 1,
        row_count: int = 10,
        extra: Optional[Dict[str, Any]] = None,
    ) -> str:
        """action=search 통합 호출."""
        params: Dict[str, Any] = {
            "action": "search",
            "target": target,
            "curPage": cur_page,
            "rowCount": row_count,
        }
        if search_query is not None:
            params["searchQuery"] = json.dumps(search_query, ensure_ascii=False)
        if extra:
            params.update(extra)
        return await self._call(params)

    async def browse(
        self,
        target: str,
        cn: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> str:
        """action=browse 통합 호출 (상세보기)."""
        params: Dict[str, Any] = {
            "action": "browse",
            "target": target,
            "cn": cn,
        }
        if extra:
            params.update(extra)
        return await self._call(params)
