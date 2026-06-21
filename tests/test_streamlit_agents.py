"""
Step(64): Tests on critical paths — GRIM, statcheck, confidence scoring, COI, reproducibility.
These test the pure-math and keyword-matching logic inlined in streamlit_app.py.
"""
import sys, os, math, importlib, types

# ── Minimal Streamlit stub so streamlit_app.py can be imported without Streamlit ──
st_stub = types.ModuleType("streamlit")
st_stub.secrets = {}
st_stub.set_page_config = lambda **kw: None
st_stub.markdown = lambda *a, **kw: None
st_stub.divider = lambda: None
class _Sidebar:
    def markdown(self, *a, **kw): pass
    def __enter__(self): return self
    def __exit__(self, *a): return False
st_stub.sidebar = _Sidebar()
class _CM:
    def __enter__(self): return self
    def __exit__(self, *a): return False
st_stub.spinner = lambda *a, **kw: _CM()
st_stub.expander = lambda *a, **kw: _CM()
st_stub.progress = lambda *a, **kw: types.SimpleNamespace(progress=lambda *a, **kw: None)
for attr in ("file_uploader", "button", "success", "info", "error", "caption",
             "columns", "tabs", "metric", "download_button"):
    setattr(st_stub, attr, lambda *a, **kw: None)
sys.modules["streamlit"] = st_stub

# Also stub openai so import doesn't require the package in the test env
if "openai" not in sys.modules:
    openai_stub = types.ModuleType("openai")
    openai_stub.OpenAI = lambda **kw: None
    sys.modules["openai"] = openai_stub

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import the module under test
import streamlit_app as app


# ── GRIM tests ─────────────────────────────────────────────────────────────────
class TestGrim:
    def test_classic_violation_5_16_n20(self):
        # 5.16 * 20 = 103.2 → round=103 → 103/20=5.15 → 5.15 ≠ 5.16
        assert app.grim_check("5.16", 20) is False

    def test_classic_violation_4_2_n7(self):
        # From demo paper: 4.2 * 7 = 29.4 → no integer/7 rounds to 4.2
        assert app.grim_check("4.2", 7) is False

    def test_classic_violation_3_67_n10(self):
        # From demo paper: 3.67 * 10 = 36.7 → no integer/10 = 3.67
        assert app.grim_check("3.67", 10) is False

    def test_valid_mean_2_5_n10(self):
        # 2.5 * 10 = 25 → 25/10 = 2.5 ✓
        assert app.grim_check("2.5", 10) is True

    def test_valid_mean_3_0_n6(self):
        # 3.0 * 6 = 18 → 18/6 = 3.0 ✓
        assert app.grim_check("3.0", 6) is True

    def test_valid_mean_1_33_n3(self):
        # 1.33 * 3 = 3.99 → round = 4 → 4/3 = 1.33... rounds to 1.33 ✓
        assert app.grim_check("1.33", 3) is True

    def test_bad_mean_string_returns_true(self):
        # Non-parseable mean → no flag (safe default)
        assert app.grim_check("abc", 10) is True

    def test_no_decimal(self):
        # Integer mean → uninformative, returns True
        assert app.grim_check("4", 10) is True


# ── statcheck tests ────────────────────────────────────────────────────────────
class TestStatcheck:
    def test_t_basic(self):
        p = app.recompute_p("t", 2.4, 18)
        assert p is not None
        assert abs(p - 0.0273) < 0.001

    def test_t_large(self):
        p = app.recompute_p("t", 4.0, 10)
        assert p is not None
        assert abs(p - 0.0025) < 0.001

    def test_t_from_demo_paper(self):
        # t(18)=1.85 → p ≈ 0.081 (NOT significant at 0.05)
        p = app.recompute_p("t", 1.85, 18)
        assert p is not None
        assert p > 0.05

    def test_F_from_demo_paper(self):
        # F(2,45)=2.10 → p ≈ 0.134 (NOT significant)
        p = app.recompute_p("F", 2.10, 2, 45)
        assert p is not None
        assert p > 0.05

    def test_chi2(self):
        p = app.recompute_p("chi2", 3.84, 1)
        assert p is not None
        assert abs(p - 0.05) < 0.01

    def test_correlation(self):
        # r=0.3, n=50 → t ≈ 2.18, p ≈ 0.034
        p = app.recompute_p("r", 0.3, 48, n=50)
        assert p is not None
        assert abs(p - 0.034) < 0.005

    def test_unknown_type_returns_none(self):
        assert app.recompute_p("z", 1.96, 100) is None


