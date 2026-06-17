# Backend — FastAPI Application

This directory contains the Python 3.11 + FastAPI backend for PEERLESS.AI.

## Structure

- `src/peerless/api/` — FastAPI routers (REST endpoints under /api/v1)
- `src/peerless/agents/` — One subfolder per analysis agent
- `src/peerless/orchestrator/` — LangGraph multi-agent orchestration graph
- `src/peerless/parsing/` — PDF → structured text via PyMuPDF
- `src/peerless/verification/` — GRIM/statcheck computations; Crossref, PubMed, arXiv clients
- `src/peerless/reports/` — Report schema, assembly logic, DB persistence
- `src/peerless/storage/` — Filesystem, database, and Redis cache abstractions
- `src/peerless/config.py` — Environment-driven settings (Pydantic BaseSettings)
- `src/peerless/main.py` — FastAPI application entry point
- `tests/` — pytest test suite

## Build system

Uses **hatchling** (via `pyproject.toml`). Install all dependencies:

```bash
pip install fastapi "uvicorn[standard]" pydantic pydantic-settings structlog \
  httpx python-multipart slowapi sqlalchemy "sqlalchemy[asyncio]" asyncpg \
  alembic redis pymupdf scipy numpy langdetect reportlab rapidfuzz \
  google-generativeai langgraph
```

## Running locally

```bash
# Requires postgres, redis running (see docker-compose.yml at repo root)
PYTHONPATH=src uvicorn peerless.main:app --reload --host 0.0.0.0 --port 8000
```

Health check: `curl http://localhost:8000/healthz`

## Database migrations

```bash
PYTHONPATH=src alembic upgrade head
```

## Tests

```bash
PYTHONPATH=src pytest tests/ -q
```
