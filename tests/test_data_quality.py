
import pandas as pd

from core.data_quality.quality_checker import (
    check_missing_values,
    check_duplicates,
    check_numeric_values,
    run_quality_checks,
    check_duplicate_ids,
    check_numeric_data_types,
    classify_quality_issues,
)

def test_unified_quality_report():

    data = {
        "machine_id": ["M001", "M002", "M001", "M004", "M005"],
        "capacity": [100, -50, 100, 0, None],
        "efficiency": [0.90, 0.85, 0.90, 1.25, 0.80],
    }

    df = pd.DataFrame(data)

    report = run_quality_checks(
        df,
        non_negative_columns=["capacity"],
        range_columns={"efficiency": (0, 1)},
    )

    print("\nUnified Data Quality Report:")
    print(report)

    assert report["dataset_summary"]["total_rows"] == 5
    assert report["overall_status"] == "ISSUES_FOUND"

    print("\nUnified quality report passed!")


def test_missing_values():

    data = {
        "machine_id": ["M001", "M002", "M003"],
        "capacity": [100, 120, None],
        "efficiency": [0.90, None, 0.85],
    }

    df = pd.DataFrame(data)

    result = check_missing_values(df)

    print("\nData Quality Results:")
    print(result)

    assert result["total_missing_values"] == 2
    assert result["has_missing_values"] is True

    print("\nMissing value detection passed!")


def test_duplicates():

    data = {
        "machine_id": ["M001", "M002", "M001"],
        "capacity": [100, 120, 100],
        "efficiency": [0.90, 0.85, 0.90],
    }

    df = pd.DataFrame(data)

    result = check_duplicates(df)

    print("\nDuplicate Detection Results:")
    print(result)

    assert result["total_duplicate_rows"] == 1
    assert result["has_duplicates"] is True

    print("\nDuplicate detection passed!")


from core.data_quality.quality_checker import check_numeric_values


def test_numeric_validation():

    data = {
        "machine_id": ["M001", "M002", "M003", "M004"],
        "capacity": [100, -50, 120, 0],
        "efficiency": [0.90, 0.85, 1.25, 0.80],
    }

    df = pd.DataFrame(data)

    result = check_numeric_values(
        df,
        non_negative_columns=["capacity"],
        range_columns={"efficiency": (0, 1)},
    )

    print("\nNumerical Validation Results:")
    print(result)

    assert result["has_invalid_values"] is True
    assert result["invalid_columns"]["capacity"]["invalid_count"] == 1
    assert result["invalid_columns"]["efficiency"]["invalid_count"] == 1

    print("\nNumerical validation passed!")
    

def test_unified_quality_report():

    data = {
        "machine_id": ["M001", "M002", "M001", "M004", "M005"],
        "capacity": [100, -50, 100, 0, None],
        "efficiency": [0.90, 0.85, 0.90, 1.25, 0.80],
    }

    df = pd.DataFrame(data)

    report = run_quality_checks(
        df,
        non_negative_columns=["capacity"],
        range_columns={"efficiency": (0, 1)},
        id_columns=["machine_id"],
        numeric_columns=["capacity", "efficiency"],
    )

    print("\nUnified Data Quality Report:")
    print(report)

    assert report["dataset_summary"]["total_rows"] == 5
    assert report["overall_status"] == "ISSUES_FOUND"
    assert report["quality_checks"]["duplicate_ids"]["has_duplicate_ids"] is True
    assert report["quality_checks"]["data_type_validation"] is not None
    assert report["severity_assessment"]["highest_severity"] == "high"

    print("\nUnified quality report passed!")


def test_duplicate_ids():

    data = {
        "machine_id": ["M001", "M002", "M001", "M003"],
        "capacity": [100, 150, 120, 200],
    }

    df = pd.DataFrame(data)

    result = check_duplicate_ids(
        df,
        id_columns=["machine_id"],
    )

    print("\nDuplicate ID Detection Results:")
    print(result)

    assert result["total_duplicate_rows"] == 2
    assert result["has_duplicate_ids"] is True
    assert result["duplicate_ids"] == [{"machine_id": "M001"}]

    print("\nDuplicate ID detection passed!")


def test_numeric_data_types():

    data = {
        "machine_id": ["M001", "M002", "M003", "M004"],
        "capacity": [100, 150, "unknown", 200],
    }

    df = pd.DataFrame(data)

    result = check_numeric_data_types(
        df,
        numeric_columns=["capacity"],
    )

    print("\nData Type Validation Results:")
    print(result)

    assert result["has_invalid_types"] is True
    assert result["invalid_columns"]["capacity"]["invalid_count"] == 1
    assert result["invalid_columns"]["capacity"]["invalid_examples"] == ["unknown"]

    print("\nData type validation passed!")


def test_severity_classification():

    quality_checks = {
        "missing_values": {
            "missing_columns": {"machine_id": 1}
        },
        "duplicates": {
            "total_duplicate_rows": 1
        },
        "duplicate_ids": {
            "total_duplicate_rows": 2
        },
        "numeric_validation": {
            "invalid_columns": {
                "capacity": {"invalid_count": 1}
            }
        },
        "data_type_validation": {
            "invalid_columns": {}
        },
    }

    result = classify_quality_issues(
        quality_checks,
        severity_rules={
            "columns": {
                "machine_id": "critical"
            }
        },
    )

    print("\nSeverity Classification Results:")
    print(result)

    assert result["highest_severity"] == "critical"
    assert result["severity_summary"]["critical"] == 1
    assert result["severity_summary"]["high"] == 2
    assert result["severity_summary"]["medium"] == 1

    print("\nSeverity classification passed!")


if __name__ == "__main__":
    test_missing_values()
    test_duplicates()
    test_numeric_validation()
    test_unified_quality_report()
    test_duplicate_ids()
    test_numeric_data_types()
    test_severity_classification()