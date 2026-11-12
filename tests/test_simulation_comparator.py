
import unittest

import pandas as pd

from core.simulation.scenario_simulator import (
    simulate_downtime_reduction,
)
from core.simulation.simulation_comparator import (
    build_simulation_comparison,
)


class TestSimulationComparator(unittest.TestCase):

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

    def test_comparison_report_structure(self):
        result = build_simulation_comparison(
            self.baseline, self.scenario
        )

        self.assertEqual(
            result["report_type"], "baseline_vs_simulated"
        )

        self.assertIsInstance(
            result["comparison"], pd.DataFrame
        )

    def test_additional_production(self):
        result = build_simulation_comparison(
            self.baseline, self.scenario
        )

        self.assertEqual(
            result["operational_impact"][
                "additional_production_qty"
            ],
            48.8,
        )

    def test_attainment_improvement(self):
        result = build_simulation_comparison(
            self.baseline, self.scenario
        )

        self.assertEqual(
            result["operational_impact"][
                "attainment_improvement_pp"
            ],
            3.26,
        )

    def test_financial_impact(self):
        result = build_simulation_comparison(
            self.baseline, self.scenario
        )

        self.assertEqual(
            result["financial_impact"][
                "estimated_incremental_operating_cost"
            ],
            32.0,
        )

    def test_comparison_contains_five_metrics(self):
        result = build_simulation_comparison(
            self.baseline, self.scenario
        )

        self.assertEqual(
            len(result["comparison"]), 5
        )

    def test_scenario_reduction_is_preserved(self):
        result = build_simulation_comparison(
            self.baseline, self.scenario
        )

        self.assertEqual(
            result["scenario_reduction_pct"], 20
        )

    def test_provenance_is_preserved(self):
        result = build_simulation_comparison(
            self.baseline, self.scenario
        )

        self.assertEqual(
            result["provenance"], "simulated"
        )

        self.assertEqual(
            result["baseline_provenance"], "synthetic"
        )

    def test_invalid_baseline_is_rejected(self):
        with self.assertRaises(ValueError):
            build_simulation_comparison(
                {}, self.scenario
            )

    def test_invalid_scenario_is_rejected(self):
        with self.assertRaises(ValueError):
            build_simulation_comparison(
                self.baseline, {}
            )

    def test_assumptions_are_preserved(self):
        result = build_simulation_comparison(
            self.baseline, self.scenario
        )

        self.assertTrue(
            len(result["assumptions"]) > 0
        )


if __name__ == "__main__":
    unittest.main()
