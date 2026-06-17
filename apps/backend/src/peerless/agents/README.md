# Analysis Agents — agents/

Each subdirectory in this package contains one analysis agent.

## Agent Contract

Every agent module must expose a function with this signature:

```python
async def run(context: PaperContext) -> list[Finding]:
    ...
```

Agents must not modify shared state and must return immutable `Finding` objects.

## MVP Agents (Phase 1)

- `statistical_integrity/` — GRIM-style and statcheck-style statistical checks
- `citation_verifier/` — Citation verification via Crossref, PubMed, arXiv
- `plain_language_summary/` — Plain-language summary via Gemini

## Phase 2 Agents

- `methodology_auditor/`
- `replication_predictor/`
- `contradiction_detector/`
- `conflict_of_interest/` *(feature-flagged)*
- `reviewer_matcher/` *(feature-flagged)*
