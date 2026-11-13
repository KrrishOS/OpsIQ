
from pathlib import Path

from core.ingestion.csv_loader import load_csv
from core.data_quality.quality_checker import run_quality_checks


REQUIRED_DATASETS = {
    "production_orders.csv",
    "downtime.csv",
    "machines.csv",
}


DATASET_RULES = {
    "bom.csv": {
        "id_columns": ["product", "material_id"],
        "numeric_columns": ["quantity_per_unit"],
        "non_negative_columns": ["quantity_per_unit"],
    },
    "downtime.csv": {
        "id_columns": ["downtime_id"],
        "numeric_columns": ["duration_min"],
        "non_negative_columns": ["duration_min"],
    },
    "inventory_transactions.csv": {
        "id_columns": ["transaction_id"],
        "numeric_columns": ["quantity"],
        "non_negative_columns": [],
    },
    "machines.csv": {
        "id_columns": ["machine_id"],
        "numeric_columns": [
            "capacity_per_hour",
            "operating_cost_per_hour",
            "efficiency_factor",
        ],
        "non_negative_columns": [
            "capacity_per_hour",
            "operating_cost_per_hour",
            "efficiency_factor",
        ],
    },
    "materials.csv": {
        "id_columns": ["material_id"],
        "numeric_columns": [
            "initial_stock",
            "reorder_point",
            "unit_cost",
            "lead_time_days",
        ],
        "non_negative_columns": [
            "initial_stock",
            "reorder_point",
            "unit_cost",
            "lead_time_days",
        ],
    },
    "production_data_sample.csv": {
        "id_columns": ["order_id"],
        "numeric_columns": [
            "planned_qty",
            "actual_qty",
            "defective_qty",
            "downtime_min",
        ],
        "non_negative_columns": [
            "planned_qty",
            "actual_qty",
            "defective_qty",
            "downtime_min",
        ],
    },
    "production_orders.csv": {
        "id_columns": ["order_id"],
        "numeric_columns": ["planned_qty", "actual_qty"],
        "non_negative_columns": ["planned_qty", "actual_qty"],
    },
    "quality_inspections.csv": {
        "id_columns": ["inspection_id"],
        "numeric_columns": ["inspected_qty", "defective_qty"],
        "non_negative_columns": [
            "inspected_qty",
            "defective_qty",
        ],
    },
}


