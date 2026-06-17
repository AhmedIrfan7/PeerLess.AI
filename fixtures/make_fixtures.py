"""
Generate synthetic fixture PDFs for PEERLESS.AI testing.
Run once: python fixtures/make_fixtures.py
All PDFs are synthetic (no copyright issues).
"""
from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

HERE = Path(__file__).parent


def _build_pdf(filename: str, title: str, sections: list[tuple[str, str]]) -> None:
    path = HERE / filename
    doc = SimpleDocTemplate(str(path), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(title, styles["Title"]))
    story.append(Spacer(1, 12))

    for heading, body in sections:
        story.append(Paragraph(heading, styles["Heading1"]))
        story.append(Paragraph(body, styles["BodyText"]))
        story.append(Spacer(1, 8))

    doc.build(story)
    print(f"  Written {path} ({path.stat().st_size:,} bytes)")


def make_clean_paper() -> None:
    _build_pdf(
        "clean_paper.pdf",
        "Efficacy of Mindfulness-Based Stress Reduction in Adults with Chronic Pain: "
        "A Randomised Controlled Trial",
        [
            ("Authors", "Smith J, Patel A, Nguyen R. Department of Psychology, State University."),
            ("Abstract",
             "Background: Chronic pain affects approximately 20% of adults. "
             "Mindfulness-based stress reduction (MBSR) has shown promise in clinical settings. "
             "Methods: We conducted a double-blind RCT with n=120 participants randomised to MBSR (n=60) "
             "or waitlist control (n=60). Primary outcome was pain intensity (VAS, 0–100) at 8 weeks. "
             "Results: MBSR reduced pain intensity (M=42.3, SD=12.1) compared to control (M=58.7, SD=14.3); "
             "t(118) = 6.23, p < .001. Cohen's d = 1.24. "
             "Conclusions: MBSR is an effective adjunct therapy for chronic pain management. "
             "Trial registration: ClinicalTrials.gov NCT04521234."),
            ("Introduction",
             "Chronic pain is a major public health concern. Previous systematic reviews (DOI:10.1016/j.pain.2020.01.001) "
             "indicate heterogeneous outcomes for pharmacological interventions. Non-pharmacological approaches "
             "offer potential benefits with fewer side effects."),
            ("Methods",
             "Participants were recruited from primary care clinics between January and June 2023. "
             "Inclusion criteria: age 18–65, chronic pain > 6 months. "
             "Randomisation: computer-generated allocation, concealed envelopes. "
             "Both assessors and participants were blinded to allocation. "
             "Intervention: 8-week MBSR programme, 2 hours/week. "
             "Statistics: two-sample t-tests; significance threshold alpha = .05."),
            ("Results",
             "120 participants completed the trial (60 per arm; no dropouts). "
             "MBSR group: M=42.3, SD=12.1, n=60. Control group: M=58.7, SD=14.3, n=60. "
             "t(118) = 6.23, p < .001. Effect size Cohen's d = 1.24 (large). "
             "Secondary: anxiety (GAD-7): t(118) = 3.14, p = .002."),
            ("Competing interests", "The authors declare no competing interests."),
            ("Data availability", "Data are available on the Open Science Framework at osf.io/example123."),
            ("References",
             "1. Kabat-Zinn J. Full catastrophe living. New York: Delacorte Press; 1990. "
             "2. Hilton L et al. Mindfulness meditation for chronic pain. Ann Intern Med. 2017; DOI:10.7326/M16-2323. "
             "3. Veehof MM et al. Acceptance-based interventions. Pain. 2016; DOI:10.1016/j.pain.2015.11.003."),
        ],
    )


