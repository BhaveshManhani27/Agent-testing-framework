from src.core.test_registry import TestRegistry
from src.core.runner import TestRunner, TestResult
from src.agents.sample_agent import SimplechatAgent
from src.evaluation.rule_evaluator import RuleEvaluator


registry = TestRegistry()
agent = SimplechatAgent()
runner = TestRunner(agent=agent, verbose=True)
results, summary = runner.run(registry.get_all())

print("\nRule Evaluation Results:")
print("─" * 60)

evaluator = RuleEvaluator()

for result in results:
    rule_result = evaluator.evaluate(result)

    # Attach to result for later use
    result.scores["rule"] = rule_result.verdict

    status_icon = {
        "PASS": "✅",
        "FAIL": "❌",
        "SKIP": "⏭️ "
    }.get(rule_result.verdict, "❓")

    print(f"{status_icon} {result.test_case.id} [{result.test_case.category}]")
    print(f"   Verdict : {rule_result.verdict}")
    print(f"   Reason  : {rule_result.reason}")

    if rule_result.failure_type:
        print(f"   Failure : {rule_result.failure_type}")

    print()