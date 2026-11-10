
import unittest

from core.recommendations.recommendation_engine import (
    generate_recommendations,
)


class TestRecommendationEngine(unittest.TestCase):

    def setUp(self):
        self.evidence = {
            "evidence_id": "EV001",
            "source_diagnostic": "analyze_downtime_impact",
            "finding": (
                "Orders with recorded downtime have lower "
                "average production attainment."
            ),
            "severity": "high",
            "provenance": "synthetic",
        }

    def test_generate_recommendation(self):
        result = generate_recommendations([self.evidence])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["rule_id"], "DOWNTIME_001")

    def test_preserve_evidence_id(self):
        result = generate_recommendations([self.evidence])

        self.assertIn("EV001", result[0]["evidence_ids"])

    def test_duplicate_recommendations_are_combined(self):
        second = {
            **self.evidence,
            "evidence_id": "EV002",
        }

        result = generate_recommendations([
            self.evidence,
            second,
        ])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["evidence_count"], 2)
        self.assertEqual(
            result[0]["evidence_ids"],
            ["EV001", "EV002"],
        )

    def test_highest_severity_is_preserved(self):
        second = {
            **self.evidence,
            "evidence_id": "EV002",
            "severity": "critical",
        }

        result = generate_recommendations([
            self.evidence,
            second,
        ])

        self.assertEqual(result[0]["severity"], "critical")

    def test_unknown_finding_is_ignored(self):
        evidence = {
            **self.evidence,
            "finding": "Unknown operational issue.",
        }

        result = generate_recommendations([evidence])

        self.assertEqual(result, [])

    def test_empty_evidence(self):
        self.assertEqual(generate_recommendations([]), [])

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            generate_recommendations("invalid")

    def test_missing_evidence_id(self):
        evidence = {
            **self.evidence,
            "evidence_id": "",
        }

        with self.assertRaises(ValueError):
            generate_recommendations([evidence])

    def test_invalid_severity(self):
        evidence = {
            **self.evidence,
            "severity": "urgent",
        }

        with self.assertRaises(ValueError):
            generate_recommendations([evidence])

    def test_confidence_assessment_is_attached(self):
        result = generate_recommendations([self.evidence])

        self.assertIn("confidence_assessment", result[0])
        self.assertIn(
            "confidence_score",
            result[0]["confidence_assessment"],
        )

    def test_confidence_level_is_attached(self):
        result = generate_recommendations([self.evidence])

        confidence = result[0]["confidence_assessment"]

        self.assertIn(
            confidence["confidence_level"],
            ["low", "moderate", "high"],
        )

    def test_confidence_preserves_evidence_count(self):
        second = {
            **self.evidence,
            "evidence_id": "EV002",
            "provenance": "verified",
        }

        result = generate_recommendations([
            self.evidence,
            second,
        ])

        confidence = result[0]["confidence_assessment"]

        self.assertEqual(confidence["evidence_count"], 2)


if __name__ == "__main__":
    unittest.main()