def make_grim_violation() -> None:
    _build_pdf(
        "grim_violation.pdf",
        "Attitudes Toward Remote Work in Small Organisations: A Survey Study",
        [
            ("Authors", "Brown K, Wilson T. School of Business, Northern College."),
            ("Abstract",
             "We surveyed 11 employees in small organisations about their attitudes toward remote work "
             "using a 5-point Likert scale (1=strongly disagree, 5=strongly agree). "
             "Mean attitude score was M=3.7 (SD=0.9, n=11). "
             "Participants who had prior remote experience scored higher (M=4.2, SD=0.8, n=7) "
             "than those without (M=2.9, SD=0.6, n=4). "
             "A t-test showed t(9) = 2.81, p = .021."),
            ("Methods",
             "Survey instrument: 1-item scale (integer responses 1–5). "
             "Sample: n=11 convenience sample from two small firms. "
             "Analysis: independent samples t-test. "
             "The mean score of 3.7 on an integer scale with n=11 reflects overall positive attitudes."),
            ("Results",
             "Overall attitude: M=3.7, SD=0.9, n=11. "
             "Prior remote experience group: M=4.2, SD=0.8, n=7. "
             "No prior experience group: M=2.9, SD=0.6, n=4. "
             "t(9) = 2.81, p = .021. "
             "Note: all responses were whole-number integers on the 5-point scale."),
            ("References",
             "1. Allen T et al. How effective is telecommuting? Psych Sci Pub Int. 2015; DOI:10.1177/1529100615593273."),
        ],
    )


def make_pvalue_inconsistency() -> None:
    _build_pdf(
        "pvalue_inconsistency.pdf",
        "Colour Priming Effects on Creative Performance: An Experimental Study",
        [
            ("Authors", "Chen L, Morris P. Cognitive Science Laboratory, East University."),
            ("Abstract",
             "We examined whether brief colour exposure affects divergent thinking in a between-subjects experiment. "
             "Participants (N=20) were assigned to red (n=10) or blue (n=10) priming conditions. "
             "Divergent thinking was measured using the Alternate Uses Task. "
             "Results: t(18) = 2.40, p < .001. The blue condition produced significantly more creative responses. "
             "These findings replicate and extend earlier work on environmental colour cues."),
            ("Methods",
             "Between-subjects design. Red condition: n=10. Blue condition: n=10. "
             "DV: number of alternative uses generated in 3 minutes. "
             "Analysis: two-tailed independent samples t-test, alpha = .05. "
             "No pre-registration. Data collected Spring 2023."),
            ("Results",
             "Blue condition: M=14.2, SD=3.1. Red condition: M=11.1, SD=3.4. "
             "t(18) = 2.40, p < .001. The result is significant at the .05 level. "
             "Cohen's d = 0.95."),
            ("References",
             "1. Mehta R, Zhu RJ. Blue or red? Exploring the effect of color on cognitive task performances. "
             "Science. 2009; DOI:10.1126/science.1169144."),
        ],
    )


def make_bad_citation() -> None:
    _build_pdf(
        "bad_citation.pdf",
        "Social Media Use and Adolescent Sleep Quality: A Cross-Sectional Analysis",
        [
            ("Authors", "Garcia M, Thompson S. Public Health Department, West University."),
            ("Abstract",
             "We examined associations between social media use duration and sleep quality among 150 adolescents "
             "aged 14–18. Sleep quality was measured with the Pittsburgh Sleep Quality Index (PSQI). "
             "Correlation between daily social media hours and PSQI score: r = 0.42 (n=150, p < .001). "
             "Findings suggest that higher social media use is associated with poorer sleep quality."),
            ("Methods",
             "Cross-sectional survey. N=150 high school students. "
             "Measures: self-reported daily social media hours; PSQI total score. "
             "Analysis: Pearson correlation."),
            ("Results",
             "Mean social media use: M=3.8 hours/day (SD=1.4). "
             "Mean PSQI: M=7.2 (SD=2.1). "
             "Pearson r = 0.42, n=150, p < .001."),
            ("References",
             "1. Twenge JM et al. Increases in depressive symptoms among US adolescents. "
             "Clinical Psychological Science. 2018; DOI:10.1177/2167702617723376. "
             "2. Lemola S et al. Adolescents' electronic media use at night. "
             "J Youth Adolesc. 2015; DOI:10.1007/s10964-014-0173-8. "
             "3. Phantom Reference X. Nonexistent study on blue light. "
             "Fake Journal. 2021; DOI:10.9999/this-doi-does-not-exist."),
        ],
    )


if __name__ == "__main__":
    print("Generating fixture PDFs...")
    make_clean_paper()
    make_grim_violation()
    make_pvalue_inconsistency()
    make_bad_citation()
    print("Done.")
