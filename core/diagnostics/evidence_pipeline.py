
from core.diagnostics.production_diagnostics import (
    analyze_downtime_impact,
)

from core.evidence.diagnostic_evidence import (
    build_diagnostic_evidence_records,
)


def analyze_downtime_with_evidence(
    production_orders,
    downtime,
    source_datasets: list[str],
    severity: str,
    origin: str,
    threshold: float = 90.0,
    severity_thresholds: dict | None = None,
) -> dict:
    """
    Run downtime diagnostics and convert findings
    into structured evidence records.
    """

    # Step 1: Run production diagnostics
    diagnostic_report = analyze_downtime_impact(
        production_orders,
        downtime,
        threshold=threshold,
    )

    # Step 2: Build structured evidence records
    evidence_records = build_diagnostic_evidence_records(
        diagnostic_report=diagnostic_report,
        source_diagnostic="analyze_downtime_impact",
        source_datasets=source_datasets,
        severity=severity,
        origin=origin,
        severity_thresholds=severity_thresholds,
    )

    # Step 3: Return both outputs
    return {
        "diagnostic_report": diagnostic_report,
        "evidence_records": evidence_records,
    }
