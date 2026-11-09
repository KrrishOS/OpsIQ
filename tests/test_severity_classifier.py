
import unittest

from core.evidence.severity_classifier import classify_severity


class TestSeverityClassifier(unittest.TestCase):

    def setUp(self):
        self.thresholds = {
            "critical": 100,
            "high": 60,
            "medium": 30,
            "low": 10,
        }

    def test_critical_severity(self):
        self.assertEqual(
            classify_severity(120, self.thresholds),
            "critical",
        )

    def test_high_severity(self):
        self.assertEqual(
            classify_severity(75, self.thresholds),
            "high",
        )

    def test_medium_severity(self):
        self.assertEqual(
            classify_severity(40, self.thresholds),
            "medium",
        )

    def test_low_severity(self):
        self.assertEqual(
            classify_severity(15, self.thresholds),
            "low",
        )

    def test_invalid_negative_impact(self):
        with self.assertRaises(ValueError):
            classify_severity(-5, self.thresholds)

    def test_invalid_threshold_order(self):
        invalid = {
            "critical": 30,
            "high": 60,
            "medium": 40,
            "low": 10,
        }

        with self.assertRaises(ValueError):
            classify_severity(50, invalid)

    def test_boolean_impact_rejected(self):
        with self.assertRaises(ValueError):
            classify_severity(True, self.thresholds)


if __name__ == "__main__":
    unittest.main()
