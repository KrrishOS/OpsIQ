
import unittest
from pathlib import Path

from core.decision_support.decision_pipeline import (
    run_decision_pipeline,
)


class TestDecisionPipeline(unittest.TestCase):

    def setUp(self):
        self.data_directory = (
            Path(__file__).resolve().parents[1]
            / "data"
            / "synthetic"
        )

    def test_decision_pipeline_completes(self):
        result = run_decision_pipeline(
            self.data_directory
        )

        self.assertEqual(
            result["pipeline_status"],
            "completed",
        )

    def test_diagnostic_evidence_is_generated(self):
        result = run_decision_pipeline(
            self.data_directory
        )

        self.assertGreater(
            result["evidence"]["total_records"],
            0,
        )

    def test_recommendations_are_generated(self):
        result = run_decision_pipeline(
            self.data_directory
        )

        self.assertGreater(
            result["recommendations"]["total"],
            0,
        )

    def test_recommendations_have_confidence(self):
        result = run_decision_pipeline(
            self.data_directory
        )

        for recommendation in result["recommendations"]["records"]:
            self.assertIn(
                "confidence_assessment",
                recommendation,
            )

    def test_simulation_is_integrated(self):
        result = run_decision_pipeline(
            self.data_directory
        )

        self.assertEqual(
            result["simulation"]["pipeline_status"],
            "completed",
        )

    def test_decision_summary_is_consistent(self):
        result = run_decision_pipeline(
            self.data_directory
        )

        self.assertEqual(
            result["decision_summary"]["total_findings"],
            result["evidence"]["total_records"],
        )

        self.assertEqual(
            result["decision_summary"]["total_recommendations"],
            result["recommendations"]["total"],
        )

    def test_synthetic_provenance_is_preserved(self):
        result = run_decision_pipeline(
            self.data_directory
        )

        self.assertEqual(
            result["provenance"]["input_data"],
            "synthetic",
        )

        self.assertEqual(
            result["provenance"]["simulation"]["baseline"],
            "synthetic",
        )

        self.assertEqual(
            result["provenance"]["simulation"]["scenario"],
            "simulated",
        )

    def test_missing_directory_is_rejected(self):
        with self.assertRaises(FileNotFoundError):
            run_decision_pipeline(
                self.data_directory / "missing"
            )


if __name__ == "__main__":
    unittest.main()
