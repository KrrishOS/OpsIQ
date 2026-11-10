
import unittest

from core.recommendations.confidence_assessor import (
    assess_recommendation_confidence,
)


class TestConfidenceAssessor(unittest.TestCase):

    def setUp(self):
        self.recommendation = {
            "recommendation_id": "REC001",
            "evidence_ids": ["EV001"],
        }

        self.evidence = [{
            "evidence_id": "EV001",
            "finding": "Mechanical downtime affects production.",
            "supporting_evidence": "45 minutes across 3 events.",
            "source_diagnostic": "analyze_downtime_impact",
            "source_datasets": ["production_orders.csv", "downtime.csv"],
            "observed_value": 45.5,
            "unit": "percent",
            "provenance": "synthetic",
        }]

    def test_synthetic_evidence_confidence(self):
        result = assess_recommendation_confidence(
            self.recommendation, self.evidence
        )

        self.assertEqual(result["confidence_score"], 64.0)
        self.assertEqual(result["confidence_level"], "moderate")

    def test_verified_evidence_confidence(self):
        evidence = [
            {**self.evidence[0], "provenance": "verified"}
        ]

        result = assess_recommendation_confidence(
            self.recommendation, evidence
        )

        self.assertEqual(result["confidence_score"], 100.0)
        self.assertEqual(result["confidence_level"], "high")

    def test_real_unverified_evidence_confidence(self):
        evidence = [
            {**self.evidence[0], "provenance": "real_unverified"}
        ]

        result = assess_recommendation_confidence(
            self.recommendation, evidence
        )

        self.assertEqual(result["confidence_score"], 82.0)

    def test_incomplete_evidence(self):
        evidence = [{
            **self.evidence[0],
            "supporting_evidence": "",
        }]

        result = assess_recommendation_confidence(
            self.recommendation, evidence
        )

        self.assertEqual(result["confidence_score"], 56.0)
        self.assertTrue(result["limitations"])

    def test_multiple_evidence_records(self):
        recommendation = {
            "evidence_ids": ["EV001", "EV002"],
        }

        evidence = [
            self.evidence[0],
            {
                **self.evidence[0],
                "evidence_id": "EV002",
                "provenance": "verified",
            },
        ]

        result = assess_recommendation_confidence(
            recommendation, evidence
        )

        self.assertEqual(result["evidence_count"], 2)
        self.assertEqual(result["confidence_score"], 82.0)

    def test_missing_evidence_reference(self):
        recommendation = {
            "evidence_ids": ["EV999"],
        }

        with self.assertRaises(ValueError):
            assess_recommendation_confidence(
                recommendation, self.evidence
            )

    def test_invalid_provenance(self):
        evidence = [
            {**self.evidence[0], "provenance": "unknown"}
        ]

        with self.assertRaises(ValueError):
            assess_recommendation_confidence(
                self.recommendation, evidence
            )

    def test_empty_evidence_ids(self):
        recommendation = {"evidence_ids": []}

        with self.assertRaises(ValueError):
            assess_recommendation_confidence(
                recommendation, self.evidence
            )

    def test_invalid_recommendation(self):
        with self.assertRaises(ValueError):
            assess_recommendation_confidence(
                None, self.evidence
            )


if __name__ == "__main__":
    unittest.main()
