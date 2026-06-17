"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-17
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Enums ──────────────────────────────────────────────────────────────────
    paper_status = postgresql.ENUM(
        "uploaded", "parsing", "parsed", "parse_failed",
        name="paper_status", create_type=True,
    )
    report_status = postgresql.ENUM(
        "pending", "partial", "complete", "failed",
        name="report_status", create_type=True,
    )
    overall_confidence = postgresql.ENUM(
        "low", "medium", "high",
        name="overall_confidence", create_type=True,
    )
    agent_name = postgresql.ENUM(
        "statistical_integrity", "citation_verifier", "plain_language_summary",
        "methodology_auditor", "replication_predictor", "contradiction_detector",
        "conflict_of_interest", "reviewer_matcher",
        name="agent_name", create_type=True,
    )
    finding_severity = postgresql.ENUM(
        "info", "low", "medium", "high",
        name="finding_severity", create_type=True,
    )
    finding_status = postgresql.ENUM(
        "draft", "approved", "rejected",
        name="finding_status", create_type=True,
    )
    review_action = postgresql.ENUM(
        "approve", "reject", "note",
        name="review_action", create_type=True,
    )

    # ── papers ─────────────────────────────────────────────────────────────────
    op.create_table(
        "papers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("original_filename", sa.Text, nullable=False),
        sa.Column("mime_type", sa.String(64), nullable=False, server_default="application/pdf"),
        sa.Column("byte_size", sa.Integer, nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("storage_path", sa.Text, nullable=False),
        sa.Column("status", paper_status, nullable=False, server_default="uploaded"),
        sa.Column("parsed_metadata", postgresql.JSONB, nullable=True),
        sa.Column("language", sa.String(16), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("opt_in_email", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("submitter_email", sa.Text, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
    )
    op.create_index("ix_papers_sha256", "papers", ["sha256"])

    # ── reports ────────────────────────────────────────────────────────────────
    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("paper_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("papers.id"), nullable=False),
        sa.Column("status", report_status, nullable=False, server_default="pending"),
        sa.Column("overall_confidence", overall_confidence, nullable=True),
        sa.Column("plain_language_summary", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text, nullable=True),
    )
    op.create_index("ix_reports_paper_id", "reports", ["paper_id"])

    # ── findings ───────────────────────────────────────────────────────────────
    op.create_table(
        "findings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reports.id"), nullable=False),
        sa.Column("agent", agent_name, nullable=False),
        sa.Column("severity", finding_severity, nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("summary", sa.Text, nullable=False),
        sa.Column("evidence", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("requires_human_review", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("status", finding_status, nullable=False, server_default="draft"),
        sa.Column("reviewer_note", sa.Text, nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_findings_report_id", "findings", ["report_id"])
    op.create_index("ix_findings_report_agent", "findings", ["report_id", "agent"])

    # ── human_review_actions ───────────────────────────────────────────────────
    op.create_table(
        "human_review_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("finding_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("findings.id"), nullable=False),
        sa.Column("action", review_action, nullable=False),
        sa.Column("actor", sa.Text, nullable=False, server_default="admin"),
        sa.Column("note", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_human_review_actions_finding_id", "human_review_actions", ["finding_id"])

    # ── external_api_cache ────────────────────────────────────────────────────
    op.create_table(
        "external_api_cache",
        sa.Column("key", sa.Text, primary_key=True),
        sa.Column("value", postgresql.JSONB, nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("ttl_seconds", sa.Integer, nullable=False, server_default="86400"),
    )

    # ── llm_usage ─────────────────────────────────────────────────────────────
    op.create_table(
        "llm_usage",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("request_id", sa.String(64), nullable=False),
        sa.Column("agent", sa.String(64), nullable=False),
        sa.Column("model", sa.String(64), nullable=False),
        sa.Column("prompt_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Float, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_llm_usage_request_id", "llm_usage", ["request_id"])


def downgrade() -> None:
    op.drop_table("llm_usage")
    op.drop_table("external_api_cache")
    op.drop_table("human_review_actions")
    op.drop_table("findings")
    op.drop_table("reports")
    op.drop_table("papers")

    for enum_name in [
        "paper_status", "report_status", "overall_confidence",
        "agent_name", "finding_severity", "finding_status", "review_action",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
