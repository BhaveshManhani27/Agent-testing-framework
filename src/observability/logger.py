import os
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List
from src.evaluation.pipeline import PipelineResult
from src.metrics.scorer import AgentScoreCard
from src.observability.log_config import get_logger

logger = get_logger(__name__)


class RunLogger:
    """
    Writes structured JSON logs for every test run.
    One line per test result — machine readable,
    queryable, and production-grade.

    Output files:
      logs/run_{run_id}.jsonl   ← one line per test
      logs/run_{run_id}_summary.json ← scorecard summary
    """

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.run_id = str(uuid.uuid4())[:8]  
        self.timestamp = datetime.now(timezone.utc).isoformat()

        self.detail_path = (
            self.log_dir / f"run_{self.run_id}.jsonl"
        )
        self.summary_path = (
            self.log_dir / f"run_{self.run_id}_summary.json"
        )

        logger.info("Logger initialized — run_id: %s", self.run_id)
        logger.info("  Detail log : %s", self.detail_path)
        logger.info("  Summary    : %s", self.summary_path)

    def log_results(self, results: List[PipelineResult]):
        """
        Writes one JSON line per PipelineResult.
        Each line is a complete record of that test.
        """
        with open(self.detail_path, "w", encoding = "utf-8") as f:
            for r in results:
                record = {
                    "run_id":       self.run_id,
                    "timestamp":    self.timestamp,
                    "test_case_id": r.test_case_id,
                    "category":     r.category,
                    "severity":     r.severity,
                    "input":        r.test_case_id,
                    "output":       r.agent_output[:500],
                    "verdict":      r.final_verdict,
                    "failure_type": r.failure_type,
                    "scores": {
                        "correctness": r.scores.get("correctness", 0),
                        "relevance":   r.scores.get("relevance", 0),
                        "safety":      r.scores.get("safety", 0),
                        "average":     r.scores.get("average", 0),
                    },
                    "confidence":   r.confidence,
                    "is_contested": r.is_contested,
                    "latency_ms":   r.latency_ms,
                    "trace":        r.trace,
                }
                f.write(json.dumps(record) + "\n")

        logger.info("Logged %d results → %s", len(results), self.detail_path)

    def log_scorecard(self, scorecard: AgentScoreCard):
        """
        Writes the full scorecard as a JSON summary file.
        """
        summary = {
            "run_id":    self.run_id,
            "timestamp": self.timestamp,
            "overall": {
                "score": scorecard.overall_score,
                "grade": scorecard.overall_grade,
                "label": scorecard.overall_label,
            },
            "dimensions": {
                "safety": {
                    "score": scorecard.safety_score.score,
                    "grade": scorecard.safety_score.grade,
                    "label": scorecard.safety_score.label,
                    "reasoning": scorecard.safety_score.reasoning,
                },
                "accuracy": {
                    "score": scorecard.accuracy_score.score,
                    "grade": scorecard.accuracy_score.grade,
                    "label": scorecard.accuracy_score.label,
                    "reasoning": scorecard.accuracy_score.reasoning,
                },
                "robustness": {
                    "score": scorecard.robustness_score.score,
                    "grade": scorecard.robustness_score.grade,
                    "label": scorecard.robustness_score.label,
                    "reasoning": scorecard.robustness_score.reasoning,
                },
                "consistency": {
                    "score": scorecard.consistency_score.score,
                    "grade": scorecard.consistency_score.grade,
                    "label": scorecard.consistency_score.label,
                    "reasoning": scorecard.consistency_score.reasoning,
                },
            },
            "counts": {
                "total":  scorecard.total_tests,
                "passed": scorecard.total_passed,
                "failed": scorecard.total_failed,
                "errors": scorecard.total_errors,
            },
            "pass_rate": scorecard.pass_rate,
            "failure_breakdown": scorecard.failure_counts,
            "category_scores":   scorecard.category_scores,
            "timing_ms": {
                "avg":    scorecard.avg_latency_ms,
                "median": scorecard.median_latency_ms,
                "max":    scorecard.max_latency_ms,
                "min":    scorecard.min_latency_ms,
            },
        }

        with open(self.summary_path, "w", encoding = "utf-8") as f:
            json.dump(summary, f, indent=2)

        logger.info("Scorecard saved → %s", self.summary_path)