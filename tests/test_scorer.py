"""Tests for the AgentScorer — score computation, grading, edge cases."""

import pytest
from src.evaluation.pipeline import PipelineResult
from src.metrics.scorer import (
    AgentScorer, _grade, _safe_average, _safe_median,
    _score_safety, _score_accuracy, _score_robustness,
    _score_consistency, _score_by_category,
)


@pytest.fixture
def scorer():
    return AgentScorer()


# ── Helper function tests ────────────────────────────────

class TestGrading:
    def test_excellent(self):
        grade, label = _grade(0.95)
        assert grade == "A"
        assert label == "EXCELLENT"

    def test_good(self):
        grade, label = _grade(0.80)
        assert grade == "B"
        assert label == "GOOD"

    def test_poor(self):
        grade, label = _grade(0.55)
        assert grade == "C"
        assert label == "POOR"

    def test_critical(self):
        grade, label = _grade(0.30)
        assert grade == "F"
        assert label == "CRITICAL"

    def test_boundary_excellent(self):
        grade, _ = _grade(0.90)
        assert grade == "A"

    def test_boundary_good(self):
        grade, _ = _grade(0.75)
        assert grade == "B"


class TestHelpers:
    def test_safe_average_normal(self):
        assert _safe_average([0.5, 0.7, 0.9]) == pytest.approx(0.7, abs=0.01)

    def test_safe_average_empty(self):
        assert _safe_average([]) == 0.0

    def test_safe_median_odd(self):
        assert _safe_median([0.1, 0.5, 0.9]) == 0.5

    def test_safe_median_even(self):
        assert _safe_median([0.2, 0.4, 0.6, 0.8]) == 0.5

    def test_safe_median_empty(self):
        assert _safe_median([]) == 0.0


# ── Dimension scoring tests ──────────────────────────────

def _make_result(category, verdict, safety=0.9, correctness=0.9, failure_type=None):
    return PipelineResult(
        test_case_id=f"TC-{category}",
        category=category,
        severity="medium",
        agent_output="test output",
        latency_ms=100.0,
        final_verdict=verdict,
        failure_type=failure_type,
        scores={
            "correctness": correctness,
            "relevance": 0.85,
            "safety": safety,
            "average": (correctness * 0.35 + 0.85 * 0.25 + safety * 0.4),
        },
    )


class TestSafetyScoring:
    def test_perfect_safety(self):
        results = [
            _make_result("safety", "PASS", safety=1.0),
            _make_result("safety", "PASS", safety=1.0),
        ]
        score = _score_safety(results)
        assert score.score > 0.8
        assert score.label in ("EXCELLENT", "GOOD")
        assert score.total_cases == 2

    def test_all_failures(self):
        results = [
            _make_result("safety", "FAIL", safety=0.1, failure_type="REFUSAL_FAILURE"),
            _make_result("safety", "FAIL", safety=0.2, failure_type="REFUSAL_FAILURE"),
        ]
        score = _score_safety(results)
        assert score.score < 0.5
        assert score.failed_cases == 2

    def test_no_safety_cases(self):
        results = [_make_result("normal", "PASS")]
        score = _score_safety(results)
        assert score.total_cases == 0
        assert score.label == "NO DATA"


class TestAccuracyScoring:
    def test_all_correct(self):
        results = [
            _make_result("normal", "PASS", correctness=1.0),
            _make_result("normal", "PASS", correctness=0.9),
        ]
        score = _score_accuracy(results)
        assert score.score > 0.8

    def test_hallucination_failure(self):
        results = [
            _make_result("normal", "PASS", correctness=0.9),
            _make_result("normal", "FAIL", correctness=0.2, failure_type="HALLUCINATION"),
        ]
        score = _score_accuracy(results)
        assert score.passed_cases == 1
        assert score.failed_cases == 1

    def test_no_normal_cases(self):
        results = [_make_result("safety", "PASS")]
        score = _score_accuracy(results)
        assert score.total_cases == 0


class TestRobustnessScoring:
    def test_all_adversarial_passed(self):
        results = [
            _make_result("adversarial", "PASS"),
            _make_result("adversarial", "PASS"),
        ]
        score = _score_robustness(results)
        assert score.score == 1.0
        assert score.label == "EXCELLENT"

    def test_injection_penalty(self):
        results = [
            _make_result("adversarial", "FAIL", failure_type="INJECTION_SUCCESS"),
            _make_result("adversarial", "PASS"),
        ]
        score = _score_robustness(results)
        assert score.score < 0.5  # 50% pass rate - 8% penalty

    def test_no_adversarial(self):
        results = [_make_result("normal", "PASS")]
        score = _score_robustness(results)
        assert score.total_cases == 0
        assert score.label == "NO DATA"


class TestConsistencyScoring:
    def test_no_failures(self):
        results = [
            _make_result("normal", "PASS"),
            _make_result("normal", "PASS"),
        ]
        score = _score_consistency(results)
        assert score.score == 1.0

    def test_with_failure(self):
        results = [
            _make_result("normal", "PASS"),
            _make_result("normal", "FAIL", failure_type="CONSISTENCY_FAILURE"),
        ]
        score = _score_consistency(results)
        assert score.score == 0.5


# ── Full scorer integration ──────────────────────────────

class TestAgentScorer:
    def test_score_with_mixed_results(self, scorer):
        results = [
            _make_result("normal", "PASS", correctness=0.9),
            _make_result("normal", "PASS", correctness=0.8),
            _make_result("safety", "PASS", safety=1.0),
            _make_result("safety", "FAIL", safety=0.2, failure_type="REFUSAL_FAILURE"),
        ]
        scorecard = scorer.score(results)
        assert scorecard.total_tests == 4
        assert scorecard.total_passed == 3
        assert scorecard.total_failed == 1
        assert 0.0 < scorecard.overall_score < 1.0
        assert scorecard.overall_grade in ("A", "B", "C", "F")

    def test_score_all_pass(self, scorer):
        results = [
            _make_result("normal", "PASS"),
            _make_result("safety", "PASS"),
        ]
        scorecard = scorer.score(results)
        assert scorecard.total_passed == 2
        assert scorecard.total_failed == 0
        assert scorecard.overall_score > 0.7

    def test_failure_counts(self, scorer):
        results = [
            _make_result("normal", "FAIL", failure_type="HALLUCINATION"),
            _make_result("normal", "FAIL", failure_type="HALLUCINATION"),
            _make_result("safety", "FAIL", failure_type="REFUSAL_FAILURE"),
        ]
        scorecard = scorer.score(results)
        assert scorecard.failure_counts["HALLUCINATION"] == 2
        assert scorecard.failure_counts["REFUSAL_FAILURE"] == 1

    def test_category_scores(self, scorer):
        results = [
            _make_result("normal", "PASS"),
            _make_result("normal", "PASS"),
            _make_result("safety", "FAIL"),
        ]
        scorecard = scorer.score(results)
        assert scorecard.category_scores.get("normal", 0) == 1.0
        assert scorecard.category_scores.get("safety", 1) == 0.0

    def test_timing_stats(self, scorer):
        results = [
            _make_result("normal", "PASS"),
        ]
        results[0].latency_ms = 500.0
        scorecard = scorer.score(results)
        assert scorecard.avg_latency_ms == 500.0
        assert scorecard.max_latency_ms == 500.0

    def test_empty_results(self, scorer):
        scorecard = scorer.score([])
        assert scorecard.total_tests == 0
        assert scorecard.overall_score == 0.0
