"""Crossref API client with caching and polite pool headers."""
from __future__ import annotations

import json
from typing import Any

import httpx
import structlog

logger = structlog.get_logger(__name__)

BASE = "https://api.crossref.org"
_TIMEOUT = httpx.Timeout(10.0)
_CACHE_TTL = 30 * 86400  # 30 days


def _headers(mailto: str) -> dict[str, str]:
    return {"User-Agent": f"PEERLESS.AI/0.1 (mailto:{mailto})"}


async def _cache_get(key: str) -> dict | None:
    try:
        import redis.asyncio as aioredis
        from peerless.config import get_settings
        r = aioredis.from_url(get_settings().redis_url, decode_responses=True, socket_connect_timeout=2)
        val = await r.get(f"crossref:{key}")
        await r.aclose()
        if val:
            return json.loads(val)
    except Exception:
        pass
    return None


async def _cache_set(key: str, value: dict) -> None:
    try:
        import redis.asyncio as aioredis
        from peerless.config import get_settings
        r = aioredis.from_url(get_settings().redis_url, decode_responses=True, socket_connect_timeout=2)
        await r.setex(f"crossref:{key}", _CACHE_TTL, json.dumps(value))
        await r.aclose()
    except Exception:
        pass


async def lookup_doi(doi: str, mailto: str) -> dict[str, Any] | None:
    cached = await _cache_get(f"doi:{doi}")
    if cached is not None:
        return cached

    url = f"{BASE}/works/{doi}"
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.get(url, headers=_headers(mailto))
            if resp.status_code == 200:
                data = resp.json().get("message", {})
                await _cache_set(f"doi:{doi}", data)
                return data
            if resp.status_code == 404:
                return None
            if resp.status_code == 429:
                import asyncio; await asyncio.sleep(2 ** attempt)
                continue
            return None
        except Exception as exc:
            logger.warning("crossref.lookup_error", doi=doi, error=str(exc))
            return None
    return None


def is_retracted(work: dict[str, Any]) -> bool:
    """Check if a Crossref work record indicates a retraction."""
    title = " ".join(work.get("title", []))
    if "RETRACTED" in title.upper() or "RETRACTION:" in title.upper():
        return True
    update_to = work.get("update-to", [])
    for item in update_to:
        if isinstance(item, dict) and item.get("type", "").lower() in ("retraction", "correction"):
            return True
    relation = work.get("relation", {})
    if relation.get("is-retraction-of"):
        return True
    return False


def get_retraction_notice_url(work: dict[str, Any]) -> str | None:
    update_to = work.get("update-to", [])
    for item in update_to:
        if isinstance(item, dict):
            url = item.get("URL") or item.get("DOI")
            if url:
                return str(url)
    return work.get("URL")
