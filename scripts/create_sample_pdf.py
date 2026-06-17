"""
Generate research_sample.pdf — a fake paper with deliberate errors for demo.

Embedded violations:
  GRIM #1 : M=4.2,  n=7   → 4.2*7=29.4 → no integer/7 rounds to 4.2  (impossible)
  GRIM #2 : M=3.67, n=10  → 3.67*10=36.7 → no integer/10 = 3.67       (impossible)
  Stat #1 : t(18)=1.85, reported p<.001  → actual p≈.081  (crosses alpha=.05)
  Stat #2 : F(2,45)=2.10, reported p<.001 → actual p≈.134 (crosses alpha=.05)
  DOI #1  : 10.9999/cogload.2024.fake    → does not exist on Crossref
  DOI #2  : 10.9876/memory.fake.2021     → does not exist on Crossref
"""
import os, sys
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib import colors

OUT = os.path.join(os.path.dirname(__file__), "..", "research_sample.pdf")

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "Title", parent=styles["Title"],
    fontSize=16, spaceAfter=6, alignment=TA_CENTER,
    textColor=colors.HexColor("#1e293b"),
)
author_style = ParagraphStyle(
    "Authors", parent=styles["Normal"],
    fontSize=10, spaceAfter=4, alignment=TA_CENTER,
    textColor=colors.HexColor("#64748b"),
)
section_style = ParagraphStyle(
    "Section", parent=styles["Heading2"],
    fontSize=12, spaceBefore=14, spaceAfter=4,
    textColor=colors.HexColor("#1e293b"),
)
body_style = ParagraphStyle(
    "Body", parent=styles["Normal"],
    fontSize=10, leading=15, spaceAfter=6,
    alignment=TA_JUSTIFY,
)
note_style = ParagraphStyle(
    "Note", parent=styles["Normal"],
    fontSize=8, leading=12,
    textColor=colors.HexColor("#64748b"),
)

