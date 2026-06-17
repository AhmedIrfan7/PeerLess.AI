# Reports — reports/

This package owns the canonical IntegrityReport schema and all report lifecycle logic.

## Contents

- `schema.py` — Pydantic models for `IntegrityReport`, `Finding`, `Evidence`, `PaperMetadata`
- `assembly.py` — Logic to aggregate agent findings into a complete report
- `persistence.py` — Read/write `IntegrityReport` to PostgreSQL

## Schema

See [MASTER_SPEC.md](../../../../../../../../docs/MASTER_SPEC.md#6-shared-report-schema-canonical) for the canonical JSON schema that all agents and the UI must conform to.
