"""Statistical Integrity agent — claim extraction + GRIM + statcheck."""
from __future__ import annotations

import re
from typing import Any

import structlog

from peerless.verification.grim import grim_check
from peerless.verification.statcheck import (
    check_chi_square, check_correlation, check_f_test, check_t_test,
)

logger = structlog.get_logger(__name__)

_FAST_MODEL = "grok-3-fast"

EXTRACT_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "kind": {"type": "string", "enum": ["mean_sd", "t_test", "chi_square", "f_test", "correlation", "proportion"]},
            "reported_values": {"type": "object"},
            "page": {"type": "integer"},
            "snippet": {"type": "string"},
        },
        "required": ["kind", "reported_values", "snippet"],
    },
}

SYSTEM = (
    "You are a scientific statistics auditor. Extract ALL statistical claims from the paper text. "
    "Return a JSON array. Each element has kind, reported_values (see schema), page (int or 0), snippet (verbatim quote). "
    "For mean_sd: reported_values = {mean: str, sd: str|null, n: int|null, integer_scale: bool, scale_min: int|null, scale_max: int|null}. "
    "For t_test: reported_values = {t: float, df: float, p_reported: str, one_tailed: bool}. "
    "For chi_square: reported_values = {chi2: float, df: float, p_reported: str}. "
    "For f_test: reported_values = {f: float, df1: float, df2: float, p_reported: str}. "
    "For correlation: reported_values = {r: float, n: int, p_reported: str|null}. "
    "Return [] if no statistical claims found. Return ONLY valid JSON."
)


