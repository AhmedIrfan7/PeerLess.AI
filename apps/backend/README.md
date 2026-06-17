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

## Running Locally

```bash
# Via Docker Compose (recommended)
docker compose up backend

# Or directly (requires postgres, redis running)
uv run uvicorn peerless.main:app --reload --port 8000
```
