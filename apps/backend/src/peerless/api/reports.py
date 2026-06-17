"""Reports router — retrieve integrity reports and findings."""
from __future__ import annotations

import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from peerless.api.schemas import (
    EvidenceItem, FindingResponse, FindingReviewRequest, ReportResponse,
)
from peerless.storage.database import get_db
from peerless.storage.models import (
    AgentName, Finding, FindingSeverity, FindingStatus,
    HumanReviewAction, OverallConfidence, Report, ReportStatus, ReviewAction,
)

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/reports", tags=["reports"])


def _finding_to_schema(f: Finding) -> FindingResponse:
    evidence = []
    if f.evidence:
        for item in f.evidence:
            evidence.append(EvidenceItem(kind=item.get("kind", "text"), content=item.get("content", {})))
    return FindingResponse(
        id=f.id,
        agent=AgentName(f.agent.value),
        severity=FindingSeverity(f.severity.value),
        confidence=f.confidence,
        title=f.title,
        summary=f.summary,
        evidence=evidence,
        requires_human_review=f.requires_human_review,
        status=FindingStatus(f.status.value),
        reviewer_note=f.reviewer_note,
        reviewed_at=f.reviewed_at,
    )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReportResponse:
    result = await db.execute(
        select(Report)
        .options(selectinload(Report.findings))
        .where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": "Report not found.", "details": None}})

    findings = [_finding_to_schema(f) for f in (report.findings or [])]
    return ReportResponse(
        id=report.id,
        paper_id=report.paper_id,
        status=ReportStatus(report.status.value),
        overall_confidence=OverallConfidence(report.overall_confidence.value) if report.overall_confidence else None,
        findings=findings,
        plain_language_summary=report.plain_language_summary,
        created_at=report.created_at,
        completed_at=report.completed_at,
        error=report.error,
    )
