# PEERLESS.AI — Master Specification (Constitution)

> **This document is the authoritative reference for every build step, sprint, and design decision in PEERLESS.AI.
> Do not deviate from the decisions recorded here without amending this file and committing the change.**

---

## 1. Project Overview

**PEERLESS.AI** is a multi-agent scientific peer-review and research-integrity tool. A user uploads a research paper (PDF). Specialized agents analyze it and the output is a single structured **Integrity Report** that surfaces *flagged concerns for human review* — never definitive accusations.

### Agent Roadmap

| Phase | Agent | Description |
|-------|-------|-------------|
| MVP | `statistical_integrity` | GRIM-style and statcheck-style checks on reported statistics |
| MVP | `citation_verifier` | Verifies citations against Crossref, PubMed, and arXiv; checks for retractions |
| MVP | `plain_language_summary` | Plain-language abstract of the paper for general audience |
| Phase 2 | `methodology_auditor` | Audits research methodology for common flaws |
| Phase 2 | `replication_predictor` | Estimates replication risk |
| Phase 2 | `contradiction_detector` | Detects internal contradictions in claims and data |
| Phase 2 | `conflict_of_interest` | Flags potential conflicts of interest *(feature-flagged)* |
| Phase 2 | `reviewer_matcher` | Matches paper to suitable expert reviewers *(feature-flagged)* |

---

## 2. Core Principles (NON-NEGOTIABLE)

### 2.1 Flag, Never Accuse
The tool flags; it does not accuse. Every finding carries:
- A **confidence score** (0.0 – 1.0)
- **Supporting evidence** with kind (`text`, `computation`, or `external_record`)
- A `requires_human_review` boolean — always `true` for non-`info` severity

Nothing leaves the system without explicit human approval.

### 2.2 Verifiable Facts Are Computed, Not Hallucinated
- Anything verifiable is **computed in code** or **fetched from a real API**.
- The LLM orchestrates and writes prose; it **does not invent facts**.
- Statistics: real GRIM-style and statcheck-style checks via `scipy` / `numpy`.
- Citations: verified against **Crossref**, **PubMed E-utilities**, and the **arXiv API**.
- Retractions: sourced from **Crossref**.
- No millions-of-papers ingest — APIs are called at query time, supplemented by a small curated local corpus.

### 2.3 Always Runnable
The application must be runnable end-to-end at **every** checkpoint, not only at project completion.

### 2.4 Prefer Widely Used Libraries
No homegrown frameworks. Use battle-tested, well-maintained open-source packages.

---

## 3. Technology Stack (FINAL — DO NOT CHANGE)

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Frontend | **Next.js 14** (App Router) + **TypeScript** + **Tailwind CSS** | Widely supported scaffolding, great DX, App Router for streaming |
| Backend | **Python 3.11** + **FastAPI** | Python required for `scipy`/`numpy` (GRIM, statcheck) |
| Primary DB | **PostgreSQL 16** | Robust, free, production-grade relational store |
| Vector DB | **ChromaDB** (embedded) | Zero-config; appropriate for small local corpus |
| LLM | **Google Gemini API** | `gemini-2.5-flash` for routine agent calls; `gemini-2.5-pro` for synthesis and final report writing |
| Agent Orchestration | **LangGraph** | Explicit state machines and parallel branches; modern multi-agent choice |
| PDF Parsing | **PyMuPDF** (`fitz`) | Fast, accurate, pure-Python PDF → structured text |
| Cache | **Redis 7** | API response caching to control cost |
| Object Storage | Local filesystem under `./storage/` *(hackathon)* | Abstracted behind one module — swap to S3/GCS without refactoring |
| Automation | **n8n** (self-hosted, Docker) | Visual workflow for human-approval gates; same Docker network |
| Local Orchestration | **Docker Compose** | Single `docker compose up` starts everything |
| Deployment Target | **localhost demo** | No cloud deploy required for hackathon |

---

## 4. Repository Layout

```
peerless/
├── README.md
├── docker-compose.yml
├── .env.example
├── .gitignore
├── apps/
│   ├── backend/
│   │   ├── pyproject.toml
│   │   ├── src/peerless/
│   │   │   ├── api/                  # FastAPI routers
│   │   │   ├── agents/               # one folder per agent
│   │   │   ├── orchestrator/         # LangGraph graph
│   │   │   ├── parsing/              # PDF -> structured text
│   │   │   ├── verification/         # real-math checks (GRIM, statcheck), Crossref, PubMed, arXiv
│   │   │   ├── reports/              # report schema, assembly, persistence
│   │   │   ├── storage/              # files, db, cache abstractions
│   │   │   ├── config.py             # env-driven settings
│   │   │   └── main.py
│   │   └── tests/
│   └── frontend/                     # Next.js
├── fixtures/                         # curated sample PDFs + expected outputs
├── n8n/                              # exported workflow JSON
└── docs/
    ├── ARCHITECTURE.md
    ├── SAFETY.md
    └── MASTER_SPEC.md
```

