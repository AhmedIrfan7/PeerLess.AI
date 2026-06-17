"""PDF report generation via reportlab."""
from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

_SEVERITY_HEX = {
    "high": colors.HexColor("#FEE2E2"),
    "medium": colors.HexColor("#FFEDD5"),
    "low": colors.HexColor("#FEF3C7"),
    "info": colors.HexColor("#F1F5F9"),
}
_SEVERITY_TEXT = {
    "high": colors.HexColor("#B91C1C"),
    "medium": colors.HexColor("#C2410C"),
    "low": colors.HexColor("#B45309"),
    "info": colors.HexColor("#475569"),
}
_CONFIDENCE_HEX = {
    "high": colors.HexColor("#16A34A"),
    "medium": colors.HexColor("#D97706"),
    "low": colors.HexColor("#DC2626"),
}


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title", parent=base["Heading1"], fontSize=18, textColor=colors.HexColor("#1E293B"), spaceAfter=4),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontSize=12, textColor=colors.HexColor("#334155"), spaceAfter=4),
        "body": ParagraphStyle("body", parent=base["Normal"], fontSize=9, textColor=colors.HexColor("#334155"), leading=13),
        "small": ParagraphStyle("small", parent=base["Normal"], fontSize=8, textColor=colors.HexColor("#64748B"), leading=11),
        "disclaimer": ParagraphStyle("disclaimer", parent=base["Normal"], fontSize=8, textColor=colors.HexColor("#92400E"), leading=11, backColor=colors.HexColor("#FFFBEB"), borderPadding=(4, 4, 4, 4)),
        "finding_title": ParagraphStyle("finding_title", parent=base["Normal"], fontSize=9, textColor=colors.HexColor("#1E293B"), leading=12, fontName="Helvetica-Bold"),
        "mono": ParagraphStyle("mono", parent=base["Code"], fontSize=7.5, textColor=colors.HexColor("#475569"), leading=10),
    }


def generate_pdf(
    report: dict[str, Any],
    paper: dict[str, Any],
    findings: list[dict[str, Any]],
) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="PEERLESS.AI Integrity Report",
    )

    s = _styles()
    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph("PEERLESS.AI — Integrity Report", s["title"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1")))
    story.append(Spacer(1, 0.3 * cm))

    meta_rows = [
        ["Report ID", str(report.get("id", ""))],
        ["Paper", paper.get("title") or paper.get("original_filename", "—")],
    ]
    if paper.get("authors"):
        authors = paper["authors"]
        if isinstance(authors, list):
            authors = ", ".join(authors)
        meta_rows.append(["Authors", authors[:120] + ("…" if len(authors) > 120 else "")])
    if paper.get("doi"):
        meta_rows.append(["DOI", paper["doi"]])

    completed = report.get("completed_at")
    if completed:
        try:
            dt = datetime.fromisoformat(completed.replace("Z", "+00:00"))
            meta_rows.append(["Generated", dt.strftime("%Y-%m-%d %H:%M UTC")])
        except ValueError:
            pass

    confidence = report.get("overall_confidence", "—")
    conf_color = _CONFIDENCE_HEX.get(confidence, colors.HexColor("#475569"))
    meta_rows.append(["Overall Confidence", confidence.upper() if confidence else "—"])

    meta_table = Table(
        [[Paragraph(k, s["small"]), Paragraph(v, s["body"])] for k, v in meta_rows],
        colWidths=[3.5 * cm, None],
    )
    meta_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#64748B")),
        ("TEXTCOLOR", (-1, len(meta_rows) - 1), (-1, len(meta_rows) - 1), conf_color),
        ("FONTNAME", (-1, len(meta_rows) - 1), (-1, len(meta_rows) - 1), "Helvetica-Bold"),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.4 * cm))

    # ── Disclaimer ────────────────────────────────────────────────────────────
    story.append(Paragraph(
        "PEERLESS.AI surfaces possible concerns in a paper for expert review. "
        "It does not adjudicate misconduct. Findings are flagged concerns pending human review — not conclusions.",
        s["disclaimer"],
    ))
    story.append(Spacer(1, 0.5 * cm))

    # ── Plain language summary ─────────────────────────────────────────────────
    pls = report.get("plain_language_summary")
    if pls:
        story.append(Paragraph("Plain-Language Summary", s["h2"]))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E2E8F0")))
        story.append(Spacer(1, 0.2 * cm))
        for para in pls.split("\n\n"):
            para = para.strip()
            if para:
                story.append(Paragraph(para.replace("\n", " "), s["body"]))
                story.append(Spacer(1, 0.15 * cm))
        story.append(Paragraph(
            "This summary is generated by AI for reader convenience and is not a substitute for the paper itself.",
            s["small"],
        ))
        story.append(Spacer(1, 0.5 * cm))

    # ── Findings ──────────────────────────────────────────────────────────────
    if findings:
        story.append(Paragraph(f"Findings ({len(findings)})", s["h2"]))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E2E8F0")))
        story.append(Spacer(1, 0.2 * cm))

        for f in sorted(findings, key=lambda x: {"high": 0, "medium": 1, "low": 2, "info": 3}.get(x.get("severity", "info"), 4)):
            sev = f.get("severity", "info")
            bg = _SEVERITY_HEX.get(sev, _SEVERITY_HEX["info"])
            tc = _SEVERITY_TEXT.get(sev, _SEVERITY_TEXT["info"])
            agent_label = f.get("agent", "").replace("_", " ").title()
            status = f.get("status", "draft")
            conf_pct = int(float(f.get("confidence", 0)) * 100)

            header_data = [[
                Paragraph(f"<b>{sev.upper()}</b>", ParagraphStyle("sev", fontSize=8, textColor=tc, fontName="Helvetica-Bold")),
                Paragraph(agent_label, s["small"]),
                Paragraph(f"{conf_pct}% confidence · {status}", s["small"]),
            ]]
            header_table = Table(header_data, colWidths=[1.5 * cm, 5 * cm, None])
            header_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, 0), bg),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
            ]))

            story.append(header_table)
            story.append(Paragraph(f.get("title", ""), s["finding_title"]))
            story.append(Spacer(1, 0.1 * cm))
            story.append(Paragraph(f.get("summary", ""), s["body"]))

            if f.get("reviewer_note"):
                story.append(Paragraph(f"Reviewer note: {f['reviewer_note']}", s["small"]))

            story.append(Spacer(1, 0.3 * cm))

    else:
        story.append(Paragraph("No concerns flagged by any agent.", s["body"]))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1")))
    story.append(Spacer(1, 0.15 * cm))
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    story.append(Paragraph(
        f"Generated by PEERLESS.AI on {now}. "
        "AI-assisted analysis for expert review only. Not for publication without independent verification.",
        s["small"],
    ))

    doc.build(story)
    return buf.getvalue()
