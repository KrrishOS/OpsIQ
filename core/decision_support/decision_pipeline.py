
from pathlib import Path

from core.ingestion.csv_loader import load_csv

from core.decision_support.data_quality_gate import (
    run_data_quality_gate,
)

from core.diagnostics.evidence_pipeline import (
    analyze_downtime_with_evidence,
)

from core.recommendations.recommendation_engine import (
    generate_recommendations,
)

from core.simulation.simulation_pipeline import (
    run_simulation_pipeline,
)


def run_decision_pipeline(
    data_directory: str | Path = "data/synthetic",
    reduction_pct: float = 20.0,
    threshold: float = 90.0,
    severity: str = "medium",
    origin: str = "synthetic_factory_data",
    severity_thresholds: dict | None = None,
) -> dict:
    """
    Execute the unified manufacturing decision-support workflow.

    Workflow:
        1. Validate available datasets through the quality gate.
        2. Stop if critical input integrity issues are detected.
        3. Load diagnostic datasets.
        4. Run production diagnostics and generate evidence.
        5. Generate evidence-backed recommendations.
        6. Run baseline and scenario simulations.
        7. Consolidate all outputs into one decision report.

    Returns:
        dict: Consolidated decision-support report.
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

    # Step 1: Run the data-quality gate.
    data_quality_report = run_data_quality_gate(
        data_directory=data_directory
    )

    # Step 2: Stop if critical integrity issues are detected.
    if data_quality_report["blocked"]:
        blocking_issues = (
            len(data_quality_report["critical_required_issues"])
            + len(data_quality_report["missing_required_datasets"])
        )

        return {
            "pipeline_status": "blocked",

            "provenance": {
                "input_data": "synthetic",
                "input_origin": origin,
                "simulation": "not_run",
            },

            "data_quality": data_quality_report,

            "input_summary": {
                "datasets_checked": (
                    data_quality_report["datasets_checked"]
                ),
                "missing_required_datasets": (
                    data_quality_report["missing_required_datasets"]
                ),
            },

            "diagnostics": None,

            "evidence": {
                "total_records": 0,
                "records": [],
            },

            "recommendations": {
                "total": 0,
                "records": [],
            },

            "simulation": None,

            "decision_summary": {
                "total_findings": 0,
                "total_recommendations": 0,
                "simulation_status": "not_run",
                "additional_production_qty": None,
                "blocking_issues": blocking_issues,
                "data_quality_status": data_quality_report["status"],
                "data_quality_warnings": (
                    data_quality_report["warning_count"]
                ),
            },
        }

    # Step 3: Load diagnostic datasets.
    production_orders = load_csv(
        data_directory / "production_orders.csv"
    )

    downtime = load_csv(
        data_directory / "downtime.csv"
    )

    # Step 4: Run diagnostics and generate evidence.
    diagnostic_output = analyze_downtime_with_evidence(
        production_orders=production_orders,
        downtime=downtime,
        source_datasets=[
            "production_orders.csv",
            "downtime.csv",
        ],
        severity=severity,
        origin=origin,
        threshold=threshold,
        severity_thresholds=severity_thresholds,
    )

    diagnostic_report = diagnostic_output[
        "diagnostic_report"
    ]

    evidence_records = diagnostic_output[
        "evidence_records"
    ]

    # Step 5: Generate recommendations and confidence.
    recommendations = generate_recommendations(
        evidence_records
    )

    # Step 6: Run baseline and scenario simulations.
    simulation_output = run_simulation_pipeline(
        data_directory=data_directory,
        reduction_pct=reduction_pct,
        threshold=threshold,
    )

    # Step 7: Consolidate the decision-support report.
    return {
        "pipeline_status": "completed",

        "provenance": {
            "input_data": "synthetic",
            "input_origin": origin,
            "simulation": simulation_output["provenance"],
        },

        "data_quality": data_quality_report,

        "input_summary": {
            "production_orders": len(production_orders),
            "downtime_events": len(downtime),
            "datasets_checked": (
                data_quality_report["datasets_checked"]
            ),
        },

        "diagnostics": diagnostic_report,

        "evidence": {
            "total_records": len(evidence_records),
            "records": evidence_records,
        },

        "recommendations": {
            "total": len(recommendations),
            "records": recommendations,
        },

        "simulation": simulation_output,

        "decision_summary": {
            "total_findings": len(evidence_records),
            "total_recommendations": len(recommendations),
            "simulation_status": simulation_output[
                "pipeline_status"
            ],
            "additional_production_qty": (
                simulation_output["impact"]["impact"][
                    "additional_production_qty"
                ]
            ),
            "data_quality_status": data_quality_report["status"],
            "data_quality_warnings": (
                data_quality_report["warning_count"]
            ),
        },
    }
