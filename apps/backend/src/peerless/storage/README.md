# Storage Abstractions — storage/

This package provides unified abstractions for all storage backends so that implementation details can be swapped without refactoring agent or API code.

## Modules

- `files.py` — Local filesystem storage for uploaded PDFs (`./storage/papers/`)
- `db.py` — SQLAlchemy async session factory for PostgreSQL
- `cache.py` — Redis client wrapper for API response caching
- `vector.py` — ChromaDB client for local corpus vector search

## Design Principle

All storage access goes through these abstractions. No agent or router imports `psycopg`, `redis`, or `chromadb` directly — only the abstractions defined here.

This makes it straightforward to swap local filesystem → S3/GCS without touching business logic.