# ── DOI extraction tests ───────────────────────────────────────────────────────
class TestDoiExtraction:
    def test_basic_doi(self):
        text = "See doi:10.1037/edu0000789"
        dois = app.extract_dois(text)
        assert "10.1037/edu0000789" in dois

    def test_multiple_dois(self):
        text = "paper1 doi:10.1037/abc paper2 doi:10.9999/xyz"
        dois = app.extract_dois(text)
        assert len(dois) == 2

    def test_no_doi(self):
        assert app.extract_dois("no references here") == []

    def test_trailing_punctuation_stripped(self):
        text = "See 10.1037/abc123."
        dois = app.extract_dois(text)
        assert "10.1037/abc123" in dois
        assert "10.1037/abc123." not in dois

    def test_deduplication(self):
        text = "10.1037/abc 10.1037/abc"
        assert len(app.extract_dois(text)) == 1


# ── confidence scoring tests ───────────────────────────────────────────────────
class TestConfidenceScoring:
    def _f(self, sev, flag=True):
        return {"severity": sev, "flag": flag}

    def test_no_findings_is_high(self):
        _, label = app.compute_confidence([])
        assert label == "high"

    def test_one_high_finding_is_medium(self):
        # 1.0 - 0.4 = 0.6 → medium
        _, label = app.compute_confidence([self._f("high")])
        assert label == "medium"

    def test_two_high_findings_is_low(self):
        # 1.0 - 0.8 = 0.2 → low
        _, label = app.compute_confidence([self._f("high"), self._f("high")])
        assert label == "low"

    def test_medium_findings_accumulate(self):
        # 1.0 - 2*0.2 = 0.6 → medium
        score, label = app.compute_confidence([self._f("medium")] * 2)
        assert label == "medium"

    def test_unflagged_findings_not_penalized(self):
        # info finding with flag=False should not reduce score
        _, label = app.compute_confidence([self._f("info", flag=False)])
        assert label == "high"

    def test_score_does_not_go_below_zero(self):
        # many high findings
        score, _ = app.compute_confidence([self._f("high")] * 10)
        assert score == 0.0


# ── reproducibility agent tests ────────────────────────────────────────────────
class TestReproducibilityAgent:
    def test_score_zero_for_empty_text(self):
        score, findings = app.run_reproducibility_agent("nothing relevant here")
        assert score == 0
        assert len(findings) == 5  # one per dimension

    def test_data_availability_detected(self):
        score, _ = app.run_reproducibility_agent("Data are available on zenodo.org")
        assert score >= 1

    def test_preregistration_detected(self):
        score, _ = app.run_reproducibility_agent("This study was pre-registered at osf.io/abc123")
        assert score >= 1

    def test_all_five_present(self):
        text = (
            "Data are available on zenodo.org. "
            "Analysis code at github.com/user/repo. "
            "Study was pre-registered. "
            "Power analysis indicated n=50 for 80% power. "
            "Stimuli and procedure were described in detail."
        )
        score, findings = app.run_reproducibility_agent(text)
        assert score == 5


# ── COI detector tests ─────────────────────────────────────────────────────────
class TestCOIAgent:
    def test_no_coi_section_flagged(self):
        findings = app.run_coi_agent("This paper describes a study on cognition.")
        titles = [f["title"] for f in findings]
        assert any("No COI" in t for t in titles)
        assert any(f["flag"] for f in findings)

    def test_explicit_no_conflict(self):
        findings = app.run_coi_agent(
            "Conflict of Interest: The authors declare no conflict of interest."
        )
        flagged = [f for f in findings if f["flag"]]
        assert len(flagged) == 0

    def test_industry_funding_flagged(self):
        findings = app.run_coi_agent(
            "This study was funded by PharmaCorp Inc. "
            "Authors declare no competing interests."
        )
        flagged = [f for f in findings if f["flag"]]
        assert len(flagged) >= 1
        assert any("Industry" in f["title"] or "conflict" in f["title"].lower() for f in flagged)
