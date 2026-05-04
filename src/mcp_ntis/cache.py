import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("mcp-ntis")

CACHE_DIR = Path.home() / ".cache" / "mcp-ntis"


def _cache_key(url: str, params: dict) -> str:
    raw = url + json.dumps(params, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()


def get_cached(url: str, params: dict, ttl_hours: int) -> Optional[Any]:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = _cache_key(url, params)
    cache_file = CACHE_DIR / f"{key}.json"
    if not cache_file.exists():
        return None
    age_seconds = time.time() - cache_file.stat().st_mtime
    if age_seconds > ttl_hours * 3600:
        cache_file.unlink(missing_ok=True)
        return None
    try:
        return json.loads(cache_file.read_text(encoding="utf-8"))
    except Exception:
        return None


def set_cached(url: str, params: dict, data: Any) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = _cache_key(url, params)
    cache_file = CACHE_DIR / f"{key}.json"
    try:
        cache_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        logger.warning(f"캐시 저장 실패: {e}")
