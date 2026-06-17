"""Papers router — upload, parse, and retrieve research papers."""
from __future__ import annotations

from fastapi import APIRouter

from peerless.api.schemas import PaperResponse

router = APIRouter(prefix="/papers", tags=["papers"])


@router.get("/", response_model=list[PaperResponse])
async def list_papers() -> list:
    """List all uploaded papers. Placeholder — implemented in Step 8."""
    return []
