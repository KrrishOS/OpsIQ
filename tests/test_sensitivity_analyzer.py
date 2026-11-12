
import unittest
from unittest.mock import patch

import pandas as pd

from core.simulation.sensitivity_analyzer import run_sensitivity_analysis


def create_pipeline_result(reduction_pct):
    """Create a controlled pipeline result for testing."""

    recovered_qty = reduction_pct * 10
    downtime_reduced = reduction_pct * 5
    cost = recovered_qty * 4

    return {
        "baseline": {
            "metrics": {
                "total_actual_qty": 1000,
            }
        },
        "scenario": {
            "provenance": "simulated",
            "metrics": {
                "simulated_total_actual_qty": 1000 + recovered_qty,
            },
        },
        "impact": {
            "impact": {
                "additional_production_qty": recovered_qty,
                "attainment_improvement_pp": reduction_pct / 10,
                "orders_recovered_to_target": int(reduction_pct / 2),
                "downtime_reduction_min": downtime_reduced,
                "estimated_incremental_operating_cost": cost,
            }
        },
    }


class TestSensitivityAnalyzer(unittest.TestCase):

    @patch("core.simulation.sensitivity_analyzer.run_simulation_pipeline")
    def test_default_reduction_levels(self, mock_pipeline):
        mock_pipeline.side_effect = (
            lambda reduction_pct, **kwargs:
            create_pipeline_result(reduction_pct)
        )

        result = run_sensitivity_analysis()

        self.assertEqual(result["scenarios_tested"], 5)
        self.assertEqual(
            result["comparison"]["reduction_pct"].tolist(),
            [0, 10, 20, 30, 40],
        )

    @patch("core.simulation.sensitivity_analyzer.run_simulation_pipeline")
    def test_custom_reduction_levels(self, mock_pipeline):
        mock_pipeline.side_effect = (
            lambda reduction_pct, **kwargs:
            create_pipeline_result(reduction_pct)
        )

        result = run_sensitivity_analysis(
            reduction_levels=[5, 15, 25]
        )

        self.assertEqual(result["scenarios_tested"], 3)
        self.assertEqual(
            result["comparison"]["reduction_pct"].tolist(),
            [5, 15, 25],
        )

    @patch("core.simulation.sensitivity_analyzer.run_simulation_pipeline")
    def test_additional_production_increases(self, mock_pipeline):
        mock_pipeline.side_effect = (
            lambda reduction_pct, **kwargs:
            create_pipeline_result(reduction_pct)
        )

        result = run_sensitivity_analysis(
            reduction_levels=[0, 10, 20]
        )

        production = result["comparison"][
            "additional_production_qty"
        ].tolist()

        self.assertEqual(production, [0, 100, 200])

    @patch("core.simulation.sensitivity_analyzer.run_simulation_pipeline")
    def test_cost_increases_with_production(self, mock_pipeline):
        mock_pipeline.side_effect = (
            lambda reduction_pct, **kwargs:
            create_pipeline_result(reduction_pct)
        )

        result = run_sensitivity_analysis(
            reduction_levels=[0, 10, 20]
        )

        costs = result["comparison"][
            "estimated_incremental_operating_cost"
        ].tolist()

        self.assertEqual(costs, [0, 400, 800])

    def test_empty_reduction_levels(self):
        with self.assertRaises(ValueError):
            run_sensitivity_analysis(reduction_levels=[])

    def test_invalid_reduction_level_above_100(self):
        with self.assertRaises(ValueError):
            run_sensitivity_analysis(reduction_levels=[10, 110])

    def test_invalid_negative_reduction_level(self):
        with self.assertRaises(ValueError):
            run_sensitivity_analysis(reduction_levels=[-10, 20])

    def test_invalid_string_reduction_level(self):
        with self.assertRaises(ValueError):
            run_sensitivity_analysis(reduction_levels=[10, "twenty"])

    def test_duplicate_reduction_levels(self):
        with self.assertRaises(ValueError):
            run_sensitivity_analysis(reduction_levels=[10, 20, 10])

    def test_boolean_reduction_level(self):
        with self.assertRaises(ValueError):
            run_sensitivity_analysis(reduction_levels=[True, 20])

    @patch("core.simulation.sensitivity_analyzer.run_simulation_pipeline")
    def test_provenance_is_simulated(self, mock_pipeline):
        mock_pipeline.side_effect = (
            lambda reduction_pct, **kwargs:
            create_pipeline_result(reduction_pct)
        )

        result = run_sensitivity_analysis(
            reduction_levels=[0, 20]
        )

        self.assertEqual(result["provenance"], "simulated")
        self.assertTrue(
            (result["comparison"]["provenance"] == "simulated").all()
        )

    @patch("core.simulation.sensitivity_analyzer.run_simulation_pipeline")
    def test_comparison_is_dataframe(self, mock_pipeline):
        mock_pipeline.side_effect = (
            lambda reduction_pct, **kwargs:
            create_pipeline_result(reduction_pct)
        )

        result = run_sensitivity_analysis(
            reduction_levels=[0, 20]
        )

        self.assertIsInstance(result["comparison"], pd.DataFrame)

    @patch("core.simulation.sensitivity_analyzer.run_simulation_pipeline")
    def test_threshold_is_passed_to_pipeline(self, mock_pipeline):
        mock_pipeline.side_effect = (
            lambda reduction_pct, **kwargs:
            create_pipeline_result(reduction_pct)
        )

        run_sensitivity_analysis(
            reduction_levels=[10, 20],
            threshold=85,
        )

        for call in mock_pipeline.call_args_list:
            self.assertEqual(call.kwargs["threshold"], 85)

    @patch("core.simulation.sensitivity_analyzer.run_simulation_pipeline")
    def test_data_directory_is_passed_to_pipeline(self, mock_pipeline):
        mock_pipeline.side_effect = (
            lambda reduction_pct, **kwargs:
            create_pipeline_result(reduction_pct)
        )

        run_sensitivity_analysis(
            reduction_levels=[10],
            data_directory="custom/data",
        )

        mock_pipeline.assert_called_once_with(
            data_directory="custom/data",
            reduction_pct=10.0,
            threshold=90.0,
        )


if __name__ == "__main__":
    unittest.main()
