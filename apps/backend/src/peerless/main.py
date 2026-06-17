"""PEERLESS.AI FastAPI application entry point."""
from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from peerless.api.findings import router as findings_router
from peerless.api.papers import router as papers_router
from peerless.api.reports import router as reports_router
from peerless.config import get_settings
from peerless.logging_config import configure_logging

configure_logging()
logger = structlog.get_logger(__name__)

_START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    settings = get_settings()
    logger.info(
        "peerless.startup",
        version=settings.version,
        environment=settings.environment,
        llm_available=settings.llm_available,
    )
    yield
    logger.info("peerless.shutdown")


app = FastAPI(
    title="PEERLESS.AI",
    version="0.1.0",
    description=(
        "Multi-agent scientific peer-review and research-integrity tool. "
        "Surfaces flagged concerns for human review — never definitive accusations."
    ),
    lifespan=lifespan,
)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz", tags=["meta"])
async def healthz() -> dict[str, Any]:
    """Health check. Reports availability of each external dependency."""
    settings = get_settings()

    db_status = "unknown"
    redis_status = "unknown"

    # Non-blocking connectivity checks
    try:
        import asyncpg  # type: ignore[import-untyped]
        conn = await asyncpg.connect(
            settings.database_url.replace("postgresql+asyncpg://", "postgresql://"),
            timeout=2,
        )
        await conn.close()
        db_status = "ok"
    except Exception as exc:
        db_status = "unreachable"
        logger.warning("healthz.db_unreachable", error=str(exc))

    try:
        import redis.asyncio as aioredis  # type: ignore[import-untyped]
        r = aioredis.from_url(settings.redis_url, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
        redis_status = "ok"
    except Exception as exc:
        redis_status = "unreachable"
        logger.warning("healthz.redis_unreachable", error=str(exc))

    return {
        "status": "ok",
        "version": settings.version,
        "uptime_seconds": round(time.time() - _START_TIME, 1),
        "llm_available": settings.llm_available,
        "db": db_status,
        "redis": redis_status,
    }


# ── v1 API router ──────────────────────────────────────────────────────────────
from fastapi import APIRouter  # noqa: E402

v1 = APIRouter(prefix="/api/v1")
v1.include_router(papers_router)
v1.include_router(reports_router)
v1.include_router(findings_router)
app.include_router(v1)


# ── Global error handler ───────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled_exception", path=str(request.url), error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "internal_error", "message": "An unexpected error occurred.", "details": None}},
    )
