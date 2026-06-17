"""LangGraph orchestration — parallel agent fan-out and report synthesis."""
from __future__ import annotations

import asyncio
from typing import Any
from uuid import UUID

import structlog

logger = structlog.get_logger(__name__)


async def run_graph(paper_id: UUID, report_id: UUID) -> None:
    """
    Main entry point for paper analysis.
    Runs all MVP agents in parallel, then assembles the report.
    """
    from peerless.storage.database import AsyncSessionLocal
    from peerless.storage.models import Paper, Report, ReportStatus
    from sqlalchemy import select

    # Mark report as partial (in-progress)
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Report).where(Report.id == report_id))
        report = result.scalar_one_or_none()
        if report:
            report.status = ReportStatus.partial
            await session.commit()

    # Load paper
    parsed_paper: dict[str, Any] = {}
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Paper).where(Paper.id == paper_id))
        paper = result.scalar_one_or_none()
        if paper and paper.parsed_metadata:
            parsed_paper = dict(paper.parsed_metadata)

    if not parsed_paper:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Report).where(Report.id == report_id))
            report = result.scalar_one_or_none()
            if report:
                report.status = ReportStatus.failed
                report.error = "Paper has no parsed metadata."
                await session.commit()
        return

    paper_id_str = str(paper_id)
    all_findings: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    # ── Parallel agent fan-out ─────────────────────────────────────────────────
    async def run_statistical_integrity() -> list[dict]:
        try:
            from peerless.agents.statistical_integrity.agent import run
            return await run(parsed_paper, paper_id_str)
        except Exception as exc:
            logger.error("agent.statistical_integrity.failed", error=str(exc))
            errors.append({"agent": "statistical_integrity", "message": str(exc)})
            return []

    async def run_citation_verifier() -> list[dict]:
        try:
            from peerless.agents.citation_verifier.agent import run
            return await run(parsed_paper, paper_id_str)
        except Exception as exc:
            logger.error("agent.citation_verifier.failed", error=str(exc))
            errors.append({"agent": "citation_verifier", "message": str(exc)})
            return []

    results = await asyncio.gather(
        run_statistical_integrity(),
        run_citation_verifier(),
        return_exceptions=False,
    )

    for r in results:
        all_findings.extend(r)

    # Plain language summary runs after other agents so it can reference their findings
    try:
        from peerless.agents.plain_language_summary import run as run_pls
        pls_findings = await run_pls(parsed_paper, all_findings, paper_id_str)
        all_findings.extend(pls_findings)
    except Exception as exc:
        logger.error("agent.plain_language_summary.failed", error=str(exc))
        errors.append({"agent": "plain_language_summary", "message": str(exc)})

    # Assemble and persist report
    from peerless.reports.assemble import assemble_and_persist
    await assemble_and_persist(report_id, paper_id, all_findings, errors)
