
import math
from numbers import Real

import pandas as pd

from core.diagnostics.production_diagnostics import (
    analyze_production_downtime,
)

from core.evidence.evidence_builder import VALID_PROVENANCE


def run_baseline_simulation(
    production_orders: pd.DataFrame,
    downtime: pd.DataFrame,
    machines: pd.DataFrame,
    threshold: float = 90.0,
    provenance: str = "synthetic",
) -> dict:
    """
    Calculate baseline factory performance from supplied datasets.

    This function calculates existing performance. It does not
    simulate an operational intervention.
    """

    if not isinstance(machines, pd.DataFrame):
        raise ValueError("Machines must be a pandas DataFrame")

    required_machine_columns = {
        "machine_id",
        "capacity_per_hour",
        "efficiency_factor",
        "operating_cost_per_hour",
    }

    missing_columns = (
        required_machine_columns - set(machines.columns)
    )

    if missing_columns:
        raise ValueError(
            f"Missing machine columns: {sorted(missing_columns)}"
        )

    if machines["machine_id"].isna().any():
        raise ValueError("Machine IDs cannot be missing")

    if machines["machine_id"].duplicated().any():
        raise ValueError("Machine IDs must be unique")

    if (
        not isinstance(provenance, str)
        or provenance not in VALID_PROVENANCE
    ):
        raise ValueError(f"Invalid provenance: {provenance}")

    # Step 1: Reuse existing production and downtime diagnostics
    order_results = analyze_production_downtime(
        production_orders=production_orders,
        downtime=downtime,
        threshold=threshold,
    )

    # Step 2: Prepare machine master data
    machine_data = machines[
        [
            "machine_id",
            "capacity_per_hour",
            "efficiency_factor",
            "operating_cost_per_hour",
        ]
    ].copy()

    numeric_columns = [
        "capacity_per_hour",
        "efficiency_factor",
        "operating_cost_per_hour",
    ]

    for column in numeric_columns:
        machine_data[column] = pd.to_numeric(
            machine_data[column],
            errors="raise",
        )

        if (
            machine_data[column].isna().any()
            or not machine_data[column].map(
                lambda value: (
                    isinstance(value, Real)
                    and not isinstance(value, bool)
                    and math.isfinite(value)
                )
            ).all()
        ):
            raise ValueError(
                f"{column} must contain finite numeric values"
            )

    if (machine_data["capacity_per_hour"] <= 0).any():
        raise ValueError("Machine capacity must be positive")

    if (machine_data["efficiency_factor"] <= 0).any():
        raise ValueError("Machine efficiency must be positive")

    if (machine_data["operating_cost_per_hour"] < 0).any():
        raise ValueError("Operating cost cannot be negative")

    # Step 3: Attach machine information to production orders
    order_results = order_results.merge(
        machine_data,
        on="machine_id",
        how="left",
        validate="many_to_one",
        indicator=True,
    )

    unmatched_machines = order_results["_merge"] != "both"

    if unmatched_machines.any():
        missing_ids = (
            order_results.loc[unmatched_machines, "machine_id"]
            .drop_duplicates()
            .tolist()
        )

        raise ValueError(
            f"Production orders reference unknown machines: {missing_ids}"
        )

    order_results = order_results.drop(columns=["_merge"])

    # Step 4: Calculate baseline KPIs
    total_orders = len(order_results)

    total_planned_qty = float(
        order_results["planned_qty"].sum()
    )

    total_actual_qty = float(
        order_results["actual_qty"].sum()
    )

    weighted_attainment = (
        total_actual_qty / total_planned_qty * 100
    )

    baseline_metrics = {
        "total_orders": total_orders,
        "total_planned_qty": total_planned_qty,
        "total_actual_qty": total_actual_qty,
        "weighted_attainment_pct": round(
            weighted_attainment, 2
        ),
        "average_order_attainment_pct": round(
            float(order_results["attainment_pct"].mean()), 2
        ),
        "below_target_orders": int(
            order_results["below_threshold"].sum()
        ),
        "total_downtime_min": float(
            order_results["total_downtime_min"].sum()
        ),
        "total_downtime_events": int(
            order_results["downtime_events"].sum()
        ),
    }

    return {
        "scenario_type": "baseline_observation",
        "provenance": provenance,
        "threshold_pct": threshold,
        "metrics": baseline_metrics,
        "order_results": order_results,
    }
