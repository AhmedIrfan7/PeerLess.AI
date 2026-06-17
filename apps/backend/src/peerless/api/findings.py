"""Findings router — human review actions on individual findings."""
from __future__ import annotations

from fastapi import APIRouter

from peerless.api.schemas import FindingResponse

router = APIRouter(prefix="/findings", tags=["findings"])


@router.get("/", response_model=list[FindingResponse])
async def list_findings() -> list:
    """List all findings. Placeholder — implemented in Step 39."""
    return []