CONTENT = [
    Paragraph("Cognitive Load Effects on Academic Performance:<br/>A Randomized Controlled Study", title_style),
    Paragraph("Ahmed Al-Rashid, Sarah M. Johnson, Bilal Chaudhry", author_style),
    Paragraph("Department of Psychology, National University — 2024", author_style),
    Spacer(1, 0.4*cm),

    Paragraph("Abstract", section_style),
    Paragraph(
        "This study examined the effects of cognitive load on academic performance in university "
        "students. Participants (N = 120) were randomly assigned to high-load or low-load conditions "
        "and completed standardized academic tasks. The high-load group showed significantly lower "
        "performance scores (M = 4.2, SD = 1.1, n = 7) compared to the control group "
        "(M = 3.67, SD = 0.9, n = 10). A significant group difference was observed, "
        "t(18) = 1.85, p &lt; .001, d = 0.71. These findings suggest cognitive load substantially "
        "impairs academic performance and have implications for instructional design.",
        body_style,
    ),
    Spacer(1, 0.3*cm),

    Paragraph("1. Introduction", section_style),
    Paragraph(
        "Cognitive load theory (CLT) proposes that working memory has limited capacity, and that "
        "exceeding this capacity impairs learning and performance (Sweller, 1988). Despite extensive "
        "research on CLT in educational settings, few studies have examined its impact on real-time "
        "academic assessments under controlled conditions. The present study addresses this gap by "
        "manipulating cognitive load in a randomized controlled design and measuring its effects "
        "on standardized test performance.",
        body_style,
    ),
    Paragraph(
        "Based on prior findings (Brown et al., 2022; Wilson, 2021), we hypothesized that "
        "participants in the high-load condition would perform significantly worse than those in "
        "the low-load control condition.",
        body_style,
    ),

    Paragraph("2. Method", section_style),
    Paragraph("<b>2.1 Participants</b>", body_style),
    Paragraph(
        "One hundred and twenty undergraduate students (mean age = 20.3 years, SD = 1.8) from a "
        "large urban university participated in exchange for course credit. Participants were randomly "
        "assigned to one of three conditions: high cognitive load (n = 40), moderate cognitive load "
        "(n = 40), or control/low load (n = 40). All participants reported normal or corrected-to-normal "
        "vision and no diagnosed learning disabilities.",
        body_style,
    ),
    Paragraph("<b>2.2 Measures</b>", body_style),
    Paragraph(
        "Academic performance was assessed using a 20-item multiple choice test validated against "
        "course examination scores (alpha = .84). All items were scored on a 7-point difficulty-weighted "
        "Likert scale. Mean performance for the experimental subsample was M = 4.2, SD = 1.1 (n = 7) "
        "and for the control subsample was M = 3.67, SD = 0.8 (n = 10).",
        body_style,
    ),
    Paragraph("<b>2.3 Cognitive Load Manipulation</b>", body_style),
    Paragraph(
        "Cognitive load was induced through a dual-task paradigm: participants maintained a sequence "
        "of digits in working memory while completing the academic performance measure. High-load "
        "participants maintained a 7-digit sequence; low-load participants maintained a 2-digit sequence.",
        body_style,
    ),

    Paragraph("3. Results", section_style),
    Paragraph(
        "Table 1 presents descriptive statistics by condition. The high-load group (M = 4.2, "
        "SD = 1.1, n = 7) scored lower than the control group (M = 3.67, SD = 0.8, n = 10) "
        "on the performance measure.",
        body_style,
    ),
    Paragraph(
        "An independent samples t-test confirmed a statistically significant difference between "
        "conditions, t(18) = 2.40, p &lt; .001, 95% CI [0.18, 0.97], Cohen's d = 0.71. This "
        "large effect size indicates that the cognitive load manipulation had a substantial impact "
        "on academic performance.",
        body_style,
    ),
    Paragraph(
        "A one-way ANOVA across all three conditions also reached significance, "
        "F(2, 45) = 2.10, p &lt; .001, partial eta-squared = .15. Post-hoc Tukey tests "
        "revealed significant differences between the high-load and control conditions "
        "(p = .021) but not between the moderate-load and control conditions (p = .182).",
        body_style,
    ),
    Paragraph(
        "Pearson correlation analysis indicated a moderate negative relationship between "
        "cognitive load score and academic performance, r = -.38 (n = 120), p = .001.",
        body_style,
    ),

    Paragraph("4. Discussion", section_style),
    Paragraph(
        "The results strongly support our hypothesis: cognitive load significantly impaired "
        "academic performance. The significant t-test result, t(18) = 1.85, p &lt; .001, "
        "confirms that even moderate working memory demands can meaningfully disrupt students' "
        "ability to perform academic tasks. These findings are consistent with CLT and extend "
        "prior work by demonstrating effects under ecologically valid assessment conditions.",
        body_style,
    ),
    Paragraph(
        "Limitations include the relatively small subsample sizes for the mean comparisons "
        "and the use of a single university sample, which may limit generalisability.",
        body_style,
    ),

    Paragraph("References", section_style),
    Paragraph("Brown, K., Davis, L., &amp; Patel, N. (2022). Academic performance under stress: "
              "A meta-analysis. <i>Journal of Educational Research, 45</i>(3), 112–128. "
              "doi: 10.1037/edu0000789fake", note_style),
    Spacer(1, 0.15*cm),
    Paragraph("Sweller, J. (1988). Cognitive load during problem solving: Effects on learning. "
              "<i>Cognitive Science, 12</i>(2), 257–285. doi: 10.1207/s15516709cog1202_4", note_style),
    Spacer(1, 0.15*cm),
    Paragraph("Wilson, R. A. (2021). Working memory and academic learning: Current perspectives. "
              "<i>Memory &amp; Cognition, 49</i>(1), 45–61. doi: 10.9876/memory.fake.2021", note_style),
    Spacer(1, 0.15*cm),
    Paragraph("Al-Rashid, A., &amp; Chaudhry, B. (2023). Dual-task interference in assessment contexts. "
              "<i>Applied Cognitive Psychology, 37</i>(4), 890–905. doi: 10.9999/cogload.2024.fake", note_style),
]

def build():
    doc = SimpleDocTemplate(
        OUT,
        pagesize=A4,
        leftMargin=2.5*cm, rightMargin=2.5*cm,
        topMargin=2.5*cm, bottomMargin=2.5*cm,
    )
    doc.build(CONTENT)
    print(f"Created: {os.path.abspath(OUT)}")
    print()
    print("Embedded violations:")
    print("  GRIM #1 : M=4.2,  n=7   -> impossible mean")
    print("  GRIM #2 : M=3.67, n=10  -> impossible mean")
    print("  Stat #1 : t(18)=1.85, reported p<.001 -> actual p~0.081  (NOT significant)")
    print("  Stat #2 : F(2,45)=2.10, reported p<.001 -> actual p~0.134 (NOT significant)")
    print("  DOI #1  : 10.9999/cogload.2024.fake    -> not on Crossref")
    print("  DOI #2  : 10.9876/memory.fake.2021     -> not on Crossref")

if __name__ == "__main__":
    build()
