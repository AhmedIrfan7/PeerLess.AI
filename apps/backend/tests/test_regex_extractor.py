"""Unit tests for regex-based statistical claim extractor."""
from peerless.verification.regex_extractor import extract_claims


class TestMeanSD:
    def test_apa_style(self):
        text = "Participants scored M = 3.50, SD = 0.80, n = 20 on the scale."
        claims = extract_claims(text)
        mean_claims = [c for c in claims if c["kind"] == "mean_sd"]
        assert len(mean_claims) >= 1
        rv = mean_claims[0]["reported_values"]
        assert rv["mean"] == "3.50"
        assert rv["n"] == 20

    def test_mean_without_n(self):
        text = "The group mean was M = 2.75."
        claims = extract_claims(text)
        mean_claims = [c for c in claims if c["kind"] == "mean_sd"]
        assert any(c["reported_values"]["mean"] == "2.75" for c in mean_claims)

    def test_no_false_positive_integer(self):
        text = "There were 3 groups with M = 4, no decimal."
        claims = extract_claims(text)
        mean_claims = [c for c in claims if c["kind"] == "mean_sd"]
        assert all("." in c["reported_values"]["mean"] for c in mean_claims)


class TestTTest:
    def test_apa_t_test(self):
        text = "Results showed t(58) = 2.45, p = .017."
        claims = extract_claims(text)
        t_claims = [c for c in claims if c["kind"] == "t_test"]
        assert len(t_claims) == 1
        rv = t_claims[0]["reported_values"]
        assert rv["t"] == 2.45
        assert rv["df"] == 58.0
        assert "017" in rv["p_reported"] or ".017" in rv["p_reported"]

    def test_t_less_than_p(self):
        text = "t(99) = 3.10, p < .001"
        claims = extract_claims(text)
        t_claims = [c for c in claims if c["kind"] == "t_test"]
        assert len(t_claims) == 1


class TestChiSquare:
    def test_chi_squared(self):
        text = "chi-squared(1) = 3.84, p = .050"
        claims = extract_claims(text)
        chi_claims = [c for c in claims if c["kind"] == "chi_square"]
        assert len(chi_claims) == 1
        rv = chi_claims[0]["reported_values"]
        assert rv["chi2"] == 3.84
        assert rv["df"] == 1.0


class TestFTest:
    def test_apa_f_test(self):
        text = "An ANOVA revealed F(2, 87) = 4.12, p = .019."
        claims = extract_claims(text)
        f_claims = [c for c in claims if c["kind"] == "f_test"]
        assert len(f_claims) == 1
        rv = f_claims[0]["reported_values"]
        assert rv["f"] == 4.12
        assert rv["df1"] == 2.0
        assert rv["df2"] == 87.0


class TestCorrelation:
    def test_apa_r_with_df(self):
        text = "r(98) = .45, p < .001"
        claims = extract_claims(text)
        r_claims = [c for c in claims if c["kind"] == "correlation"]
        assert len(r_claims) >= 1
        rv = r_claims[0]["reported_values"]
        assert rv["r"] == 0.45
        assert rv["n"] == 100

    def test_r_with_n(self):
        text = "r = .32, n = 50, p = .024"
        claims = extract_claims(text)
        r_claims = [c for c in claims if c["kind"] == "correlation"]
        assert any(c["reported_values"]["r"] == 0.32 for c in r_claims)


class TestMixed:
    def test_multiple_claims_in_paragraph(self):
        text = (
            "Group A scored M = 4.20, SD = 0.90, n = 30. "
            "An independent t-test showed t(58) = 2.10, p = .040. "
            "The correlation between scores was r(58) = .31, p = .018."
        )
        claims = extract_claims(text)
        kinds = {c["kind"] for c in claims}
        assert "mean_sd" in kinds
        assert "t_test" in kinds
        assert "correlation" in kinds

    def test_empty_text_returns_empty(self):
        assert extract_claims("") == []

    def test_no_statistics_returns_empty(self):
        assert extract_claims("The study was conducted in 2023.") == []
