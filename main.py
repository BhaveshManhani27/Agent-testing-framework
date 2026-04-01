import argparse
import sys
from src.core.test_registry import TestRegistry
from src.core.runner import TestRunner
from src.agents.sample_agent import SimplechatAgent
from src.adversarial.generator import AdversarialGenerator
from src.adversarial.catalog import get_catalog
from src.evaluation.pipeline import EvaluationPipeline
from src.evaluation.consistency_evaluator import ConsistencyEvaluator
from src.metrics.scorer import AgentScorer
from src.reporting.reporter import Reporter
from src.observability.logger import RunLogger


def parse_args():
    parser = argparse.ArgumentParser(
        description="Agent Testing Framework"
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
        "--no-report", action="store_true",
        help="Skip file report generation"
    )
    return parser.parse_args()


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════╗
║           AGENT TESTING FRAMEWORK v1.0                  ║
║     Production-grade AI agent evaluation system         ║
╚══════════════════════════════════════════════════════════╝
    """)


def main():
    args = parse_args()
    print_banner()

    # ── Step 1: Initialize logger ─────────────────────────────────
    logger = RunLogger()

    # ── Step 2: Load test cases ───────────────────────────────────
    print("\n📋 Loading test suite...")
    registry = TestRegistry()
    registry.summary()

    test_cases = registry.get_all()

    if args.quick:
        test_cases = test_cases[:6]
        print(f"   ⚡ Quick mode: running {len(test_cases)} tests")

    # ── Step 3: Add adversarial cases (optional) ──────────────────
    if args.adversarial:
        print("\n🧬 Generating adversarial mutations...")
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
        print(
            f"   Added {len(adversarial_cases)} adversarial cases. "
            f"Total: {len(test_cases)}"
        )

    # ── Step 4: Run agent ─────────────────────────────────────────
    print("\nInitializing agent...")
    agent  = SimplechatAgent()
    runner = TestRunner(agent=agent, verbose=True)

    print(f"\n🚀 Running {len(test_cases)} test cases...")
    results, run_summary = runner.run(test_cases)

    # ── Step 5: Consistency testing (optional) ────────────────────
    if args.consistency:
        print("\nRunning behavioral consistency tests...")
        consistency_evaluator = ConsistencyEvaluator(
            agent=agent, num_runs=3
        )
        # Check one from each category
        for category in ("normal", "safety", "adversarial"):
            cat_cases = registry.get_by_category(category)
            if cat_cases:
                c_result = consistency_evaluator.evaluate(cat_cases[0])
                print(
                    f"   {cat_cases[0].id}: "
                    f"consistency={c_result.consistency_score} "
                    f"→ {c_result.verdict}"
                    + (" CRITICAL" if c_result.is_critical else "")
                )

    # ── Step 6: Evaluation pipeline ───────────────────────────────
    use_consensus = not args.no_consensus
    print(
        f"\nRunning evaluation pipeline "
        f"({'consensus' if use_consensus else 'single'} judge)..."
    )

    pipeline = EvaluationPipeline(
        use_consensus=use_consensus,
        verbose=True
    )
    pipeline_results = pipeline.evaluate_batch(results)

    # ── Step 7: Score ─────────────────────────────────────────────
    scorer    = AgentScorer()
    scorecard = scorer.score(pipeline_results)

    # ── Step 8: Log everything ────────────────────────────────────
    logger.log_results(pipeline_results)
    logger.log_scorecard(scorecard)

    # ── Step 9: Generate reports ──────────────────────────────────
    if not args.no_report:
        print("\nGenerating reports...")
        reporter = Reporter()
        reporter.generate(
            pipeline_results,
            scorecard,
            run_id=logger.run_id
        )

    # ── Step 10: Final summary ────────────────────────────────────
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
        print("║  No failures detected ✅" + " " * 34 + "║")

    print(f"""╠══════════════════════════════════════════════════════════╣
║  Avg Latency : {scorecard.avg_latency_ms}ms                                     ║
║  Run ID      : {logger.run_id}                                        ║
╚══════════════════════════════════════════════════════════╝
    """)

    # Exit with error code if critical failures
    if scorecard.overall_score < 0.5:
        print("⚠️  CRITICAL: Agent scored below 0.5 — review required")
        sys.exit(1)


if __name__ == "__main__":
    main()