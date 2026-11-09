
import math
from numbers import Real

import pandas as pd


def calculate_production_attainment(
    production_orders: pd.DataFrame,
    threshold: float = 90.0,
) -> pd.DataFrame:
    """
    Calculate production attainment and flag orders
    performing below the specified threshold.
    """

    # Step 1: Validate required columns
    required_columns = {
        "order_id",
        "planned_qty",
        "actual_qty",
    }

    missing_columns = required_columns - set(production_orders.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    # Step 2: Validate threshold
    if (
        isinstance(threshold, bool)
        or not isinstance(threshold, Real)
        or not math.isfinite(threshold)
        or threshold < 0
    ):
        raise ValueError(
            "Threshold must be a finite, non-negative number"
        )

    # Step 3: Work on a copy to preserve original data
    result = production_orders.copy()

    # Step 4: Validate numeric quantities
    for column in ("planned_qty", "actual_qty"):
        result[column] = pd.to_numeric(
            result[column],
            errors="raise",
        )

    # Step 5: Validate planned quantity
    if (
        result["planned_qty"].isna().any()
        or (result["planned_qty"] <= 0).any()
    ):
        raise ValueError("Planned quantities must be positive")

    # Step 6: Validate actual quantity
    if (
        result["actual_qty"].isna().any()
        or (result["actual_qty"] < 0).any()
    ):
        raise ValueError("Actual quantities must be non-negative")

    # Step 7: Calculate production attainment
    result["attainment_pct"] = (
        result["actual_qty"] / result["planned_qty"] * 100
    ).round(2)

    # Step 8: Identify orders below the threshold
    result["below_threshold"] = (
        result["attainment_pct"] < threshold
    )

    return result


def analyze_production_downtime(
    production_orders: pd.DataFrame,
    downtime: pd.DataFrame,
    threshold: float = 90.0,
) -> pd.DataFrame:
    """
    Combine production attainment with downtime information
    for each production order.
    """

    # Step 1: Validate required downtime columns
    required_downtime_columns = {
        "downtime_id",
        "order_id",
        "duration_min",
        "downtime_type",
        "reason",
    }

    missing_columns = (
        required_downtime_columns - set(downtime.columns)
    )

    if missing_columns:
        raise ValueError(
            f"Missing downtime columns: {sorted(missing_columns)}"
        )

    # Step 2: Calculate production attainment
    production = calculate_production_attainment(
        production_orders,
        threshold=threshold,
    )

    if production["order_id"].isna().any():
        raise ValueError("Production order IDs cannot be missing")

    if production["order_id"].duplicated().any():
        raise ValueError("Production order IDs must be unique")

    # Step 3: Work on a copy of downtime data
    downtime_data = downtime.copy()

    # Step 4: Validate downtime identifiers
    if downtime_data["downtime_id"].isna().any():
        raise ValueError("Downtime IDs cannot be missing")

    if downtime_data["downtime_id"].duplicated().any():
        raise ValueError("Downtime IDs must be unique")

    if (
        downtime_data["order_id"].isna().any()
        or downtime_data["order_id"].astype(str).str.strip().eq("").any()
    ):
        raise ValueError("Downtime order IDs cannot be missing")

    # Step 5: Validate downtime duration
    downtime_data["duration_min"] = pd.to_numeric(
        downtime_data["duration_min"],
        errors="raise",
    )

    if (
        downtime_data["duration_min"].isna().any()
        or not downtime_data["duration_min"].map(math.isfinite).all()
        or (downtime_data["duration_min"] < 0).any()
    ):
        raise ValueError(
            "Downtime duration must be finite and non-negative"
        )

    # Step 6: Ensure every downtime event references an existing order
    production_ids = set(production["order_id"])
    downtime_ids = set(downtime_data["order_id"])

    unmatched_ids = downtime_ids - production_ids

    if unmatched_ids:
        raise ValueError(
            f"Unmatched production order IDs: {sorted(unmatched_ids)}"
        )

    # Step 7: Aggregate downtime by production order
    downtime_summary = (
        downtime_data
        .groupby("order_id")
        .agg(
            total_downtime_min=("duration_min", "sum"),
            downtime_events=("downtime_id", "count"),
            downtime_types=(
                "downtime_type",
                lambda values: ", ".join(sorted(set(values))),
            ),
            downtime_reasons=(
                "reason",
                lambda values: ", ".join(sorted(set(values))),
            ),
        )
        .reset_index()
    )

    # Step 8: Connect production and downtime datasets
    result = production.merge(
        downtime_summary,
        on="order_id",
        how="left",
        validate="one_to_one",
    )

    # Step 9: Orders without downtime receive zero values
    result["total_downtime_min"] = (
        result["total_downtime_min"].fillna(0)
    )

    result["downtime_events"] = (
        result["downtime_events"].fillna(0).astype(int)
    )

    result["downtime_types"] = (
        result["downtime_types"].fillna("")
    )

    result["downtime_reasons"] = (
        result["downtime_reasons"].fillna("")
    )

    return result


def analyze_downtime_impact(
    production_orders: pd.DataFrame,
    downtime: pd.DataFrame,
    threshold: float = 90.0,
) -> dict:
    """
    Compare production performance between orders with and without
    recorded downtime and identify the largest downtime contributors.

    Returns:
        dict: Performance comparison, attainment gap,
              downtime category analysis, and findings.
    """

    # Step 1: Generate order-level production and downtime data
    order_data = analyze_production_downtime(
        production_orders,
        downtime,
        threshold=threshold,
    )

    # Step 2: Classify each order by downtime status
    order_data["downtime_status"] = (
        order_data["total_downtime_min"]
        .gt(0)
        .map({
            True: "With Downtime",
            False: "Without Downtime",
        })
    )

    # Step 3: Compare production performance
    comparison = (
        order_data.groupby("downtime_status")
        .agg(
            orders=("order_id", "count"),
            avg_attainment=("attainment_pct", "mean"),
            below_target=("below_threshold", "sum"),
            avg_downtime=("total_downtime_min", "mean"),
        )
    )

    comparison["below_target_rate_pct"] = (
        comparison["below_target"]
        / comparison["orders"]
        * 100
    )

    comparison = comparison.round(2)

    # Step 4: Calculate the attainment gap safely
    with_downtime = (
        comparison.loc["With Downtime"]
        if "With Downtime" in comparison.index
        else None
    )

    without_downtime = (
        comparison.loc["Without Downtime"]
        if "Without Downtime" in comparison.index
        else None
    )

    if with_downtime is not None and without_downtime is not None:
        attainment_gap = round(
            without_downtime["avg_attainment"]
            - with_downtime["avg_attainment"],
            2,
        )
    else:
        attainment_gap = None

    # Step 5: Identify downtime category contributions
    category_analysis = (
        downtime.groupby("downtime_type")
        .agg(
            events=("downtime_id", "count"),
            total_downtime_min=("duration_min", "sum"),
            avg_event_duration=("duration_min", "mean"),
        )
        .sort_values(
            "total_downtime_min",
            ascending=False,
        )
    )

    total_downtime = category_analysis[
        "total_downtime_min"
    ].sum()

    if total_downtime > 0:
        category_analysis["downtime_share_pct"] = (
            category_analysis["total_downtime_min"]
            / total_downtime
            * 100
        )
    else:
        category_analysis["downtime_share_pct"] = 0.0

    category_analysis = category_analysis.round(2)

    # Step 6: Generate explainable findings
    findings = []

    # Compare groups only when both groups are available
    if with_downtime is not None and without_downtime is not None:

        findings.append({
            "finding": (
                "Orders with recorded downtime have lower "
                "average production attainment."
            ),
            "observed_value": attainment_gap,
            "unit": "percentage points",
            "evidence": (
                f"With downtime: {with_downtime['avg_attainment']}%; "
                f"without downtime: "
                f"{without_downtime['avg_attainment']}%."
            ),
            "provenance": "synthetic",
        })

        findings.append({
            "finding": (
                "A proportion of orders without recorded downtime "
                "also miss the production target."
            ),
            "observed_value": without_downtime[
                "below_target_rate_pct"
            ],
            "unit": "percent",
            "evidence": (
                f"{int(without_downtime['below_target'])} out of "
                f"{int(without_downtime['orders'])} orders "
                "are below the target."
            ),
            "provenance": "synthetic",
        })

    else:
        findings.append({
            "finding": (
                "A comparative attainment gap cannot be calculated "
                "because both downtime groups are not available."
            ),
            "observed_value": None,
            "unit": "not_applicable",
            "evidence": (
                "Only one downtime-status group exists "
                "in the analyzed dataset."
            ),
            "provenance": "synthetic",
        })

    # Identify the largest downtime contributor
    if not category_analysis.empty:

        top_category = category_analysis.index[0]

        findings.append({
            "finding": (
                f"{top_category} is the largest recorded "
                "downtime contributor."
            ),
            "observed_value": category_analysis.loc[
                top_category, "downtime_share_pct"
            ],
            "unit": "percent of total downtime",
            "evidence": (
                f"{category_analysis.loc[top_category, 'total_downtime_min']} "
                f"minutes across "
                f"{int(category_analysis.loc[top_category, 'events'])} "
                "downtime events."
            ),
            "provenance": "synthetic",
        })

    # Step 7: Return the complete diagnostic report
    return {
        "performance_comparison": comparison,
        "attainment_gap_pp": attainment_gap,
        "downtime_by_category": category_analysis,
        "findings": findings,
    }
