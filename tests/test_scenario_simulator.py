
import unittest

import pandas as pd

from core.simulation.scenario_simulator import (
    simulate_downtime_reduction,
)


class TestScenarioSimulator(unittest.TestCase):

    def setUp(self):
        self.baseline = {
            "scenario_type": "baseline_observation",
            "provenance": "synthetic",
            "order_results": pd.DataFrame({
                "order_id": ["ORD001", "ORD002"],
                "planned_qty": [1000, 500],
                "actual_qty": [800, 450],
                "total_downtime_min": [120, 60],
                "capacity_per_hour": [100, 80],
                "efficiency_factor": [0.90, 0.80],
            }),
        }

    def test_downtime_reduction_calculation(self):
        result = simulate_downtime_reduction(
            self.baseline, 20
        )

        orders = result["order_results"]

        # First order: 120 * 20% = 24 minutes
        self.assertAlmostEqual(
            orders.loc[0, "recovered_time_min"], 24
        )

        # 24 / 60 * 100 * 0.90 = 36 units
        self.assertAlmostEqual(
            orders.loc[0, "recovered_qty"], 36
        )

        self.assertAlmostEqual(
            orders.loc[0, "simulated_actual_qty"], 836
        )

    def test_total_recovered_production(self):
        result = simulate_downtime_reduction(
            self.baseline, 20
        )

        # Order 1: 36 units
        # Order 2: 12.8 units
        self.assertAlmostEqual(
            result["metrics"]["total_recovered_qty"],
            48.8,
        )

    def test_production_cannot_exceed_planned_quantity(self):
        baseline = self.baseline.copy()

        baseline["order_results"] = (
            baseline["order_results"].copy()
        )

        baseline["order_results"].loc[0, "actual_qty"] = 990

        result = simulate_downtime_reduction(
            baseline, 100
        )

        self.assertEqual(
            result["order_results"].loc[
                0, "simulated_actual_qty"
            ],
            1000,
        )

    def test_zero_reduction(self):
        result = simulate_downtime_reduction(
            self.baseline, 0
        )

        self.assertEqual(
            result["metrics"]["total_recovered_qty"],
            0,
        )

    def test_invalid_reduction_percentage(self):
        for value in [-10, 101, float("nan"), float("inf"), True]:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    simulate_downtime_reduction(
                        self.baseline, value
                    )

    def test_invalid_baseline_type(self):
        with self.assertRaises(ValueError):
            simulate_downtime_reduction({}, 20)

    def test_missing_required_column(self):
        baseline = self.baseline.copy()

        baseline["order_results"] = (
            baseline["order_results"].drop(
                columns=["capacity_per_hour"]
            )
        )

        with self.assertRaises(ValueError):
            simulate_downtime_reduction(
                baseline, 20
            )

    def test_original_baseline_is_not_modified(self):
        original = self.baseline["order_results"].copy()

        simulate_downtime_reduction(
            self.baseline, 20
        )

        pd.testing.assert_frame_equal(
            self.baseline["order_results"],
            original,
        )

    def test_simulation_provenance(self):
        result = simulate_downtime_reduction(
            self.baseline, 20
        )

        self.assertEqual(
            result["provenance"], "simulated"
        )

        self.assertEqual(
            result["baseline_provenance"], "synthetic"
        )


if __name__ == "__main__":
    unittest.main()
