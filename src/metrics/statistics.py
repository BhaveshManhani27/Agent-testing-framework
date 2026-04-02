"""
Statistical analysis utilities for agent evaluation.

Provides:
  - Bootstrap confidence intervals for scores
  - Wilson score intervals for pass rates (small sample correction)
  - Cohen's d effect size for consistency comparisons
  - Summary statistics with proper uncertainty quantification
"""

import math
import random
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class ConfidenceInterval:
    """A score with proper uncertainty bounds."""
    point_estimate: float
    lower: float
    upper: float
    confidence_level: float = 0.95
    method: str = ""

    def __str__(self) -> str:
        return (
            f"{self.point_estimate:.4f} "
            f"[{self.lower:.4f}, {self.upper:.4f}] "
            f"({int(self.confidence_level * 100)}% CI, {self.method})"
        )


def bootstrap_ci(
    values: List[float],
    n_bootstrap: int = 1000,
    confidence: float = 0.95,
    statistic: str = "mean"
) -> ConfidenceInterval:
    """
    Compute bootstrap confidence interval for a statistic.

    Non-parametric — works for any distribution.
    Resamples with replacement and computes the statistic
    on each bootstrap sample, then takes percentiles.

    Args:
        values      : observed values
        n_bootstrap : number of bootstrap resamples
        confidence  : confidence level (default 0.95)
        statistic   : "mean" or "median"

    Returns:
        ConfidenceInterval with point estimate, lower, upper bounds
    """
    if not values:
        return ConfidenceInterval(
            point_estimate=0.0, lower=0.0, upper=0.0,
            confidence_level=confidence, method="bootstrap"
        )

    if len(values) == 1:
        v = values[0]
        return ConfidenceInterval(
            point_estimate=v, lower=v, upper=v,
            confidence_level=confidence, method="bootstrap (n=1)"
        )

    stat_fn = _mean if statistic == "mean" else _median
    point_estimate = stat_fn(values)

    # Generate bootstrap resamples
    boot_stats = []
    rng = random.Random(42)  # reproducible
    for _ in range(n_bootstrap):
        sample = [rng.choice(values) for _ in range(len(values))]
        boot_stats.append(stat_fn(sample))

    boot_stats.sort()

    # Percentile method
    alpha = 1 - confidence
    lower_idx = int(math.floor(alpha / 2 * n_bootstrap))
    upper_idx = int(math.ceil((1 - alpha / 2) * n_bootstrap)) - 1

    lower_idx = max(0, min(lower_idx, n_bootstrap - 1))
    upper_idx = max(0, min(upper_idx, n_bootstrap - 1))

    return ConfidenceInterval(
        point_estimate=round(point_estimate, 4),
        lower=round(boot_stats[lower_idx], 4),
        upper=round(boot_stats[upper_idx], 4),
        confidence_level=confidence,
        method="bootstrap"
    )


def wilson_score_interval(
    successes: int,
    total: int,
    confidence: float = 0.95
) -> ConfidenceInterval:
    """
    Wilson score interval for binomial proportions.

    Better than normal approximation for small samples
    (n < 30) and extreme proportions (p near 0 or 1).
    Standard in evaluation literature.

    Args:
        successes  : number of successes (e.g., passed tests)
        total      : total trials
        confidence : confidence level

    Returns:
        ConfidenceInterval with point estimate, lower, upper
    """
    if total == 0:
        return ConfidenceInterval(
            point_estimate=0.0, lower=0.0, upper=0.0,
            confidence_level=confidence, method="wilson"
        )

    p_hat = successes / total

    # Z-score for confidence level
    z = _z_score(confidence)
    z2 = z * z

    denominator = 1 + z2 / total
    center = (p_hat + z2 / (2 * total)) / denominator
    spread = (z / denominator) * math.sqrt(
        (p_hat * (1 - p_hat) / total) + (z2 / (4 * total * total))
    )

    lower = max(0.0, center - spread)
    upper = min(1.0, center + spread)

    return ConfidenceInterval(
        point_estimate=round(p_hat, 4),
        lower=round(lower, 4),
        upper=round(upper, 4),
        confidence_level=confidence,
        method="wilson"
    )


def cohens_d(
    group1: List[float],
    group2: List[float]
) -> float:
    """
    Cohen's d effect size between two groups.

    Interpretation:
      |d| < 0.2  → negligible
      |d| < 0.5  → small
      |d| < 0.8  → medium
      |d| >= 0.8 → large

    Args:
        group1, group2 : two lists of values to compare

    Returns:
        Cohen's d (positive = group1 > group2)
    """
    if not group1 or not group2:
        return 0.0

    mean1 = _mean(group1)
    mean2 = _mean(group2)

    var1 = _variance(group1)
    var2 = _variance(group2)

    # Pooled standard deviation
    n1, n2 = len(group1), len(group2)
    pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
    pooled_sd = math.sqrt(pooled_var) if pooled_var > 0 else 1e-10

    return round((mean1 - mean2) / pooled_sd, 4)


def effect_size_label(d: float) -> str:
    """Human-readable label for Cohen's d."""
    d_abs = abs(d)
    if d_abs < 0.2:
        return "NEGLIGIBLE"
    elif d_abs < 0.5:
        return "SMALL"
    elif d_abs < 0.8:
        return "MEDIUM"
    else:
        return "LARGE"


@dataclass
class StatisticalSummary:
    """Complete statistical summary for a set of scores."""
    n: int
    mean: float
    median: float
    std_dev: float
    ci: ConfidenceInterval
    pass_rate_ci: Optional[ConfidenceInterval] = None


def compute_summary(
    values: List[float],
    successes: Optional[int] = None,
    total: Optional[int] = None,
) -> StatisticalSummary:
    """
    Compute a full statistical summary including CIs.

    Args:
        values    : raw score values
        successes : number of passed tests (for Wilson CI)
        total     : total tests (for Wilson CI)
    """
    if not values:
        empty_ci = ConfidenceInterval(
            point_estimate=0.0, lower=0.0, upper=0.0, method="n/a"
        )
        return StatisticalSummary(
            n=0, mean=0.0, median=0.0, std_dev=0.0, ci=empty_ci
        )

    n = len(values)
    mean_val = _mean(values)
    median_val = _median(values)
    std = math.sqrt(_variance(values)) if n > 1 else 0.0

    ci = bootstrap_ci(values)

    pass_ci = None
    if successes is not None and total is not None:
        pass_ci = wilson_score_interval(successes, total)

    return StatisticalSummary(
        n=n,
        mean=round(mean_val, 4),
        median=round(median_val, 4),
        std_dev=round(std, 4),
        ci=ci,
        pass_rate_ci=pass_ci,
    )


# ── Internal helpers ─────────────────────────────────────

def _mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _median(values: List[float]) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    mid = n // 2
    if n % 2 == 0:
        return (sorted_vals[mid - 1] + sorted_vals[mid]) / 2
    return sorted_vals[mid]


def _variance(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean_val = _mean(values)
    return sum((x - mean_val) ** 2 for x in values) / (len(values) - 1)


def _z_score(confidence: float) -> float:
    """Approximate z-score for common confidence levels."""
    # Lookup for common values (avoids scipy dependency)
    z_table = {
        0.90: 1.645,
        0.95: 1.960,
        0.99: 2.576,
    }
    return z_table.get(confidence, 1.960)
