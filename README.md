# PEERLESS.AI

> Multi-agent scientific peer-review and research-integrity tool.
> Built for National AI Hackathon '26 — Atom Camp / FAST NUCES Islamabad.

PEERLESS.AI surfaces potential integrity concerns in research papers using seven automated agents.
It does **not** make definitive judgements — all findings require human expert review before any action.

## Live Demo

Deployed on Streamlit Community Cloud:
[share.streamlit.io/AhmedIrfan7/PeerLess.AI](https://share.streamlit.io/AhmedIrfan7/PeerLess.AI/main/streamlit_app.py)

## Quick Start (Streamlit)

```bash
git clone https://github.com/AhmedIrfan7/PeerLess.AI.git
cd PeerLess.AI
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Add secrets in `.streamlit/secrets.toml`:
```toml
GROQ_API_KEY = "gsk_..."          # required for Plain Language Summary
CROSSREF_MAILTO = "you@email.com" # recommended for Crossref polite pool
```

Upload `research_sample.pdf` (included in the repo) to see all seven agents in action.

## Seven Agents

| # | Agent | Method | Needs API |
|---|-------|--------|-----------|
| 1 | **Statistical Integrity** | GRIM check + statcheck p-value recomputation | No |
| 2 | **Citation Verifier** | DOI extraction + Crossref lookup | No (rate-limited) |
| 3 | **Reproducibility Checker** | 5-dimension keyword scoring | No |
| 4 | **Methodology Auditor** | CONSORT / STROBE / PRISMA / ARRIVE checklist | No |
| 5 | **Replication Predictor** | 7-feature heuristic score (OSC 2015 base rates) | No |
| 6 | **COI Detector** | Conflict-of-interest and funding signal scan | No |
| 7 | **Plain Language Summary** | Groq LLaMA-3.3-70b | Yes (Groq) |

## Demo Paper

`research_sample.pdf` contains deliberate violations for demo purposes:

| Violation | Type | Expected Finding |
|-----------|------|-----------------|
| M=4.2, n=7 | GRIM | Impossible mean — HIGH |
| M=3.67, n=10 | GRIM | Impossible mean — HIGH |
| t(18)=1.85, p<.001 | statcheck | p≈0.081, not significant — HIGH |
| F(2,45)=2.10, p<.001 | statcheck | p≈0.134, not significant — HIGH |
| doi:10.9999/cogload.2024.fake | Citation | DOI not found — HIGH |
| doi:10.9876/memory.fake.2021 | Citation | DOI not found — HIGH |

## Stack

| Layer | Technology |
|-------|-----------|
| App | Python 3.11, Streamlit |
| Stats | scipy, decimal (GRIM) |
| Citations | Crossref REST API (httpx/requests) |
| LLM | Groq API — LLaMA-3.3-70b-versatile |
| PDF parse | pypdf |
| PDF export | reportlab |
| Deployment | Streamlit Community Cloud (free) |

## Project Structure

```
PeerLess.AI/
├── streamlit_app.py        — Main app (all 7 agents inlined)
├── requirements.txt        — Streamlit Cloud dependencies
├── research_sample.pdf     — Demo paper with deliberate violations
├── scripts/
│   └── create_sample_pdf.py — Regenerate demo paper
├── .streamlit/
│   ├── config.toml         — Theme (indigo, light)
│   └── secrets.toml        — API keys (never committed)
├── apps/backend/           — FastAPI backend (original architecture, not deployed)
└── docs/                   — Architecture and safety docs
```

## Safety Notice

PEERLESS.AI surfaces possible concerns for expert review. It does not adjudicate misconduct.
Findings are not conclusions. All flagged items require verification by a qualified human reviewer.
See [docs/SAFETY.md](docs/SAFETY.md).

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `No text extracted` | PDF is a scanned image — OCR not supported; use a text-based PDF |
| Plain Language Summary blank | Set `GROQ_API_KEY` in `.streamlit/secrets.toml` |
| Crossref timeout | Network issue or rate limit; statistical and reproducibility checks still run |
| `ImportError: reportlab` | Run `pip install reportlab>=4.0.0` or re-run `pip install -r requirements.txt` |
| PDF export button missing | reportlab failed silently — check terminal logs |
