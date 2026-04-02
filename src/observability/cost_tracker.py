"""
Cost Tracker — Monitors API usage and estimated costs.

Tracks token usage per API call and provides per-test,
per-component (agent vs judge), and per-run cost reporting.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from src.observability.log_config import get_logger

logger = get_logger(__name__)


# ── Pricing per 1M tokens (approximate, as of 2026) ─────
# Update these when models change
PRICING = {
    "llama-3.3-70b-versatile": {
        "input": 0.59,    # $ per 1M input tokens
        "output": 0.79,   # $ per 1M output tokens
    },
    "llama-3.1-8b-instant": {
        "input": 0.05,
        "output": 0.08,
    },
    "gemini-2.5-flash-lite": {
        "input": 0.075,
        "output": 0.30,
    },
    "gpt-4o-mini": {
        "input": 0.15,
        "output": 0.60,
    },
    "gpt-4o": {
        "input": 2.50,
        "output": 10.00,
    },
    # Default fallback
    "default": {
        "input": 0.15,
        "output": 0.60,
    },
}


@dataclass
class APICall:
    """Record of a single API call."""
    component: str          # "agent" or "judge"
    model: str
    input_tokens: int
    output_tokens: int
    test_case_id: str = ""
    estimated_cost: float = 0.0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class CostReport:
    """Aggregated cost report for a full run."""
    total_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    total_estimated_cost: float = 0.0

    agent_calls: int = 0
    agent_tokens: int = 0
    agent_cost: float = 0.0

    judge_calls: int = 0
    judge_tokens: int = 0
    judge_cost: float = 0.0

    cost_per_test: float = 0.0
    model_breakdown: Dict[str, float] = field(default_factory=dict)


class CostTracker:
    """
    Tracks API usage and costs across a test run.

    Usage:
        tracker = CostTracker()
        tracker.record_call("agent", "llama-3.3-70b-versatile", 100, 50, "TC001")
        tracker.record_call("judge", "llama-3.3-70b-versatile", 200, 100, "TC001")
        report = tracker.get_report(num_tests=20)
    """

    def __init__(self):
        self.calls: List[APICall] = []

    def record_call(
        self,
        component: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        test_case_id: str = ""
    ):
        """Record a single API call."""
        cost = self._estimate_cost(model, input_tokens, output_tokens)

        call = APICall(
            component=component,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            test_case_id=test_case_id,
            estimated_cost=cost,
        )
        self.calls.append(call)

    def get_report(self, num_tests: int = 0) -> CostReport:
        """Generate an aggregated cost report."""
        agent_calls = [c for c in self.calls if c.component == "agent"]
        judge_calls = [c for c in self.calls if c.component == "judge"]

        total_input = sum(c.input_tokens for c in self.calls)
        total_output = sum(c.output_tokens for c in self.calls)
        total_cost = sum(c.estimated_cost for c in self.calls)

        agent_tokens = sum(c.total_tokens for c in agent_calls)
        agent_cost = sum(c.estimated_cost for c in agent_calls)

        judge_tokens = sum(c.total_tokens for c in judge_calls)
        judge_cost = sum(c.estimated_cost for c in judge_calls)

        # Model breakdown
        model_costs: Dict[str, float] = {}
        for call in self.calls:
            model_costs[call.model] = model_costs.get(call.model, 0) + call.estimated_cost

        cost_per_test = total_cost / num_tests if num_tests > 0 else 0.0

        return CostReport(
            total_calls=len(self.calls),
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            total_tokens=total_input + total_output,
            total_estimated_cost=round(total_cost, 6),
            agent_calls=len(agent_calls),
            agent_tokens=agent_tokens,
            agent_cost=round(agent_cost, 6),
            judge_calls=len(judge_calls),
            judge_tokens=judge_tokens,
            judge_cost=round(judge_cost, 6),
            cost_per_test=round(cost_per_test, 6),
            model_breakdown={k: round(v, 6) for k, v in model_costs.items()},
        )

    def print_report(self, num_tests: int = 0):
        """Log a formatted cost report."""
        report = self.get_report(num_tests)

        logger.info("─" * 50)
        logger.info("COST REPORT")
        logger.info("─" * 50)
        logger.info("  Total API calls    : %d", report.total_calls)
        logger.info("  Total tokens       : %d (in: %d, out: %d)",
                     report.total_tokens, report.total_input_tokens,
                     report.total_output_tokens)
        logger.info("  Estimated cost     : $%.4f", report.total_estimated_cost)
        logger.info("  ├── Agent          : $%.4f (%d calls, %d tokens)",
                     report.agent_cost, report.agent_calls, report.agent_tokens)
        logger.info("  └── Judge          : $%.4f (%d calls, %d tokens)",
                     report.judge_cost, report.judge_calls, report.judge_tokens)
        if num_tests > 0:
            logger.info("  Cost per test      : $%.6f", report.cost_per_test)
        for model, cost in report.model_breakdown.items():
            logger.info("  Model %s: $%.4f", model, cost)
        logger.info("─" * 50)

    def _estimate_cost(
        self, model: str, input_tokens: int, output_tokens: int
    ) -> float:
        """Estimate cost based on model pricing."""
        pricing = PRICING.get(model, PRICING["default"])
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost

    def to_dict(self) -> dict:
        """Serialize for JSON logging."""
        report = self.get_report()
        return {
            "total_calls": report.total_calls,
            "total_tokens": report.total_tokens,
            "estimated_cost_usd": report.total_estimated_cost,
            "agent_cost_usd": report.agent_cost,
            "judge_cost_usd": report.judge_cost,
            "cost_per_test_usd": report.cost_per_test,
            "model_breakdown": report.model_breakdown,
        }


# Global tracker instance
COST_TRACKER = CostTracker()
