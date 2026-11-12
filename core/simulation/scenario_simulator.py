
import math
from numbers import Real

import pandas as pd


def simulate_downtime_reduction(
    baseline: dict,
    reduction_pct: float,
) -> dict:
    """
    Simulate the production impact of reducing downtime.

    Assumes recovered time can be used for production,
    subject to remaining planned order quantity.
    """

    if (
        isinstance(reduction_pct, bool)
        or not isinstance(reduction_pct, Real)
        or not math.isfinite(reduction_pct)
        or not 0 <= reduction_pct <= 100
    ):
        raise ValueError(
            "Reduction percentage must be between 0 and 100"
        )

    if not isinstance(baseline, dict):
        raise ValueError("Baseline must be a dictionary")

    if baseline.get("scenario_type") != "baseline_observation":
        raise ValueError("Expected a baseline observation")

    orders = baseline.get("order_results")

    if not isinstance(orders, pd.DataFrame):
        raise ValueError("Baseline order results must be a DataFrame")

    required_columns = {
        "order_id",
        "planned_qty",
        "actual_qty",
        "total_downtime_min",
        "capacity_per_hour",
        "efficiency_factor",
    }

    missing = required_columns - set(orders.columns)

    if missing:
        raise ValueError(
            f"Missing simulation columns: {sorted(missing)}"
        )

    orders = orders.copy()

    numeric_columns = required_columns - {"order_id"}

    for column in numeric_columns:
        orders[column] = pd.to_numeric(
            orders[column], errors="raise"
        )

        if not orders[column].map(
            lambda x: isinstance(x, Real)
            and not isinstance(x, bool)
            and math.isfinite(x)
        ).all():
            raise ValueError(
                f"{column} must contain finite numeric values"
            )

    if (orders["planned_qty"] <= 0).any():
        raise ValueError("Planned quantity must be positive")

    if (orders["actual_qty"] < 0).any():
        raise ValueError("Actual quantity cannot be negative")

    if (orders["total_downtime_min"] < 0).any():
        raise ValueError("Downtime cannot be negative")

    if (orders["capacity_per_hour"] <= 0).any():
        raise ValueError("Machine capacity must be positive")

    if (orders["efficiency_factor"] <= 0).any():
        raise ValueError("Machine efficiency must be positive")

    reduction_fraction = reduction_pct / 100

    orders["recovered_time_min"] = (
        orders["total_downtime_min"] * reduction_fraction
    )

    orders["potential_recovered_qty"] = (
        orders["recovered_time_min"]
        / 60
        * orders["capacity_per_hour"]
        * orders["efficiency_factor"]
    )

    orders["remaining_planned_qty"] = (
        orders["planned_qty"] - orders["actual_qty"]
    ).clip(lower=0)

    orders["recovered_qty"] = orders[
        ["potential_recovered_qty", "remaining_planned_qty"]
    ].min(axis=1)

    orders["simulated_actual_qty"] = (
        orders["actual_qty"] + orders["recovered_qty"]
    )

    orders["simulated_attainment_pct"] = (
        orders["simulated_actual_qty"]
        / orders["planned_qty"]
        * 100
    )

    orders["simulated_downtime_min"] = (
        orders["total_downtime_min"]
        - orders["recovered_time_min"]
    )

    return {
        "scenario_type": "downtime_reduction",
        "provenance": "simulated",
        "baseline_provenance": baseline.get("provenance"),
        "reduction_pct": float(reduction_pct),
        "assumptions": [
            "Recovered downtime is available for production.",
            "Machine capacity and efficiency remain constant.",
            "Material and labor availability are sufficient.",
            "Additional output is capped at planned quantity.",
        ],
        "metrics": {
            "total_recovered_time_min": float(
                orders["recovered_time_min"].sum()
            ),
            "total_recovered_qty": float(
                orders["recovered_qty"].sum()
            ),
            "simulated_total_actual_qty": float(
                orders["simulated_actual_qty"].sum()
            ),
        },
        "order_results": orders,
    }
