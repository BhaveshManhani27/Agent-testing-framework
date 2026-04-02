"""
Agent Testing Framework — Main Entrypoint

Production-grade AI agent evaluation system with:
  - Multi-stage evaluation pipeline
  - Multi-judge consensus scoring
  - Adversarial mutation engine
  - Behavioral consistency testing
  - Multi-turn conversation testing
  - Dimensional scoring with statistical analysis
  - Cost tracking and reporting
"""

import argparse
import asyncio
import sys

from src.observability.log_config import setup_logging, get_logger
from src.core.test_registry import TestRegistry
from src.core.runner import TestRunner
from src.agents.sample_agent import SimpleChatAgent
from src.adversarial.generator import AdversarialGenerator
from src.adversarial.catalog import get_catalog
from src.evaluation.pipeline import EvaluationPipeline
from src.evaluation.consistency_evaluator import ConsistencyEvaluator
from src.metrics.scorer import AgentScorer
from src.reporting.reporter import Reporter
from src.observability.logger import RunLogger
from src.observability.cost_tracker import COST_TRACKER

logger = get_logger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Agent Testing Framework — Production-grade AI agent evaluation"
    )
    parser.add_argument(
        "--quick", action="store_true",
        help="Run first 6 tests only (faster, saves API costs)"
    )
    parser.add_argument(
        "--no-consensus", action="store_true",
        help="Use single judge instead of 3-judge consensus"
    )
    parser.add_argument(
        "--adversarial", action="store_true",
        help="Generate and include adversarial mutation cases"
    )
    parser.add_argument(
        "--consistency", action="store_true",
        help="Run behavioral consistency tests"
    )
    parser.add_argument(
        "--multi-turn", action="store_true",
        help="Run multi-turn conversation tests"
    )
    parser.add_argument(
        "--async-mode", action="store_true",
        help="Run tests in parallel using async runner"
    )
    parser.add_argument(
        "--max-concurrent", type=int, default=3,
        help="Max concurrent tests in async mode (default: 3)"
    )
    parser.add_argument(
        "--no-report", action="store_true",
        help="Skip file report generation"
    )
    parser.add_argument(
        "--no-cost", action="store_true",
        help="Skip cost tracking report"
    )
    return parser.parse_args()


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════╗
║           AGENT TESTING FRAMEWORK v2.0                  ║
║     Production-grade AI agent evaluation system         ║
╚══════════════════════════════════════════════════════════╝
    """)


def main():
    # ── Initialize ────────────────────────────────────────────────
    setup_logging()
    args = parse_args()
    print_banner()

    # ── Step 1: Initialize logger ─────────────────────────────────
    run_logger = RunLogger()

    # ── Step 2: Load test cases ───────────────────────────────────
    logger.info("Loading test suite...")
    registry = TestRegistry()
    registry.summary()

    test_cases = registry.get_all()

    if args.quick:
        test_cases = test_cases[:6]
        logger.info("Quick mode: running %d tests", len(test_cases))

    # ── Step 3: Add adversarial cases (optional) ──────────────────
    if args.adversarial:
        logger.info("Generating adversarial mutations...")
        generator = AdversarialGenerator(llm_mode=False)
        normal_cases = registry.get_by_category("normal")[:2]
        mutated = generator.mutate_batch(
            normal_cases,
            mutation_types=[
                "prompt_injection",
                "role_confusion",
                "goal_hijacking"
            ]
        )
        catalog = get_catalog()
        adversarial_cases = (
            [m.test_case for m in mutated] + catalog
        )
        test_cases = test_cases + adversarial_cases
        logger.info(
            "Added %d adversarial cases. Total: %d",
            len(adversarial_cases), len(test_cases)
        )

    # ── Step 4: Run agent ─────────────────────────────────────────
    logger.info("Initializing agent")
    agent  = SimpleChatAgent()

    if args.async_mode:
        from src.core.async_runner import AsyncTestRunner
        runner = AsyncTestRunner(
            agent=agent,
            max_concurrent=args.max_concurrent,
            verbose=True
        )
        logger.info("Running %d test cases (async, max_concurrent=%d)",
                     len(test_cases), args.max_concurrent)
        results, run_summary = asyncio.run(runner.run(test_cases))
    else:
        runner = TestRunner(agent=agent, verbose=True)
        logger.info("Running %d test cases", len(test_cases))
        results, run_summary = runner.run(test_cases)

    # ── Step 5: Multi-turn conversation tests (optional) ──────────
    if args.multi_turn:
        from src.evaluation.multi_turn import (
            ConversationRunner, load_conversation_tests
        )
        logger.info("Running multi-turn conversation tests...")
        conv_tests = load_conversation_tests()
        if conv_tests:
            conv_runner = ConversationRunner(agent=agent, verbose=True)
            conv_results = conv_runner.run_batch(conv_tests)
        else:
            logger.warning("No conversation tests found")

    # ── Step 6: Consistency testing (optional) ────────────────────
    if args.consistency:
        logger.info("Running behavioral consistency tests...")
        consistency_evaluator = ConsistencyEvaluator(
            agent=agent, num_runs=3
        )
        # Check one from each category
        for category in ("normal", "safety", "adversarial"):
            cat_cases = registry.get_by_category(category)
            if cat_cases:
                c_result = consistency_evaluator.evaluate(cat_cases[0])
                logger.info(
                    "  %s: consistency=%.4f → %s%s",
                    cat_cases[0].id,
                    c_result.consistency_score,
                    c_result.verdict,
                    " CRITICAL" if c_result.is_critical else ""
                )

    # ── Step 7: Evaluation pipeline ───────────────────────────────
    use_consensus = not args.no_consensus
    logger.info(
        "Running evaluation pipeline (%s judge)",
        'consensus' if use_consensus else 'single'
    )

    pipeline = EvaluationPipeline(
        use_consensus=use_consensus,
        verbose=True
    )
    pipeline_results = pipeline.evaluate_batch(results)

    # ── Step 8: Score ─────────────────────────────────────────────
    scorer    = AgentScorer()
    scorecard = scorer.score(pipeline_results)

    # ── Step 9: Log everything ────────────────────────────────────
    run_logger.log_results(pipeline_results)
    run_logger.log_scorecard(scorecard)

    # ── Step 10: Generate reports ─────────────────────────────────
    if not args.no_report:
        logger.info("Generating reports")
        reporter = Reporter()
        reporter.generate(
            pipeline_results,
            scorecard,
            run_id=run_logger.run_id
        )

    # ── Step 11: Cost report ──────────────────────────────────────
    if not args.no_cost:
        COST_TRACKER.print_report(num_tests=len(test_cases))

    # ── Step 12: Final summary ────────────────────────────────────
    _print_final_summary(scorecard, run_logger)

    # Exit with error code if critical failures
    if scorecard.overall_score < 0.5:
        logger.warning("CRITICAL: Agent scored below 0.5 — review required")
        sys.exit(1)


def _print_final_summary(scorecard, run_logger):
    """Print the final scorecard to terminal."""
    # CI info
    ci_str = ""
    if scorecard.overall_ci:
        ci_str = f" CI: [{scorecard.overall_ci.lower:.2f}, {scorecard.overall_ci.upper:.2f}]"

    print(f"""
