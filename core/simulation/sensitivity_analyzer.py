
from numbers import Real

import pandas as pd

from core.simulation.simulation_pipeline import run_simulation_pipeline


def run_sensitivity_analysis(
    reduction_levels: list[float] | None = None,
    data_directory: str = "data/synthetic",
    threshold: float = 90.0,
) -> dict:
    """
    Run multiple downtime-reduction scenarios and compare their impact.

    Each scenario is simulated independently against the same baseline data.
    """

    if reduction_levels is None:
        reduction_levels = [0, 10, 20, 30, 40]

    if not isinstance(reduction_levels, (list, tuple)) or not reduction_levels:
        raise ValueError("reduction_levels must be a non-empty list or tuple")

    validated_levels = []

    for level in reduction_levels:
        if (
            isinstance(level, bool)
            or not isinstance(level, Real)
            or not pd.notna(level)
            or not 0 <= level <= 100
        ):
            raise ValueError(
                "Each reduction level must be a number between 0 and 100"
            )

        if level in validated_levels:
            raise ValueError("Reduction levels must be unique")

        validated_levels.append(float(level))

    results = []

    for level in validated_levels:
        pipeline_result = run_simulation_pipeline(
            data_directory=data_directory,
            reduction_pct=level,
            threshold=threshold,
        )

        impact = pipeline_result["impact"]["impact"]
        baseline_metrics = pipeline_result["baseline"]["metrics"]
        scenario_metrics = pipeline_result["scenario"]["metrics"]

        results.append(
            {
                "reduction_pct": level,
                "additional_production_qty": impact[
                    "additional_production_qty"
                ],
                "attainment_improvement_pp": impact[
                    "attainment_improvement_pp"
                ],
                "orders_recovered_to_target": impact[
                    "orders_recovered_to_target"
                ],
                "downtime_reduction_min": impact[
                    "downtime_reduction_min"
                ],
                "estimated_incremental_operating_cost": impact[
                    "estimated_incremental_operating_cost"
                ],
                "simulated_total_actual_qty": scenario_metrics[
                    "simulated_total_actual_qty"
                ],
                "baseline_total_actual_qty": baseline_metrics[
                    "total_actual_qty"
                ],
                "provenance": pipeline_result["scenario"]["provenance"],
            }
        )

    comparison = pd.DataFrame(results)

    return {
        "analysis_type": "downtime_reduction_sensitivity",
        "provenance": "simulated",
        "threshold_pct": threshold,
        "scenarios_tested": len(comparison),
        "comparison": comparison,
        "assumptions": [
            "Each scenario uses the same baseline production dataset.",
            "Downtime reduction is applied as a percentage of recorded downtime.",
            "Recovered production is capped by the remaining planned quantity.",
            "Incremental operating cost is estimated from recovered production.",
        ],
    }
