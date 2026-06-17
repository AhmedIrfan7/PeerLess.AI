# Verification Modules — verification/

This package contains all code-based and API-based verification logic.

## Modules

- `grim.py` — GRIM (Granularity-Related Inconsistency of Means) test implementation using numpy
- `statcheck.py` — statcheck-style p-value recalculation using scipy
- `crossref.py` — Crossref REST API client for DOI resolution and retraction checks
- `pubmed.py` — PubMed E-utilities client for citation metadata lookup
- `arxiv.py` — arXiv API client for preprint lookup and verification

## Principle

All verification modules produce **computed evidence**, not LLM-inferred claims. Results are structured as `Evidence` objects with `kind='computation'` or `kind='external_record'`.
