
import pandas as pd

from core.data_quality.quality_checker import (
    check_missing_values,
    check_duplicates,
    check_numeric_values,
    run_quality_checks,
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
    )

    print("\nUnified Data Quality Report:")
    print(report)

    assert report["dataset_summary"]["total_rows"] == 5
    assert report["overall_status"] == "ISSUES_FOUND"

    print("\nUnified quality report passed!")




if __name__ == "__main__":
    test_missing_values()
    test_duplicates()
    test_numeric_validation()
    test_unified_quality_report()
