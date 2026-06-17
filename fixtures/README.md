# Fixtures — fixtures/

Curated sample PDFs and expected agent outputs used for testing and development.

## Contents

- `papers/` — Sample research PDFs in various states (clean, with statistical errors, with bad citations)
- `expected/` — JSON files containing expected `IntegrityReport` outputs for each sample paper

## Usage

Fixtures are referenced by pytest conftest.py and by n8n workflow test scenarios.
Add new fixtures whenever a new edge case or agent feature is developed.
