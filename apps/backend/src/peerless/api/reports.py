"""Reports router — retrieve integrity reports and findings."""
from __future__ import annotations

import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from peerless.api.schemas import (
    EvidenceItem, FindingResponse, FindingReviewRequest, ReportResponse,
)
from peerless.storage.database import get_db
from peerless.storage.models import (
    AgentName, Finding, FindingSeverity, FindingStatus,
    HumanReviewAction, OverallConfidence, Paper, Report, ReportStatus, ReviewAction,
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


@router.get("/{report_id}/export")
async def export_report_pdf(
    report_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    result = await db.execute(
        select(Report)
        .options(selectinload(Report.findings))
        .where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": "Report not found.", "details": None}})
    if report.status.value not in ("complete", "partial"):
        raise HTTPException(status_code=409, detail={"error": {"code": "not_ready", "message": "Report not yet complete.", "details": None}})

    paper_result = await db.execute(select(Paper).where(Paper.id == report.paper_id))
    paper = paper_result.scalar_one_or_none()
    paper_meta: dict = {}
    if paper:
        paper_meta = {
            "original_filename": paper.original_filename,
            **(paper.parsed_metadata or {}),
        }

    findings_dicts = [
        {
            "id": str(f.id),
            "agent": f.agent.value,
            "severity": f.severity.value,
            "confidence": f.confidence,
            "title": f.title,
            "summary": f.summary,
            "evidence": f.evidence or [],
            "status": f.status.value,
            "reviewer_note": f.reviewer_note,
        }
        for f in (report.findings or [])
    ]

    from peerless.reports.pdf_export import generate_pdf
    report_dict = {
        "id": str(report.id),
        "overall_confidence": report.overall_confidence.value if report.overall_confidence else None,
        "plain_language_summary": report.plain_language_summary,
        "completed_at": report.completed_at.isoformat() if report.completed_at else None,
    }

    try:
        pdf_bytes = generate_pdf(report_dict, paper_meta, findings_dicts)
    except Exception as exc:
        logger.error("pdf_export.failed", error=str(exc))
        raise HTTPException(status_code=500, detail={"error": {"code": "export_failed", "message": "Could not generate PDF.", "details": None}})

    filename = f"peerless_report_{str(report_id)[:8]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
