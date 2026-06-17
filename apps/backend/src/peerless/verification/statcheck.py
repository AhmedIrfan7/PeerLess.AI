"""statcheck-style p-value recomputation using scipy.stats."""
from __future__ import annotations

import re
from dataclasses import dataclass

from scipy import stats


@dataclass
class StatcheckResult:
    test_type: str
    reported_p_str: str
    reported_p: float | None
    recomputed_p: float
    consistent: bool
    crosses_threshold: bool
    severity: str  # "info" | "medium" | "high"
    confidence: float
    note: str = ""


_P_RE = re.compile(r"p\s*[=<>]\s*\.?(\d[\d.e\-]*)", re.IGNORECASE)


def _parse_p(p_str: str) -> float | None:
    """Parse strings like 'p < .001', 'p = .027', 'p=0.05'."""
    p_str = p_str.strip().lower().replace(" ", "")
    m = re.search(r"[=<>]\s*\.?(\d[\d.e\-]*)", p_str)
    if not m:
        return None
    val_str = m.group(1)
    if not val_str.startswith("0") and not val_str.startswith("."):
        val_str = "0." + val_str if "." not in val_str else val_str
    try:
        return float(val_str)
    except ValueError:
        return None


def _classify(reported: float | None, recomputed: float, tolerance: float = 0.001) -> tuple[bool, bool, str, float]:
    """Returns (consistent, crosses_threshold, severity, confidence)."""
    if reported is None:
        return True, False, "info", 0.5

    diff = abs(recomputed - reported)
    consistent = bool(diff <= tolerance)

    sig_reported = reported < 0.05
    sig_recomputed = recomputed < 0.05
    crosses_threshold = bool(sig_reported != sig_recomputed)

    if crosses_threshold:
        severity = "high"
        confidence = 0.9
    elif not consistent:
        severity = "medium"
        confidence = 0.85
    else:
        severity = "info"
        confidence = 0.95

    return consistent, crosses_threshold, severity, confidence


def check_t_test(t: float, df: float, p_reported_str: str, one_tailed: bool = False) -> StatcheckResult:
    recomputed = stats.t.sf(abs(t), df) * (1 if one_tailed else 2)
    reported = _parse_p(p_reported_str)
    consistent, crosses, severity, conf = _classify(reported, recomputed)
    return StatcheckResult(
        test_type="t_test",
        reported_p_str=p_reported_str,
        reported_p=reported,
        recomputed_p=round(recomputed, 6),
        consistent=consistent,
        crosses_threshold=crosses,
        severity=severity,
        confidence=conf,
        note="one-tailed" if one_tailed else "",
    )


def check_chi_square(chi2: float, df: float, p_reported_str: str) -> StatcheckResult:
    recomputed = stats.chi2.sf(chi2, df)
    reported = _parse_p(p_reported_str)
    consistent, crosses, severity, conf = _classify(reported, recomputed)
    return StatcheckResult(
        test_type="chi_square",
        reported_p_str=p_reported_str,
        reported_p=reported,
        recomputed_p=round(recomputed, 6),
        consistent=consistent,
        crosses_threshold=crosses,
        severity=severity,
        confidence=conf,
    )


def check_f_test(f: float, df1: float, df2: float, p_reported_str: str) -> StatcheckResult:
    recomputed = stats.f.sf(f, df1, df2)
    reported = _parse_p(p_reported_str)
    consistent, crosses, severity, conf = _classify(reported, recomputed)
    return StatcheckResult(
        test_type="f_test",
        reported_p_str=p_reported_str,
        reported_p=reported,
        recomputed_p=round(recomputed, 6),
        consistent=consistent,
        crosses_threshold=crosses,
        severity=severity,
        confidence=conf,
    )


def check_correlation(r: float, n: int, p_reported_str: str) -> StatcheckResult:
    if n <= 2 or abs(r) >= 1:
        return StatcheckResult("correlation", p_reported_str, None, 0.0, True, False, "info", 0.3, "cannot compute")
    t_stat = r * ((n - 2) ** 0.5) / ((1 - r ** 2) ** 0.5)
    recomputed = stats.t.sf(abs(t_stat), n - 2) * 2
    reported = _parse_p(p_reported_str)
    consistent, crosses, severity, conf = _classify(reported, recomputed)
    return StatcheckResult(
        test_type="correlation",
        reported_p_str=p_reported_str,
        reported_p=reported,
        recomputed_p=round(recomputed, 6),
        consistent=consistent,
        crosses_threshold=crosses,
        severity=severity,
        confidence=conf,
    )
