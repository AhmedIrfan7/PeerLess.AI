# PEERLESS.AI

> Multi-agent scientific peer-review and research-integrity tool.

## Quick Start

```bash
cp .env.example .env
# Fill in required secrets in .env
docker compose up
```

The app will be available at http://localhost:3000.

## Documentation

- [Master Specification](docs/MASTER_SPEC.md) — The project constitution. Start here.
- [Architecture](docs/ARCHITECTURE.md) — System design and data flow.
- [Safety Policy](docs/SAFETY.md) — Legal and safety requirements. Non-negotiable.

## Repo Layout

```
peerless/
├── apps/backend/     — Python 3.11 + FastAPI backend, LangGraph agents
├── apps/frontend/    — Next.js 14 + TypeScript + Tailwind CSS frontend
├── fixtures/         — Sample PDFs and expected agent outputs for testing
├── n8n/              — n8n workflow JSON exports
└── docs/             — Architecture, safety, and master spec documents
```

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS |
| Backend | Python 3.11, FastAPI, LangGraph |
| LLM | Google Gemini API (gemini-2.5-flash / gemini-2.5-pro) |
| Database | PostgreSQL 16 |
| Vector DB | ChromaDB (embedded) |
| Cache | Redis 7 |
| Automation | n8n (self-hosted) |
| Orchestration | Docker Compose |

## ⚠️ Safety Notice

PEERLESS.AI surfaces possible concerns for expert review. It does not adjudicate misconduct. Findings are not conclusions.
See [SAFETY.md](docs/SAFETY.md) for full policy.
