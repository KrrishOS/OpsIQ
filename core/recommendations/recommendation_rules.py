
"""
Rule-based operational recommendation mapping.

Converts recognized diagnostic evidence into
explainable operational recommendations.
"""


DOWNTIME_DIAGNOSTIC = "analyze_downtime_impact"


def match_recommendation_rule(evidence_record: dict) -> dict | None:
    """
    Match an evidence record against known operational rules.

    Returns:
        dict: Recommendation template if a rule matches.
        None: If the evidence cannot be interpreted.
    """

    if not isinstance(evidence_record, dict):
        raise ValueError("Evidence record must be a dictionary")

    finding = evidence_record.get("finding")
    source = evidence_record.get("source_diagnostic")

    if not isinstance(finding, str) or not finding.strip():
        raise ValueError("Evidence finding must be non-empty")

    if source != DOWNTIME_DIAGNOSTIC:
        return None

    # Rule 1: Production attainment gap associated with downtime
    if finding == (
        "Orders with recorded downtime have lower "
        "average production attainment."
    ):
        return {
            "rule_id": "DOWNTIME_001",
            "title": "Investigate downtime-related production losses",
            "action": (
                "Compare affected production orders with downtime "
                "records and investigate recurring equipment issues."
            ),
            "rationale": (
                "Orders with recorded downtime show lower average "
                "production attainment than orders without downtime."
            ),
            "expected_impact": (
                "May help identify opportunities to improve "
                "production attainment."
            ),
            "risks": [
                "The observed relationship does not establish causation.",
                "Other production constraints may contribute to the gap."
            ],
            "assumptions": [
                "Production order and downtime records are reliable.",
                "The comparison groups are sufficiently representative."
            ],
            "validation_steps": [
                "Review downtime events for affected orders.",
                "Compare machine-level downtime patterns.",
                "Validate findings against maintenance records."
            ],
        }

    # Rule 2: Production shortfall without recorded downtime
    if finding == (
        "A proportion of orders without recorded downtime "
        "also miss the production target."
    ):
        return {
            "rule_id": "PRODUCTION_001",
            "title": "Investigate non-downtime production constraints",
            "action": (
                "Review production scheduling, material availability, "
                "quality losses and process constraints."
            ),
            "rationale": (
                "Some orders miss production targets despite having "
                "no recorded downtime."
            ),
            "expected_impact": (
                "May help identify production losses not captured "
                "by downtime records."
            ),
            "risks": [
                "Downtime records may be incomplete.",
                "Multiple operational constraints may overlap."
            ],
            "assumptions": [
                "Production targets are correctly recorded.",
                "Absence of recorded downtime does not guarantee "
                "absence of operational interruptions."
            ],
            "validation_steps": [
                "Review material issue and consumption records.",
                "Compare planned and actual production schedules.",
                "Inspect quality rejection and rework records."
            ],
        }

    # Rule 3: Largest recorded downtime contributor
    suffix = " is the largest recorded downtime contributor."

    if finding.endswith(suffix):
        category = finding.removesuffix(suffix).strip()

        if not category:
            return None

        return {
            "rule_id": "DOWNTIME_002",
            "title": f"Investigate {category} downtime",
            "action": (
                f"Prioritize investigation of {category.lower()} "
                "downtime events and their recurring reasons."
            ),
            "rationale": (
                f"{category} represents the largest recorded "
                "share of total downtime."
            ),
            "expected_impact": (
                "May help prioritize improvement efforts "
                "toward a major downtime contributor."
            ),
            "risks": [
                "The largest downtime category may not have "
                "the highest financial impact.",
                "Historical patterns may not predict future events."
            ],
            "assumptions": [
                "Downtime categories are consistently classified.",
                "Recorded downtime durations are accurate."
            ],
            "validation_steps": [
                "Review individual downtime events.",
                "Identify recurring downtime reasons.",
                "Compare event frequency and duration.",
                "Validate findings with maintenance or production teams."
            ],
        }

    # No recognized rule
    return None
