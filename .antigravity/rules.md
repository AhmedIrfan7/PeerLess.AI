# PEERLESS.AI — Antigravity Rules File
# Read this at the start of every session. All decisions here are final.

---

## 1. STACK (pinned versions)

| Layer | Choice |
|---|---|
| Frontend | Next.js 14 App Router + TypeScript + Tailwind CSS |
| Backend | Python 3.11+ + FastAPI |
| Primary DB | PostgreSQL 16 (host port 5433) |
| Vector DB | ChromaDB embedded (host port 8001) |
| LLM fast | gemini-2.5-flash |
| LLM smart | gemini-2.5-pro |
| Agent orchestration | LangGraph |
| Automation | n8n self-hosted via Docker Compose (port 5678) |
| Cache | Redis 7 (host port 6380) |
| PDF parsing | PyMuPDF (fitz) |
| PDF export | reportlab |
| Packaging | hatchling (pyproject.toml) |

Run command: `PYTHONPATH=apps/backend/src uvicorn peerless.main:app --reload --port 8000`
Frontend: `cd apps/frontend && npm run dev`

---

## 2. CONVENTIONS

**Python**
- Formatter: black (line-length 88)
- Linter: ruff
- Type hints: required on all public functions
- Naming: snake_case modules, PascalCase classes
- Imports: `from __future__ import annotations` at top of every file
- Logging: structlog with JSON renderer in prod, ConsoleRenderer in dev

**TypeScript**
- Formatter: Prettier
- Linter: ESLint
- Naming: PascalCase components, camelCase variables
- API types: defined in `lib/api.ts`, reused everywhere

**API**
- REST under `/api/v1`
- JSON only; errors: `{ error: { code, message, details|null } }` with correct HTTP status
- File uploads: multipart/form-data

**Commits**
- Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`, `step(N):`
- Never commit `.env` or any credential file

---

## 3. **SAFETY RULES** (NON-NEGOTIABLE)

1. **The tool flags, it does not accuse.** Every finding must include a confidence score and supporting evidence. The title must never imply misconduct.
2. **Nothing leaves the system without human approval.** The `ensure_all_approved(report_id)` gate blocks export and n8n notifications until every finding is status=`approved`.
3. **The LLM orchestrates and writes prose; it does not invent facts.** All statistics use `scipy.stats` / `decimal.Decimal`. All citations are verified via Crossref, PubMed, or arXiv APIs — never from LLM memory.
4. **n8n notification drafts are HOLD-by-default.** No workflow ever auto-sends an email or notification. A human must manually approve and send.
5. **COI agent and Reviewer Matcher are feature-flagged.** `FEATURE_COI_AGENT` and `FEATURE_REVIEWER_MATCHER` default to `false`. Only enable after Phase 2 safety review.

Every report page and finding card must display: *"Flagged concern — pending human review."*

---

## 4. REPORT SCHEMA (canonical)

```json
{
  "report_id": "uuid",
  "paper_id": "uuid",
  "paper_metadata": { "title": "str|null", "authors": ["str"], "doi": "str|null", "abstract": "str|null", "page_count": "int|null" },
  "created_at": "ISO8601",
  "overall_confidence": "low|medium|high|null",
  "findings": [
    {
      "agent": "statistical_integrity|citation_verifier|plain_language_summary|methodology_auditor|replication_predictor|contradiction_detector|conflict_of_interest|reviewer_matcher",
      "severity": "info|low|medium|high",
      "confidence": "0.0..1.0",
      "title": "str",
      "summary": "str",
      "evidence": [{ "kind": "text|computation|external_record", "content": {} }],
      "requires_human_review": true,
      "status": "draft|approved|rejected"
    }
  ],
  "plain_language_summary": "str|null"
}
```

All findings start with `status=draft` and `requires_human_review=true`.

---

## 5. AGENT IMPLEMENTATION GUIDELINES

- Use Gemini's JSON output mode for any agent that returns structured data. Pass `response_mime_type="application/json"` and a schema.
- Every external fact must come from a real API (Crossref, PubMed E-utilities, arXiv, OpenAlex) — **never** from LLM parametric memory.
- Any statistics check must use `scipy.stats` (p-values) or `decimal.Decimal` (GRIM). Unit-test with golden values.
- All HTTP calls use a shared `httpx.AsyncClient` with: timeout=10s, retry-on-429 with exponential backoff (max 3 tries), Redis-backed caching with TTLs from docs/CACHING.md.
- LLM wrapper (`agents/llm.py`): every call checks daily cost cap before hitting the API; caches responses in Redis (7-day TTL); logs `agent_name`, `model`, `tokens`, `cost_usd`, `cached`, `latency_ms`.
- Agent node errors must append to `state["errors"]` — never raise out of the LangGraph node.

---

## 6. TESTING

- Every agent must have at least one fixture-based test in `tests/agents/`.
- Fixtures live in `fixtures/` — four PDFs: `clean_paper.pdf`, `grim_violation.pdf`, `pvalue_inconsistency.pdf`, `bad_citation.pdf`.
- Each fixture has a matching `.expected.json` describing minimum expected findings.
- Run tests: `PYTHONPATH=apps/backend/src pytest apps/backend/tests/ -q`

---

## 7. FILE LAYOUT

```
peerless/
├── .antigravity/rules.md       ← THIS FILE
├── apps/
│   ├── backend/
│   │   ├── pyproject.toml
│   │   └── src/peerless/
│   │       ├── api/            # FastAPI routers + schemas.py
│   │       ├── agents/         # one subfolder per agent
│   │       ├── orchestrator/   # LangGraph graph
│   │       ├── parsing/        # PDF → structured text
│   │       ├── verification/   # GRIM, statcheck, Crossref, PubMed, arXiv
│   │       ├── reports/        # report assembly + persistence
│   │       ├── storage/        # models.py, database.py, cache.py
│   │       ├── config.py
│   │       ├── logging_config.py
│   │       └── main.py
│   └── frontend/               # Next.js 14 App Router
├── fixtures/                   # sample PDFs + expected JSON
├── n8n/                        # exported workflow JSON
├── scripts/                    # checkpoint scripts
├── docs/                       # MASTER_SPEC, SAFETY, ARCHITECTURE
├── docker-compose.yml
├── Makefile
└── .env.example
```
