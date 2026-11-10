
from core.ingestion.csv_loader import load_csv

from core.diagnostics.evidence_pipeline import (
    analyze_downtime_with_evidence,
)

from core.recommendations.recommendation_engine import (
    generate_recommendations,
)


def test_synthetic_data_to_recommendation_pipeline():

    # Step 1: Load synthetic factory datasets
    production_orders = load_csv(
        "data/synthetic/production_orders.csv"
    )

    downtime = load_csv(
        "data/synthetic/downtime.csv"
    )

    # Step 2: Run diagnostics and generate evidence
    pipeline_output = analyze_downtime_with_evidence(
        production_orders=production_orders,
        downtime=downtime,
        source_datasets=[
            "production_orders.csv",
            "downtime.csv",
        ],
        severity="medium",
        origin="synthetic_factory_data",
    )

    diagnostic_report = pipeline_output["diagnostic_report"]
    evidence_records = pipeline_output["evidence_records"]

    # Step 3: Validate diagnostic and evidence outputs
    assert isinstance(diagnostic_report, dict)
    assert isinstance(evidence_records, list)
    assert len(evidence_records) > 0

    for evidence in evidence_records:
        assert evidence["provenance"] == "synthetic"
        assert evidence["source_diagnostic"] == (
            "analyze_downtime_impact"
        )
        assert evidence["evidence_id"]
        assert evidence["supporting_evidence"]

    # Step 4: Generate recommendations
    recommendations = generate_recommendations(
        evidence_records
    )

    # Step 5: Validate recommendation outputs
    assert isinstance(recommendations, list)
    assert len(recommendations) > 0

    for recommendation in recommendations:
        assert recommendation["recommendation_id"]
        assert recommendation["title"]
        assert recommendation["severity"]
        assert recommendation["evidence_count"] > 0

        # Verify evidence references
        assert recommendation["evidence_ids"]

        # Verify confidence integration
        assert "confidence_assessment" in recommendation

        confidence = recommendation["confidence_assessment"]

        assert 0 <= confidence["confidence_score"] <= 100
        assert confidence["confidence_level"] in [
            "low",
            "moderate",
            "high",
        ]

        # Synthetic data must remain explicitly identified
        assert "synthetic" in recommendation["provenance"]
