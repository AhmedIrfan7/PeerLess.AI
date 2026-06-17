# PDF Parsing — parsing/

This package converts uploaded PDF files into structured text and metadata for agent consumption.

## Technology

- **PyMuPDF** (`fitz`) — Fast, accurate PDF text extraction with page-level structure

## Output

The parser produces a `PaperContext` object containing:

- `full_text` — Concatenated page text
- `pages` — Per-page text list (preserves page numbers for evidence citations)
- `metadata` — Title, authors, DOI (if embedded), page count
- `sections` — Heuristically detected section blocks (Abstract, Introduction, Methods, Results, etc.)
