
import unittest

from core.recommendations.priority_assessor import (
    assess_recommendation_priority,
)


class TestPriorityAssessor(unittest.TestCase):

    def setUp(self):
        self.evidence_records = [
            {
                "evidence_id": "EV001",
                "severity": "high",
                "provenance": "synthetic",
                "observed_value": 4668,
                "unit": "minutes",
            },
            {
                "evidence_id": "EV002",
                "severity": "medium",
                "provenance": "synthetic",
                "observed_value": 12.05,
                "unit": "percentage_points",
            },
        ]

        self.recommendation = {
            "recommendation_id": "REC001",
            "evidence_ids": ["EV001"],
            "confidence_assessment": {
                "confidence_score": 64.0,
            },
        }

    def test_high_severity_produces_high_priority(self):
        result = assess_recommendation_priority(
            self.recommendation,
            self.evidence_records,
        )

        self.assertEqual(
            result["priority_tier"],
            "high",
        )

    def test_highest_linked_severity_is_used(self):
        recommendation = {
            "evidence_ids": ["EV001", "EV002"],
            "confidence_assessment": {
                "confidence_score": 64.0,
            },
        }

        result = assess_recommendation_priority(
            recommendation,
            self.evidence_records,
        )

        self.assertEqual(
            result["highest_evidence_severity"],
            "high",
        )

    def test_confidence_is_kept_separate_from_priority(self):
        recommendation = {
            "evidence_ids": ["EV001"],
            "confidence_assessment": {
                "confidence_score": 35.0,
            },
        }

        result = assess_recommendation_priority(
            recommendation,
            self.evidence_records,
        )

        self.assertEqual(result["priority_tier"], "high")
        self.assertEqual(result["confidence_score"], 35.0)

    def test_synthetic_evidence_adds_limitation(self):
        result = assess_recommendation_priority(
            self.recommendation,
            self.evidence_records,
        )

        self.assertTrue(
            any(
                "Synthetic evidence" in limitation
                for limitation in result["limitations"]
            )
        )

    def test_missing_numeric_impact_adds_limitation(self):
        evidence = [{
            "evidence_id": "EV003",
            "severity": "medium",
            "provenance": "verified",
            "observed_value": None,
            "unit": "not_available",
        }]

        recommendation = {
            "evidence_ids": ["EV003"],
            "confidence_assessment": {
                "confidence_score": 90.0,
            },
        }

        result = assess_recommendation_priority(
            recommendation,
            evidence,
        )

        self.assertTrue(
            any(
                "No numeric operational impact" in limitation
                for limitation in result["limitations"]
            )
        )

    def test_missing_evidence_is_rejected(self):
        recommendation = {
            "evidence_ids": ["UNKNOWN"],
        }

        with self.assertRaises(ValueError):
            assess_recommendation_priority(
                recommendation,
                self.evidence_records,
            )

    def test_invalid_severity_is_rejected(self):
        evidence = [{
            "evidence_id": "EV004",
            "severity": "urgent",
            "provenance": "synthetic",
        }]

        recommendation = {
            "evidence_ids": ["EV004"],
        }

        with self.assertRaises(ValueError):
            assess_recommendation_priority(
                recommendation,
                evidence,
            )


if __name__ == "__main__":
    unittest.main()
