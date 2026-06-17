"""Unit tests for GRIM (Granularity-Related Inconsistency of Means) check."""
import pytest
from peerless.verification.grim import grim_check


class TestGrimCheck:
    def test_known_impossible_mean(self):
        r = grim_check("2.50", 7)
        assert r.possible is False

    def test_known_possible_mean(self):
        r = grim_check("2.57", 7)
        assert r.possible is True

    def test_whole_number_always_possible(self):
        r = grim_check("3.0", 5)
        assert r.possible is True

    def test_n1_whole_value_possible(self):
        r = grim_check("4.00", 1)
        assert r.possible is True

    def test_large_n_rounds_correctly(self):
        # 5.00 * 100 = 500 — valid
        r = grim_check("5.00", 100)
        assert r.possible is True

    def test_result_carries_input(self):
        r = grim_check("2.50", 7)
        assert r.M == "2.50"
        assert r.n == 7
        assert r.d == 2

    def test_impossible_returns_empty_candidates(self):
        r = grim_check("2.50", 7)
        assert r.candidates == []

    def test_possible_returns_nonempty_candidates(self):
        r = grim_check("2.57", 7)
        assert len(r.candidates) > 0

    def test_one_decimal_place(self):
        # 2.3 * 10 = 23, round(23/10,1) = 2.3 — possible
        r = grim_check("2.3", 10)
        assert r.possible is True

    def test_scale_constraint_applied(self):
        r = grim_check("2.50", 7, scale_min=1, scale_max=5)
        assert r.possible is False

    def test_zero_mean(self):
        r = grim_check("0.00", 5)
        assert r.possible is True
