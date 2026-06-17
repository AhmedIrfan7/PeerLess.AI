"""Findings router — human review approve/reject actions."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from peerless.api.schemas import FindingReviewRequest
from peerless.storage.database import get_db
from peerless.storage.models import Finding, FindingStatus, HumanReviewAction, ReviewAction, ReportStatus, Report

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/findings", tags=["findings"])


@router.post("/{finding_id}/review")
async def review_finding(
    finding_id: uuid.UUID,
    body: FindingReviewRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    result = await db.execute(select(Finding).where(Finding.id == finding_id))
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": "Finding not found.", "details": None}})

    # Check report is not failed
    report_result = await db.execute(select(Report).where(Report.id == finding.report_id))
    report = report_result.scalar_one_or_none()
    if report and report.status == ReportStatus.failed:
        raise HTTPException(status_code=409, detail={"error": {"code": "report_failed", "message": "Cannot review findings on a failed report.", "details": None}})

    if body.action == "approve":
        finding.status = FindingStatus.approved
    elif body.action == "reject":
        finding.status = FindingStatus.rejected
    finding.reviewer_note = body.note
    finding.reviewed_at = datetime.now(timezone.utc)

    action = HumanReviewAction(
        finding_id=finding_id,
        action=ReviewAction(body.action.value),
        actor="admin",
        note=body.note,
    )
    db.add(action)
    await db.flush()

    return {"finding_id": str(finding_id), "status": finding.status.value}
