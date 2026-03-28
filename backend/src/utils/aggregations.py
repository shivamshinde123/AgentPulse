"""Statistical calculations and quality scoring for analytics."""

import statistics
from typing import Dict, List, Optional, Tuple


def calculate_quality_score(
    cyclomatic_complexity: Optional[float],
    lines_of_code: Optional[int],
    has_type_hints: Optional[bool],
    max_nesting_depth: Optional[int] = None,
) -> float:
    """Calculate a 0-1 code quality score from metrics.

    Factors:
    - Lower complexity is better (40% weight)
    - Type hints present (30% weight)
    - Shallow nesting (30% weight)
    - Lines of code acts as a tie-breaker signal (not separately weighted)
    """
    score = 0.0

    if cyclomatic_complexity is not None:
        score += (1 - min(cyclomatic_complexity, 10) / 10) * 0.4
    else:
        score += 0.2  # neutral if unknown

    if has_type_hints:
        score += 0.3
    else:
        score += 0.1

    if max_nesting_depth is not None:
        score += 0.3 if max_nesting_depth <= 3 else 0.1
    else:
        score += 0.15  # neutral if unknown

    return max(0.0, min(1.0, score))


def detect_error_patterns(errors: List[Dict]) -> Dict:
    """Analyze error patterns across a set of errors.

    Args:
        errors: List of dicts with keys: error_type, recovery_interactions_count,
                was_resolved_in_next_interaction.

    Returns:
        Dict with distribution, most_common, avg_recovery, recovery_rate.
    """
    if not errors:
        return {
            "distribution": {},
            "most_common": None,
            "avg_recovery": 0.0,
            "recovery_rate": 0.0,
        }

    distribution: Dict[str, int] = {}
    for error in errors:
        error_type = error.get("error_type", "unknown")
        distribution[error_type] = distribution.get(error_type, 0) + 1

    most_common = max(distribution, key=distribution.get) if distribution else None

    recovery_counts = [
        e["recovery_interactions_count"]
        for e in errors
        if e.get("recovery_interactions_count") is not None
    ]
    avg_recovery = statistics.mean(recovery_counts) if recovery_counts else 0.0

    resolved = sum(1 for e in errors if e.get("was_resolved_in_next_interaction"))
    recovery_rate = resolved / len(errors)

    return {
        "distribution": distribution,
        "most_common": most_common,
        "avg_recovery": round(avg_recovery, 2),
        "recovery_rate": round(recovery_rate, 4),
    }


def compute_rolling_average(
    data: List[Tuple[str, float]],
    window: int = 5,
) -> List[Tuple[str, float]]:
    """Compute rolling average over time-series data.

    Args:
        data: List of (timestamp_str, value) tuples, sorted by time.
        window: Number of points in the rolling window.

    Returns:
        Smoothed list of (timestamp_str, averaged_value) tuples.
    """
    if len(data) <= window:
        return data

    result = []
    for i in range(len(data) - window + 1):
        window_values = [v for _, v in data[i : i + window]]
        avg = statistics.mean(window_values)
        result.append((data[i + window - 1][0], round(avg, 4)))

    return result


def detect_trend(values: List[float]) -> str:
    """Detect whether a series of values is improving, declining, or stable.

    Compares the average of the first half to the second half.
    """
    if len(values) < 4:
        return "stable"

    mid = len(values) // 2
    first_half = statistics.mean(values[:mid])
    second_half = statistics.mean(values[mid:])

    diff = second_half - first_half
    threshold = 0.05  # 5% change threshold

    if diff > threshold:
        return "improving"
    elif diff < -threshold:
        return "declining"
    return "stable"
