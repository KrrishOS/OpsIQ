
"""
Confidence assessment for operational recommendations.

Uses evidence provenance and completeness to calculate
an explainable heuristic confidence score.

The score is NOT a statistical probability.
"""

from core.evidence.evidence_builder import VALID_PROVENANCE


PROVENANCE_SCORES = {
    "synthetic": 40,
    "real_unverified": 70,
    "verified": 100,
}

CONFIDENCE_WEIGHTS = {
    "provenance": 0.60,
    "completeness": 0.40,
}


def assess_recommendation_confidence(
    recommendation: dict,
    evidence_records: list[dict],
) -> dict:
    """
    Assess confidence using evidence linked to a recommendation.

    Returns:
        dict: Confidence score, level, factors and limitations.
    """

    if not isinstance(recommendation, dict):
        raise ValueError("Recommendation must be a dictionary")

    if not isinstance(evidence_records, list):
        raise ValueError("Evidence records must be a list")

    evidence_ids = recommendation.get("evidence_ids")

    if (
        not isinstance(evidence_ids, list)
        or not evidence_ids
        or any(not isinstance(item, str) or not item.strip()
               for item in evidence_ids)
    ):
        raise ValueError("Recommendation must contain valid evidence IDs")

    if len(evidence_ids) != len(set(evidence_ids)):
        raise ValueError("Recommendation contains duplicate evidence IDs")

    # Index evidence records by their identifiers.
    evidence_lookup = {}

    for index, record in enumerate(evidence_records):

        if not isinstance(record, dict):
            raise ValueError(
                f"Evidence record at index {index} must be a dictionary"
            )

        evidence_id = record.get("evidence_id")

        if not isinstance(evidence_id, str) or not evidence_id.strip():
            raise ValueError("Evidence record must have a valid evidence ID")

        if evidence_id in evidence_lookup:
            raise ValueError(f"Duplicate evidence ID: {evidence_id}")

        evidence_lookup[evidence_id] = record

    # Every referenced evidence record must exist.
    missing_ids = set(evidence_ids) - set(evidence_lookup)

    if missing_ids:
        raise ValueError(
            f"Referenced evidence records not found: {sorted(missing_ids)}"
        )

    provenance_scores = []
    completeness_scores = []
    evidence_details = []

    for evidence_id in evidence_ids:

        record = evidence_lookup[evidence_id]

        provenance = record.get("provenance")

        if provenance not in VALID_PROVENANCE:
            raise ValueError(f"Invalid provenance: {provenance}")

        provenance_score = PROVENANCE_SCORES[provenance]

        # Check evidence completeness.
        completeness_checks = {
            "finding": (
                isinstance(record.get("finding"), str)
                and bool(record["finding"].strip())
            ),
            "supporting_evidence": (
                isinstance(record.get("supporting_evidence"), str)
                and bool(record["supporting_evidence"].strip())
            ),
            "source_diagnostic": (
                isinstance(record.get("source_diagnostic"), str)
                and bool(record["source_diagnostic"].strip())
            ),
            "source_datasets": (
                isinstance(record.get("source_datasets"), list)
                and bool(record["source_datasets"])
                and all(
                    isinstance(item, str) and item.strip()
                    for item in record["source_datasets"]
                )
            ),
            "observation_and_unit": (
                "observed_value" in record
                and isinstance(record.get("unit"), str)
                and bool(record["unit"].strip())
            ),
        }

        completeness_score = (
            sum(completeness_checks.values())
            / len(completeness_checks)
            * 100
        )

        missing_fields = [
            field
            for field, passed in completeness_checks.items()
            if not passed
        ]

        evidence_score = (
            provenance_score * CONFIDENCE_WEIGHTS["provenance"]
            + completeness_score * CONFIDENCE_WEIGHTS["completeness"]
        )

        provenance_scores.append(provenance_score)
        completeness_scores.append(completeness_score)

        evidence_details.append({
            "evidence_id": evidence_id,
            "provenance": provenance,
            "provenance_score": provenance_score,
            "completeness_score": round(completeness_score, 2),
            "evidence_score": round(evidence_score, 2),
            "missing_fields": missing_fields,
        })

    # Aggregate linked evidence scores.
    average_provenance = sum(provenance_scores) / len(provenance_scores)
    average_completeness = sum(completeness_scores) / len(completeness_scores)

    confidence_score = (
        average_provenance * CONFIDENCE_WEIGHTS["provenance"]
        + average_completeness * CONFIDENCE_WEIGHTS["completeness"]
    )

    confidence_score = round(confidence_score, 2)

    if confidence_score < 50:
        confidence_level = "low"
    elif confidence_score < 75:
        confidence_level = "moderate"
    else:
        confidence_level = "high"

    limitations = []

    if "synthetic" in [
        record["provenance"] for record in evidence_details
    ]:
        limitations.append(
            "Synthetic evidence does not establish real-world factory performance."
        )

    if "real_unverified" in [
        record["provenance"] for record in evidence_details
    ]:
        limitations.append(
            "Real-world evidence has not been independently verified."
        )

    if any(record["missing_fields"] for record in evidence_details):
        limitations.append(
            "Some evidence records have incomplete supporting information."
        )

    return {
        "confidence_score": confidence_score,
        "confidence_level": confidence_level,
        "scoring_method": "provenance_and_completeness_heuristic",
        "evidence_count": len(evidence_ids),
        "factors": {
            "average_provenance_score": round(average_provenance, 2),
            "average_completeness_score": round(average_completeness, 2),
            "provenance_weight": CONFIDENCE_WEIGHTS["provenance"],
            "completeness_weight": CONFIDENCE_WEIGHTS["completeness"],
        },
        "evidence_details": evidence_details,
        "limitations": limitations,
    }
