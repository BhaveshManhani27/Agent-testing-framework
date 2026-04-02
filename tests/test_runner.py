"""Tests for the TestRunner — execution, error handling, summary statistics."""

import pytest
from src.core.runner import TestRunner, RunSummary
from tests.conftest import MockAgent, MockRefusingAgent, MockCrashingAgent


class TestRunnerExecution:
    def test_run_returns_results(self, mock_agent, normal_test_case):
        runner = TestRunner(agent=mock_agent, verbose=False)
        results, summary = runner.run([normal_test_case])
        assert len(results) == 1
        assert results[0].agent_output == "Hello, I'm a helpful assistant."
        assert results[0].latency_ms >= 0

    def test_run_multiple(self, mock_agent, normal_test_case, safety_test_case):
        runner = TestRunner(agent=mock_agent, verbose=False)
        results, summary = runner.run([normal_test_case, safety_test_case])
        assert len(results) == 2
        assert summary.total == 2

    def test_run_captures_error(self, refusing_agent, normal_test_case):
        """Refusing agent doesn't crash — just returns refusal text."""
        runner = TestRunner(agent=refusing_agent, verbose=False)
        results, _ = runner.run([normal_test_case])
        assert len(results) == 1
        assert results[0].error is None  # refusal is content, not an error


class TestRunnerErrorHandling:
    def test_crashing_agent(self, crashing_agent, normal_test_case):
        """Runner should catch agent exceptions and report as ERROR."""
        runner = TestRunner(agent=crashing_agent, verbose=False)
        results, summary = runner.run([normal_test_case])
        assert results[0].verdict == "ERROR"
        assert results[0].failure_type == "RUNNER_ERROR"
        assert "Connection timed out" in results[0].error
        assert summary.errors == 1

    def test_error_agent(self, normal_test_case):
        """Agent that returns an error string."""
        agent = MockAgent(output="", error="API rate limited")
        runner = TestRunner(agent=agent, verbose=False)
        results, summary = runner.run([normal_test_case])
        assert results[0].verdict == "ERROR"
        assert results[0].failure_type == "RUNNER_ERROR"
        assert summary.errors == 1


class TestRunSummary:
    def test_pass_rate_all_pass(self):
        summary = RunSummary(total=10, passed=10)
        assert summary.pass_rate == 100.0

    def test_pass_rate_half(self):
        summary = RunSummary(total=10, passed=5)
        assert summary.pass_rate == 50.0

    def test_pass_rate_empty(self):
        summary = RunSummary(total=0)
        assert summary.pass_rate == 0.0

    def test_latency_stats(self):
        summary = RunSummary(
            total=3,
            latencies=[100.0, 200.0, 300.0]
        )
        assert summary.avg_latency == 200.0
        assert summary.max_latency == 300.0
        assert summary.min_latency == 100.0

    def test_latency_empty(self):
        summary = RunSummary(total=0, latencies=[])
        assert summary.avg_latency == 0.0
        assert summary.max_latency == 0.0
        assert summary.min_latency == 0.0
