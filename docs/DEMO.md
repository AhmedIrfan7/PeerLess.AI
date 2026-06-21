# PEERLESS.AI — Demo Runbook

Scripted 6–8 minute live demo for the National AI Hackathon '26.

## Pre-Demo Checklist (run 10 minutes before)

- [ ] Open the Streamlit app URL in a browser tab
- [ ] Confirm `research_sample.pdf` is ready on your desktop
- [ ] Confirm the Groq API key is configured (Plain Language Summary agent needs it)
- [ ] Zoom browser to 125% for audience visibility
- [ ] Clear any previous upload results

## Click-by-Click Demo Flow

### Opening (Member 1 — 1 min)

1. Open the app. Read the disclaimer aloud:
   > "PEERLESS.AI surfaces potential concerns — it does not make definitive judgements.
   > All flagged items require human expert review."

2. Point to the sidebar — show the seven agents listed and explain the architecture:
   - Statistical Integrity, Citation Verifier, Reproducibility (no LLM needed)
   - Methodology Auditor, Replication Predictor, COI Detector (pure text analysis)
   - Plain Language Summary (uses Groq LLaMA-3.3)

3. Click "What does PEERLESS.AI check?" to expand the description. Read it briefly.

---

### Upload and Run (Member 2 — 2 min)

4. Upload `research_sample.pdf` (drag-and-drop or file picker).
   - File loads instantly. Confirm file name and size appear.

5. Click **Run Peer Review** (primary button).
   - Watch the progress bar advance through 7 agents.
   - Citation Verifier may take 5–10s (live Crossref API).

6. When done, point to the **Results** row:
   - Total Findings, Flagged Issues, High Severity, Medium Severity
   - Reproducibility score, Overall Confidence

---

### Statistical Integrity (Member 2 — 1 min)

7. Click **Statistical Integrity** tab.

8. Point to the two GRIM violations:
   > "M=4.2, n=7 — this mean is mathematically impossible. No integer sum divided by 7
   > rounds to 4.2. This is the GRIM test — it uses pure arithmetic, no LLM."

9. Point to the two statcheck violations:
   > "t(18)=1.85, reported p<.001 — but the actual p-value is 0.081. This result is
   > NOT significant at alpha=0.05. The paper's significance claim is wrong."

---

### Citation Verifier + Reproducibility (Member 3 — 1 min)

10. Click **Citation Verifier** tab.
    - Point to two HIGH-severity findings: DOIs that returned 404 from Crossref.
    > "These references don't exist. We query the real Crossref API live, right now."

11. Click **Reproducibility** tab.
    - Show the 0/5 or low score (the demo paper has no data/code/pre-reg).
    > "The paper shares no data, no code, no pre-registration. Reproducibility score: 0/5."

---

### New Agents (Member 3 — 1 min)

12. Click **Methodology Auditor** tab.
    - Show the detected study type (General) and missing checklist items.

13. Click **Replication Predictor** tab.
    - Show the score and estimated probability.
    > "Based on 7 features from the replication crisis literature, we estimate a ~25% chance
    > this paper would replicate."

14. Click **COI Detector** tab.
    - Show whether a conflict of interest section is present.

---

### Plain Language Summary (Member 1 — 30 sec)

15. Click **Plain Language Summary** tab.
    - Show the AI-generated summary from LLaMA-3.3.
    > "This is the only agent that uses an LLM. The other six run entirely on math
    > and keyword matching — no GPU required, no API cost per paper."

---

### PDF Export (Member 1 — 30 sec)

16. Click **Download PDF Report**.
    - Open the downloaded PDF.
    - Point to the disclaimer banner on every page.
    - Show that all findings are listed with severity labels.
    > "Reviewers get a downloadable, printable report they can share with their team."

---

### Close (Any member — 30 sec)

17. Final statement:
    > "PEERLESS.AI catches issues that take a human reviewer hours to find — impossible
    > means, wrong p-values, fake citations — in under 30 seconds. Every flag still needs
    > a human to confirm. We give reviewers a head start, not a verdict."

---

## Violations in research_sample.pdf (the 'caught' problems per agent)

| Agent | Violation | Expected finding |
|-------|-----------|-----------------|
| Statistical Integrity | M=4.2, n=7 | GRIM: impossible mean — **HIGH** |
| Statistical Integrity | M=3.67, n=10 | GRIM: impossible mean — **HIGH** |
| Statistical Integrity | t(18)=1.85, p<.001 | statcheck: actual p=0.081 — **HIGH** |
| Statistical Integrity | F(2,45)=2.10, p<.001 | statcheck: actual p=0.134 — **HIGH** |
| Citation Verifier | doi:10.9999/cogload.2024.fake | 404 from Crossref — **HIGH** |
| Citation Verifier | doi:10.9876/memory.fake.2021 | 404 from Crossref — **HIGH** |
| Reproducibility | No data/code/pre-reg | Score 0–1/5 — **MEDIUM** |
| Methodology Auditor | No CONSORT items detected | Missing checklist items — **MEDIUM** |
| Replication Predictor | No pre-registration, no effect size | Low score — **LOW** |
| COI Detector | No COI disclosure section | Missing disclosure — **MEDIUM** |

---

## Fallback Plan

If the Streamlit app is unavailable during the demo:
1. Use a screen recording made the day before as a fallback video.
2. Walk through the code in `streamlit_app.py` to explain each agent's logic.
3. Demo the GRIM check manually: `M=4.2, n=7 → round(4.2×7)=29 → 29÷7=4.142... ≠ 4.2`

## Tech Q&A Prep

| Question | Answer |
|----------|--------|
| "How does GRIM work?" | Pure arithmetic: round(M×n)/n must equal M. No LLM. |
| "How do you check p-values?" | scipy.stats recomputes from t/F/chi2 statistics. No LLM. |
| "How do you verify citations?" | Live Crossref API call. If DOI returns 404, it doesn't exist. |
| "Why not use GPT-4 for everything?" | Deterministic math is more reliable and auditable than LLMs for numeric checks. |
| "Can it detect plagiarism?" | Not in this version — out of scope for the hackathon MVP. |
| "What's the cost per paper?" | ~$0.001 (6 agents free, LLM ~$0.001 for summary). |
