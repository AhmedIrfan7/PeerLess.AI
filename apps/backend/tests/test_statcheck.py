"""Unit tests for statcheck p-value recomputation."""
import pytest
from peerless.verification.statcheck import (
    check_t_test,
    check_chi_square,
    check_f_test,
    check_correlation,
)


class TestTTest:
    def test_consistent_p(self):
        r = check_t_test(2.0, 30, "p = 0.055")
        assert r.consistent is True

    def test_inconsistent_p(self):
        r = check_t_test(2.0, 30, "p = 0.010")
        assert r.consistent is False

    def test_one_tailed(self):
        r = check_t_test(2.0, 30, "p = 0.028", one_tailed=True)
        assert r.consistent is True

    def test_carries_inputs(self):
        r = check_t_test(1.96, 100, "0.052")
        assert r.test_type == "t_test"

    def test_p_near_boundary(self):
        r = check_t_test(1.96, 120, "0.052")
        assert r.recomputed_p is not None
        assert 0.0 < r.recomputed_p < 1.0


class TestChiSquare:
    def test_consistent(self):
        r = check_chi_square(3.84, 1, "p = 0.050")
        assert r.consistent is True

    def test_inconsistent(self):
        r = check_chi_square(3.84, 1, "p = 0.010")
        assert r.consistent is False

    def test_test_type(self):
        r = check_chi_square(3.84, 1, "p = 0.050")
        assert r.test_type == "chi_square"


class TestFTest:
    def test_consistent(self):
        r = check_f_test(4.0, 1, 30, "p = 0.054")
        assert r.consistent is True

    def test_inconsistent(self):
        r = check_f_test(4.0, 1, 30, "p = 0.001")
        assert r.consistent is False

    def test_test_type(self):
        r = check_f_test(4.0, 1, 30, "p = 0.054")
        assert r.test_type == "f_test"


class TestCorrelation:
    def test_consistent(self):
        r = check_correlation(0.30, 100, "p = 0.002")
        assert r.consistent is True

    def test_inconsistent(self):
        r = check_correlation(0.10, 100, "p = 0.001")
        assert r.consistent is False

    def test_negative_correlation(self):
        r = check_correlation(-0.30, 100, "p = 0.002")
        assert r.consistent is True

    def test_test_type(self):
        r = check_correlation(0.30, 100, "p = 0.002")
        assert r.test_type == "correlation"
