
import pandas as pd

from core.simulation.impact_calculator import (
    calculate_simulation_impact,
)


def build_simulation_comparison(
    baseline: dict,
    scenario: dict,
) -> dict:
    """
    Build a structured baseline-versus-simulated
    operational performance comparison.
    """

    impact_report = calculate_simulation_impact(
        baseline=baseline,
        scenario=scenario,
    )

    baseline_metrics = impact_report["baseline_metrics"]
    scenario_metrics = impact_report["scenario_metrics"]
    impact = impact_report["impact"]

    comparison_rows = [
        {
            "metric": "Total production",
            "baseline": baseline_metrics["total_actual_qty"],
            "simulated": scenario_metrics["total_actual_qty"],
            "change": impact["additional_production_qty"],
            "unit": "units",
            "direction": "increase",
        },
        {
            "metric": "Weighted attainment",
            "baseline": baseline_metrics["weighted_attainment_pct"],
            "simulated": scenario_metrics["weighted_attainment_pct"],
            "change": impact["attainment_improvement_pp"],
            "unit": "percentage points",
            "direction": "increase",
        },
        {
            "metric": "Average order attainment",
            "baseline": baseline_metrics[
                "average_order_attainment_pct"
            ],
            "simulated": scenario_metrics[
                "average_order_attainment_pct"
            ],
            "change": round(
                scenario_metrics["average_order_attainment_pct"]
                - baseline_metrics["average_order_attainment_pct"],
                2,
            ),
            "unit": "percentage points",
            "direction": "increase",
        },
        {
            "metric": "Orders below target",
            "baseline": baseline_metrics["below_target_orders"],
            "simulated": scenario_metrics["below_target_orders"],
            "change": (
                baseline_metrics["below_target_orders"]
                - scenario_metrics["below_target_orders"]
            ),
            "unit": "orders recovered",
            "direction": "decrease",
        },
        {
            "metric": "Total downtime",
            "baseline": baseline_metrics["total_downtime_min"],
            "simulated": scenario_metrics["total_downtime_min"],
            "change": impact["downtime_reduction_min"],
            "unit": "minutes reduced",
            "direction": "decrease",
        },
    ]

    comparison_table = pd.DataFrame(comparison_rows)

    return {
        "report_type": "baseline_vs_simulated",
        "provenance": "simulated",
        "baseline_provenance": impact_report[
            "baseline_provenance"
        ],
        "scenario_provenance": impact_report[
            "scenario_provenance"
        ],
        "scenario_reduction_pct": scenario.get(
            "reduction_pct"
        ),
        "comparison": comparison_table,
        "financial_impact": {
            "estimated_incremental_operating_cost": impact[
                "estimated_incremental_operating_cost"
            ],
        },
        "operational_impact": {
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
            "downtime_reduction_pct": impact[
                "downtime_reduction_pct"
            ],
        },
        "assumptions": impact_report["assumptions"],
    }
