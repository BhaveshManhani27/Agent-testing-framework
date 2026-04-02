"""
Async Test Runner — Parallel test execution using asyncio.

Runs test cases concurrently with a configurable semaphore
to control parallelism. Significantly faster than sequential
execution for I/O-bound agent calls.
"""

import asyncio
import time
from dataclasses import dataclass
from typing import List, Optional
from src.core.agent_interface import BaseAgent
from src.core.runner import TestResult, RunSummary
from src.core.test_registry import TestCase
from src.observability.log_config import get_logger

logger = get_logger(__name__)


class AsyncTestRunner:
    """
    Runs test cases in parallel using asyncio.

    Uses a semaphore to limit concurrency — avoids
    overwhelming the agent or hitting rate limits.

    Usage:
        runner = AsyncTestRunner(agent, max_concurrent=3)
        results, summary = asyncio.run(runner.run(test_cases))
    """

    def __init__(
        self,
        agent: BaseAgent,
        max_concurrent: int = 3,
        verbose: bool = True
    ):
        """
        agent          : any class inheriting BaseAgent
        max_concurrent : max simultaneous agent calls
        verbose        : print progress
        """
        self.agent = agent
        self.max_concurrent = max_concurrent
        self.verbose = verbose
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._completed = 0
        self._total = 0

    async def _run_single(self, test_case: TestCase) -> TestResult:
        """
        Runs ONE test case, respecting the concurrency semaphore.
        Uses run_in_executor to run the synchronous agent.run()
        in a thread pool — keeps the event loop responsive.
        """
        async with self._semaphore:
            if self.verbose:
                logger.info(
                    "[%d/%d] Running %s [%s]",
                    self._completed + 1, self._total,
                    test_case.id, test_case.category
                )

            start = time.time()

            try:
                # Run synchronous agent in thread pool
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None, self.agent.run, test_case.input
                )
                latency = round((time.time() - start) * 1000, 2)

                if response.error:
                    result = TestResult(
                        test_case=test_case,
                        agent_output="",
                        latency_ms=latency,
                        error=response.error,
                        verdict="ERROR",
                        failure_type="RUNNER_ERROR"
                    )
                else:
                    result = TestResult(
                        test_case=test_case,
                        agent_output=response.output,
                        latency_ms=latency
                    )

            except Exception as e:
                latency = round((time.time() - start) * 1000, 2)
                result = TestResult(
                    test_case=test_case,
                    agent_output="",
                    latency_ms=latency,
                    error=str(e),
                    verdict="ERROR",
                    failure_type="RUNNER_ERROR"
                )

            self._completed += 1

            if self.verbose:
                status = "ERROR" if result.error else "done"
                logger.info(
                    "  [%d/%d] %s %s in %sms",
                    self._completed, self._total,
                    test_case.id, status, result.latency_ms
                )

            return result

    async def run(
        self, test_cases: List[TestCase]
    ) -> tuple[List[TestResult], RunSummary]:
        """
        Runs ALL test cases concurrently (up to max_concurrent at a time).
        Returns results in the same order as input test cases.
        """
        self._total = len(test_cases)
        self._completed = 0

        logger.info(
            "Starting async test run — %d cases — "
            "max_concurrent=%d — Agent: %s",
            len(test_cases), self.max_concurrent, self.agent
        )

        start_time = time.time()

        # Create tasks preserving input order
        tasks = [
            self._run_single(tc) for tc in test_cases
        ]

        # Run all concurrently, limited by semaphore
        results = await asyncio.gather(*tasks)

        total_time = round((time.time() - start_time) * 1000, 2)

        # Build summary
        summary = RunSummary(total=len(test_cases))
        for result in results:
            summary.latencies.append(result.latency_ms)
            if result.verdict == "ERROR":
                summary.errors += 1

        logger.info("─" * 60)
        logger.info("Async test run complete.")
        logger.info("  Total wall time: %sms", total_time)
        logger.info("  Total tests    : %d", summary.total)
        logger.info("  Errors         : %d", summary.errors)
        logger.info("  Avg Latency    : %sms", summary.avg_latency)
        logger.info(
            "  Speedup vs sequential: ~%.1fx",
            (summary.avg_latency * len(test_cases)) / max(total_time, 1)
        )

        return list(results), summary
