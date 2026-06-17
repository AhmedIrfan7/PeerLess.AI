# PEERLESS.AI — Architecture

> System design, data flow, and component interaction for PEERLESS.AI.
> See [MASTER_SPEC.md](MASTER_SPEC.md) for technology decisions and rationale.

---

## High-Level Data Flow

```
User (Browser)
    │  Upload PDF
    ▼
Next.js Frontend (port 3000)
    │  POST /api/v1/papers
    ▼
FastAPI Backend (port 8000)
    │  Store PDF → ./storage/papers/
    │  Extract text → PyMuPDF
    │  Enqueue analysis job
    ▼
LangGraph Orchestrator
    ├── [parallel] statistical_integrity agent
    ├── [parallel] citation_verifier agent
    └── [parallel] plain_language_summary agent
         │  Each agent queries external APIs or runs computations
         │  Results assembled into IntegrityReport
    ▼
PostgreSQL 16 (port 5432)
    │  Persist report + findings
    ▼
Frontend polls / SSE stream
    │  Render IntegrityReport
    ▼
Human Reviewer
    │  Approve / Reject each finding
    ▼
(Optional) n8n workflow
    │  Draft notification → HOLD for human approval
    ▼
Human approves → send
```

## Component Map

| Component | Port | Technology | Responsibility |
|-----------|------|-----------|----------------|
| `frontend` | 3000 | Next.js 14 | UI, report rendering, human review |
| `backend` | 8000 | FastAPI | REST API, agent orchestration, verification |
| `postgres` | 5432 | PostgreSQL 16 | Persistent storage for papers, reports, findings |
| `redis` | 6379 | Redis 7 | API response cache |
| `chromadb` | 8001 | ChromaDB | Local corpus vector search |
| `n8n` | 5678 | n8n | Notification drafting (human-gated) |

## Agent Architecture

Each agent in `apps/backend/src/peerless/agents/` follows this contract:

1. Receives a `PaperContext` (structured text, metadata)
2. Runs its specific analysis (code computation OR API call OR LLM inference)
3. Returns a list of `Finding` objects conforming to the shared schema
4. Never modifies shared state directly — returns immutable output

The LangGraph orchestrator in `apps/backend/src/peerless/orchestrator/` runs MVP agents in parallel, collects findings, calls the synthesis LLM pass (`gemini-2.5-pro`), and assembles the final `IntegrityReport`.

---

*Last amended: 2026-06-17 — Step 0 bootstrap.*
