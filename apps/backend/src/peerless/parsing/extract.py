"""PDF → structured text extraction via PyMuPDF."""
from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF
import structlog

logger = structlog.get_logger(__name__)

_DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"'<>]+", re.IGNORECASE)
_SECTION_HEADINGS = re.compile(
    r"^(abstract|introduction|methods?|materials?\s+and\s+methods?|results?|"
    r"discussion|conclusion|references?|bibliography|works\s+cited|"
    r"acknowledgements?|funding|competing\s+interests?)$",
    re.IGNORECASE,
)
_REF_HEADING = re.compile(r"^(references?|bibliography|works\s+cited)\s*$", re.IGNORECASE)
_NUMBERED_REF = re.compile(r"^\s*\[?\d+[\]\.]\s+")


def extract_paper(pdf_path: str) -> dict[str, Any]:
    """Extract structured content from a PDF. Returns the parsed_metadata dict."""
    try:
        doc = fitz.open(pdf_path)
    except Exception as exc:
        return {"error_code": "open_failed", "error_message": str(exc)}

    page_count = doc.page_count
    if page_count == 0:
        return {"error_code": "no_pages", "error_message": "PDF has no pages."}

    max_pages = min(page_count, 100)
    truncated = page_count > 100

    # Check for extractable text
    total_chars = sum(len(doc[i].get_text()) for i in range(min(3, page_count)))
    if total_chars < 50:
        return {
            "error_code": "no_text_extracted",
            "error_message": "PDF appears to be scanned; OCR is not implemented in MVP.",
        }

    # Collect pages
    pages_text: list[str] = [doc[i].get_text() for i in range(max_pages)]
    full_text = "\n".join(pages_text)

    # ── Title heuristic ────────────────────────────────────────────────────────
    title = _extract_title(doc)

    # ── DOI ───────────────────────────────────────────────────────────────────
    doi: str | None = None
    for i in range(min(3, page_count)):
        m = _DOI_RE.search(doc[i].get_text())
        if m:
            doi = m.group(0).rstrip(".),;")
            break

    # ── Authors ───────────────────────────────────────────────────────────────
    authors = _extract_authors(pages_text[0] if pages_text else "")

    # ── Sections ──────────────────────────────────────────────────────────────
    sections, abstract, references_raw = _extract_sections(pages_text)

    # ── Language ──────────────────────────────────────────────────────────────
    language = _detect_language(abstract or full_text[:1000])

    return {
        "title": title,
        "authors": authors,
        "abstract": abstract,
        "doi": doi,
        "page_count": page_count,
        "language": language,
        "sections": sections,
        "references_raw": references_raw,
        "truncated": truncated,
    }


def _extract_title(doc: fitz.Document) -> str | None:
    if doc.page_count == 0:
        return None
    page = doc[0]
    blocks = page.get_text("dict")["blocks"]
    max_size = 0.0
    title_candidate = None
    for block in blocks:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                size = span.get("size", 0)
                text = span.get("text", "").strip()
                if size > max_size and len(text) >= 8:
                    max_size = size
                    title_candidate = text
    if title_candidate:
        return title_candidate
    # Fallback: first long line on page 1
    for line in page.get_text().splitlines():
        line = line.strip()
        if len(line.split()) >= 4:
            return line
    return None


def _extract_authors(page1_text: str) -> list[str]:
    lines = [l.strip() for l in page1_text.splitlines() if l.strip()]
    authors: list[str] = []
    # Look for lines after the title that contain comma-separated names
    for line in lines[1:8]:
        if re.search(r"\b(department|university|institute|school|abstract|introduction)\b", line, re.IGNORECASE):
            break
        if re.search(r"[A-Z][a-z]+\s+[A-Z][a-z]+", line):
            parts = re.split(r",\s*|\s+and\s+", line)
            for p in parts:
                p = p.strip().rstrip("1234567890*†‡")
                if re.match(r"[A-Z][a-z]+ [A-Z]", p):
                    authors.append(p)
    return authors[:10]


def _extract_sections(pages_text: list[str]) -> tuple[list[dict], str | None, list[str]]:
    sections: list[dict[str, Any]] = []
    abstract: str | None = None
    references_raw: list[str] = []

    current_heading: str | None = None
    current_lines: list[str] = []
    in_references = False

    for page_idx, page_text in enumerate(pages_text):
        for line in page_text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue

            if _REF_HEADING.match(stripped):
                if current_heading and current_lines:
                    sections.append({"heading": current_heading, "text": " ".join(current_lines), "page": page_idx + 1})
                in_references = True
                current_heading = stripped
                current_lines = []
                continue

            if in_references:
                if _NUMBERED_REF.match(stripped) or (stripped and stripped[0].isdigit()):
                    references_raw.append(stripped)
                elif references_raw:
                    references_raw[-1] += " " + stripped
                continue

            if _SECTION_HEADINGS.match(stripped):
                if current_heading and current_lines:
                    text = " ".join(current_lines)
                    sections.append({"heading": current_heading, "text": text, "page": page_idx + 1})
                    if current_heading.lower() == "abstract":
                        abstract = text
                current_heading = stripped
                current_lines = []
            else:
                current_lines.append(stripped)

    if current_heading and current_lines and not in_references:
        text = " ".join(current_lines)
        sections.append({"heading": current_heading, "text": text, "page": len(pages_text)})
        if current_heading.lower() == "abstract":
            abstract = text

    # Fallback abstract: first ~500 chars of text if no Abstract heading found
    if not abstract and pages_text:
        abstract = pages_text[0][:800].replace("\n", " ").strip() or None

    return sections, abstract, references_raw[:200]


def _detect_language(text: str) -> str:
    try:
        from langdetect import detect, LangDetectException
        return detect(text[:2000])
    except Exception:
        return "en"


# ── Background task ────────────────────────────────────────────────────────────

async def parse_paper_background(paper_id: uuid.UUID, storage_path: str) -> None:
    """Run extraction and persist results. Called as a FastAPI BackgroundTask."""
    from peerless.storage.database import AsyncSessionLocal
    from peerless.storage.models import Paper, PaperStatus
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(select(Paper).where(Paper.id == paper_id))
            paper = result.scalar_one_or_none()
            if not paper:
                return

            paper.status = PaperStatus.parsing
            await session.commit()

            data = extract_paper(storage_path)

            if "error_code" in data:
                paper.status = PaperStatus.parse_failed
                paper.error_message = data["error_message"]
                paper.parsed_metadata = {"error_code": data["error_code"]}
            else:
                paper.status = PaperStatus.parsed
                paper.language = data.get("language")
                paper.parsed_metadata = data

            await session.commit()
            logger.info("paper.parsed", paper_id=str(paper_id), status=paper.status.value)

        except Exception as exc:
            logger.error("paper.parse_error", paper_id=str(paper_id), error=str(exc))
            try:
                paper.status = PaperStatus.parse_failed
                paper.error_message = str(exc)
                await session.commit()
            except Exception:
                pass
