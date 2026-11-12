
import unittest

import pandas as pd

from core.simulation.scenario_simulator import (
    simulate_downtime_reduction,
)
from core.simulation.impact_calculator import (
    calculate_simulation_impact,
)


class TestImpactCalculator(unittest.TestCase):

    def setUp(self):
        self.baseline = {
            "scenario_type": "baseline_observation",
            "provenance": "synthetic",
            "threshold_pct": 90.0,
            "order_results": pd.DataFrame({
                "order_id": ["ORD001", "ORD002"],
                "planned_qty": [1000, 500],
                "actual_qty": [800, 450],
                "total_downtime_min": [120, 60],
                "capacity_per_hour": [100, 80],
                "efficiency_factor": [0.90, 0.80],
                "operating_cost_per_hour": [60, 40],
            }),
        }

        self.scenario = simulate_downtime_reduction(
            self.baseline, 20
        )

    def test_additional_production_calculation(self):
        result = calculate_simulation_impact(
            self.baseline, self.scenario
        )

        self.assertEqual(
            result["impact"]["additional_production_qty"],
            48.8,
        )

    def test_attainment_improvement(self):
        result = calculate_simulation_impact(
            self.baseline, self.scenario
        )

        self.assertEqual(
            result["impact"]["attainment_improvement_pp"],
            3.26,
        )

    def test_downtime_reduction(self):
        result = calculate_simulation_impact(
            self.baseline, self.scenario
        )

        self.assertEqual(
            result["impact"]["downtime_reduction_min"],
            36.0,
        )

        self.assertEqual(
            result["impact"]["downtime_reduction_pct"],
            20.0,
        )

    def test_incremental_operating_cost(self):
        result = calculate_simulation_impact(
            self.baseline, self.scenario
        )

        # Order 1: 36 / 90 * 60 = 24
        # Order 2: 12.8 / 64 * 40 = 8
        self.assertEqual(
            result["impact"][
                "estimated_incremental_operating_cost"
            ],
            32.0,
        )

    def test_provenance_is_preserved(self):
        result = calculate_simulation_impact(
            self.baseline, self.scenario
        )

        self.assertEqual(
            result["baseline_provenance"], "synthetic"
        )

        self.assertEqual(
            result["scenario_provenance"], "simulated"
        )

    def test_invalid_baseline(self):
        with self.assertRaises(ValueError):
            calculate_simulation_impact(
                {}, self.scenario
            )

    def test_invalid_scenario(self):
        with self.assertRaises(ValueError):
            calculate_simulation_impact(
                self.baseline, {}
            )

    def test_mismatched_provenance(self):
        scenario = self.scenario.copy()
        scenario["baseline_provenance"] = "verified"

        with self.assertRaises(ValueError):
            calculate_simulation_impact(
                self.baseline, scenario
            )

    def test_missing_scenario_column(self):
        scenario = self.scenario.copy()

        scenario["order_results"] = (
            scenario["order_results"].drop(
                columns=["operating_cost_per_hour"]
            )
        )

        with self.assertRaises(ValueError):
            calculate_simulation_impact(
                self.baseline, scenario
            )

    def test_baseline_is_not_modified(self):
        original = self.baseline["order_results"].copy()

        calculate_simulation_impact(
            self.baseline, self.scenario
        )

        pd.testing.assert_frame_equal(
            self.baseline["order_results"],
            original,
        )

    def test_existing_overproduction_is_preserved(self):
        baseline = self.baseline.copy()

        baseline["order_results"] = (
            baseline["order_results"].copy()
        )

        baseline["order_results"].loc[
            0, "actual_qty"
        ] = 1050

        scenario = simulate_downtime_reduction(
            baseline, 20
        )

        result = calculate_simulation_impact(
            baseline, scenario
        )

        # ORD001 already exceeded its target.
        # ORD002 can still recover 12.8 units.
        self.assertEqual(
            result["scenario_metrics"]["total_actual_qty"],
            1512.8,
        )

        self.assertAlmostEqual(
            result["impact"]["additional_production_qty"],
            12.8,
        )


if __name__ == "__main__":
    unittest.main()
