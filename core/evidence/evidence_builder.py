from datetime import datetime, timezone
from uuid import uuid4


VALID_SEVERITIES = {"critical", "high", "medium", "low"}

VALID_PROVENANCE = {
    "synthetic",
    "real_unverified",
    "verified",
}


def create_evidence_record(
    dataset_name: str,
    category: str,
    column: str,
    record_id: str | None,
    observed_value,
    expected_rule: str,
    severity: str,
    provenance: str,
    origin: str,
) -> dict:

    # Validate required text fields
    required_fields = {
        "dataset_name": dataset_name,
        "category": category,
        "column": column,
        "expected_rule": expected_rule,
        "origin": origin,
    }

    for field, value in required_fields.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be a non-empty string")

    # Validate severity
    if severity not in VALID_SEVERITIES:
        raise ValueError(f"Invalid severity: {severity}")

    # Validate provenance
    if provenance not in VALID_PROVENANCE:
        raise ValueError(f"Invalid provenance: {provenance}")

    evidence_record = {
        "issue_id": str(uuid4()),
        "dataset_name": dataset_name,
        "category": category,
        "column": column,
        "record_id": record_id,
        "observed_value": observed_value,
        "expected_rule": expected_rule,
        "severity": severity,
        "provenance": provenance,
        "origin": origin,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    return evidence_record