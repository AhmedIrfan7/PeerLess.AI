"""GRIM (Granularity-Related Inconsistency of Means) check using decimal.Decimal."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation


@dataclass
class GrimResult:
    possible: bool
    M: str
    n: int
    d: int
    candidates: list[int]
    note: str = ""


def grim_check(mean_str: str, n: int, scale_min: int | None = None, scale_max: int | None = None) -> GrimResult:
    """
    Determine whether `mean_str` is a possible mean for `n` integer responses.

    Returns GrimResult(possible=True) if at least one integer sum S in [s_min, s_max]
    rounds to the reported mean.
    """
    if n <= 0:
        return GrimResult(possible=True, M=mean_str, n=n, d=0, candidates=[], note="n<=0, skipped")

    # Infer decimal places from string representation
    if "." in mean_str:
        d = len(mean_str.split(".")[1])
    else:
        return GrimResult(possible=True, M=mean_str, n=n, d=0, candidates=[], note="no decimals, uninformative")

    try:
        M = Decimal(mean_str)
    except InvalidOperation:
        return GrimResult(possible=True, M=mean_str, n=n, d=0, candidates=[], note="parse error")

    quant = Decimal("0." + "0" * d)

    # Candidate sum neighbourhood: round(M * n) ± 2
    base = int((M * n).to_integral_value(rounding=ROUND_HALF_UP))
    candidates_to_check = range(max(0, base - 2), base + 3)

    # Restrict by scale bounds if known
    if scale_min is not None and scale_max is not None:
        lo, hi = scale_min * n, scale_max * n
        candidates_to_check = range(max(lo, base - 2), min(hi, base + 3) + 1)

    valid_sums: list[int] = []
    for S in candidates_to_check:
        reconstructed = (Decimal(S) / Decimal(n)).quantize(quant, rounding=ROUND_HALF_UP)
        if reconstructed == M:
            valid_sums.append(S)

    return GrimResult(
        possible=len(valid_sums) > 0,
        M=mean_str,
        n=n,
        d=d,
        candidates=valid_sums,
    )
