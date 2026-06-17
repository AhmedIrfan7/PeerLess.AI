"""SQLAlchemy ORM models for PEERLESS.AI."""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Any

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer, String, Text,
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


# ── Enums ──────────────────────────────────────────────────────────────────────

class PaperStatus(str, PyEnum):
    uploaded = "uploaded"
    parsing = "parsing"
    parsed = "parsed"
    parse_failed = "parse_failed"


class ReportStatus(str, PyEnum):
    pending = "pending"
    partial = "partial"
    complete = "complete"
    failed = "failed"


class OverallConfidence(str, PyEnum):
    low = "low"
    medium = "medium"
    high = "high"


class AgentName(str, PyEnum):
    statistical_integrity = "statistical_integrity"
    citation_verifier = "citation_verifier"
    plain_language_summary = "plain_language_summary"
    methodology_auditor = "methodology_auditor"
    replication_predictor = "replication_predictor"
    contradiction_detector = "contradiction_detector"
    conflict_of_interest = "conflict_of_interest"
    reviewer_matcher = "reviewer_matcher"


class FindingSeverity(str, PyEnum):
    info = "info"
    low = "low"
    medium = "medium"
    high = "high"


class FindingStatus(str, PyEnum):
    draft = "draft"
    approved = "approved"
    rejected = "rejected"


class ReviewAction(str, PyEnum):
    approve = "approve"
    reject = "reject"
    note = "note"


# ── Models ─────────────────────────────────────────────────────────────────────

class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_filename: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(64), nullable=False, default="application/pdf")
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[PaperStatus] = mapped_column(
        SAEnum(PaperStatus, name="paper_status"), nullable=False, default=PaperStatus.uploaded
    )
    parsed_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    opt_in_email: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    submitter_email: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    reports: Mapped[list["Report"]] = relationship("Report", back_populates="paper")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("papers.id"), nullable=False, index=True)
    status: Mapped[ReportStatus] = mapped_column(
        SAEnum(ReportStatus, name="report_status"), nullable=False, default=ReportStatus.pending
    )
    overall_confidence: Mapped[OverallConfidence | None] = mapped_column(
        SAEnum(OverallConfidence, name="overall_confidence"), nullable=True
    )
    plain_language_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    paper: Mapped["Paper"] = relationship("Paper", back_populates="reports")
    findings: Mapped[list["Finding"]] = relationship("Finding", back_populates="report")


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("reports.id"), nullable=False, index=True)
    agent: Mapped[AgentName] = mapped_column(SAEnum(AgentName, name="agent_name"), nullable=False)
    severity: Mapped[FindingSeverity] = mapped_column(SAEnum(FindingSeverity, name="finding_severity"), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    requires_human_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[FindingStatus] = mapped_column(
        SAEnum(FindingStatus, name="finding_status"), nullable=False, default=FindingStatus.draft
    )
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    report: Mapped["Report"] = relationship("Report", back_populates="findings")
    review_actions: Mapped[list["HumanReviewAction"]] = relationship("HumanReviewAction", back_populates="finding")


class HumanReviewAction(Base):
    __tablename__ = "human_review_actions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    finding_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("findings.id"), nullable=False, index=True)
    action: Mapped[ReviewAction] = mapped_column(SAEnum(ReviewAction, name="review_action"), nullable=False)
    actor: Mapped[str] = mapped_column(Text, nullable=False, default="admin")
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    finding: Mapped["Finding"] = relationship("Finding", back_populates="review_actions")


class ExternalApiCache(Base):
    __tablename__ = "external_api_cache"

    key: Mapped[str] = mapped_column(Text, primary_key=True)
    value: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ttl_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=86400)


class LlmUsage(Base):
    __tablename__ = "llm_usage"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    agent: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
