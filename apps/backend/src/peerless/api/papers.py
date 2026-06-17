"""Papers router — upload, parse, and retrieve research papers."""
from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import Annotated

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from peerless.api.schemas import PaperMetadata, PaperResponse, PaperUploadResponse
from peerless.config import get_settings
from peerless.storage.database import get_db
from peerless.storage.models import Paper, PaperStatus

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/papers", tags=["papers"])


async def _save_file(content: bytes, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


@router.post("/", status_code=201, response_model=PaperUploadResponse)
async def upload_paper(
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(...),
    submitter_email: str | None = Form(default=None),
    opt_in_email: bool = Form(default=False),
) -> PaperUploadResponse:
    settings = get_settings()

    # Content-type check
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        content = await file.read(4)
        if content[:4] != b"%PDF":
            raise HTTPException(status_code=415, detail={"error": {"code": "unsupported_media_type", "message": "Only PDF files are accepted.", "details": None}})
        await file.seek(0)

    content = await file.read()

    # Magic bytes check
    if not content.startswith(b"%PDF"):
        raise HTTPException(status_code=415, detail={"error": {"code": "unsupported_media_type", "message": "File does not appear to be a PDF.", "details": None}})

    # Size check
    if len(content) == 0:
        raise HTTPException(status_code=400, detail={"error": {"code": "empty_file", "message": "Uploaded file is empty.", "details": None}})

    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail={"error": {"code": "file_too_large", "message": f"File exceeds maximum size of {settings.max_upload_bytes // (1024*1024)} MB.", "details": None}})

    sha256 = hashlib.sha256(content).hexdigest()

    # Duplicate check
    existing = await db.execute(select(Paper).where(Paper.sha256 == sha256))
    existing_paper = existing.scalar_one_or_none()
    if existing_paper:
        return PaperUploadResponse(
            paper_id=existing_paper.id,
            sha256=sha256,
            byte_size=existing_paper.byte_size,
            duplicate=True,
        )

    paper_id = uuid.uuid4()
    storage_path = Path(settings.storage_path) / "papers" / f"{paper_id}.pdf"

    try:
        await _save_file(content, storage_path)
    except OSError as exc:
        logger.error("upload.disk_write_failed", error=str(exc))
        raise HTTPException(status_code=500, detail={"error": {"code": "storage_error", "message": "Failed to save file. Please retry.", "details": None}})

    paper = Paper(
        id=paper_id,
        original_filename=file.filename or "upload.pdf",
        mime_type="application/pdf",
        byte_size=len(content),
        sha256=sha256,
        storage_path=str(storage_path),
        status=PaperStatus.uploaded,
        submitter_email=submitter_email,
        opt_in_email=opt_in_email,
    )
    db.add(paper)
    await db.flush()

    # Auto-parse in background
    from peerless.parsing.extract import parse_paper_background
    background_tasks.add_task(parse_paper_background, paper_id=paper_id, storage_path=str(storage_path))

    logger.info("paper.uploaded", paper_id=str(paper_id), byte_size=len(content))
    return PaperUploadResponse(paper_id=paper_id, sha256=sha256, byte_size=len(content))


@router.get("/{paper_id}", response_model=PaperResponse)
async def get_paper(
    paper_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PaperResponse:
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": "Paper not found.", "details": None}})

    meta = None
    if paper.parsed_metadata:
        meta = PaperMetadata(**{k: paper.parsed_metadata.get(k) for k in PaperMetadata.model_fields if k in paper.parsed_metadata})

    return PaperResponse(
        id=paper.id,
        original_filename=paper.original_filename,
        byte_size=paper.byte_size,
        status=paper.status,
        language=paper.language,
        parsed_metadata=meta,
        uploaded_at=paper.uploaded_at,
        error_message=paper.error_message,
    )


@router.post("/{paper_id}/reparse", response_model=PaperResponse)
async def reparse_paper(
    paper_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PaperResponse:
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": "Paper not found.", "details": None}})

    if paper.status == PaperStatus.parsing:
        raise HTTPException(status_code=409, detail={"error": {"code": "parse_in_progress", "message": "Parse already in progress.", "details": None}})

    paper.status = PaperStatus.parsing
    paper.parsed_metadata = None
    paper.error_message = None
    await db.flush()

    from peerless.parsing.extract import parse_paper_background
    background_tasks.add_task(parse_paper_background, paper_id=paper_id, storage_path=paper.storage_path)

    return PaperResponse(
        id=paper.id,
        original_filename=paper.original_filename,
        byte_size=paper.byte_size,
        status=paper.status,
        language=paper.language,
        parsed_metadata=None,
        uploaded_at=paper.uploaded_at,
        error_message=None,
    )


@router.post("/{paper_id}/analyze", status_code=202)
async def analyze_paper(
    paper_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": "Paper not found.", "details": None}})

    if paper.status == PaperStatus.uploaded:
        raise HTTPException(status_code=409, detail={"error": {"code": "paper_not_parsed", "message": "Paper has not been parsed yet.", "details": None}})

    if paper.status == PaperStatus.parse_failed:
        raise HTTPException(status_code=409, detail={"error": {"code": "paper_parse_failed", "message": "Paper parsing failed. Use /reparse first.", "details": None}})

    from peerless.storage.models import Report, ReportStatus
    from sqlalchemy import and_
    existing_report = await db.execute(
        select(Report).where(and_(Report.paper_id == paper_id, Report.status.in_([ReportStatus.pending, ReportStatus.partial])))
    )
    running = existing_report.scalar_one_or_none()
    if running:
        return {"report_id": str(running.id)}

    from peerless.storage.models import Report
    report = Report(paper_id=paper_id, status=ReportStatus.pending)
    db.add(report)
    await db.flush()
    report_id = report.id

    from peerless.orchestrator.graph import run_graph
    background_tasks.add_task(run_graph, paper_id=paper_id, report_id=report_id)

    return {"report_id": str(report_id)}
