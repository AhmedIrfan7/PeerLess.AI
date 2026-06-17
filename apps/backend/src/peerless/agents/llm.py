"""Grok (xAI) LLM wrapper — caching, retries, cost cap, structured output.

xAI exposes an OpenAI-compatible endpoint at https://api.x.ai/v1, so we use
the openai SDK with a custom base_url.
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

_GROQ_BASE_URL = "https://api.groq.com/openai/v1"


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
        raise LlmCostCapExceeded(
            f"Daily LLM cost cap ${settings.max_daily_llm_cost_usd} exceeded "
            f"(spent ${total:.4f})"
        )
    return total


async def _record_usage(
    request_id: str, agent: str, model: str,
    prompt_tokens: int, completion_tokens: int, cost: float,
) -> None:
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


def _make_client(api_key: str):
    from openai import AsyncOpenAI
    return AsyncOpenAI(api_key=api_key, base_url=_GROQ_BASE_URL)


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
) -> Any:
    from peerless.config import get_settings
    settings = get_settings()

    if not settings.llm_available:
        raise LLMUnavailable("GROQ_API_KEY is not configured.")

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

    client = _make_client(settings.groq_api_key)

    sys_msg = system
    if schema:
        sys_msg += "\n\nRespond ONLY with valid JSON. No markdown, no explanation."

    messages = [
        {"role": "system", "content": sys_msg},
        {"role": "user", "content": prompt},
    ]
    if schema:
        messages[1]["content"] += f"\n\nJSON schema to follow:\n{json.dumps(schema)}"

    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
    }
    if schema:
        kwargs["response_format"] = {"type": "json_object"}

    last_exc: Exception | None = None
    t0 = time.time()
    for attempt in range(3):
        try:
            response = await client.chat.completions.create(**kwargs)
            break
        except Exception as exc:
            last_exc = exc
            err_str = str(exc)
            if "429" in err_str or "rate" in err_str.lower():
                import asyncio
                await asyncio.sleep(2 ** attempt)
                continue
            raise UpstreamUnavailable(err_str) from exc
    else:
        raise UpstreamUnavailable(str(last_exc))

    latency_ms = round((time.time() - t0) * 1000)
    raw_text = (response.choices[0].message.content or "").strip()

    # Strip markdown code fences if the model wraps its JSON
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        raw_text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError:
        # One retry with stricter instruction
        try:
            retry_messages = messages + [
                {"role": "assistant", "content": raw_text},
                {"role": "user", "content": "That was not valid JSON. Reply ONLY with the JSON object, no other text."},
            ]
            retry_kwargs = {**kwargs, "messages": retry_messages}
            response2 = await client.chat.completions.create(**retry_kwargs)
            raw2 = (response2.choices[0].message.content or "").strip()
            result = json.loads(raw2)
        except Exception as exc2:
            raise UpstreamMalformed(
                f"LLM returned non-JSON after retry: {str(exc2)[:200]}"
            ) from exc2

    usage = response.usage
    p_tokens = usage.prompt_tokens if usage else len(str(messages)) // 4
    c_tokens = usage.completion_tokens if usage else len(raw_text) // 4

    is_fast = "fast" in model or "mini" in model
    per_1k = (
        settings.llm_pricing_fast_per_1k_tokens if is_fast
        else settings.llm_pricing_smart_per_1k_tokens
    )
    cost = (p_tokens + c_tokens) / 1000 * per_1k
    req_id = str(uuid.uuid4())[:8]

    await _record_usage(req_id, agent_name, model, p_tokens, c_tokens, cost)
    logger.info(
        "llm.call", agent=agent_name, model=model,
        prompt_tokens=p_tokens, completion_tokens=c_tokens,
        cost_usd=round(cost, 6), cached=False, latency_ms=latency_ms,
    )

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
    from peerless.config import get_settings
    settings = get_settings()

    if not settings.llm_available:
        raise LLMUnavailable("GROQ_API_KEY is not configured.")

    await _check_cost_cap()

    key = _cache_key(model, system, prompt, None)
    if use_cache:
        try:
            r = await _get_redis()
            cached = await r.get(key)
            await r.aclose()
            if cached:
                return cached
        except Exception:
            pass

    client = _make_client(settings.groq_api_key)
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]

    last_exc: Exception | None = None
    t0 = time.time()
    for attempt in range(3):
        try:
            response = await client.chat.completions.create(
                model=model, messages=messages, max_tokens=max_tokens,
            )
            break
        except Exception as exc:
            last_exc = exc
            if "429" in str(exc) or "rate" in str(exc).lower():
                import asyncio
                await asyncio.sleep(2 ** attempt)
                continue
            raise UpstreamUnavailable(str(exc)) from exc
    else:
        raise UpstreamUnavailable(str(last_exc))

    latency_ms = round((time.time() - t0) * 1000)
    text = (response.choices[0].message.content or "").strip()

    usage = response.usage
    p_tokens = usage.prompt_tokens if usage else len(str(messages)) // 4
    c_tokens = usage.completion_tokens if usage else len(text) // 4

    is_fast = "fast" in model or "mini" in model
    per_1k = (
        settings.llm_pricing_fast_per_1k_tokens if is_fast
        else settings.llm_pricing_smart_per_1k_tokens
    )
    cost = (p_tokens + c_tokens) / 1000 * per_1k
    req_id = str(uuid.uuid4())[:8]

    await _record_usage(req_id, agent_name, model, p_tokens, c_tokens, cost)
    logger.info(
        "llm.call", agent=agent_name, model=model,
        prompt_tokens=p_tokens, completion_tokens=c_tokens,
        cost_usd=round(cost, 6), cached=False, latency_ms=latency_ms,
    )

    if use_cache:
        try:
            r = await _get_redis()
            await r.setex(key, 7 * 86400, text)
            await r.aclose()
        except Exception:
            pass

    return text
