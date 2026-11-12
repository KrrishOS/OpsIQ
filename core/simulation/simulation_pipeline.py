
from pathlib import Path

from core.ingestion.csv_loader import load_csv

from core.simulation.baseline_simulator import (
    run_baseline_simulation,
)
from core.simulation.scenario_simulator import (
    simulate_downtime_reduction,
)
from core.simulation.impact_calculator import (
    calculate_simulation_impact,
)
from core.simulation.simulation_comparator import (
    build_simulation_comparison,
)


def run_simulation_pipeline(
    data_directory: str | Path = "data/synthetic",
    reduction_pct: float = 20.0,
    threshold: float = 90.0,
) -> dict:
    """
    Execute the complete factory simulation workflow.

    Workflow:
        1. Load factory datasets.
        2. Calculate baseline performance.
        3. Simulate downtime reduction.
        4. Calculate operational and financial impact.
        5. Generate baseline-versus-simulated comparison.
    """

    data_directory = Path(data_directory)

    if not data_directory.exists():
        raise FileNotFoundError(
            f"Data directory not found: {data_directory}"
        )

    if not data_directory.is_dir():
        raise ValueError(
            f"Expected a data directory: {data_directory}"
        )

    # Step 1: Load required factory datasets
    production_orders = load_csv(
        data_directory / "production_orders.csv",
        required_columns=[
            "order_id",
            "machine_id",
            "planned_qty",
            "actual_qty",
        ],
    )

    downtime = load_csv(
        data_directory / "downtime.csv",
        required_columns=[
            "downtime_id",
            "order_id",
            "duration_min",
            "downtime_type",
            "reason",
        ],
    )

    machines = load_csv(
        data_directory / "machines.csv",
        required_columns=[
            "machine_id",
            "capacity_per_hour",
            "efficiency_factor",
            "operating_cost_per_hour",
        ],
    )

    # Step 2: Calculate observed baseline performance
    baseline = run_baseline_simulation(
        production_orders=production_orders,
        downtime=downtime,
        machines=machines,
        threshold=threshold,
        provenance="synthetic",
    )

    # Step 3: Simulate the operational intervention
    scenario = simulate_downtime_reduction(
        baseline=baseline,
        reduction_pct=reduction_pct,
    )

    # Step 4: Calculate operational and financial impact
    impact = calculate_simulation_impact(
        baseline=baseline,
        scenario=scenario,
    )

    # Step 5: Generate structured comparison report
    comparison = build_simulation_comparison(
        baseline=baseline,
        scenario=scenario,
    )

    return {
        "pipeline_status": "completed",
        "provenance": {
            "baseline": baseline["provenance"],
            "scenario": scenario["provenance"],
        },
        "input_summary": {
            "production_orders": len(production_orders),
            "downtime_events": len(downtime),
            "machines": len(machines),
        },
        "baseline": baseline,
        "scenario": scenario,
        "impact": impact,
        "comparison": comparison,
    }