async def run(parsed_paper: dict[str, Any], paper_id: str) -> list[dict[str, Any]]:
    """Run the statistical integrity agent. Returns a list of Finding dicts."""
    findings: list[dict[str, Any]] = []

    # Build text from Results + Methods sections
    sections = parsed_paper.get("sections", [])
    relevant = " ".join(
        s["text"] for s in sections
        if any(kw in s.get("heading", "").lower() for kw in ["result", "method", "statistic"])
    )
    if not relevant:
        relevant = " ".join(s["text"] for s in sections)

    if not relevant.strip():
        findings.append(_info_finding("No statistical claims detected", "No extractable text found for statistical analysis."))
        return findings

    # Extract claims — try Gemini first, fall back to regex so GRIM/statcheck
    # still run without an API key.
    claims: list[dict] = []
    extraction_method = "llm"
    try:
        from peerless.agents.llm import LLMUnavailable, UpstreamMalformed, generate_json
        raw = await generate_json(
            model=_FAST_MODEL,
            system=SYSTEM,
            prompt=f"Extract statistical claims from this paper text:\n\n{relevant[:6000]}",
            schema=EXTRACT_SCHEMA,
            max_tokens=2048,
            agent_name="statistical_integrity",
            paper_id=paper_id,
        )
        claims = raw if isinstance(raw, list) else []
    except LLMUnavailable:
        extraction_method = "regex"
    except UpstreamMalformed:
        extraction_method = "regex"
        logger.warning("statistical_integrity.llm_malformed_using_regex")
    except Exception as exc:
        extraction_method = "regex"
        logger.warning("statistical_integrity.llm_error_using_regex", error=str(exc))

    if extraction_method == "regex":
        from peerless.verification.regex_extractor import extract_claims
        claims = extract_claims(relevant)
        if claims:
            findings.append(_info_finding(
                "Statistical claims extracted via pattern matching",
                f"LLM unavailable; {len(claims)} statistical claim(s) found by regex. "
                "GRIM and p-value checks proceeded automatically.",
            ))
        else:
            findings.append(_info_finding(
                "No statistical claims detected",
                "No APA-format statistics found. LLM unavailable for deeper extraction.",
            ))
            return findings

    if not claims:
        findings.append(_info_finding("No statistical claims detected", "No statistical claims found in the paper."))
        return findings

    # Run GRIM on mean_sd claims
    for claim in claims:
        if claim.get("kind") != "mean_sd":
            continue
        rv = claim.get("reported_values", {})
        mean_str = str(rv.get("mean", ""))
        n = rv.get("n")
        if not mean_str or n is None:
            continue
        try:
            n = int(n)
        except (TypeError, ValueError):
            continue

        integer_scale = rv.get("integer_scale", False)
        scale_min = rv.get("scale_min")
        scale_max = rv.get("scale_max")

        result = grim_check(
            mean_str, n,
            scale_min=int(scale_min) if scale_min is not None else None,
            scale_max=int(scale_max) if scale_max is not None else None,
        )

        if result.note in ("n<=0, skipped", "no decimals, uninformative", "parse error"):
            continue

        if not result.possible:
            snippet = claim.get("snippet", "")
            severity = "high" if any(kw in claim.get("heading", "").lower() for kw in ["result", "main", "primary"]) else "medium"
            findings.append({
                "agent": "statistical_integrity",
                "severity": severity,
                "confidence": 0.9,
                "title": f"Reported mean M={mean_str} appears mathematically impossible for n={n}",
                "summary": (
                    f"GRIM check: mean {mean_str} with n={n} cannot be produced from integer responses. "
                    f"Nearest valid candidates: {result.candidates or 'none found'}."
                ),
                "evidence": [
                    {"kind": "computation", "content": {"check": "GRIM", "M": mean_str, "n": n, "d": result.d, "candidates": result.candidates}},
                    {"kind": "text", "content": {"snippet": snippet}},
                ],
                "requires_human_review": True,
                "status": "draft",
            })

    # Run statcheck on t_test, chi_square, f_test, correlation
    for claim in claims:
        kind = claim.get("kind")
        rv = claim.get("reported_values", {})
        snippet = claim.get("snippet", "")
        sc_result = None

        try:
            if kind == "t_test":
                t = float(rv.get("t", 0))
                df = float(rv.get("df", 1))
                p_str = str(rv.get("p_reported", ""))
                if p_str:
                    sc_result = check_t_test(t, df, p_str, one_tailed=rv.get("one_tailed", False))

            elif kind == "chi_square":
                chi2 = float(rv.get("chi2", 0))
                df = float(rv.get("df", 1))
                p_str = str(rv.get("p_reported", ""))
                if p_str:
                    sc_result = check_chi_square(chi2, df, p_str)

            elif kind == "f_test":
                f = float(rv.get("f", 0))
                df1 = float(rv.get("df1", 1))
                df2 = float(rv.get("df2", 1))
                p_str = str(rv.get("p_reported", ""))
                if p_str:
                    sc_result = check_f_test(f, df1, df2, p_str)

            elif kind == "correlation":
                r = float(rv.get("r", 0))
                n = int(rv.get("n", 0))
                p_str = str(rv.get("p_reported", "") or "")
                if p_str and n > 2:
                    sc_result = check_correlation(r, n, p_str)

        except (TypeError, ValueError):
            continue

        if sc_result and not sc_result.consistent:
            findings.append({
                "agent": "statistical_integrity",
                "severity": sc_result.severity,
                "confidence": sc_result.confidence,
                "title": f"p-value inconsistency detected ({kind}): reported {sc_result.reported_p_str}, recomputed p≈{sc_result.recomputed_p}",
                "summary": (
                    f"The reported {kind} result appears statistically inconsistent. "
                    f"Reported: {sc_result.reported_p_str}. Recomputed p≈{sc_result.recomputed_p}."
                    + (" This crosses the p=0.05 significance threshold." if sc_result.crosses_threshold else "")
                ),
                "evidence": [
                    {"kind": "computation", "content": {
                        "test": kind,
                        "reported_p": sc_result.reported_p,
                        "recomputed_p": sc_result.recomputed_p,
                        "crosses_threshold": sc_result.crosses_threshold,
                    }},
                    {"kind": "text", "content": {"snippet": snippet}},
                ],
                "requires_human_review": True,
                "status": "draft",
            })

    return findings


def _info_finding(title: str, summary: str, severity: str = "info") -> dict[str, Any]:
    return {
        "agent": "statistical_integrity",
        "severity": severity,
        "confidence": 0.5,
        "title": title,
        "summary": summary,
        "evidence": [],
        "requires_human_review": True,
        "status": "draft",
    }
