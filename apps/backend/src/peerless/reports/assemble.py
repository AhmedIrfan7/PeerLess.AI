"""Report assembly — synthesize agent findings into a complete Report."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import structlog

logger = structlog.get_logger(__name__)


def compute_overall_confidence(findings: list[dict[str, Any]]) -> str:
    """
    Simple severity-based rule:
    any high → low  |  any medium → medium  |  else → high
    """
    severities = {f.get("severity") for f in findings}
    if "high" in severities:
        return "low"
    if "medium" in severities:
        return "medium"
    return "high"


async def assemble_and_persist(
    report_id: UUID,
    paper_id: UUID,
    all_findings: list[dict[str, Any]],
    errors: list[dict[str, Any]],
) -> None:
    from peerless.storage.database import AsyncSessionLocal
    from peerless.storage.models import (
        AgentName, Finding, FindingSeverity, FindingStatus, OverallConfidence,
        Report, ReportStatus,
    )
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Report).where(Report.id == report_id))
        report = result.scalar_one_or_none()
        if not report:
            logger.error("assemble.report_not_found", report_id=str(report_id))
            return

        # Add error findings for any failed agents
        for err in errors:
            all_findings.append({
                "agent": err.get("agent", "unknown"),
                "severity": "info",
                "confidence": 0.0,
                "title": f"Agent failed: {err.get('agent', 'unknown')}",
                "summary": err.get("message", "Unknown error"),
                "evidence": [],
                "requires_human_review": True,
                "status": "draft",
            })

        # Extract plain language summary
        plain_summary: str | None = None
        non_summary_findings: list[dict] = []
        for f in all_findings:
            if f.get("_is_summary"):
                plain_summary = f.get("_summary_text")
            else:
                non_summary_findings.append(f)

        all_findings = non_summary_findings

        if not all_findings and not errors:
            overall = "high"
        elif all(f.get("agent") == "unknown" for f in all_findings):
            report.status = ReportStatus.failed
            report.error = "All agents failed"
            report.completed_at = datetime.now(timezone.utc)
            await session.commit()
            return
        else:
            overall = compute_overall_confidence(all_findings)

        # Persist findings
        for f in all_findings:
            try:
                agent = AgentName(f["agent"])
                severity = FindingSeverity(f["severity"])
            except ValueError:
                continue

            finding = Finding(
                report_id=report_id,
                agent=agent,
                severity=severity,
                confidence=float(f.get("confidence", 0.5)),
                title=f["title"],
                summary=f["summary"],
                evidence=f.get("evidence", []),
                requires_human_review=f.get("requires_human_review", True),
                status=FindingStatus.draft,
            )
            session.add(finding)

        report.overall_confidence = OverallConfidence(overall)
        report.plain_language_summary = plain_summary
        report.status = ReportStatus.complete
        report.completed_at = datetime.now(timezone.utc)

        await session.commit()
        logger.info("report.assembled", report_id=str(report_id), findings=len(all_findings), confidence=overall)
