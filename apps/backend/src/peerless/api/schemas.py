"""Shared Pydantic response/request schemas used by all routers and the frontend client."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ── Enums ─────────────────────────────────────────────────────────────────────

class PaperStatus(str, Enum):
    uploaded = "uploaded"
    parsing = "parsing"
    parsed = "parsed"
    parse_failed = "parse_failed"


class ReportStatus(str, Enum):
    pending = "pending"
    partial = "partial"
    complete = "complete"
    failed = "failed"


class OverallConfidence(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class AgentName(str, Enum):
    statistical_integrity = "statistical_integrity"
    citation_verifier = "citation_verifier"
    plain_language_summary = "plain_language_summary"
    methodology_auditor = "methodology_auditor"
    replication_predictor = "replication_predictor"
    contradiction_detector = "contradiction_detector"
    conflict_of_interest = "conflict_of_interest"
    reviewer_matcher = "reviewer_matcher"


class FindingSeverity(str, Enum):
    info = "info"
    low = "low"
    medium = "medium"
    high = "high"


class FindingStatus(str, Enum):
    draft = "draft"
    approved = "approved"
    rejected = "rejected"


# ── Paper schemas ─────────────────────────────────────────────────────────────

class PaperUploadResponse(BaseModel):
    paper_id: UUID
    sha256: str
    byte_size: int
    duplicate: bool = False


class PaperMetadata(BaseModel):
    title: str | None = None
    authors: list[str] = []
    abstract: str | None = None
    doi: str | None = None
    page_count: int | None = None
    language: str | None = None
    truncated: bool = False


class PaperResponse(BaseModel):
    id: UUID
    original_filename: str
    byte_size: int
    status: PaperStatus
    language: str | None
    parsed_metadata: PaperMetadata | None
    uploaded_at: datetime
    error_message: str | None = None

    model_config = {"from_attributes": True}


# ── Report / Finding schemas ───────────────────────────────────────────────────

class EvidenceItem(BaseModel):
    kind: str  # "text" | "computation" | "external_record"
    content: dict[str, Any]


class FindingResponse(BaseModel):
    id: UUID
    agent: AgentName
    severity: FindingSeverity
    confidence: float = Field(ge=0.0, le=1.0)
    title: str
    summary: str
    evidence: list[EvidenceItem] = []
    requires_human_review: bool
    status: FindingStatus
    reviewer_note: str | None = None
    reviewed_at: datetime | None = None

    model_config = {"from_attributes": True}


class ReportResponse(BaseModel):
    id: UUID
    paper_id: UUID
    status: ReportStatus
    overall_confidence: OverallConfidence | None
    findings: list[FindingResponse] = []
    plain_language_summary: str | None
    created_at: datetime
    completed_at: datetime | None
    error: str | None = None

    model_config = {"from_attributes": True}


# ── Human review schemas ───────────────────────────────────────────────────────

class ReviewAction(str, Enum):
    approve = "approve"
    reject = "reject"
    note = "note"


class FindingReviewRequest(BaseModel):
    action: ReviewAction
    note: str | None = None


# ── Error schema ───────────────────────────────────────────────────────────────

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Any = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
