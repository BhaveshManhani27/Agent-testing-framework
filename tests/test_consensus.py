"""Tests for consensus judge math — averaging, variance, majority verdict."""

import pytest
from src.evaluation.consensus_judge import (
    _average, _variance, _max_spread,
    _assign_confidence, _majority_verdict,
    CONTESTED_THRESHOLD, CONFIDENCE_HIGH, CONFIDENCE_MEDIUM,
)


class TestAverage:
    def test_basic(self):
        assert _average([0.5, 0.7, 0.9]) == pytest.approx(0.7, abs=0.001)

    def test_identical(self):
        assert _average([0.8, 0.8, 0.8]) == 0.8

    def test_single(self):
        assert _average([0.5]) == 0.5


class TestVariance:
    def test_zero_variance(self):
        assert _variance([0.8, 0.8, 0.8]) == 0.0

    def test_high_variance(self):
        v = _variance([0.1, 0.5, 0.9])
        assert v > 0.1  # significant spread

    def test_single_element(self):
        assert _variance([0.5]) == 0.0


class TestMaxSpread:
    def test_basic(self):
        assert _max_spread([0.1, 0.5, 0.9]) == pytest.approx(0.8)

    def test_identical(self):
        assert _max_spread([0.5, 0.5, 0.5]) == 0.0


class TestConfidence:
    def test_high_confidence(self):
        # Very low variance in all dimensions
        conf = _assign_confidence(0.01, 0.01, 0.01)
        assert conf == "HIGH"

    def test_medium_confidence(self):
        conf = _assign_confidence(0.05, 0.01, 0.01)
        assert conf == "MEDIUM"

    def test_low_confidence(self):
        conf = _assign_confidence(0.2, 0.01, 0.01)
        assert conf == "LOW"


class TestMajorityVerdict:
    def test_all_pass(self):
        assert _majority_verdict(["PASS", "PASS", "PASS"]) == "PASS"

    def test_all_fail(self):
        assert _majority_verdict(["FAIL", "FAIL", "FAIL"]) == "FAIL"

    def test_majority_pass(self):
        assert _majority_verdict(["PASS", "PASS", "FAIL"]) == "PASS"

    def test_majority_fail(self):
        assert _majority_verdict(["PASS", "FAIL", "FAIL"]) == "FAIL"
