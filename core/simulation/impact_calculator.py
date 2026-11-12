
import math
from numbers import Real

import pandas as pd


def calculate_simulation_impact(
    baseline: dict,
    scenario: dict,
) -> dict:
    """
    Compare baseline factory performance with simulated performance.

    Estimates incremental machine operating costs for additional
    production. Does not calculate total intervention ROI.
    """

    if not isinstance(baseline, dict):
        raise ValueError("Baseline must be a dictionary")

    if not isinstance(scenario, dict):
        raise ValueError("Scenario must be a dictionary")

    if baseline.get("scenario_type") != "baseline_observation":
        raise ValueError("Invalid baseline scenario")

    if scenario.get("scenario_type") != "downtime_reduction":
        raise ValueError("Invalid improvement scenario")

    if scenario.get("provenance") != "simulated":
        raise ValueError("Scenario must have simulated provenance")

    if scenario.get("baseline_provenance") != baseline.get("provenance"):
        raise ValueError("Baseline provenance mismatch")

    baseline_orders = baseline.get("order_results")
    scenario_orders = scenario.get("order_results")

    if not isinstance(baseline_orders, pd.DataFrame):
        raise ValueError("Invalid baseline order results")

    if not isinstance(scenario_orders, pd.DataFrame):
        raise ValueError("Invalid scenario order results")

    baseline_required = {
        "order_id",
        "planned_qty",
        "actual_qty",
        "total_downtime_min",
    }

    scenario_required = {
        "order_id",
        "simulated_actual_qty",
        "simulated_downtime_min",
        "recovered_qty",
        "capacity_per_hour",
        "efficiency_factor",
        "operating_cost_per_hour",
    }

    missing_baseline = baseline_required - set(
        baseline_orders.columns
    )

    missing_scenario = scenario_required - set(
        scenario_orders.columns
    )

    if missing_baseline or missing_scenario:
        raise ValueError(
            f"Missing baseline columns: {sorted(missing_baseline)}; "
            f"missing scenario columns: {sorted(missing_scenario)}"
        )

    baseline_data = baseline_orders.copy()
    scenario_data = scenario_orders.copy()

    for data, name in (
        (baseline_data, "Baseline"),
        (scenario_data, "Scenario"),
    ):
        if (
            data["order_id"].isna().any()
            or data["order_id"].duplicated().any()
        ):
            raise ValueError(
                f"{name} order IDs must be present and unique"
            )

    if set(baseline_data["order_id"]) != set(
        scenario_data["order_id"]
    ):
        raise ValueError("Baseline and scenario orders do not match")

    scenario_data = scenario_data.set_index("order_id").loc[
        baseline_data["order_id"]
    ].reset_index()

    baseline_numeric = [
        "planned_qty",
        "actual_qty",
        "total_downtime_min",
    ]

    scenario_numeric = [
        "simulated_actual_qty",
        "simulated_downtime_min",
        "recovered_qty",
        "capacity_per_hour",
        "efficiency_factor",
        "operating_cost_per_hour",
    ]

    for data, columns, name in (
        (baseline_data, baseline_numeric, "Baseline"),
        (scenario_data, scenario_numeric, "Scenario"),
    ):
        for column in columns:
            data[column] = pd.to_numeric(
                data[column], errors="raise"
            )

            if not data[column].map(
                lambda value: (
                    isinstance(value, Real)
                    and not isinstance(value, bool)
                    and math.isfinite(value)
                )
            ).all():
                raise ValueError(
                    f"{name} {column} must contain finite numbers"
                )

    if (baseline_data["planned_qty"] <= 0).any():
        raise ValueError("Planned quantities must be positive")

    if (
        baseline_data["actual_qty"] < 0
    ).any() or (scenario_data["simulated_actual_qty"] < 0).any():
        raise ValueError("Production quantities cannot be negative")

    if (
        baseline_data["total_downtime_min"] < 0
    ).any() or (scenario_data["simulated_downtime_min"] < 0).any():
        raise ValueError("Downtime cannot be negative")

    if (scenario_data["recovered_qty"] < 0).any():
        raise ValueError("Recovered production cannot be negative")

    if (scenario_data["capacity_per_hour"] <= 0).any():
        raise ValueError("Machine capacity must be positive")

    if (scenario_data["efficiency_factor"] <= 0).any():
        raise ValueError("Machine efficiency must be positive")

    if (scenario_data["operating_cost_per_hour"] < 0).any():
        raise ValueError("Operating cost cannot be negative")

        # Existing overproduction is valid baseline performance.
    # Simulation must not increase production beyond the
    # greater of planned quantity or existing actual quantity.

    maximum_allowed_qty = baseline_data[
        ["planned_qty", "actual_qty"]
    ].max(axis=1)

    if (
        scenario_data["simulated_actual_qty"]
        > maximum_allowed_qty
    ).any():
        raise ValueError(
            "Simulated production exceeds the allowed quantity"
        )

    if (
        scenario_data["simulated_actual_qty"]
        < baseline_data["actual_qty"]
    ).any():
        raise ValueError("Simulation cannot reduce actual production")

    threshold = baseline.get("threshold_pct")

    if (
        isinstance(threshold, bool)
        or not isinstance(threshold, Real)
        or not math.isfinite(threshold)
        or threshold < 0
    ):
        raise ValueError("Invalid baseline production threshold")

    # Baseline performance
    planned_qty = baseline_data["planned_qty"]
    actual_qty = baseline_data["actual_qty"]

    baseline_attainment = actual_qty / planned_qty * 100

    baseline_metrics = {
        "total_orders": len(baseline_data),
        "total_planned_qty": float(planned_qty.sum()),
        "total_actual_qty": float(actual_qty.sum()),
        "weighted_attainment_pct": round(
            float(actual_qty.sum() / planned_qty.sum() * 100), 2
        ),
        "average_order_attainment_pct": round(
            float(baseline_attainment.mean()), 2
        ),
        "below_target_orders": int(
            (baseline_attainment < threshold).sum()
        ),
        "total_downtime_min": float(
            baseline_data["total_downtime_min"].sum()
        ),
    }

    # Simulated performance
    simulated_qty = scenario_data["simulated_actual_qty"]
    simulated_attainment = simulated_qty / planned_qty * 100

    scenario_metrics = {
        "total_orders": len(scenario_data),
        "total_planned_qty": float(planned_qty.sum()),
        "total_actual_qty": float(simulated_qty.sum()),
        "weighted_attainment_pct": round(
            float(simulated_qty.sum() / planned_qty.sum() * 100), 2
        ),
        "average_order_attainment_pct": round(
            float(simulated_attainment.mean()), 2
        ),
        "below_target_orders": int(
            (simulated_attainment < threshold).sum()
        ),
        "total_downtime_min": float(
            scenario_data["simulated_downtime_min"].sum()
        ),
    }

    recovered_qty = scenario_data["recovered_qty"]

    # Estimate machine operating cost for additional production.
    incremental_cost = (
        recovered_qty
        / (
            scenario_data["capacity_per_hour"]
            * scenario_data["efficiency_factor"]
        )
        * scenario_data["operating_cost_per_hour"]
    ).sum()

    baseline_downtime = baseline_metrics["total_downtime_min"]
    simulated_downtime = scenario_metrics["total_downtime_min"]

    return {
        "comparison_type": "baseline_vs_simulated",
        "baseline_provenance": baseline.get("provenance"),
        "scenario_provenance": scenario.get("provenance"),

        "baseline_metrics": baseline_metrics,
        "scenario_metrics": scenario_metrics,

        "impact": {
            "additional_production_qty": round(
                scenario_metrics["total_actual_qty"]
                - baseline_metrics["total_actual_qty"],
                2,
            ),
            "attainment_improvement_pp": round(
                scenario_metrics["weighted_attainment_pct"]
                - baseline_metrics["weighted_attainment_pct"],
                2,
            ),
            "orders_recovered_to_target": (
                baseline_metrics["below_target_orders"]
                - scenario_metrics["below_target_orders"]
            ),
            "downtime_reduction_min": round(
                baseline_downtime - simulated_downtime, 2
            ),
            "downtime_reduction_pct": round(
                (baseline_downtime - simulated_downtime)
                / baseline_downtime * 100,
                2,
            ) if baseline_downtime > 0 else 0.0,
            "estimated_incremental_operating_cost": round(
                float(incremental_cost), 2
            ),
        },

        "assumptions": [
            "Baseline and simulated orders represent the same period.",
            "Machine capacity and efficiency remain constant.",
            "Operating costs are variable per productive machine hour.",
            "Material, labor and demand constraints are not modeled.",
        ],
    }