def run_data_quality_gate(
    data_directory: str | Path = "data/synthetic",
) -> dict:
    """
    Validate available datasets before decision-support analysis.

    The gate:
    - Checks required datasets.
    - Runs dataset-specific quality checks.
    - Applies inventory transaction business rules.
    - Checks cross-dataset references.
    - Blocks execution when critical issues affect required datasets.
    """

    data_directory = Path(data_directory)

    if not data_directory.exists():
        raise FileNotFoundError(
            f"Data directory not found: {data_directory}"
        )

    if not data_directory.is_dir():
        raise ValueError(
            f"Expected a data directory: {data_directory}"
        )

    datasets = {}
    missing_required = []

    # Step 1: Load available datasets.
    for filename in DATASET_RULES:
        path = data_directory / filename

        if not path.exists():
            if filename in REQUIRED_DATASETS:
                missing_required.append(filename)
            continue

        datasets[filename] = load_csv(path)

    reports = {}
    relationship_findings = []

    # Step 2: Run dataset-specific quality checks.
    for filename, df in datasets.items():
        rules = DATASET_RULES[filename]

        validation_df = df.copy()
        business_notes = []

        # Inventory transaction business rules.
        if filename == "inventory_transactions.csv":
            transaction_type = df["transaction_type"]
            order_id = df["order_id"]
            quantity = df["quantity"]

            optional_mask = transaction_type.isin(
                ["Opening Receipt", "Replenishment"]
            )

            valid_optional_nulls = (
                order_id.isna() & optional_mask
            )

            # Permit missing order IDs for valid receipt transactions.
            validation_df.loc[
                valid_optional_nulls, "order_id"
            ] = "__OPTIONAL_ORDER_ID__"

            consumption = transaction_type.eq("Consumption")

            receipts = transaction_type.isin(
                ["Opening Receipt", "Replenishment"]
            )

            consumption_sign_errors = (
                consumption & (quantity >= 0)
            )

            receipt_sign_errors = (
                receipts & (quantity <= 0)
            )

            missing_consumption_ids = (
                consumption & order_id.isna()
            )

            business_notes.extend([
                {
                    "rule": "Consumption quantities must be negative",
                    "violations": int(
                        consumption_sign_errors.sum()
                    ),
                    "status": (
                        "passed"
                        if not consumption_sign_errors.any()
                        else "failed"
                    ),
                },
                {
                    "rule": (
                        "Receipt and replenishment quantities "
                        "must be positive"
                    ),
                    "violations": int(
                        receipt_sign_errors.sum()
                    ),
                    "status": (
                        "passed"
                        if not receipt_sign_errors.any()
                        else "failed"
                    ),
                },
                {
                    "rule": (
                        "Consumption transactions require order_id"
                    ),
                    "violations": int(
                        missing_consumption_ids.sum()
                    ),
                    "status": (
                        "passed"
                        if not missing_consumption_ids.any()
                        else "failed"
                    ),
                },
            ])

        # Run the existing data-quality framework.
        quality_report = run_quality_checks(
            df=validation_df,
            id_columns=rules["id_columns"],
            numeric_columns=rules["numeric_columns"],
            non_negative_columns=rules["non_negative_columns"],
        )

        reports[filename] = {
            "rows": len(df),
            "columns": len(df.columns),
            "quality_report": quality_report,
            "business_rules": business_notes,
        }

    # Step 3: Check cross-dataset relationships.
    if (
        "production_orders.csv" in datasets
        and "machines.csv" in datasets
    ):
        invalid = ~datasets["production_orders.csv"][
            "machine_id"
        ].isin(datasets["machines.csv"]["machine_id"])

        relationship_findings.append({
            "rule": (
                "Production orders must reference existing machines"
            ),
            "violations": int(invalid.sum()),
            "severity": "high",
            "dataset": "production_orders.csv",
        })

    if "downtime.csv" in datasets:
        downtime = datasets["downtime.csv"]

        if "machines.csv" in datasets:
            invalid = ~downtime["machine_id"].isin(
                datasets["machines.csv"]["machine_id"]
            )

            relationship_findings.append({
                "rule": "Downtime must reference existing machines",
                "violations": int(invalid.sum()),
                "severity": "high",
                "dataset": "downtime.csv",
            })

        if "production_orders.csv" in datasets:
            invalid = ~downtime["order_id"].isin(
                datasets["production_orders.csv"]["order_id"]
            )

            relationship_findings.append({
                "rule": "Downtime must reference existing orders",
                "violations": int(invalid.sum()),
                "severity": "high",
                "dataset": "downtime.csv",
            })

    # Step 4: Evaluate quality findings.
    critical_required_issues = []
    warnings = []

    for filename, result in reports.items():
        quality = result["quality_report"]
        severity = quality["severity_assessment"]

        findings = severity["findings"]

        for finding in findings:
            issue = {
                "dataset": filename,
                **finding,
            }

            if finding["severity"] == "critical":
                if filename in REQUIRED_DATASETS:
                    critical_required_issues.append(issue)
                else:
                    warnings.append(issue)

            elif finding["severity"] in {
                "high",
                "medium",
                "low",
            }:
                warnings.append(issue)

        # Failed business rules are reported as warnings for now.
        for rule in result["business_rules"]:
            if rule["status"] == "failed":
                warnings.append({
                    "dataset": filename,
                    "category": "business_rule",
                    "rule": rule["rule"],
                    "violations": rule["violations"],
                    "severity": "high",
                })

    # Relationship violations are high-severity warnings.
    for finding in relationship_findings:
        if finding["violations"] > 0:
            warnings.append(finding)

    # Step 5: Decide whether the pipeline can proceed.
    blocked = (
        bool(missing_required)
        or bool(critical_required_issues)
    )

    if blocked:
        status = "blocked"
    elif warnings:
        status = "passed_with_warnings"
    else:
        status = "passed"

    return {
        "status": status,
        "blocked": blocked,
        "missing_required_datasets": missing_required,
        "datasets_checked": len(reports),
        "dataset_reports": reports,
        "relationship_findings": relationship_findings,
        "critical_required_issues": critical_required_issues,
        "warnings": warnings,
        "warning_count": len(warnings),
    }
