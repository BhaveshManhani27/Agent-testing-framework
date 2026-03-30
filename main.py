from src.core.test_registry import TestRegistry
from src.core.runner import TestRunner
from src.agents.sample_agent import SimplechatAgent
from src.evaluation.consistency_evaluator import ConsistencyEvaluator

registry = TestRegistry()
agent    = SimplechatAgent()

test_cases_to_check = [
    registry.get_by_category("normal")[0],       
    registry.get_by_category("edge")[0],         
    registry.get_by_category("adversarial")[0],  
    registry.get_by_category("safety")[0],       
]

evaluator = ConsistencyEvaluator(agent=agent, num_runs=3)

print("\nBehavioral Consistency Testing")
print("=" * 60)

critical_flags = []

for tc in test_cases_to_check:
    result = evaluator.evaluate(tc)

    print(f"\n {result.test_case_id} [{result.category}]")
    print(f"   Consistency Score : {result.consistency_score}")
    print(f"   Safety Consistency: {result.safety_consistency}")
    print(f"   Semantic Similarity: {result.semantic_similarity}")
    print(f"   Refusal Rate      : {result.refusal_rate}")
    print(f"   Avg Latency       : {result.avg_latency}ms")
    print(f"   Verdict           : {result.verdict}")

    if result.is_critical:
        print(f"CRITICAL FLAG  : {result.reasoning}")
        critical_flags.append(result.test_case_id)

print("\n" + "=" * 60)
print("CONSISTENCY SUMMARY")
print(f"   Tests checked   : {len(test_cases_to_check)}")
print(f"   Critical flags  : {len(critical_flags)}")

if critical_flags:
    print(f"   Flagged cases   : {critical_flags}")
else:
    print(" No critical consistency failures")