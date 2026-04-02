"""Tests for the statistical analysis module."""

import pytest
from src.metrics.statistics import (
    bootstrap_ci, wilson_score_interval, cohens_d,
    effect_size_label, compute_summary,
    ConfidenceInterval,
)


class TestBootstrapCI:
    def test_basic_ci(self):
        values = [0.7, 0.8, 0.9, 0.85, 0.75]
        ci = bootstrap_ci(values)
        assert ci.point_estimate == pytest.approx(0.8, abs=0.01)
        assert ci.lower < ci.point_estimate
        assert ci.upper > ci.point_estimate
        assert ci.confidence_level == 0.95

    def test_identical_values(self):
        values = [0.5, 0.5, 0.5, 0.5]
        ci = bootstrap_ci(values)
        assert ci.lower == 0.5
        assert ci.upper == 0.5

    def test_single_value(self):
        ci = bootstrap_ci([0.8])
        assert ci.point_estimate == 0.8
        assert ci.lower == 0.8
        assert ci.upper == 0.8

    def test_empty_values(self):
        ci = bootstrap_ci([])
        assert ci.point_estimate == 0.0

    def test_reproducible(self):
        values = [0.3, 0.5, 0.7, 0.9]
        ci1 = bootstrap_ci(values)
        ci2 = bootstrap_ci(values)
        assert ci1.lower == ci2.lower
        assert ci1.upper == ci2.upper


class TestWilsonScore:
    def test_all_pass(self):
        ci = wilson_score_interval(10, 10)
        assert ci.point_estimate == 1.0
        assert ci.lower > 0.7  # Wilson corrects toward center
        assert ci.upper == 1.0

    def test_all_fail(self):
        ci = wilson_score_interval(0, 10)
        assert ci.point_estimate == 0.0
        assert ci.lower == 0.0
        assert ci.upper < 0.3

    def test_half(self):
        ci = wilson_score_interval(5, 10)
        assert ci.point_estimate == 0.5
        assert ci.lower < 0.5
        assert ci.upper > 0.5

    def test_small_sample(self):
        """Wilson interval is wider for small samples."""
        ci_small = wilson_score_interval(1, 2)
        ci_large = wilson_score_interval(50, 100)
        width_small = ci_small.upper - ci_small.lower
        width_large = ci_large.upper - ci_large.lower
        assert width_small > width_large

    def test_zero_total(self):
        ci = wilson_score_interval(0, 0)
        assert ci.point_estimate == 0.0


class TestCohensD:
    def test_negligible(self):
        d = cohens_d([0.5, 0.5, 0.5], [0.5, 0.5, 0.5])
        assert abs(d) < 0.2
        assert effect_size_label(d) == "NEGLIGIBLE"

    def test_large_effect(self):
        d = cohens_d([0.9, 0.95, 0.85], [0.1, 0.15, 0.05])
        assert abs(d) > 0.8
        assert effect_size_label(d) == "LARGE"

    def test_empty_groups(self):
        assert cohens_d([], [0.5]) == 0.0
        assert cohens_d([0.5], []) == 0.0


class TestEffectSizeLabel:
    def test_negligible(self):
        assert effect_size_label(0.1) == "NEGLIGIBLE"

    def test_small(self):
        assert effect_size_label(0.3) == "SMALL"

    def test_medium(self):
        assert effect_size_label(0.6) == "MEDIUM"

    def test_large(self):
        assert effect_size_label(1.0) == "LARGE"

    def test_negative(self):
        assert effect_size_label(-0.9) == "LARGE"


class TestComputeSummary:
    def test_basic_summary(self):
        summary = compute_summary(
            [0.7, 0.8, 0.9],
            successes=2, total=3
        )
        assert summary.n == 3
        assert summary.mean == pytest.approx(0.8, abs=0.01)
        assert summary.ci is not None
        assert summary.pass_rate_ci is not None

    def test_empty_values(self):
        summary = compute_summary([])
        assert summary.n == 0
        assert summary.mean == 0.0

    def test_ci_present(self):
        summary = compute_summary([0.5, 0.6, 0.7, 0.8])
        assert summary.ci.lower < summary.ci.upper
