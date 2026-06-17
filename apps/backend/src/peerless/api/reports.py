"""Reports router — retrieve integrity reports."""
from __future__ import annotations

from fastapi import APIRouter

from peerless.api.schemas import ReportResponse

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/", response_model=list[ReportResponse])
async def list_reports() -> list:
    """List all reports. Placeholder — implemented in Step 14."""
    return []
