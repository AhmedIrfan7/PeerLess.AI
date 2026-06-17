"""Citation Verifier agent — extract references and verify via Crossref/PubMed/arXiv."""
from __future__ import annotations

import re
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

_DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"'<>,;]+", re.IGNORECASE)
_ARXIV_RE = re.compile(r"arXiv:(\d{4}\.\d{4,5}|[a-z\-]+/\d{7})", re.IGNORECASE)
_PMID_RE = re.compile(r"PMID:\s*(\d+)", re.IGNORECASE)


def _extract_identifiers(raw: str) -> dict[str, str | None]:
    doi_m = _DOI_RE.search(raw)
    arxiv_m = _ARXIV_RE.search(raw)
    pmid_m = _PMID_RE.search(raw)
    return {
        "doi": doi_m.group(0).rstrip(".,);") if doi_m else None,
        "arxiv_id": arxiv_m.group(1) if arxiv_m else None,
        "pubmed_id": pmid_m.group(1) if pmid_m else None,
    }


async def run(parsed_paper: dict[str, Any], paper_id: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    refs_raw: list[str] = parsed_paper.get("references_raw", [])

    if not refs_raw:
        findings.append(_info("No references detected", "No bibliography entries found in the paper."))
        return findings

    capped = refs_raw[:100]
    if len(refs_raw) > 100:
        findings.append(_info("Verified first 100 references", f"Paper has {len(refs_raw)} references; verified first 100."))

    from peerless.config import get_settings
    settings = get_settings()
    mailto = settings.crossref_mailto

    from peerless.verification.crossref import lookup_doi, is_retracted, get_retraction_notice_url

    for ref in capped:
        ids = _extract_identifiers(ref)
        doi = ids.get("doi")

        if not doi:
            continue

        work = await lookup_doi(doi, mailto)

        if work is None:
            findings.append({
                "agent": "citation_verifier",
                "severity": "low",
                "confidence": 0.8,
                "title": f"Unresolved citation: {doi}",
                "summary": f"DOI '{doi}' could not be resolved in Crossref. The reference may be incorrect or unavailable.",
                "evidence": [{"kind": "text", "content": {"raw_reference": ref, "doi": doi, "lookup": "crossref"}}],
                "requires_human_review": True,
                "status": "draft",
            })
            continue

        if is_retracted(work):
            notice_url = get_retraction_notice_url(work) or "see Crossref"
            findings.append({
                "agent": "citation_verifier",
                "severity": "high",
                "confidence": 0.95,
                "title": "Cited reference has been retracted",
                "summary": (
                    f"DOI '{doi}' corresponds to a retracted work. "
                    f"Citing retracted papers may undermine the paper's evidence base. Retraction notice: {notice_url}"
                ),
                "evidence": [
                    {"kind": "external_record", "content": {"doi": doi, "retraction_notice": notice_url, "crossref_title": " ".join(work.get("title", []))}},
                    {"kind": "text", "content": {"raw_reference": ref}},
                ],
                "requires_human_review": True,
                "status": "draft",
            })

    return findings


def _info(title: str, summary: str) -> dict[str, Any]:
    return {
        "agent": "citation_verifier",
        "severity": "info",
        "confidence": 0.5,
        "title": title,
        "summary": summary,
        "evidence": [],
        "requires_human_review": True,
        "status": "draft",
    }
