
from numbers import Real
import math

VALID_SEVERITIES = {"critical", "high", "medium", "low"}


def classify_severity(
    impact_value: float,
    thresholds: dict[str, float],
) -> str:
    """
    Classify operational impact using configurable thresholds.

    Thresholds must be supplied from highest to lowest severity.
    """

    if (
        isinstance(impact_value, bool)
        or not isinstance(impact_value, Real)
        or not math.isfinite(impact_value)
        or impact_value < 0
    ):
        raise ValueError("Impact value must be finite and non-negative")

    if not isinstance(thresholds, dict):
        raise ValueError("Thresholds must be a dictionary")

    if set(thresholds) != VALID_SEVERITIES:
        raise ValueError(
            "Thresholds must define critical, high, medium and low"
        )

    for severity, value in thresholds.items():
        if (
            isinstance(value, bool)
            or not isinstance(value, Real)
            or not math.isfinite(value)
            or value < 0
        ):
            raise ValueError(
                f"Invalid threshold for {severity}"
            )

    if not (
        thresholds["critical"] > thresholds["high"]
        > thresholds["medium"] > thresholds["low"]
    ):
        raise ValueError(
            "Thresholds must decrease from critical to low"
        )

    if impact_value >= thresholds["critical"]:
        return "critical"

    if impact_value >= thresholds["high"]:
        return "high"

    if impact_value >= thresholds["medium"]:
        return "medium"

    return "low"
