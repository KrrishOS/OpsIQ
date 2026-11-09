
import unittest
import pandas as pd

from core.diagnostics.production_diagnostics import (
    calculate_production_attainment,
    analyze_production_downtime,
    analyze_downtime_impact,
)


class TestProductionDiagnostics(unittest.TestCase):

    def setUp(self):
        # Test data for production attainment
        self.df = pd.DataFrame({
            "order_id": ["O001", "O002", "O003"],
            "planned_qty": [100, 200, 100],
            "actual_qty": [80, 200, 110],
        })

    def setUp_downtime(self):
        # Test data for downtime analysis
        self.orders = pd.DataFrame({
            "order_id": ["O001", "O002", "O003"],
            "planned_qty": [100, 100, 100],
            "actual_qty": [80, 95, 100],
        })

        self.downtime = pd.DataFrame({
            "downtime_id": ["D001", "D002", "D003"],
            "order_id": ["O001", "O001", "O002"],
            "duration_min": [20, 30, 15],
            "downtime_type": [
                "Mechanical",
                "Electrical",
                "Operational",
            ],
            "reason": [
                "Component failure",
                "Power issue",
                "Setup delay",
            ],
        })

    # ==========================================
    # PRODUCTION ATTAINMENT TESTS
    # ==========================================

    def test_calculate_attainment(self):
        result = calculate_production_attainment(self.df)

        self.assertEqual(
            result["attainment_pct"].tolist(),
            [80.0, 100.0, 110.0],
        )

    def test_below_threshold(self):
        result = calculate_production_attainment(
            self.df,
            threshold=90,
        )

        self.assertEqual(
            result["below_threshold"].tolist(),
            [True, False, False],
        )

    def test_custom_threshold(self):
        result = calculate_production_attainment(
            self.df,
            threshold=105,
        )

        self.assertEqual(
            result["below_threshold"].tolist(),
            [True, True, False],
        )

    def test_invalid_threshold(self):
        with self.assertRaises(ValueError):
            calculate_production_attainment(
                self.df,
                threshold=-10,
            )

    def test_non_finite_threshold(self):
        with self.assertRaises(ValueError):
            calculate_production_attainment(
                self.df,
                threshold=float("nan"),
            )

    def test_missing_column(self):
        invalid_df = self.df.drop(columns=["actual_qty"])

        with self.assertRaises(ValueError):
            calculate_production_attainment(invalid_df)

    def test_zero_planned_quantity(self):
        invalid_df = self.df.copy()
        invalid_df.loc[0, "planned_qty"] = 0

        with self.assertRaises(ValueError):
            calculate_production_attainment(invalid_df)

    def test_negative_actual_quantity(self):
        invalid_df = self.df.copy()
        invalid_df.loc[0, "actual_qty"] = -10

        with self.assertRaises(ValueError):
            calculate_production_attainment(invalid_df)

    # ==========================================
    # DOWNTIME ANALYSIS TESTS
    # ==========================================

    def test_downtime_aggregation(self):
        self.setUp_downtime()

        result = analyze_production_downtime(
            self.orders,
            self.downtime,
        )

        order = result.set_index("order_id")

        self.assertEqual(
            order.loc["O001", "total_downtime_min"],
            50,
        )

        self.assertEqual(
            order.loc["O001", "downtime_events"],
            2,
        )

    def test_orders_without_downtime(self):
        self.setUp_downtime()

        result = analyze_production_downtime(
            self.orders,
            self.downtime,
        )

        order = result.set_index("order_id")

        self.assertEqual(
            order.loc["O003", "total_downtime_min"],
            0,
        )

        self.assertEqual(
            order.loc["O003", "downtime_events"],
            0,
        )

    def test_negative_downtime(self):
        self.setUp_downtime()
        self.downtime.loc[0, "duration_min"] = -10

        with self.assertRaises(ValueError):
            analyze_production_downtime(
                self.orders,
                self.downtime,
            )

    def test_unmatched_order_id(self):
        self.setUp_downtime()
        self.downtime.loc[0, "order_id"] = "O999"

        with self.assertRaises(ValueError):
            analyze_production_downtime(
                self.orders,
                self.downtime,
            )

    def test_duplicate_downtime_id(self):
        self.setUp_downtime()
        self.downtime.loc[1, "downtime_id"] = "D001"

        with self.assertRaises(ValueError):
            analyze_production_downtime(
                self.orders,
                self.downtime,
            )

    def test_missing_downtime_order_id(self):
        self.setUp_downtime()
        self.downtime.loc[0, "order_id"] = None

        with self.assertRaises(ValueError):
            analyze_production_downtime(
                self.orders,
                self.downtime,
            )

    # ==========================================
    # DOWNTIME IMPACT TESTS
    # ==========================================

    def test_downtime_impact_returns_expected_structure(self):
        production_orders = pd.DataFrame({
            "order_id": ["O1", "O2", "O3", "O4"],
            "planned_qty": [100, 100, 100, 100],
            "actual_qty": [70, 95, 80, 100],
        })

        downtime = pd.DataFrame({
            "downtime_id": ["D1", "D2"],
            "order_id": ["O1", "O3"],
            "duration_min": [30, 20],
            "downtime_type": ["Mechanical", "Electrical"],
            "reason": ["Failure", "Power issue"],
        })

        report = analyze_downtime_impact(
            production_orders,
            downtime,
        )

        self.assertIn("performance_comparison", report)
        self.assertIn("attainment_gap_pp", report)
        self.assertIn("downtime_by_category", report)
        self.assertIn("findings", report)

    def test_downtime_impact_calculates_attainment_gap(self):
        production_orders = pd.DataFrame({
            "order_id": ["O1", "O2", "O3", "O4"],
            "planned_qty": [100, 100, 100, 100],
            "actual_qty": [70, 95, 80, 100],
        })

        downtime = pd.DataFrame({
            "downtime_id": ["D1", "D2"],
            "order_id": ["O1", "O3"],
            "duration_min": [30, 20],
            "downtime_type": ["Mechanical", "Electrical"],
            "reason": ["Failure", "Power issue"],
        })

        report = analyze_downtime_impact(
            production_orders,
            downtime,
        )

        self.assertEqual(
            report["attainment_gap_pp"],
            22.5,
        )

    def test_downtime_category_analysis(self):
        production_orders = pd.DataFrame({
            "order_id": ["O1", "O2"],
            "planned_qty": [100, 100],
            "actual_qty": [70, 95],
        })

        downtime = pd.DataFrame({
            "downtime_id": ["D1", "D2", "D3"],
            "order_id": ["O1", "O1", "O2"],
            "duration_min": [30, 20, 10],
            "downtime_type": [
                "Mechanical",
                "Mechanical",
                "Electrical",
            ],
            "reason": [
                "Failure",
                "Failure",
                "Power issue",
            ],
        })

        report = analyze_downtime_impact(
            production_orders,
            downtime,
        )

        categories = report["downtime_by_category"]

        self.assertEqual(
            categories.loc["Mechanical", "total_downtime_min"],
            50,
        )

        self.assertEqual(
            categories.loc["Mechanical", "downtime_share_pct"],
            83.33,
        )

    def test_downtime_impact_generates_findings(self):
        production_orders = pd.DataFrame({
            "order_id": ["O1", "O2"],
            "planned_qty": [100, 100],
            "actual_qty": [70, 95],
        })

        downtime = pd.DataFrame({
            "downtime_id": ["D1"],
            "order_id": ["O1"],
            "duration_min": [30],
            "downtime_type": ["Mechanical"],
            "reason": ["Failure"],
        })

        report = analyze_downtime_impact(
            production_orders,
            downtime,
        )

        self.assertGreaterEqual(
            len(report["findings"]),
            2,
        )

        self.assertIn(
            "evidence",
            report["findings"][0],
        )


if __name__ == "__main__":
    unittest.main()
