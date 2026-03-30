import time
from dataclasses import dataclass, field
from typing import List, Optional
from src.core.agent_interface import BaseAgent
from src.core.test_registry import TestCase

@dataclass
class TestResult:
    """
    Everything we know about one test case after running it.
    This gets passed downstream to the evaluation pipeline.
    """
    test_case: TestCase          
    agent_output: str            
    latency_ms: float            
    error: Optional[str] = None  


    verdict: Optional[str] = None          
    failure_type: Optional[str] = None    
    scores: Optional[dict] = field(default_factory=dict)
    evaluation_reason: Optional[str] = None


@dataclass
class RunSummary:
    """
    High-level statistics after running the full test suite.
    """
    total: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    latencies: List[float] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return round((self.passed / self.total) * 100, 2)

    @property
    def avg_latency(self) -> float:
        if not self.latencies:
            return 0.0
        return round(sum(self.latencies) / len(self.latencies), 2)

    @property
    def max_latency(self) -> float:
        return round(max(self.latencies), 2) if self.latencies else 0.0

    @property
    def min_latency(self) -> float:
        return round(min(self.latencies), 2) if self.latencies else 0.0


class TestRunner:
    """
    Runs a list of test cases against any agent that
    follows the BaseAgent interface.

    Completely agent-agnostic — swap the agent, everything else stays.
    """

    def __init__(self, agent: BaseAgent, verbose: bool = True):
        """
        agent   : any class that inherits from BaseAgent
        verbose : if True, prints progress to console as tests run
        """
        self.agent = agent
        self.verbose = verbose

    def _run_single(self, test_case: TestCase) -> TestResult:
        """
        Runs ONE test case against the agent.
        Catches all exceptions so one failure never stops the whole suite.
        """
        if self.verbose:
            print(f"Running {test_case.id} [{test_case.category}] — {test_case.input[:60]}")

        start = time.time()

        try:
            response = self.agent.run(test_case.input)
            latency = round((time.time() - start) * 1000, 2)

            if response.error:
                return TestResult(
                    test_case=test_case,
                    agent_output="",
                    latency_ms=latency,
                    error=response.error,
                    verdict="ERROR",
                    failure_type="RUNNER_ERROR"
                )

            return TestResult(
                test_case=test_case,
                agent_output=response.output,
                latency_ms=latency
            )

        except Exception as e:
            latency = round((time.time() - start) * 1000, 2)
            return TestResult(
                test_case=test_case,
                agent_output="",
                latency_ms=latency,
                error=str(e),
                verdict="ERROR",
                failure_type="RUNNER_ERROR"
            )

    def run(self, test_cases: List[TestCase]) -> tuple[List[TestResult], RunSummary]:
        """
        Runs ALL test cases one by one.
        Returns:
            - list of TestResult (one per test case)
            - RunSummary (aggregate stats)
        """
        results: List[TestResult] = []
        summary = RunSummary(total=len(test_cases))

        print(f"\nStarting test run — {len(test_cases)} cases — Agent: {self.agent}")
        print("─" * 60)

        for i, test_case in enumerate(test_cases, 1):
            result = self._run_single(test_case)
            results.append(result)

            summary.latencies.append(result.latency_ms)

            if result.verdict == "ERROR":
                summary.errors += 1

            if self.verbose:
                status = "ERROR" if result.error else "ran"
                print(f"    {status} in {result.latency_ms}ms")

        print("─" * 60)
        print(f"Test run complete.")
        print(f"   Total      : {summary.total}")
        print(f"   Errors     : {summary.errors}")
        print(f"   Avg Latency: {summary.avg_latency}ms")
        print(f"   Max Latency: {summary.max_latency}ms")
        print(f"   Min Latency: {summary.min_latency}ms\n")

        return results, summary