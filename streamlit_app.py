"""PEERLESS.AI - Multi-agent scientific peer-review assistant"""
from __future__ import annotations
import io, re, math, requests
import streamlit as st
from scipy import stats as sp

st.set_page_config(page_title="PEERLESS.AI", page_icon="magnifying_glass", layout="wide")

# ── Secrets ───────────────────────────────────────────────────────────────────
def _secret(key: str, default: str = "") -> str:
    try:
        return st.secrets[key]
    except Exception:
        return default

GROQ_KEY = _secret("GROQ_API_KEY")
CROSSREF_MAILTO = _secret("CROSSREF_MAILTO", "demo@example.com")
GROQ_BASE = "https://api.groq.com/openai/v1"
SMART_MODEL = "llama-3.3-70b-versatile"

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.finding-high   {border-left:4px solid #ef4444;background:#fef2f2;padding:12px 16px;border-radius:6px;margin:6px 0}
.finding-medium {border-left:4px solid #f59e0b;background:#fffbeb;padding:12px 16px;border-radius:6px;margin:6px 0}
.finding-low    {border-left:4px solid #3b82f6;background:#eff6ff;padding:12px 16px;border-radius:6px;margin:6px 0}
.finding-info   {border-left:4px solid #9ca3af;background:#f9fafb;padding:12px 16px;border-radius:6px;margin:6px 0}
.badge {padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;color:white}
.badge-high{background:#ef4444}.badge-medium{background:#f59e0b}
.badge-low{background:#3b82f6}.badge-info{background:#9ca3af}
h1{margin-bottom:0!important}
</style>
""", unsafe_allow_html=True)

# ── PDF ───────────────────────────────────────────────────────────────────────
def extract_text(pdf_bytes: bytes) -> str:
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(pdf_bytes))
        return "\n".join(p.extract_text() or "" for p in reader.pages)
    except Exception as e:
        st.error(f"PDF parse error: {e}")
        return ""

# ── GRIM ─────────────────────────────────────────────────────────────────────
def grim_check(mean_str: str, n: int) -> bool:
    try:
        M = float(mean_str)
        d = len(mean_str.split(".")[-1]) if "." in mean_str else 0
        S = round(M * n)
        return round(S / n, d) == M
    except Exception:
        return True

# ── Statcheck ─────────────────────────────────────────────────────────────────
def recompute_p(stat_type: str, value: float, df1: int,
                df2: int | None = None, n: int | None = None) -> float | None:
    try:
        if stat_type == "t":
            return float(2 * sp.t.sf(abs(value), df1))
        if stat_type == "F":
            return float(sp.f.sf(value, df1, df2))
        if stat_type == "chi2":
            return float(sp.chi2.sf(value, df1))
        if stat_type == "r" and n:
            t = value * math.sqrt((n - 2) / max(1e-10, 1 - value ** 2))
            return float(2 * sp.t.sf(abs(t), n - 2))
    except Exception:
        pass
    return None

# ── Regex extractors ──────────────────────────────────────────────────────────
_MEAN_RE  = re.compile(r'M\s*=\s*(\d+\.\d+)[^.]*?[nN]\s*=\s*(\d+)', re.I)
_TTEST_RE = re.compile(r't\s*\(\s*(\d+)\s*\)\s*=\s*(-?\d+\.?\d*)\s*[,;]\s*p\s*([<>=]\s*\.?\d+)', re.I)
_FTEST_RE = re.compile(r'F\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)\s*=\s*(\d+\.?\d*)\s*[,;]\s*p\s*([<>=]\s*\.?\d+)', re.I)
_CHI2_RE  = re.compile(r'[xXχ]2?\s*\(\s*(\d+)\s*\)\s*=\s*(\d+\.?\d*)\s*[,;]\s*p\s*([<>=]\s*\.?\d+)', re.I)
_DOI_RE   = re.compile(r'10\.\d{4,9}/[^\s,;)\]"]+')

def _parse_p(s: str) -> float | None:
    s = re.sub(r'[<>=\s]', '', s)
    if s.startswith("."):
        s = "0" + s
    try:
        return float(s)
    except Exception:
        return None

def extract_dois(text: str) -> list[str]:
    return list(dict.fromkeys(d.rstrip(".,;)") for d in _DOI_RE.findall(text)))

# ── LLM ───────────────────────────────────────────────────────────────────────
def call_groq(prompt: str) -> str:
    if not GROQ_KEY:
        return ""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=GROQ_KEY, base_url=GROQ_BASE)
        r = client.chat.completions.create(
            model=SMART_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1200,
            temperature=0.1,
        )
        return r.choices[0].message.content or ""
    except Exception:
        return ""

# ── Agent 1: Statistical Integrity ───────────────────────────────────────────
def run_statistical_agent(text: str) -> list[dict]:
    findings: list[dict] = []

    for m in _MEAN_RE.finditer(text):
        mean_str, n = m.group(1), int(m.group(2))
        if not grim_check(mean_str, n):
            findings.append(dict(
                severity="high", agent="Statistical Integrity",
                title=f"GRIM inconsistency: M={mean_str}, n={n}",
                detail=(f"No integer sum divided by {n} can round to {mean_str}. "
                        "This mean is arithmetically impossible given the reported sample size."),
                flag=True,
            ))

    stat_claims = []
    for m in _TTEST_RE.finditer(text):
        stat_claims.append(dict(type="t", df=int(m.group(1)), val=float(m.group(2)),
                                p_str=m.group(3), raw=m.group(0)[:70]))
    for m in _FTEST_RE.finditer(text):
        stat_claims.append(dict(type="F", df1=int(m.group(1)), df2=int(m.group(2)),
                                val=float(m.group(3)), p_str=m.group(4), raw=m.group(0)[:70]))
    for m in _CHI2_RE.finditer(text):
        stat_claims.append(dict(type="chi2", df=int(m.group(1)), val=float(m.group(2)),
                                p_str=m.group(3), raw=m.group(0)[:70]))

    for c in stat_claims:
        p_rep = _parse_p(c["p_str"])
        if p_rep is None:
            continue
        if c["type"] == "t":
            p_calc = recompute_p("t", c["val"], c["df"])
        elif c["type"] == "F":
            p_calc = recompute_p("F", c["val"], c["df1"], c["df2"])
        else:
            p_calc = recompute_p("chi2", c["val"], c["df"])
        if p_calc is None:
            continue
        diff = abs(p_calc - p_rep)
        crosses = (p_rep < 0.05) != (p_calc < 0.05)
        if crosses:
            findings.append(dict(
                severity="high", agent="Statistical Integrity",
                title=f"Significance error: {c['raw']}",
                detail=(f"Reported p={p_rep:.4f}, recomputed p={p_calc:.4f}. "
                        "The significance conclusion changes at alpha=0.05."),
                flag=True,
            ))
        elif diff > 0.01:
            findings.append(dict(
                severity="medium", agent="Statistical Integrity",
                title=f"p-value inconsistency: {c['raw']}",
                detail=f"Reported p={p_rep:.4f}, recomputed p={p_calc:.4f} (difference={diff:.4f}).",
                flag=True,
            ))

    if not findings:
        findings.append(dict(
            severity="info", agent="Statistical Integrity",
            title="No statistical inconsistencies detected",
            detail="GRIM check and p-value recomputation found no issues in the extracted statistics.",
            flag=False,
        ))
    return findings

# ── Agent 2: Citation Verifier ────────────────────────────────────────────────
def run_citation_agent(text: str) -> list[dict]:
    dois = extract_dois(text)
    if not dois:
        return [dict(severity="info", agent="Citation Verifier",
                     title="No DOIs found in paper",
                     detail="No DOI patterns (10.xxxx/...) were detected in the text.",
                     flag=False)]
    findings: list[dict] = []
    for doi in dois[:15]:
        try:
            r = requests.get(
                f"https://api.crossref.org/works/{doi}",
                headers={"User-Agent": f"PEERLESS.AI/1.0 (mailto:{CROSSREF_MAILTO})"},
                timeout=5,
            )
            if r.status_code == 200:
                title = (r.json()["message"].get("title") or [""])[0]
                findings.append(dict(
                    severity="info", agent="Citation Verifier",
                    title=f"DOI verified: {doi}",
                    detail=f"Title: {title[:120] or '(no title)'}",
                    flag=False,
                ))
            elif r.status_code == 404:
                findings.append(dict(
                    severity="high", agent="Citation Verifier",
                    title=f"DOI not found: {doi}",
                    detail="Crossref returned 404. This reference may be fabricated, mistyped, or unregistered.",
                    flag=True,
                ))
            else:
                findings.append(dict(
                    severity="low", agent="Citation Verifier",
                    title=f"DOI check inconclusive: {doi}",
                    detail=f"Crossref returned HTTP {r.status_code}.",
                    flag=False,
                ))
        except Exception:
            findings.append(dict(
                severity="low", agent="Citation Verifier",
                title=f"DOI check timed out: {doi}",
                detail="Network request to Crossref timed out.",
                flag=False,
            ))
    return findings

# ── Agent 3: Plain Language Summary ──────────────────────────────────────────
def run_pls_agent(text: str) -> str:
    if not GROQ_KEY:
        return "_No API key configured. Add GROQ\\_API\\_KEY in Streamlit secrets to enable this agent._"
    result = call_groq(
        f"Write a 3-paragraph plain-language summary of this research paper for a general audience. "
        f"No jargon. Cover: what was studied, what was found, why it matters.\n\n"
        f"Paper (first 4000 chars):\n{text[:4000]}\n\nPlain language summary:"
    )
    return result or "_Summary generation failed. Check API key._"

# ── Agent 4: Reproducibility Checker ─────────────────────────────────────────
_REPRO_CHECKS = [
    (
        "Data Availability",
        [r"data\s+avail", r"dataset\s+avail", r"zenodo", r"figshare", r"osf\.io",
         r"dryad", r"raw\s+data", r"data\s+deposit", r"data\s+are\s+avail"],
        "No data availability statement found. Readers cannot access or verify the raw data.",
    ),
    (
        "Code / Software",
        [r"code\s+avail", r"analysis\s+code", r"github\.com", r"gitlab\.com",
         r"spss", r"r\s+version\s+\d", r"python\s+\d", r"matlab", r"stata"],
        "No analysis code or software version mentioned. The analysis cannot be independently reproduced.",
    ),
    (
        "Pre-registration",
        [r"pre.?regist", r"osf\.io/\w", r"clinicaltrials\.gov", r"aspredicted",
         r"registered\s+report", r"prior\s+to\s+data\s+collect"],
        "No pre-registration found. Hypotheses may have been decided after seeing the data (HARKing).",
    ),
    (
        "Power Analysis",
        [r"power\s+anal", r"sample\s+size\s+calc", r"a\s+priori", r"g\*?power",
         r"80%?\s+power", r"\.80\s+power", r"effect\s+size.*sampl"],
        "No power analysis found. The study may be underpowered and results unreliable.",
    ),
    (
        "Materials & Procedure Detail",
        [r"stimul[ui]", r"questionnaire", r"instrument", r"appendix", r"supplementar",
         r"items?\s+were", r"scale\s+consist", r"procedure\s+was", r"measure[sd]?\s+using"],
        "Materials and procedure are not described in enough detail to replicate this study.",
    ),
]

def run_reproducibility_agent(text: str) -> tuple[int, list[dict]]:
    text_lower = text.lower()
    score = 0
    findings: list[dict] = []
    for label, patterns, fail_msg in _REPRO_CHECKS:
        passed = any(re.search(p, text_lower) for p in patterns)
        if passed:
            score += 1
            findings.append(dict(
                severity="info", agent="Reproducibility",
                title=f"{label}: Present",
                detail=f"Paper includes {label.lower()} information.",
                flag=False,
            ))
        else:
            findings.append(dict(
                severity="medium", agent="Reproducibility",
                title=f"{label}: Missing",
                detail=fail_msg,
                flag=True,
            ))
    return score, findings

# ── Render finding card ───────────────────────────────────────────────────────
def render_finding(f: dict):
    sev = f.get("severity", "info")
    flag_note = " &nbsp;<em>Flagged for review</em>" if f.get("flag") else ""
    st.markdown(
        f'<div class="finding-{sev}">'
        f'<span class="badge badge-{sev}">{sev.upper()}</span>&nbsp; '
        f'<strong>{f["title"]}</strong>{flag_note}<br>'
        f'<small style="color:#555;margin-top:4px;display:block">{f["detail"]}</small>'
        f'</div>',
        unsafe_allow_html=True,
    )

# ── App ───────────────────────────────────────────────────────────────────────
def main():
    st.markdown("# PEERLESS.AI")
    st.markdown("**Multi-agent scientific peer-review assistant** &nbsp;·&nbsp; National AI Hackathon '26 &nbsp;·&nbsp; Atom Camp / FAST NUCES Islamabad", unsafe_allow_html=True)
    st.divider()

    with st.sidebar:
        st.markdown("### Agents")
        st.markdown("""
| Agent | Status |
|-------|--------|
| Statistical Integrity | Always on |
| Citation Verifier | Always on |
| Reproducibility Checker | Always on |
| Plain Language Summary | Needs API key |
""")
        st.markdown("---")
        st.markdown("### How it works")
        st.markdown("""
1. Upload a research paper PDF
2. Four agents analyse it in parallel
3. Review flagged concerns
4. All findings require **human approval** before any action
""")
        st.markdown("---")
        llm_ok = bool(GROQ_KEY)
        st.markdown(f"**LLM:** {'Active (Groq LLaMA-3.3)' if llm_ok else 'No key — stat checks still run'}")

    uploaded = st.file_uploader("Upload a research paper (PDF)", type=["pdf"], label_visibility="visible")

    if not uploaded:
        st.info("Upload a PDF research paper above to start automated peer review.")
        with st.expander("What does PEERLESS.AI check?"):
            st.markdown("""
**Statistical Integrity Agent**
- GRIM test: checks if reported means are arithmetically possible given the sample size
- Statcheck: recomputes p-values from test statistics (t, F, chi-squared) and compares to reported values

**Citation Verifier Agent**
- Extracts all DOIs from the paper
- Queries Crossref API to confirm each DOI resolves to a real publication

**Reproducibility Checker Agent**
- Scores the paper 0–5 across five dimensions: data availability, code availability, pre-registration, power analysis, and materials detail

**Plain Language Summary Agent**
- Uses Groq LLaMA-3.3 to generate a jargon-free summary for non-expert reviewers

*All findings are flagged for human review — PEERLESS.AI never makes definitive accusations.*
""")
        return

    st.success(f"Loaded: **{uploaded.name}** ({uploaded.size / 1024:.1f} KB)")

    if not st.button("Run Peer Review", type="primary", use_container_width=True):
        return

    pdf_bytes = uploaded.read()

    with st.spinner("Extracting text from PDF..."):
        text = extract_text(pdf_bytes)

    if not text.strip():
        st.error("Could not extract text. Make sure the PDF is text-based (not a scanned image).")
        return

    st.caption(f"Extracted {len(text):,} characters from {uploaded.name}")

    prog = st.progress(0, text="Running agents...")

    with st.spinner("Agent 1/4 — Statistical Integrity (GRIM + statcheck)..."):
        stat_findings = run_statistical_agent(text)
    prog.progress(25, text="Agent 2/4 — Citation Verifier...")

    with st.spinner("Agent 2/4 — Citation Verifier (Crossref)..."):
        cite_findings = run_citation_agent(text)
    prog.progress(50, text="Agent 3/4 — Reproducibility Checker...")

    with st.spinner("Agent 3/4 — Reproducibility Checker..."):
        repro_score, repro_findings = run_reproducibility_agent(text)
    prog.progress(75, text="Agent 4/4 — Plain Language Summary...")

    with st.spinner("Agent 4/4 — Plain Language Summary (Groq LLaMA)..."):
        pls = run_pls_agent(text)
    prog.progress(100, text="Done")

    all_findings = stat_findings + cite_findings + repro_findings
    flagged = [f for f in all_findings if f.get("flag")]
    high = sum(1 for f in flagged if f["severity"] == "high")
    medium = sum(1 for f in flagged if f["severity"] == "medium")

    if repro_score >= 4:
        repro_color = "green"
    elif repro_score >= 2:
        repro_color = "orange"
    else:
        repro_color = "red"

    st.markdown("### Results")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Findings", len(all_findings))
    c2.metric("Flagged Issues", len(flagged))
    c3.metric("High Severity", high)
    c4.metric("Medium Severity", medium)
    c5.metric("Reproducibility", f"{repro_score}/5")

    tab1, tab2, tab3, tab4 = st.tabs([
        "Statistical Integrity", "Citation Verifier",
        "Reproducibility", "Plain Language Summary"
    ])

    with tab1:
        st.markdown(f"**{len(stat_findings)} finding(s)**")
        for f in sorted(stat_findings, key=lambda x: ["high", "medium", "low", "info"].index(x["severity"])):
            render_finding(f)

    with tab2:
        n_dois = len(extract_dois(text))
        st.markdown(f"**{n_dois} DOI(s) found &nbsp;·&nbsp; {len(cite_findings)} finding(s)**", unsafe_allow_html=True)
        for f in sorted(cite_findings, key=lambda x: ["high", "medium", "low", "info"].index(x["severity"])):
            render_finding(f)

    with tab3:
        filled = "█" * repro_score
        empty = "░" * (5 - repro_score)
        st.markdown(
            f"#### Reproducibility Score: "
            f"<span style='color:{repro_color};font-size:1.3em'><b>{repro_score}/5</b></span> "
            f"&nbsp; <span style='letter-spacing:3px;font-size:1.2em'>{filled}{empty}</span>",
            unsafe_allow_html=True,
        )
        st.caption("Checks: data availability · code availability · pre-registration · power analysis · materials detail")
        st.markdown("")
        for f in repro_findings:
            render_finding(f)

    with tab4:
        st.markdown("#### Plain Language Summary")
        st.markdown(pls)

    st.divider()
    st.caption("All findings require human expert review before any action is taken. "
               "PEERLESS.AI surfaces potential concerns — it does not make definitive judgements.")


main()
