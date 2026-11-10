
import unittest

from core.recommendations.recommendation_rules import (
    match_recommendation_rule,
)


class TestRecommendationRules(unittest.TestCase):

    def test_downtime_attainment_rule(self):
        evidence = {
            "source_diagnostic": "analyze_downtime_impact",
            "finding": (
                "Orders with recorded downtime have lower "
                "average production attainment."
            ),
        }

        result = match_recommendation_rule(evidence)

        self.assertEqual(result["rule_id"], "DOWNTIME_001")

    def test_non_downtime_production_rule(self):
        evidence = {
            "source_diagnostic": "analyze_downtime_impact",
            "finding": (
                "A proportion of orders without recorded downtime "
                "also miss the production target."
            ),
        }

        result = match_recommendation_rule(evidence)

        self.assertEqual(result["rule_id"], "PRODUCTION_001")

    def test_downtime_category_rule(self):
        evidence = {
            "source_diagnostic": "analyze_downtime_impact",
            "finding": (
                "Mechanical is the largest recorded "
                "downtime contributor."
            ),
        }

        result = match_recommendation_rule(evidence)

        self.assertEqual(result["title"], "Investigate Mechanical downtime")

    def test_unknown_finding(self):
        evidence = {
            "source_diagnostic": "analyze_downtime_impact",
            "finding": "Unknown operational issue."
        }

        self.assertIsNone(match_recommendation_rule(evidence))

    def test_unsupported_diagnostic(self):
        evidence = {
            "source_diagnostic": "unknown_diagnostic",
            "finding": "Some issue."
        }

        self.assertIsNone(match_recommendation_rule(evidence))

    def test_invalid_evidence(self):
        with self.assertRaises(ValueError):
            match_recommendation_rule(None)


if __name__ == "__main__":
    unittest.main()
