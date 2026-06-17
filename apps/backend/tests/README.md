# Tests — tests/

pytest test suite for the PEERLESS.AI backend.

## Structure

- `conftest.py` — Shared fixtures (database, Redis, test paper PDFs)
- `test_api/` — API endpoint integration tests
- `test_agents/` — Per-agent fixture-based unit tests
- `test_verification/` — GRIM, statcheck, and API client tests
- `test_parsing/` — PDF parsing tests against fixtures

## Running Tests

```bash
pytest                          # All tests
pytest tests/test_agents/       # Agent tests only
pytest -v --tb=short            # Verbose with short tracebacks
```

## Fixtures

Sample PDFs and expected outputs live in `fixtures/` at the repo root.
