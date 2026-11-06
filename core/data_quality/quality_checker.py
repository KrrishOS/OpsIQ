
import pandas as pd


def check_missing_values(df: pd.DataFrame) -> dict:
    """
    Identify missing values in a dataset.

    Args:
        df: Input Pandas DataFrame.

    Returns:
        Dictionary containing missing-value statistics.
    """

    missing_counts = df.isnull().sum()

    total_missing = int(missing_counts.sum())

    missing_columns = {
        column: int(count)
        for column, count in missing_counts.items()
        if count > 0
    }

    return {
        "total_missing_values": total_missing,
        "missing_columns": missing_columns,
        "has_missing_values": total_missing > 0,
    }

def check_duplicates(df: pd.DataFrame) -> dict:
    """
    Identify duplicate records in a dataset.

    Args:
        df: Input Pandas DataFrame.

    Returns:
        Dictionary containing duplicate-record statistics.
    """

    duplicate_mask = df.duplicated()

    duplicate_count = int(duplicate_mask.sum())

    return {
        "total_duplicate_rows": duplicate_count,
        "has_duplicates": duplicate_count > 0,
    }

def check_numeric_values(
    df: pd.DataFrame,
    non_negative_columns: list[str] | None = None,
    range_columns: dict[str, tuple[float, float]] | None = None,
) -> dict:
    """
    Validate numerical values against defined constraints.
    """

    issues = {}

    non_negative_columns = non_negative_columns or []
    range_columns = range_columns or {}

    for column in non_negative_columns:

        if column not in df.columns:
            continue

        invalid_count = int((df[column] < 0).sum())

        if invalid_count > 0:
            issues[column] = {
                "rule": "non_negative",
                "invalid_count": invalid_count,
            }

    for column, (minimum, maximum) in range_columns.items():

        if column not in df.columns:
            continue

        invalid_count = int(
            (~df[column].between(minimum, maximum)).sum()
        )

        if invalid_count > 0:
            issues[column] = {
                "rule": "allowed_range",
                "invalid_count": invalid_count,
                "expected_range": [minimum, maximum],
            }

    return {
        "invalid_columns": issues,
        "has_invalid_values": len(issues) > 0,
    }

def run_quality_checks(
    df: pd.DataFrame,
    non_negative_columns: list[str] | None = None,
    range_columns: dict[str, tuple[float, float]] | None = None,
) -> dict:
    """
    Run all data-quality checks and generate a unified report.
    """

    missing_results = check_missing_values(df)
    duplicate_results = check_duplicates(df)

    numeric_results = check_numeric_values(
        df,
        non_negative_columns=non_negative_columns,
        range_columns=range_columns,
    )

    has_issues = (
        missing_results["has_missing_values"]
        or duplicate_results["has_duplicates"]
        or numeric_results["has_invalid_values"]
    )

    return {
        "dataset_summary": {
            "total_rows": len(df),
            "total_columns": len(df.columns),
        },
        "quality_checks": {
            "missing_values": missing_results,
            "duplicates": duplicate_results,
            "numeric_validation": numeric_results,
        },
        "overall_status": "ISSUES_FOUND" if has_issues else "PASSED",
    }
