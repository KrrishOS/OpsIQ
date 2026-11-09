
import unittest
import pandas as pd

from core.diagnostics.evidence_pipeline import (
    analyze_downtime_with_evidence,
)


class TestEvidencePipeline(unittest.TestCase):

    def setUp(self):
        self.production_orders = pd.DataFrame({
            "order_id": ["O1", "O2", "O3"],
            "planned_qty": [100, 100, 100],
            "actual_qty": [70, 95, 80],
        })

        self.downtime = pd.DataFrame({
            "downtime_id": ["D1", "D2"],
            "order_id": ["O1", "O3"],
            "duration_min": [30, 20],
            "downtime_type": ["Mechanical", "Electrical"],
            "reason": ["Failure", "Power issue"],
        })

    def test_pipeline_generates_diagnostic_and_evidence(self):
        result = analyze_downtime_with_evidence(
            production_orders=self.production_orders,
            downtime=self.downtime,
            source_datasets=[
                "production_orders.csv",
                "downtime.csv",
            ],
            severity="high",
            origin="Production diagnostics",
        )

        self.assertIn("diagnostic_report", result)
        self.assertIn("evidence_records", result)

        findings = result["diagnostic_report"]["findings"]
        records = result["evidence_records"]

        self.assertEqual(len(findings), len(records))

    def test_evidence_preserves_diagnostic_findings(self):
        result = analyze_downtime_with_evidence(
            production_orders=self.production_orders,
            downtime=self.downtime,
            source_datasets=[
                "production_orders.csv",
                "downtime.csv",
            ],
            severity="high",
            origin="Production diagnostics",
        )

        for finding, record in zip(
            result["diagnostic_report"]["findings"],
            result["evidence_records"],
        ):
            self.assertEqual(
                finding["finding"],
                record["finding"],
            )

            self.assertEqual(
                finding["observed_value"],
                record["observed_value"],
            )

    def test_invalid_severity_is_rejected(self):
        with self.assertRaises(ValueError):
            analyze_downtime_with_evidence(
                production_orders=self.production_orders,
                downtime=self.downtime,
                source_datasets=["production_orders.csv", "downtime.csv"],
                severity="urgent",
                origin="Production diagnostics",
            )


if __name__ == "__main__":
    unittest.main()
