
import unittest
from pathlib import Path

from core.simulation.simulation_pipeline import (
    run_simulation_pipeline,
)


class TestSimulationPipeline(unittest.TestCase):

    def setUp(self):
        self.data_directory = (
            Path(__file__).resolve().parents[1]
            / "data"
            / "synthetic"
        )

    def test_pipeline_completes_successfully(self):
        result = run_simulation_pipeline(
            self.data_directory
        )

        self.assertEqual(
            result["pipeline_status"], "completed"
        )

    def test_all_datasets_are_loaded(self):
        result = run_simulation_pipeline(
            self.data_directory
        )

        self.assertEqual(
            result["input_summary"]["production_orders"],
            1000,
        )

        self.assertEqual(
            result["input_summary"]["machines"],
            10,
        )

        self.assertGreater(
            result["input_summary"]["downtime_events"],
            0,
        )

    def test_baseline_and_scenario_provenance(self):
        result = run_simulation_pipeline(
            self.data_directory
        )

        self.assertEqual(
            result["provenance"]["baseline"], "synthetic"
        )

        self.assertEqual(
            result["provenance"]["scenario"], "simulated"
        )

    def test_simulation_produces_additional_output(self):
        result = run_simulation_pipeline(
            self.data_directory,
            reduction_pct=20,
        )

        self.assertGreaterEqual(
            result["impact"]["impact"][
                "additional_production_qty"
            ],
            0,
        )

    def test_comparison_report_is_generated(self):
        result = run_simulation_pipeline(
            self.data_directory
        )

        self.assertEqual(
            result["comparison"]["report_type"],
            "baseline_vs_simulated",
        )

        self.assertEqual(
            len(result["comparison"]["comparison"]),
            5,
        )

    def test_custom_reduction_percentage(self):
        result = run_simulation_pipeline(
            self.data_directory,
            reduction_pct=30,
        )

        self.assertEqual(
            result["scenario"]["reduction_pct"],
            30,
        )

    def test_missing_directory_is_rejected(self):
        with self.assertRaises(FileNotFoundError):
            run_simulation_pipeline(
                self.data_directory / "missing"
            )


if __name__ == "__main__":
    unittest.main()
