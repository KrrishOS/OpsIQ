import unittest

from core.evidence.evidence_builder import create_evidence_record


class TestEvidenceBuilder(unittest.TestCase):

    def test_create_evidence_record(self):

        record = create_evidence_record(
            dataset_name="machines.csv",
            category="missing_value",
            column="capacity_per_hour",
            record_id="M005",
            observed_value=None,
            expected_rule="Value must not be missing",
            severity="medium",
            provenance="synthetic",
            origin="Synthetic manufacturing dataset",
        )

        self.assertIn("issue_id", record)
        self.assertEqual(record["dataset_name"], "machines.csv")
        self.assertEqual(record["severity"], "medium")
        self.assertEqual(record["provenance"], "synthetic")
        self.assertIn("timestamp", record)

    def test_invalid_severity(self):

        with self.assertRaises(ValueError):
            create_evidence_record(
                dataset_name="machines.csv",
                category="missing_value",
                column="capacity_per_hour",
                record_id="M005",
                observed_value=None,
                expected_rule="Value must not be missing",
                severity="urgent",
                provenance="synthetic",
                origin="Test dataset",
            )

    def test_invalid_provenance(self):

        with self.assertRaises(ValueError):
            create_evidence_record(
                dataset_name="machines.csv",
                category="missing_value",
                column="capacity_per_hour",
                record_id="M005",
                observed_value=None,
                expected_rule="Value must not be missing",
                severity="medium",
                provenance="unknown",
                origin="Test dataset",
            )


if __name__ == "__main__":
    unittest.main()