---

## 5. Coding Conventions

### Python (backend)
- Formatter: **black**
- Linter: **ruff**
- **Type hints required** on all public functions and class attributes
- Module naming: `snake_case`

### TypeScript (frontend)
- Linter/Formatter: **ESLint** + **Prettier**
- Component naming: `PascalCase`
- Variable naming: `camelCase`

### API Design
- All endpoints under `/api/v1`
- JSON only (Content-Type: `application/json`)
- Error envelope:
  ```json
  {
    "error": {
      "code": "STRING_CODE",
      "message": "Human-readable message",
      "details": null
    }
  }
  ```
- Correct HTTP status codes in all responses

### Logging
- Backend: **structlog** (structured JSON output)
- Frontend: **pino** (structured JSON output)

### Secrets
- Only via environment variables; **never committed**
- `.env.example` lists every required key with placeholder values and comments

### Testing
- Backend: **pytest** — every agent must have at least one fixture-based test
- Frontend: **vitest** — unit and component tests
- Fixtures live under `fixtures/` for PDF samples and expected agent outputs

### Commit Style
**Conventional Commits** — prefix every commit message:
- `feat:` — new feature
- `fix:` — bug fix
- `chore:` — tooling, scaffolding, maintenance
- `docs:` — documentation only
- `test:` — test additions/changes
- `refactor:` — code changes with no feature/fix impact

---

## 6. Shared Report Schema (Canonical)

This schema is used by **every agent** and **the UI**. Do not deviate without amending this spec.

```json
{
  "report_id": "<uuid>",
  "paper_id": "<uuid>",
  "paper_metadata": {
    "title": "string",
    "authors": ["string"],
    "doi": "string | null",
    "abstract": "string",
    "page_count": 0
  },
  "created_at": "<ISO8601>",
  "overall_confidence": "low | medium | high",
  "findings": [
    {
      "agent": "statistical_integrity | citation_verifier | plain_language_summary | methodology_auditor | replication_predictor | contradiction_detector | conflict_of_interest | reviewer_matcher",
      "severity": "info | low | medium | high",
      "confidence": 0.0,
      "title": "string",
      "summary": "string",
      "evidence": [
        {
          "kind": "text | computation | external_record",
          "content": {}
        }
      ],
      "requires_human_review": true,
      "status": "draft | approved | rejected"
    }
  ],
  "plain_language_summary": "string | null"
}
```

### Schema Rules
- `findings[].status` defaults to `"draft"` — a human must transition it to `"approved"` or `"rejected"`.
- `findings[].requires_human_review` is `true` for any severity other than `"info"`.
- `overall_confidence` is computed from the distribution of finding severities and confidence scores — never set manually.

---

## 7. Legal & Safety (See Also: SAFETY.md)

### UI Requirements
Every finding displayed in the UI **must** carry the label:
> *Flagged concern — pending human review.*

Every report page **must** display the following disclaimer at the top:
> *PEERLESS.AI surfaces possible concerns for expert review. It does not adjudicate misconduct. Findings are not conclusions.*

### Prohibited Actions (Hard Constraints)
- **No external email**, no notification to any author, and no public post is ever sent **automatically**.
- n8n workflows that draft notifications are **HOLD-by-default** — they create a draft for a human to approve and send.
- No finding data is ever exposed outside the authenticated session without explicit human export action.

### Feature Flags
- `conflict_of_interest` agent: **disabled** by default; enabled only in Phase 2 via `FEATURE_COI_ENABLED=true`.
- `reviewer_matcher` agent: **disabled** by default; enabled only in Phase 2 via `FEATURE_REVIEWER_ENABLED=true`.

---

## 8. Acceptance Criteria for Step 0 (Bootstrap)

- [x] `docs/MASTER_SPEC.md` created and matches this content.
- [x] `docs/SAFETY.md` created with legal & safety section expanded.
- [x] Directory tree matches the repo layout above; every subfolder has a one-line README.
- [x] `.gitignore` covers Python, Node, IDE, env, and storage files.
- [x] Git repo initialized with commit: `chore: bootstrap master spec`.

---

*Last amended: 2026-06-17 — Step 0 bootstrap.*
