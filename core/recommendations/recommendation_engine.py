
"""
Operational recommendation engine.

Processes diagnostic evidence and generates
structured, explainable recommendations.
"""

from uuid import uuid4

from core.evidence.evidence_builder import (
    VALID_PROVENANCE,
    VALID_SEVERITIES,
)

from core.recommendations.recommendation_rules import (
    match_recommendation_rule,
)

from core.recommendations.confidence_assessor import (
    assess_recommendation_confidence,
)


SEVERITY_RANK = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


def generate_recommendations(evidence_records: list[dict]) -> list[dict]:
    """
    Generate recommendations from structured evidence records.

    Duplicate recommendations are combined while preserving
    all supporting evidence IDs.

    Returns:
        list[dict]: Structured operational recommendations.
    """

    if not isinstance(evidence_records, list):
        raise ValueError("Evidence records must be a list")

    recommendations = {}

    for index, evidence in enumerate(evidence_records):

        if not isinstance(evidence, dict):
            raise ValueError(
                f"Evidence record at index {index} must be a dictionary"
            )

        # Validate evidence identifier
        evidence_id = evidence.get("evidence_id")

        if not isinstance(evidence_id, str) or not evidence_id.strip():
            raise ValueError("Evidence ID must be a non-empty string")

        # Validate severity
        severity = evidence.get("severity")

        if severity not in VALID_SEVERITIES:
            raise ValueError(f"Invalid severity: {severity}")

        # Validate provenance
        provenance = evidence.get("provenance")

        if provenance not in VALID_PROVENANCE:
            raise ValueError(f"Invalid provenance: {provenance}")

        # Match evidence against recommendation rules
        template = match_recommendation_rule(evidence)

        if template is None:
            continue

        # Include the recommendation title in the key.
        # Different downtime categories must remain separate.
        recommendation_key = (
            template["rule_id"],
            template["title"],
        )

        if recommendation_key not in recommendations:

            recommendations[recommendation_key] = {
                "recommendation_id": str(uuid4()),
                **template,
                "severity": severity,
                "evidence_ids": [evidence_id],
                "provenance": [provenance],
                "evidence_count": 1,
                "source_diagnostics": [
                    evidence["source_diagnostic"]
                ],
            }

        else:
            recommendation = recommendations[recommendation_key]

            # Preserve unique evidence references
            if evidence_id not in recommendation["evidence_ids"]:
                recommendation["evidence_ids"].append(evidence_id)
                recommendation["evidence_count"] += 1

            # Preserve the highest observed severity
            if SEVERITY_RANK[severity] > SEVERITY_RANK[
                recommendation["severity"]
            ]:
                recommendation["severity"] = severity

            # Preserve distinct provenance values
            if provenance not in recommendation["provenance"]:
                recommendation["provenance"].append(provenance)

            source = evidence["source_diagnostic"]

            if source not in recommendation["source_diagnostics"]:
                recommendation["source_diagnostics"].append(source)


    # Convert grouped recommendations into a list
    final_recommendations = list(recommendations.values())

    # Attach confidence assessment to every recommendation
    for recommendation in final_recommendations:
        confidence = assess_recommendation_confidence(
            recommendation=recommendation,
            evidence_records=evidence_records,
        )

        recommendation["confidence_assessment"] = confidence

    return final_recommendations

