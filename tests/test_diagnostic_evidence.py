
import unittest

from core.evidence.diagnostic_evidence import (
    build_diagnostic_evidence_records,
)


class TestDiagnosticEvidence(unittest.TestCase):

    def setUp(self):
        self.report = {
            "findings": [
                {
                    "finding": "Mechanical downtime affects production.",
                    "observed_value": 45.5,
                    "unit": "percent",
                    "evidence": "45 minutes across 3 events.",
                    "provenance": "synthetic",
                }
            ]
        }

        self.kwargs = {
            "diagnostic_report": self.report,
            "source_diagnostic": "analyze_downtime_impact",
            "source_datasets": [
                "production_orders.csv",
                "downtime.csv",
            ],
            "severity": "high",
            "origin": "Production diagnostics",
        }

    def test_build_evidence_records(self):
        records = build_diagnostic_evidence_records(**self.kwargs)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["severity"], "high")
        self.assertEqual(records[0]["provenance"], "synthetic")
        self.assertIn("evidence_id", records[0])
        self.assertIn("timestamp", records[0])

    def test_unique_evidence_ids(self):
        first = build_diagnostic_evidence_records(**self.kwargs)
        second = build_diagnostic_evidence_records(**self.kwargs)

        self.assertNotEqual(
            first[0]["evidence_id"],
            second[0]["evidence_id"],
        )

    def test_empty_findings(self):
        report = {"findings": []}

        records = build_diagnostic_evidence_records(
            **{**self.kwargs, "diagnostic_report": report}
        )

        self.assertEqual(records, [])

    def test_invalid_severity(self):
        with self.assertRaises(ValueError):
            build_diagnostic_evidence_records(
                **{**self.kwargs, "severity": "urgent"}
            )

    def test_invalid_provenance(self):
        report = {
            "findings": [
                {
                    **self.report["findings"][0],
                    "provenance": "unknown",
                }
            ]
        }

        with self.assertRaises(ValueError):
            build_diagnostic_evidence_records(
                **{**self.kwargs, "diagnostic_report": report}
            )

    def test_missing_finding_field(self):
        report = {"findings": [{"finding": "Test issue"}]}

        with self.assertRaises(ValueError):
            build_diagnostic_evidence_records(
                **{**self.kwargs, "diagnostic_report": report}
            )

    def test_critical_severity_from_thresholds(self):
        report = {
            "findings": [{
                **self.report["findings"][0],
                "observed_value": 85.0,
            }]
        }

        thresholds = {
            "percent": {
                "critical": 80,
                "high": 60,
                "medium": 30,
                "low": 10,
            }
        }

        records = build_diagnostic_evidence_records(
            **{
                **self.kwargs,
                "diagnostic_report": report,
                "severity_thresholds": thresholds,
            }
        )

        self.assertEqual(records[0]["severity"], "critical")
        self.assertEqual(records[0]["severity_basis"], "threshold_based: percent")

    def test_medium_severity_from_thresholds(self):
        thresholds = {
            "percent": {
                "critical": 80,
                "high": 60,
                "medium": 30,
                "low": 10,
            }
        }

        records = build_diagnostic_evidence_records(
            **{
                **self.kwargs,
                "severity_thresholds": thresholds,
            }
        )

        self.assertEqual(records[0]["severity"], "medium")

    def test_negative_value_uses_fallback_severity(self):
        report = {
            "findings": [{
                **self.report["findings"][0],
                "observed_value": -5.0,
            }]
        }

        records = build_diagnostic_evidence_records(
            **{
                **self.kwargs,
                "diagnostic_report": report,
                "severity_thresholds": {
                    "percent": {
                        "critical": 80,
                        "high": 60,
                        "medium": 30,
                        "low": 10,
                    }
                },
            }
        )

        self.assertEqual(records[0]["severity"], "high")
        self.assertEqual(
            records[0]["severity_basis"],
            "fallback: negative_directional_value",
        )

    def test_missing_unit_threshold_uses_fallback(self):
        records = build_diagnostic_evidence_records(
            **{
                **self.kwargs,
                "severity_thresholds": {
                    "hours": {
                        "critical": 80,
                        "high": 60,
                        "medium": 30,
                        "low": 10,
                    }
                },
            }
        )

        self.assertEqual(records[0]["severity"], "high")
        self.assertEqual(
            records[0]["severity_basis"],
            "fallback: no_thresholds_for_unit",
        )

    def test_none_observation_uses_fallback(self):
        report = {
            "findings": [{
                **self.report["findings"][0],
                "observed_value": None,
            }]
        }

        records = build_diagnostic_evidence_records(
            **{
                **self.kwargs,
                "diagnostic_report": report,
                "severity_thresholds": {
                    "percent": {
                        "critical": 80,
                        "high": 60,
                        "medium": 30,
                        "low": 10,
                    }
                },
            }
        )

        self.assertEqual(records[0]["severity"], "high")
        self.assertEqual(
            records[0]["severity_basis"],
            "fallback: no_numeric_observation",
        )

if __name__ == "__main__":
    unittest.main()
