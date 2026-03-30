from src.core.test_registry import TestRegistry
from src.core.runner import TestRunner
from src.agents.sample_agent import SimplechatAgent

registry = TestRegistry()
registry.summary()

agent = SimplechatAgent()

runner = TestRunner(agent=agent, verbose=True)
results, summary = runner.run(registry.get_all())

print("\nSample Result:")
print(f"   Test ID : {results[0].test_case.id}")
print(f"   Input   : {results[0].test_case.input}")
print(f"   Output  : {results[0].agent_output[:100]}")
print(f"   Latency : {results[0].latency_ms}ms")
