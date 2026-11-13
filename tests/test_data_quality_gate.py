
import unittest
import tempfile
import shutil

from pathlib import Path
from unittest.mock import patch

import pandas as pd

from core.decision_support.data_quality_gate import (
    run_data_quality_gate,
)


class TestDataQualityGate(unittest.TestCase):

    def setUp(self):
        self.data_directory = (
            Path(__file__).resolve().parents[1]
            / "data"
            / "synthetic"
        )

        self.temp_directory = tempfile.TemporaryDirectory()

        self.test_data_directory = (
            Path(self.temp_directory.name) / "synthetic"
        )

        shutil.copytree(
            self.data_directory,
            self.test_data_directory,
        )

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_quality_gate_passes_on_valid_datasets(self):
        result = run_data_quality_gate(
            self.test_data_directory
        )

        self.assertEqual(result["status"], "passed")
        self.assertFalse(result["blocked"])
        self.assertEqual(result["datasets_checked"], 8)
        self.assertEqual(result["warning_count"], 0)

    def test_missing_required_dataset_blocks_gate(self):
        (
            self.test_data_directory / "production_orders.csv"
        ).unlink()

        result = run_data_quality_gate(
            self.test_data_directory
        )

        self.assertTrue(result["blocked"])
        self.assertEqual(result["status"], "blocked")

        self.assertIn(
            "production_orders.csv",
            result["missing_required_datasets"],
        )

    def test_critical_issue_in_required_dataset_blocks_gate(self):
        critical_report = {
            "overall_status": "ISSUES_FOUND",
            "severity_assessment": {
                "highest_severity": "critical",
                "severity_summary": {
                    "critical": 1,
                    "high": 0,
                    "medium": 0,
                    "low": 0,
                },
                "findings": [
                    {
                        "category": "duplicate_ids",
                        "column": "order_id",
                        "count": 1,
                        "severity": "critical",
                    }
                ],
            },
        }

        with patch(
            "core.decision_support.data_quality_gate.run_quality_checks",
            return_value=critical_report,
        ):
            result = run_data_quality_gate(
                self.test_data_directory
            )

        self.assertTrue(result["blocked"])
        self.assertEqual(result["status"], "blocked")
        self.assertGreater(
            len(result["critical_required_issues"]),
            0,
        )

    def test_high_severity_issue_generates_warning(self):
        warning_report = {
            "overall_status": "ISSUES_FOUND",
            "severity_assessment": {
                "highest_severity": "high",
                "severity_summary": {
                    "critical": 0,
                    "high": 1,
                    "medium": 0,
                    "low": 0,
                },
                "findings": [
                    {
                        "category": "numeric_validation",
                        "column": "planned_qty",
                        "count": 1,
                        "severity": "high",
                    }
                ],
            },
        }

        with patch(
            "core.decision_support.data_quality_gate.run_quality_checks",
            return_value=warning_report,
        ):
            result = run_data_quality_gate(
                self.test_data_directory
            )

        self.assertFalse(result["blocked"])
        self.assertEqual(
            result["status"],
            "passed_with_warnings",
        )
        self.assertGreater(result["warning_count"], 0)

    def test_invalid_consumption_sign_is_detected(self):
        inventory_path = (
            self.test_data_directory
            / "inventory_transactions.csv"
        )

        df = pd.read_csv(inventory_path)

        consumption_index = df.index[
            df["transaction_type"] == "Consumption"
        ][0]

        # Consumption must have a negative quantity.
        df.loc[consumption_index, "quantity"] = 10.0

        df.to_csv(inventory_path, index=False)

        result = run_data_quality_gate(
            self.test_data_directory
        )

        inventory_rules = result[
            "dataset_reports"
        ]["inventory_transactions.csv"]["business_rules"]

        consumption_rule = next(
            rule for rule in inventory_rules
            if rule["rule"] == "Consumption quantities must be negative"
        )

        self.assertEqual(
            consumption_rule["violations"],
            1,
        )
        self.assertEqual(
            consumption_rule["status"],
            "failed",
        )

    def test_valid_optional_inventory_order_ids_are_accepted(self):
        result = run_data_quality_gate(
            self.test_data_directory
        )

        inventory_rules = result[
            "dataset_reports"
        ]["inventory_transactions.csv"]["business_rules"]

        for rule in inventory_rules:
            self.assertEqual(
                rule["status"],
                "passed",
            )

        self.assertFalse(result["blocked"])


if __name__ == "__main__":
    unittest.main()
