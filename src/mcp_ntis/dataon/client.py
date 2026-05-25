"""DataON (국가연구데이터플랫폼) REST API 클라이언트.

엔드포인트: https://dataon.kisti.re.kr/rest/api/search/dataset
인증: key 파라미터 (발급받은 API key)
파라미터: query, from, size, sortCon, sortArr

응답은 JSON, 다국어 필드 (kor/etc_main/etc_sub) 포함.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("mcp-ntis.dataon")


# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------


API_URL = "https://dataon.kisti.re.kr/rest/api/search/dataset"
# 연구데이터 상세 조회는 동일 엔드포인트에 trailing slash + 다른 발급키 사용
DETAIL_URL = "https://dataon.kisti.re.kr/rest/api/search/dataset/"

# 응답 raw 필드 → 정제된 키 매핑 (mcp-opendart 패턴)
_KEY_MAP: dict[str, str] = {
    # 제목·설명·키워드 (한글 우선, 다국어는 alt에)
    "dataset_title_kor": "title",
    "dataset_title_etc_main": "title_en",
    "dataset_title_etc_sub": "title_alt",
    "dataset_expl_kor": "description",
    "dataset_expl_etc_main": "description_en",
    "dataset_expl_etc_sub": "description_alt",
    "dataset_kywd_kor": "keywords",
    "dataset_kywd_etc_main": "keywords_en",
    "dataset_kywd_etc_sub": "keywords_alt",
    # 식별·접근
    "dataset_doi": "doi",
    "dataset_lndgpg": "landing_url",
    "dataset_access_type_pc": "access_type",
    "ctlg_type_pc": "catalog_type",
    "dataset_mnsb_pc": "subject_class",
    "repo_pc": "repository",
    "dataset_id": "id",
    "dataset_pblc_dt": "publish_date",
    "dataset_lstm_dt": "modify_date",
    "dataset_creator": "creator",
    "dataset_publisher": "publisher",
    "dataset_license": "license",
    "dataset_size": "size_bytes",
    "dataset_format": "format",
    "dataset_lang": "language",
}


def _map_keys(record: dict[str, Any]) -> dict[str, Any]:
    """raw record dict → snake_case 정제 dict.

    매핑되지 않은 키는 원본 그대로 보존(미래 확장 대비).
    빈 값은 제거.
    """
    out: dict[str, Any] = {}
    for k, v in record.items():
        if v in (None, "", []):
            continue
        new_key = _KEY_MAP.get(k, k)
        out[new_key] = v
    return out


# ---------------------------------------------------------------------------
# DataON 클라이언트
# ---------------------------------------------------------------------------


class DataONClient:
    """DataON OpenAPI 통합 클라이언트.

    환경변수:
        DATAON_API_KEY — 발급받은 인증키 (필수)
    """

    def __init__(
        self,
        api_key: str | None = None,
        detail_api_key: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.api_key = (api_key or os.getenv("DATAON_API_KEY", "")).strip()
        if not self.api_key:
            raise ValueError(
                "DATAON_API_KEY 환경변수가 설정되지 않았습니다. "
                "DataON OpenAPI 키를 .env 또는 환경변수에 설정하세요."
            )
        # 메타 상세 조회용 별도 키 (KISTI가 검색·상세를 별도 발급)
        self.detail_api_key = (
            detail_api_key or os.getenv("DATAON_DETAIL_API_KEY", "")
        ).strip()
        self._timeout = timeout
        self._http: httpx.AsyncClient | None = None

    @property
    def http(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(timeout=self._timeout)
        return self._http

    async def close(self) -> None:
        if self._http and not self._http.is_closed:
            await self._http.aclose()

    # ------------------------------------------------------------------ 검색

    async def search_datasets(
        self,
        query: str,
        from_: int = 0,
        size: int = 10,
        sort_con: str | None = None,
        sort_arr: str | None = None,
    ) -> dict[str, Any]:
        """연구데이터 검색.

        Args:
            query: 검색 키워드 (필수)
            from_: 페이지 시작 위치 (기본 0)
            size: 페이지당 결과 수 (기본 10)
            sort_con: 정렬 기준 — 'title' | 'date' | 'score' (생략 시 score 기본)
            sort_arr: 정렬 순서 — 'asc' | 'desc'

        Returns:
            정제된 dict:
                {
                  "status": "ok" | "error",
                  "total_count": int,
                  "from": int, "size": int, "returned": int,
                  "elapsed_time_ms": int | None,
                  "items": [{... 정제된 record ...}],
                  "pagination_hint": str | None,  # total > returned 시
                  "error": {"code": ..., "message": ...} | None
                }
        """
        params: dict[str, Any] = {
            "key": self.api_key,
            "query": query,
            "from": from_,
            "size": size,
        }
        if sort_con:
            params["sortCon"] = sort_con
        if sort_arr:
            params["sortArr"] = sort_arr

        try:
            resp = await self.http.get(API_URL, params=params)
        except httpx.TimeoutException as exc:
            return {
                "status": "error",
                "total_count": 0,
                "items": [],
                "error": {
                    "code": "E_TIMEOUT",
                    "message": f"DataON 응답 지연 ({self._timeout}s) — 잠시 후 재시도",
                },
            }
        except httpx.RequestError as exc:
            return {
                "status": "error",
                "total_count": 0,
                "items": [],
                "error": {"code": "E_NETWORK", "message": str(exc)[:200]},
            }

        # HTTP 비-200 응답
        if resp.status_code != 200:
            text = resp.text[:300] if resp.text else ""
            return {
                "status": "error",
                "total_count": 0,
                "items": [],
                "error": {
                    "code": f"E_HTTP_{resp.status_code}",
                    "message": text or f"HTTP {resp.status_code}",
                },
            }

        # JSON 파싱
        try:
            data = resp.json()
        except Exception as exc:
            return {
                "status": "error",
                "total_count": 0,
                "items": [],
                "error": {"code": "E_PARSE", "message": f"JSON 파싱 실패: {exc}"[:200]},
            }

        # DataON 응답 구조:
        # { "response": { "elapsed time": "...", "status": "200", "total count": N, ... },
        #   "records": [ {...}, ... ] }
        # 일부 환경에선 wrapping 없이 top-level에 키가 올 수도 있어 양쪽 모두 처리.
        meta = data.get("response") if isinstance(data.get("response"), dict) else data

        total_count = (
            meta.get("total_count")
            or meta.get("totalCount")
            or meta.get("total count")
            or meta.get("total")
            or 0
        )
        elapsed = (
            meta.get("elapsed_time")
            or meta.get("elapsedTime")
            or meta.get("elapsed time")
        )

        # items 배열 후보 — DataON은 "records"가 표준
        raw_items: list[Any] = []
        for k in ("records", "items", "result", "results", "data", "hits", "documents", "list"):
            v = data.get(k)
            if isinstance(v, list):
                raw_items = v
                break
        # 응답 자체가 list라면
        if not raw_items and isinstance(data, list):
            raw_items = data

        items = [_map_keys(r) if isinstance(r, dict) else {"raw": str(r)} for r in raw_items]

        out: dict[str, Any] = {
            "status": "ok",
            "total_count": int(total_count) if total_count else 0,
            "from": from_,
            "size": size,
            "returned": len(items),
            "items": items,
        }
        if elapsed is not None:
            out["elapsed_time_ms"] = elapsed

        if out["total_count"] > len(items) and out["total_count"] > from_ + size:
            remaining = out["total_count"] - (from_ + size)
            out["pagination_hint"] = (
                f"총 {out['total_count']:,}건 중 {len(items)}건 반환 — "
                f"남은 {remaining:,}건은 from={from_ + size} 부터 순회."
            )

        return out

    # ----------------------------------------------------------- 메타 상세

    async def get_dataset_detail(
        self,
        dataset_id: str,
        query: str | None = None,
    ) -> dict[str, Any]:
        """연구데이터 메타 상세 조회.

        Args:
            dataset_id: 검색 결과의 dataset id (DOI 또는 내부 id)
            query: 일부 환경에서 query 파라미터를 필수로 요구하므로 보조 입력

        Returns:
            search_datasets 와 동일 스키마. items에는 단일 레코드.
        """
        if not self.detail_api_key:
            return {
                "status": "error",
                "error": {
                    "code": "E_NO_DETAIL_KEY",
                    "message": "DATAON_DETAIL_API_KEY가 설정되지 않았습니다.",
                },
                "items": [],
                "total_count": 0,
            }

        params: dict[str, Any] = {
            "key": self.detail_api_key,
            "from": 0,
            "size": 1,
        }
        if query:
            params["query"] = query
        # dataset_id는 doi 또는 식별자 — KISTI 명세상 query에 doi/id를 그대로 줘도 매칭
        # 명시적 필드명이 있다면 보강
        params.setdefault("query", dataset_id)
        params["dataset_id"] = dataset_id

        try:
            resp = await self.http.get(DETAIL_URL, params=params)
        except httpx.TimeoutException:
            return {
                "status": "error",
                "items": [],
                "total_count": 0,
                "error": {"code": "E_TIMEOUT", "message": "DataON 상세 응답 지연"},
            }
        except httpx.RequestError as exc:
            return {
                "status": "error",
                "items": [],
                "total_count": 0,
                "error": {"code": "E_NETWORK", "message": str(exc)[:200]},
            }

        if resp.status_code != 200:
            return {
                "status": "error",
                "items": [],
                "total_count": 0,
                "error": {
                    "code": f"E_HTTP_{resp.status_code}",
                    "message": (resp.text or "")[:300],
                },
            }
        try:
            data = resp.json()
        except Exception as exc:
            return {
                "status": "error",
                "items": [],
                "total_count": 0,
                "error": {"code": "E_PARSE", "message": str(exc)[:200]},
            }

        raw_items: list[Any] = []
        for k in ("records", "items", "result", "results", "data", "hits", "documents", "list"):
            v = data.get(k)
            if isinstance(v, list):
                raw_items = v
                break
        if not raw_items and isinstance(data, list):
            raw_items = data
        if not raw_items and isinstance(data, dict) and "dataset_doi" in data:
            # 응답 자체가 단일 record인 경우
            raw_items = [data]

        items = [_map_keys(r) if isinstance(r, dict) else {"raw": str(r)} for r in raw_items]
        return {
            "status": "ok",
            "total_count": len(items),
            "returned": len(items),
            "items": items,
            "dataset_id": dataset_id,
        }
