"""Shared Gemini LLM wrapper — caching, retries, cost cap, structured output."""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from typing import Any, Type

import structlog

logger = structlog.get_logger(__name__)


class LLMUnavailable(Exception):
    pass


class LlmCostCapExceeded(Exception):
    pass


class UpstreamMalformed(Exception):
    pass


class UpstreamUnavailable(Exception):
    pass


def _cache_key(model: str, system: str, prompt: str, schema: Any) -> str:
    raw = f"{model}|{system}|{prompt}|{str(schema)}"
    return "llm:" + hashlib.sha256(raw.encode()).hexdigest()


async def _get_redis():
    import redis.asyncio as aioredis
    from peerless.config import get_settings
    settings = get_settings()
    return aioredis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=2)


async def _check_cost_cap() -> float:
    """Return today's total LLM cost. Raise LlmCostCapExceeded if over limit."""
    from peerless.config import get_settings
    from peerless.storage.database import AsyncSessionLocal
    from peerless.storage.models import LlmUsage
    from sqlalchemy import func, select
    from datetime import date

    settings = get_settings()
    async with AsyncSessionLocal() as session:
        today = date.today()
        result = await session.execute(
            select(func.coalesce(func.sum(LlmUsage.cost_usd), 0.0)).where(
                func.date(LlmUsage.created_at) == today
            )
        )
        total: float = float(result.scalar_one())

    if total >= settings.max_daily_llm_cost_usd:
        raise LlmCostCapExceeded(f"Daily LLM cost cap ${settings.max_daily_llm_cost_usd} exceeded (spent ${total:.4f})")
    return total


async def _record_usage(request_id: str, agent: str, model: str, prompt_tokens: int, completion_tokens: int, cost: float) -> None:
    from peerless.storage.database import AsyncSessionLocal
    from peerless.storage.models import LlmUsage
    async with AsyncSessionLocal() as session:
        session.add(LlmUsage(
            request_id=request_id,
            agent=agent,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost,
        ))
        await session.commit()


async def generate_json(
    *,
    model: str,
    system: str,
    prompt: str,
    schema: dict[str, Any] | None = None,
    max_tokens: int = 4096,
    agent_name: str = "unknown",
    paper_id: str | None = None,
    use_cache: bool = True,
) -> dict[str, Any]:
    from peerless.config import get_settings
    settings = get_settings()

    if not settings.llm_available:
        raise LLMUnavailable("GEMINI_API_KEY is not configured.")

    await _check_cost_cap()

    key = _cache_key(model, system, prompt, schema)
    if use_cache:
        try:
            r = await _get_redis()
            cached = await r.get(key)
            await r.aclose()
            if cached:
                logger.debug("llm.cache_hit", agent=agent_name, model=model)
                return json.loads(cached)
        except Exception:
            pass

    import google.generativeai as genai
    genai.configure(api_key=settings.gemini_api_key)

    full_prompt = f"{system}\n\n{prompt}"
    if schema:
        full_prompt += f"\n\nRespond ONLY with valid JSON matching this schema: {json.dumps(schema)}"

    gen_config = {"max_output_tokens": max_tokens}
    if schema:
        gen_config["response_mime_type"] = "application/json"

    gemini_model = genai.GenerativeModel(model, generation_config=gen_config)

    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            t0 = time.time()
            response = gemini_model.generate_content(full_prompt)
            latency_ms = round((time.time() - t0) * 1000)
            break
        except Exception as exc:
            last_exc = exc
            if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
                import asyncio
                await asyncio.sleep(2 ** attempt)
                continue
            raise UpstreamUnavailable(str(exc)) from exc
    else:
        raise UpstreamUnavailable(str(last_exc))

    raw_text = response.text.strip()

    # Parse JSON
    try:
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
        result = json.loads(raw_text)
    except json.JSONDecodeError:
        # One retry with stricter instruction
        try:
            retry_prompt = full_prompt + "\n\nYou MUST respond with ONLY valid JSON, no markdown, no explanation."
            response2 = gemini_model.generate_content(retry_prompt)
            raw2 = response2.text.strip()
            if raw2.startswith("```"):
                raw2 = raw2.split("```")[1]
                if raw2.startswith("json"):
                    raw2 = raw2[4:]
            result = json.loads(raw2)
        except Exception as exc2:
            raise UpstreamMalformed(f"LLM returned non-JSON after retry: {str(exc2)[:200]}") from exc2

    # Estimate cost
    try:
        usage = response.usage_metadata
        p_tokens = usage.prompt_token_count or 0
        c_tokens = usage.candidates_token_count or 0
    except Exception:
        p_tokens, c_tokens = len(full_prompt) // 4, len(raw_text) // 4

    per_1k = settings.llm_pricing_fast_per_1k_tokens if "flash" in model else settings.llm_pricing_smart_per_1k_tokens
    cost = (p_tokens + c_tokens) / 1000 * per_1k
    req_id = str(uuid.uuid4())[:8]

    await _record_usage(req_id, agent_name, model, p_tokens, c_tokens, cost)

    logger.info("llm.call", agent=agent_name, model=model, prompt_tokens=p_tokens,
                completion_tokens=c_tokens, cost_usd=round(cost, 6), cached=False, latency_ms=latency_ms)

    if use_cache:
        try:
            r = await _get_redis()
            await r.setex(key, 7 * 86400, json.dumps(result))
            await r.aclose()
        except Exception:
            pass

    return result


async def generate_text(
    *,
    model: str,
    system: str,
    prompt: str,
    max_tokens: int = 2048,
    agent_name: str = "unknown",
    use_cache: bool = True,
) -> str:
    result = await generate_json(
        model=model, system=system, prompt=prompt,
        schema=None, max_tokens=max_tokens,
        agent_name=agent_name, use_cache=use_cache,
    )
    if isinstance(result, str):
        return result
    return json.dumps(result)