╔══════════════════════════════════════════════════════════╗
║                  FINAL RESULTS                          ║
╠══════════════════════════════════════════════════════════╣
║  Overall Score : {scorecard.overall_score:<6}  Grade: {scorecard.overall_grade}  [{scorecard.overall_label:<10}]       ║
╠══════════════════════════════════════════════════════════╣
║  Safety      : {scorecard.safety_score.score:<6}  [{scorecard.safety_score.label:<10}]                    ║
║  Accuracy    : {scorecard.accuracy_score.score:<6}  [{scorecard.accuracy_score.label:<10}]                    ║
║  Robustness  : {scorecard.robustness_score.score:<6}  [{scorecard.robustness_score.label:<10}]                    ║
║  Consistency : {scorecard.consistency_score.score:<6}  [{scorecard.consistency_score.label:<10}]                    ║
╠══════════════════════════════════════════════════════════╣
║  Tests  : {scorecard.total_tests:<4}  Pass: {scorecard.total_passed:<4}  Fail: {scorecard.total_failed:<4}  Error: {scorecard.total_errors:<3}   ║
║  Pass Rate   : {scorecard.pass_rate}%                                   ║
╠══════════════════════════════════════════════════════════╣
║  FAILURE BREAKDOWN                                       ║""")

    if scorecard.failure_counts:
        for ft, count in sorted(
            scorecard.failure_counts.items(), key=lambda x: -x[1]
        ):
            print(f"║  {ft:<25} {count} case(s)"
                  + " " * (27 - len(str(count))) + "║")
    else:
        print("║  No failures detected " + " " * 34 + "║")

    print(f"""╠══════════════════════════════════════════════════════════╣
║  Avg Latency : {scorecard.avg_latency_ms}ms                                     ║
║  Run ID      : {run_logger.run_id}                                        ║
╚══════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    main()