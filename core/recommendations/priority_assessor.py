
"""
Explainable operational recommendation prioritization.

Separates operational priority from recommendation confidence.
Priority tiers are based on validated severity, while evidence
and confidence provide supporting context.
"""

from core.evidence.evidence_builder import (
    VALID_SEVERITIES,
)


SEVERITY_PRIORITY = {
    "low": "low",
    "medium": "medium",
    "high": "high",
    "critical": "critical",
}

PRIORITY_ORDER = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


def assess_recommendation_priority(
    recommendation: dict,
    evidence_records: list[dict],
) -> dict:
    """
    Assess the operational priority of a recommendation.

    Priority is determined by the highest validated severity
    among its linked evidence records.

    Confidence is reported separately and is not used to
    artificially increase or decrease operational severity.
    """

    if not isinstance(recommendation, dict):
        raise ValueError("Recommendation must be a dictionary")

    if not isinstance(evidence_records, list):
        raise ValueError("Evidence records must be a list")

    evidence_ids = recommendation.get("evidence_ids")

    if (
        not isinstance(evidence_ids, list)
        or not evidence_ids
        or any(
            not isinstance(item, str) or not item.strip()
            for item in evidence_ids
        )
    ):
        raise ValueError(
            "Recommendation must contain valid evidence IDs"
        )

    if len(evidence_ids) != len(set(evidence_ids)):
        raise ValueError(
            "Recommendation contains duplicate evidence IDs"
        )

    evidence_lookup = {}

    for index, record in enumerate(evidence_records):
        if not isinstance(record, dict):
            raise ValueError(
                f"Evidence record at index {index} must be a dictionary"
            )

        evidence_id = record.get("evidence_id")

        if (
            not isinstance(evidence_id, str)
            or not evidence_id.strip()
        ):
            raise ValueError(
                "Evidence record must have a valid evidence ID"
            )

        if evidence_id in evidence_lookup:
            raise ValueError(
                f"Duplicate evidence ID: {evidence_id}"
            )

        evidence_lookup[evidence_id] = record

    missing_ids = set(evidence_ids) - set(evidence_lookup)

    if missing_ids:
        raise ValueError(
            f"Referenced evidence records not found: {sorted(missing_ids)}"
        )

    linked_evidence = [
        evidence_lookup[evidence_id]
        for evidence_id in evidence_ids
    ]

    severities = []

    for record in linked_evidence:
        severity = record.get("severity")

        if severity not in VALID_SEVERITIES:
            raise ValueError(
                f"Invalid evidence severity: {severity}"
            )

        severities.append(severity)

    highest_severity = max(
        severities,
        key=lambda item: PRIORITY_ORDER[item],
    )

    priority_tier = SEVERITY_PRIORITY[highest_severity]

    confidence = recommendation.get(
        "confidence_assessment",
        {},
    )

    confidence_score = confidence.get("confidence_score")

    if confidence_score is not None:
        if (
            isinstance(confidence_score, bool)
            or not isinstance(confidence_score, (int, float))
            or not 0 <= confidence_score <= 100
        ):
            raise ValueError(
                "Confidence score must be between 0 and 100"
            )

    priority_reasons = [
        f"Highest linked evidence severity is {highest_severity}.",
        (
            f"{len(linked_evidence)} supporting evidence record(s) "
            "are linked to this recommendation."
        ),
    ]

    limitations = []

    if confidence_score is None:
        limitations.append(
            "Recommendation confidence has not been assessed."
        )
    elif confidence_score < 50:
        limitations.append(
            "Low confidence: validate supporting evidence before implementation."
        )
    elif confidence_score < 75:
        limitations.append(
            "Moderate confidence: further validation is advisable."
        )

    if any(
        record.get("provenance") == "synthetic"
        for record in linked_evidence
    ):
        limitations.append(
            "Synthetic evidence cannot establish real-world operational impact."
        )

    if not any(
        isinstance(record.get("observed_value"), (int, float))
        and not isinstance(record.get("observed_value"), bool)
        for record in linked_evidence
    ):
        limitations.append(
            "No numeric operational impact measurement is available."
        )

    if priority_tier in {"critical", "high"}:
        next_step = "investigate_and_validate"
    elif priority_tier == "medium":
        next_step = "investigate"
    else:
        next_step = "monitor"

    return {
        "priority_tier": priority_tier,
        "priority_basis": "highest_linked_evidence_severity",
        "highest_evidence_severity": highest_severity,
        "supporting_evidence_count": len(linked_evidence),
        "confidence_score": confidence_score,
        "priority_reasons": priority_reasons,
        "limitations": limitations,
        "recommended_next_step": next_step,
        "priority_order": PRIORITY_ORDER[priority_tier],
        "scoring_method": "severity_based_explainable_priority",
    }
