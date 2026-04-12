from pathlib import Path
from datetime import datetime, timezone
from typing import List
from src.evaluation.pipeline import PipelineResult
from src.metrics.scorer import AgentScoreCard
from src.observability.log_config import get_logger

logger = get_logger(__name__)


class Reporter:
    """
    Generates two reports:
      1. reports/report_{timestamp}.txt  — clean terminal-style text report
      2. reports/report_{timestamp}.html — rich HTML report for sharing
    """

    def __init__(self, report_dir: str = "reports"):
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    def generate(
        self,
        results: List[PipelineResult],
        scorecard: AgentScoreCard,
        run_id: str = "N/A"
    ):
        """Generates both text and HTML reports."""
        self._generate_text(results, scorecard, run_id)
        self._generate_html(results, scorecard, run_id)

    # ─────────────────────────────────────────
    # Text Report
    # ─────────────────────────────────────────

    def _generate_text(
        self,
        results: List[PipelineResult],
        scorecard: AgentScoreCard,
        run_id: str
    ):
        path = self.report_dir / f"report_{self.timestamp}.txt"
        lines = []

        def L(text=""):
            lines.append(text)

        L("=" * 65)
        L("  AGENT TESTING FRAMEWORK — EVALUATION REPORT")
        L("=" * 65)
        L(f"  Run ID    : {run_id}")
        L(f"  Timestamp : {self.timestamp}")
        L(f"  Total Tests: {scorecard.total_tests}")
        L("=" * 65)

        # Overall
        L()
        L("  OVERALL SCORE")
        L("  " + "─" * 40)
        L(
            f"  Score : {scorecard.overall_score}  "
            f"Grade: {scorecard.overall_grade}  "
            f"[{scorecard.overall_label}]"
        )
        L(f"  Pass Rate : {scorecard.pass_rate}%  "
          f"({scorecard.total_passed}/{scorecard.total_tests})")

        # Dimensional scores
        L()
        L("  DIMENSIONAL SCORES")
        L("  " + "─" * 40)

        dims = [
            scorecard.safety_score,
            scorecard.accuracy_score,
            scorecard.robustness_score,
            scorecard.consistency_score,
        ]
        for d in dims:
            bar = "█" * int(d.score * 20) + "░" * (20 - int(d.score * 20))
            L(f"  {d.name:<12} {bar}  {d.score:.2f}  {d.grade}")
            L(f"               {d.reasoning}")
            L()

        # Failure taxonomy
        L("  FAILURE TAXONOMY")
        L("  " + "─" * 40)
        if scorecard.failure_counts:
            for ft, count in sorted(
                scorecard.failure_counts.items(), key=lambda x: -x[1]
            ):
                L(f"  {ft:<28} {count} case(s)")
        else:
            L("  No failures detected")
        L()

        # Category breakdown
        L("  CATEGORY BREAKDOWN")
        L("  " + "─" * 40)
        for cat, score in scorecard.category_scores.items():
            bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
            L(f"  {cat:<12} {bar}  {score:.2f}")
        L()

        # Timing
        L("  TIMING")
        L("  " + "─" * 40)
        L(f"  Average : {scorecard.avg_latency_ms}ms")
        L(f"  Median  : {scorecard.median_latency_ms}ms")
        L(f"  Max     : {scorecard.max_latency_ms}ms")
        L(f"  Min     : {scorecard.min_latency_ms}ms")
        L()

        # Per-test results
        L("  PER-TEST RESULTS")
        L("  " + "─" * 40)
        for r in results:
            icon    = "PASS" if r.passed else "FAIL"
            tag     = f"[{r.failure_type}]" if r.failure_type else ""
            L(
                f"  [{icon}] {r.test_case_id:<12} "
                f"cat={r.category:<12} "
                f"score={r.average_score:<6} "
                f"conf={r.confidence:<8} "
                f"{tag}"
            )
            if r.reasoning:
                L(f"         → {r.reasoning[:80]}")
        L()
        L("=" * 65)
        L("  END OF REPORT")
        L("=" * 65)

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        logger.info("Text report saved  → %s", path)

    # ─────────────────────────────────────────
    # HTML Report
    # ─────────────────────────────────────────

    def _generate_html(
        self,
        results: List[PipelineResult],
        scorecard: AgentScoreCard,
        run_id: str
    ):
        path = self.report_dir / f"report_{self.timestamp}.html"

        # ── Color helpers ────────────────────────────────────────
        def score_color(score: float) -> str:
            if score >= 0.90:
                return "#22c55e"   # green
            elif score >= 0.75:
                return "#3b82f6"   # blue
            elif score >= 0.50:
                return "#f59e0b"   # amber
            else:
                return "#ef4444"   # red

        def verdict_color(verdict: str) -> str:
            return {
                "PASS":  "#22c55e",
                "FAIL":  "#ef4444",
                "ERROR": "#f59e0b",
            }.get(verdict, "#6b7280")

        # ── Build per-test rows ───────────────────────────────────
        rows = ""
        for r in results:
            ft   = r.failure_type or "—"
            vcol = verdict_color(r.final_verdict)
            scol = score_color(r.average_score)
            rows += f"""
            <tr>
              <td>{r.test_case_id}</td>
              <td>{r.category}</td>
              <td>{r.severity}</td>
              <td style="color:{vcol};font-weight:bold">{r.final_verdict}</td>
              <td style="color:{scol}">{r.average_score}</td>
              <td>{r.confidence}</td>
              <td style="color:#ef4444">{ft}</td>
              <td>{r.latency_ms}ms</td>
            </tr>"""

        # ── Build dimension cards ─────────────────────────────────
        dims = [
            scorecard.safety_score,
            scorecard.accuracy_score,
            scorecard.robustness_score,
            scorecard.consistency_score,
        ]
        dim_cards = ""
        for d in dims:
            col  = score_color(d.score)
            pct  = int(d.score * 100)
            dim_cards += f"""
            <div class="card">
              <h3>{d.name}</h3>
              <div class="big-score" style="color:{col}">{d.score:.2f}</div>
              <div class="grade">{d.grade} — {d.label}</div>
              <div class="bar-bg">
                <div class="bar-fill"
                     style="width:{pct}%;background:{col}"></div>
              </div>
              <p class="reasoning">{d.reasoning}</p>
              <small>{d.passed_cases}/{d.total_cases} tests passed</small>
            </div>"""

        # ── Build failure rows ────────────────────────────────────
        failure_rows = ""
        if scorecard.failure_counts:
            for ft, count in sorted(
                scorecard.failure_counts.items(), key=lambda x: -x[1]
            ):
                failure_rows += f"""
                <tr>
                  <td style="color:#ef4444">{ft}</td>
                  <td>{count}</td>
                </tr>"""
        else:
            failure_rows = (
                "<tr><td colspan='2'>No failures ✅</td></tr>"
            )

        # ── Overall color ─────────────────────────────────────────
        oc = score_color(scorecard.overall_score)

        # ── Full HTML ─────────────────────────────────────────────
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Agent Evaluation Report</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont,
                   'Segoe UI', sans-serif;
      background: #0f172a; color: #e2e8f0;
      padding: 2rem;
    }}
    h1 {{ font-size: 1.8rem; margin-bottom: 0.3rem; color: #f8fafc; }}
    h2 {{ font-size: 1.2rem; color: #94a3b8;
          margin: 2rem 0 1rem; border-bottom: 1px solid #334155;
          padding-bottom: 0.4rem; }}
    h3 {{ font-size: 1rem; color: #cbd5e1; margin-bottom: 0.5rem; }}
    .meta {{ color: #64748b; font-size: 0.85rem; margin-bottom: 2rem; }}

    .overall {{
      background: #1e293b; border-radius: 12px;
      padding: 1.5rem; margin-bottom: 2rem;
      border-left: 4px solid {oc};
    }}
    .overall-score {{
      font-size: 3rem; font-weight: bold;
      color: {oc};
    }}
    .overall-grade {{
      font-size: 1.1rem; color: #94a3b8; margin-top: 0.3rem;
    }}
    .stats {{
      display: flex; gap: 2rem; margin-top: 1rem;
      flex-wrap: wrap;
    }}
    .stat {{ text-align: center; }}
    .stat-val {{
      font-size: 1.5rem; font-weight: bold; color: #f8fafc;
    }}
    .stat-label {{
      font-size: 0.75rem; color: #64748b; text-transform: uppercase;
    }}

    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 1rem; margin-bottom: 2rem;
    }}
    .card {{
      background: #1e293b; border-radius: 10px; padding: 1.2rem;
    }}
    .big-score {{
      font-size: 2.2rem; font-weight: bold; margin: 0.3rem 0;
    }}
    .grade {{ font-size: 0.85rem; color: #94a3b8; margin-bottom: 0.8rem; }}
    .bar-bg {{
      height: 6px; background: #334155; border-radius: 3px;
      margin-bottom: 0.7rem;
    }}
    .bar-fill {{ height: 100%; border-radius: 3px; }}
    .reasoning {{ font-size: 0.78rem; color: #64748b; }}

    table {{
      width: 100%; border-collapse: collapse;
      background: #1e293b; border-radius: 10px;
      overflow: hidden; margin-bottom: 2rem;
      font-size: 0.85rem;
    }}
    th {{
      background: #0f172a; color: #94a3b8;
      padding: 0.7rem 1rem; text-align: left;
      font-weight: 600; text-transform: uppercase;
      font-size: 0.75rem; letter-spacing: 0.05em;
    }}
    td {{ padding: 0.65rem 1rem; border-top: 1px solid #334155; }}
    tr:hover td {{ background: #263044; }}

    .timing-grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 1rem; margin-bottom: 2rem;
    }}
    .timing-card {{
      background: #1e293b; border-radius: 10px;
      padding: 1rem; text-align: center;
    }}
    .timing-val {{
      font-size: 1.4rem; font-weight: bold; color: #38bdf8;
    }}
    .timing-label {{
      font-size: 0.75rem; color: #64748b;
      text-transform: uppercase; margin-top: 0.3rem;
    }}
  </style>
</head>
<body>

  <h1>🤖 Agent Evaluation Report</h1>
  <p class="meta">
    Run ID: {run_id} &nbsp;|&nbsp;
    Timestamp: {self.timestamp} &nbsp;|&nbsp;
    Tests: {scorecard.total_tests}
  </p>

  <div class="overall">
    <div class="overall-score">{scorecard.overall_score:.2f}</div>
    <div class="overall-grade">
      Grade {scorecard.overall_grade} — {scorecard.overall_label}
    </div>
    <div class="stats">
      <div class="stat">
        <div class="stat-val">{scorecard.pass_rate}%</div>
        <div class="stat-label">Pass Rate</div>
      </div>
      <div class="stat">
        <div class="stat-val" style="color:#22c55e">
          {scorecard.total_passed}
        </div>
        <div class="stat-label">Passed</div>
      </div>
      <div class="stat">
        <div class="stat-val" style="color:#ef4444">
          {scorecard.total_failed}
        </div>
        <div class="stat-label">Failed</div>
      </div>
      <div class="stat">
        <div class="stat-val" style="color:#f59e0b">
          {scorecard.total_errors}
        </div>
        <div class="stat-label">Errors</div>
      </div>
    </div>
  </div>

  <h2>Dimensional Scores</h2>
  <div class="cards">{dim_cards}</div>

  <h2>Failure Taxonomy</h2>
  <table>
    <thead>
      <tr><th>Failure Type</th><th>Count</th></tr>
    </thead>
    <tbody>{failure_rows}</tbody>
  </table>

  <h2>Timing</h2>
  <div class="timing-grid">
    <div class="timing-card">
      <div class="timing-val">{scorecard.avg_latency_ms}ms</div>
      <div class="timing-label">Average</div>
    </div>
    <div class="timing-card">
      <div class="timing-val">{scorecard.median_latency_ms}ms</div>
      <div class="timing-label">Median</div>
    </div>
    <div class="timing-card">
      <div class="timing-val">{scorecard.max_latency_ms}ms</div>
      <div class="timing-label">Max</div>
    </div>
    <div class="timing-card">
      <div class="timing-val">{scorecard.min_latency_ms}ms</div>
      <div class="timing-label">Min</div>
    </div>
  </div>

  <h2>Per-Test Results</h2>
  <table>
    <thead>
      <tr>
        <th>ID</th><th>Category</th><th>Severity</th>
        <th>Verdict</th><th>Score</th><th>Confidence</th>
        <th>Failure Type</th><th>Latency</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>

</body>
</html>"""

        with open(path, "w", encoding="utf-8") as f:
            f.write(html)

        logger.info("HTML report saved  → %s", path)