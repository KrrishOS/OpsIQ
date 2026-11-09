
import math
from numbers import Real
from datetime import datetime, timezone
from uuid import uuid4

from core.evidence.evidence_builder import (
    VALID_PROVENANCE,
    VALID_SEVERITIES,
)

from core.evidence.severity_classifier import classify_severity


def build_diagnostic_evidence_records(
    diagnostic_report: dict,
    source_diagnostic: str,
    source_datasets: list[str],
    severity: str,
    origin: str,
    severity_thresholds: dict | None = None,
) -> list[dict]:
    """
    Convert diagnostic findings into structured evidence records.
    Supports metric-specific severity classification.
    """

    if not isinstance(diagnostic_report, dict):
        raise ValueError("Diagnostic report must be a dictionary")

    findings = diagnostic_report.get("findings")

    if not isinstance(findings, list):
        raise ValueError("Diagnostic report must contain a findings list")

    if not isinstance(source_diagnostic, str) or not source_diagnostic.strip():
        raise ValueError("Source diagnostic must be non-empty")

    if (
        not isinstance(source_datasets, list)
        or not source_datasets
        or any(not isinstance(d, str) or not d.strip() for d in source_datasets)
    ):
        raise ValueError("Source datasets must be a non-empty list of strings")

    if not isinstance(origin, str) or not origin.strip():
        raise ValueError("Origin must be non-empty")

    if not isinstance(severity, str) or severity not in VALID_SEVERITIES:
        raise ValueError(f"Invalid severity: {severity}")

    if severity_thresholds is not None and not isinstance(
        severity_thresholds, dict
    ):
        raise ValueError("Severity thresholds must be a dictionary")

    evidence_records = []

    for index, finding in enumerate(findings):

        if not isinstance(finding, dict):
            raise ValueError(f"Finding at index {index} must be a dictionary")

        required_fields = (
            "finding",
            "observed_value",
            "unit",
            "evidence",
            "provenance",
        )

        for field in required_fields:
            if field not in finding:
                raise ValueError(
                    f"Finding at index {index} is missing {field}"
                )

        if not isinstance(finding["finding"], str) or not finding["finding"].strip():
            raise ValueError("Finding description must be non-empty")

        if not isinstance(finding["unit"], str) or not finding["unit"].strip():
            raise ValueError("Finding unit must be non-empty")

        if not isinstance(finding["evidence"], str) or not finding["evidence"].strip():
            raise ValueError("Supporting evidence must be non-empty")

        provenance = finding["provenance"]

        if not isinstance(provenance, str) or provenance not in VALID_PROVENANCE:
            raise ValueError(f"Invalid provenance: {provenance}")

        observed_value = finding["observed_value"]
        unit = finding["unit"]

        if observed_value is not None:
            if isinstance(observed_value, bool) or not isinstance(observed_value, Real):
                raise ValueError("Observed value must be numeric or None")

            if not math.isfinite(observed_value):
                raise ValueError("Observed value must be finite")

        # Step: Classify severity using metric-specific thresholds
        assigned_severity = severity
        severity_basis = "caller_supplied"

        if (
            severity_thresholds is not None
            and unit in severity_thresholds
            and observed_value is not None
            and observed_value >= 0
        ):
            assigned_severity = classify_severity(
                observed_value,
                severity_thresholds[unit],
            )
            severity_basis = f"threshold_based: {unit}"

        elif observed_value is None:
            severity_basis = "fallback: no_numeric_observation"

        elif observed_value < 0:
            severity_basis = "fallback: negative_directional_value"

        elif severity_thresholds is not None:
            severity_basis = "fallback: no_thresholds_for_unit"

        record = {
            "evidence_id": str(uuid4()),
            "source_diagnostic": source_diagnostic,
            "source_datasets": source_datasets.copy(),
            "category": "operational_diagnostic",
            "finding": finding["finding"],
            "observed_value": observed_value,
            "unit": unit,
            "supporting_evidence": finding["evidence"],
            "severity": assigned_severity,
            "severity_basis": severity_basis,
            "provenance": provenance,
            "origin": origin,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        evidence_records.append(record)

    return evidence_records
