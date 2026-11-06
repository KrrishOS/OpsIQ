
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

    issues = {}

    non_negative_columns = non_negative_columns or []
    range_columns = range_columns or {}

    for column in non_negative_columns:

        if column not in df.columns:
            continue

        values = pd.to_numeric(df[column], errors="coerce")

        invalid_count = int((values < 0).sum())

        if invalid_count > 0:
            issues[column] = {
                "rule": "non_negative",
                "invalid_count": invalid_count,
            }

    for column, (minimum, maximum) in range_columns.items():

        if column not in df.columns:
            continue

        values = pd.to_numeric(df[column], errors="coerce")

        invalid_mask = (
            values.notna()
            & ~values.between(minimum, maximum)
        )

        invalid_count = int(invalid_mask.sum())

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
    id_columns: list[str] | None = None,
    numeric_columns: list[str] | None = None,
    severity_rules: dict | None = None,
) -> dict:

    missing_results = check_missing_values(df)
    duplicate_results = check_duplicates(df)

    numeric_results = check_numeric_values(
        df,
        non_negative_columns=non_negative_columns,
        range_columns=range_columns,
    )

    duplicate_id_results = (
        check_duplicate_ids(df, id_columns)
        if id_columns else None
    )

    data_type_results = (
        check_numeric_data_types(df, numeric_columns)
        if numeric_columns else None
    )

    quality_checks = {
        "missing_values": missing_results,
        "duplicates": duplicate_results,
        "duplicate_ids": duplicate_id_results,
        "numeric_validation": numeric_results,
        "data_type_validation": data_type_results,
    }

    severity_results = classify_quality_issues(
        quality_checks,
        severity_rules=severity_rules,
    )

    has_issues = severity_results["highest_severity"] != "none"

    return {
        "dataset_summary": {
            "total_rows": len(df),
            "total_columns": len(df.columns),
        },
        "quality_checks": quality_checks,
        "severity_assessment": severity_results,
        "overall_status": "ISSUES_FOUND" if has_issues else "PASSED",
    }



def check_duplicate_ids(
    df: pd.DataFrame,
    id_columns: list[str],
) -> dict:
    """
    Detect duplicate identifiers in specified columns.
    """

    missing_columns = [
        column for column in id_columns
        if column not in df.columns
    ]

    if not id_columns:
        raise ValueError("At least one ID column is required.")

    if missing_columns:
        raise ValueError(
            f"ID columns not found: {missing_columns}"
        )

    duplicate_mask = df.duplicated(
        subset=id_columns,
        keep=False,
    )

    duplicate_rows = df.loc[duplicate_mask, id_columns]

    duplicate_ids = (
        duplicate_rows
        .drop_duplicates()
        .to_dict(orient="records")
    )

    return {
        "id_columns": id_columns,
        "total_duplicate_rows": int(duplicate_mask.sum()),
        "duplicate_ids": duplicate_ids,
        "has_duplicate_ids": bool(duplicate_mask.any()),
    }

def check_numeric_data_types(
    df: pd.DataFrame,
    numeric_columns: list[str],
) -> dict:
    """
    Detect non-numeric values in columns expected to be numerical.

    Missing values are handled separately by check_missing_values().
    """

    if not numeric_columns:
        raise ValueError("At least one numeric column is required.")

    missing_columns = [
        column for column in numeric_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Numeric columns not found: {missing_columns}"
        )

    invalid_columns = {}

    for column in numeric_columns:

        converted = pd.to_numeric(
            df[column],
            errors="coerce",
        )

        invalid_mask = df[column].notna() & converted.isna()

        invalid_count = int(invalid_mask.sum())

        if invalid_count > 0:
            invalid_columns[column] = {
                "invalid_count": invalid_count,
                "invalid_rows": df.index[invalid_mask].tolist(),
                "invalid_examples": (
                    df.loc[invalid_mask, column]
                    .astype(str)
                    .head(5)
                    .tolist()
                ),
            }

    return {
        "invalid_columns": invalid_columns,
        "has_invalid_types": len(invalid_columns) > 0,
    }

def classify_quality_issues(
    quality_checks: dict,
    severity_rules: dict | None = None,
) -> dict:
    """
    Classify detected quality issues by severity.

    Severity rules can be customized by dataset.
    """

    rules = {
        "missing_values": "medium",
        "duplicates": "medium",
        "duplicate_ids": "high",
        "numeric_validation": "high",
        "data_type_validation": "high",
        "columns": {},
    }

    if severity_rules:
        rules.update(severity_rules)

    valid_levels = ["critical", "high", "medium", "low"]

    findings = []

    def add_finding(category, count, column=None):
        if count <= 0:
            return

        severity = rules["columns"].get(
            column,
            rules[category],
        )

        if severity not in valid_levels:
            raise ValueError(
                f"Invalid severity level: {severity}"
            )

        findings.append({
            "category": category,
            "column": column,
            "count": count,
            "severity": severity,
        })

    missing = quality_checks["missing_values"]

    for column, count in missing["missing_columns"].items():
        add_finding("missing_values", count, column)

    duplicates = quality_checks["duplicates"]

    add_finding(
        "duplicates",
        duplicates["total_duplicate_rows"],
    )

    duplicate_ids = quality_checks["duplicate_ids"]

    if duplicate_ids:
        add_finding(
            "duplicate_ids",
            duplicate_ids["total_duplicate_rows"],
        )

    numeric = quality_checks["numeric_validation"]

    for column, issue in numeric["invalid_columns"].items():
        add_finding(
            "numeric_validation",
            issue["invalid_count"],
            column,
        )

    data_types = quality_checks["data_type_validation"]

    if data_types:
        for column, issue in data_types["invalid_columns"].items():
            add_finding(
                "data_type_validation",
                issue["invalid_count"],
                column,
            )

    severity_summary = {
        level: sum(
            1 for finding in findings
            if finding["severity"] == level
        )
        for level in valid_levels
    }

    highest_severity = next(
        (
            level for level in valid_levels
            if severity_summary[level] > 0
        ),
        "none",
    )

    return {
        "findings": findings,
        "severity_summary": severity_summary,
        "highest_severity": highest_severity,
    }
