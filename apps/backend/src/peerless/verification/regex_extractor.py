"""Regex-based statistical claim extractor — runs without any LLM."""
from __future__ import annotations

import re
from typing import Any

# APA-style patterns ──────────────────────────────────────────────────────────

# M = 2.50, SD = 1.20, n = 14   or   M (SD) = 2.50 (1.20), n = 14
_MEAN_SD_1 = re.compile(
    r"\bM\s*[=:]\s*(-?[\d]+\.[\d]+)"
    r"(?:,?\s*SD\s*[=:]\s*(-?[\d]+\.[\d]+))?"
    r"(?:,?\s*[Nn]\s*[=:]\s*(\d+))?",
)

# mean of 2.50 (SD = 1.20) for n = 14
_MEAN_SD_2 = re.compile(
    r"mean\s+of\s+(-?[\d]+\.[\d]+)"
    r"(?:\s*\(SD\s*=\s*(-?[\d]+\.[\d]+)\))?"
    r"(?:.*?[Nn]\s*[=:]\s*(\d+))?",
    re.IGNORECASE,
)

# t(30) = 2.34, p = .043  or  t(30) = 2.34, p < .001
_T_TEST = re.compile(
    r"\bt\s*\(\s*(\d+(?:\.\d+)?)\s*\)\s*=\s*(-?[\d]+\.[\d]+)"
    r"[,\s]+p\s*[=<>]\s*\.?(\d[\d.e\-]*)",
    re.IGNORECASE,
)

# chi-squared / chi2 / χ² (df) = value, p = ...
_CHI2 = re.compile(
    r"(?:chi[\s\-]?squ?a?r?e?d?|χ²?)\s*\(\s*(\d+)(?:[^)]*)\)\s*=\s*([\d]+\.[\d]+)"
    r"[,\s]+p\s*[=<>]\s*\.?(\d[\d.e\-]*)",
    re.IGNORECASE,
)

# F(df1, df2) = value, p = ...
_F_TEST = re.compile(
    r"\bF\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)\s*=\s*([\d]+\.[\d]+)"
    r"[,\s]+p\s*[=<>]\s*\.?(\d[\d.e\-]*)",
)

# r(n-2) = .34, p = .001  or  r = .34, n = 100, p = .001
_CORR_1 = re.compile(
    r"\br\s*\(\s*(\d+)\s*\)\s*=\s*(-?\.?\d[\d.]*)"
    r"[,\s]+p\s*[=<>]\s*\.?(\d[\d.e\-]*)",
    re.IGNORECASE,
)
_CORR_2 = re.compile(
    r"\br\s*=\s*(-?\.?\d[\d.]*)"
    r"[,\s]+[Nn]\s*=\s*(\d+)"
    r"[,\s]+p\s*[=<>]\s*\.?(\d[\d.e\-]*)",
    re.IGNORECASE,
)


def _snippet(text: str, match: re.Match, radius: int = 80) -> str:
    start = max(0, match.start() - radius)
    end = min(len(text), match.end() + radius)
    raw = text[start:end].replace("\n", " ")
    return f"…{raw}…" if start > 0 else raw


def _p_str(raw: str, full_match: str) -> str:
    """Reconstruct 'p = .043' format from a bare digit group."""
    op = "="
    for ch in full_match:
        if ch in "<>":
            op = ch
            break
    val = raw if "." in raw else f"0.{raw}"
    return f"p {op} {val}"


def extract_claims(text: str) -> list[dict[str, Any]]:
    """Return list of claim dicts compatible with EXTRACT_SCHEMA."""
    claims: list[dict[str, Any]] = []
    seen: set[str] = set()  # deduplicate by (kind, key_values)

    def _add(kind: str, rv: dict, snippet: str) -> None:
        key = f"{kind}:{sorted(rv.items())}"
        if key in seen:
            return
        seen.add(key)
        claims.append({"kind": kind, "reported_values": rv, "page": 0, "snippet": snippet})

    # mean / SD
    for m in _MEAN_SD_1.finditer(text):
        mean_str = m.group(1)
        n_str = m.group(3)
        if not mean_str:
            continue
        rv: dict[str, Any] = {"mean": mean_str, "sd": m.group(2), "n": int(n_str) if n_str else None,
                               "integer_scale": False, "scale_min": None, "scale_max": None}
        _add("mean_sd", rv, _snippet(text, m))

    for m in _MEAN_SD_2.finditer(text):
        mean_str = m.group(1)
        if not mean_str:
            continue
        n_str = m.group(3)
        rv = {"mean": mean_str, "sd": m.group(2), "n": int(n_str) if n_str else None,
              "integer_scale": False, "scale_min": None, "scale_max": None}
        _add("mean_sd", rv, _snippet(text, m))

    # t-test
    for m in _T_TEST.finditer(text):
        df, t_val, p_raw = m.group(1), m.group(2), m.group(3)
        rv = {"t": float(t_val), "df": float(df), "p_reported": _p_str(p_raw, m.group(0)), "one_tailed": False}
        _add("t_test", rv, _snippet(text, m))

    # chi-square
    for m in _CHI2.finditer(text):
        df, chi2_val, p_raw = m.group(1), m.group(2), m.group(3)
        rv = {"chi2": float(chi2_val), "df": float(df), "p_reported": _p_str(p_raw, m.group(0))}
        _add("chi_square", rv, _snippet(text, m))

    # F-test
    for m in _F_TEST.finditer(text):
        df1, df2, f_val, p_raw = m.group(1), m.group(2), m.group(3), m.group(4)
        rv = {"f": float(f_val), "df1": float(df1), "df2": float(df2), "p_reported": _p_str(p_raw, m.group(0))}
        _add("f_test", rv, _snippet(text, m))

    # Correlations
    for m in _CORR_1.finditer(text):
        df_minus2, r_val, p_raw = m.group(1), m.group(2), m.group(3)
        n = int(df_minus2) + 2
        rv = {"r": float(r_val), "n": n, "p_reported": _p_str(p_raw, m.group(0))}
        _add("correlation", rv, _snippet(text, m))

    for m in _CORR_2.finditer(text):
        r_val, n_str, p_raw = m.group(1), m.group(2), m.group(3)
        rv = {"r": float(r_val), "n": int(n_str), "p_reported": _p_str(p_raw, m.group(0))}
        _add("correlation", rv, _snippet(text, m))

    return claims
