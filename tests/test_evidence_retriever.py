"""
test_evidence_retriever.py — Evidence Retrieval Infrastructure Tests

Validates:
1. Relevant query -> correct chunk(s) retrieved.
2. Semantically similar but unauthorized chunk -> excluded.
3. Wrong condition scope -> excluded.
4. Restricted/diagnostic source -> cannot enter recommendation retrieval.
5. Below-threshold query -> zero-evidence result ([]).
6. Retrieval result preserves exact provenance and metadata.
"""

import os
import sys
import pytest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.recommendations.evidence_retriever import EvidenceRetriever


@pytest.fixture
def retriever():
    return EvidenceRetriever()


def test_retrieval_test_1_relevant_query(retriever):
    """Test 1: Relevant query returns correct chunks with high similarity score."""
    query = "moderate intensity aerobic physical activity 150 minutes per week"
    results = retriever.retrieve(
        query=query,
        target_condition="Type2_Diabetes",
        recommendation_category="physical_activity",
        recommendation_only=True,
        top_k=3
    )

    assert len(results) > 0
    top_chunk_ids = [r["chunk_id"] for r in results]
    assert "WHO_PA_2020_CHUNK_01" in top_chunk_ids or "CDC_DPP_2024_CHUNK_02" in top_chunk_ids
    assert results[0]["similarity_score"] >= 0.20
    print(f"\n[PASS] Test 1 Relevant Query: Retrieved {len(results)} chunks. Top chunk: {results[0]['chunk_id']} (score: {results[0]['similarity_score']})")


def test_retrieval_test_2_unauthorized_category_excluded(retriever):
    """Test 2: Category filter excludes semantically matching chunks from other categories."""
    query = "reduce caloric intake by 500 to 750 calories per day to lose weight"
    # Filter for category = physical_activity (dietary chunk should be excluded)
    results = retriever.retrieve(
        query=query,
        target_condition="High_Adiposity_Risk",
        recommendation_category="physical_activity",
        recommendation_only=True
    )

    # Dietary chunks CDC_DPP_2024_CHUNK_03 and AHA_OBESITY_2013_CHUNK_01 must NOT be in results
    for r in results:
        assert r["chunk_id"] not in ("CDC_DPP_2024_CHUNK_03", "AHA_OBESITY_2013_CHUNK_01")
        assert "physical_activity" in r["allowed_recommendation_categories"]
    print(f"\n[PASS] Test 2 Category Filtering: Successfully excluded dietary chunks from physical_activity query.")


def test_retrieval_test_3_wrong_condition_scope_excluded(retriever):
    """Test 3: Condition scope filter strictly excludes chunks not tagged for the target condition."""
    query = "hepatic steatosis liver fat resolution Mediterranean diet"
    # Query with target_condition = "Type2_Diabetes"
    # EASL_MASLD_2024_CHUNK_01 and 02 allowed conditions: ["NAFLD", "Metabolic_Syndrome", "High_Adiposity_Risk"]
    results = retriever.retrieve(
        query=query,
        target_condition="Type2_Diabetes",
        recommendation_only=True
    )

    # EASL chunks must be excluded for Type2_Diabetes
    for r in results:
        assert r["source_id"] != "EASL_EASD_EASO_MASLD_2024"
        assert "Type2_Diabetes" in r["allowed_condition_scopes"] or "All_Cardiometabolic" in r["allowed_condition_scopes"]
    print("\n[PASS] Test 3 Condition Scope Filtering: EASL MASLD chunks correctly excluded for Type2_Diabetes.")


def test_retrieval_test_4_diagnostic_source_restricted(retriever):
    """Test 4: Restricted/diagnostic sources (AHA Metsyn 2005) cannot enter recommendation retrieval."""
    query = "elevated triglycerides blood pressure fasting glucose metabolic syndrome criteria"
    # Recommendation retrieval: recommendation_only = True
    rec_results = retriever.retrieve(
        query=query,
        target_condition="Metabolic_Syndrome",
        recommendation_only=True
    )

    for r in rec_results:
        assert r["source_id"] != "AHA_NHLBI_METSYN_2005"
        assert r["recommendation_generation_allowed"] is True

    # Diagnostic explanation retrieval: recommendation_only = False
    diag_results = retriever.retrieve(
        query=query,
        target_condition="Metabolic_Syndrome",
        recommendation_only=False
    )
    diag_chunk_ids = [r["chunk_id"] for r in diag_results]
    assert "AHA_METSYN_2005_CHUNK_01" in diag_chunk_ids
    print("\n[PASS] Test 4 Diagnostic Restriction: AHA_METSYN_2005 excluded from recommendations, present for explanation.")


def test_retrieval_test_5_below_threshold_zero_evidence(retriever):
    """Test 5: Below-threshold unrelated query returns explicit zero-evidence list ([])."""
    unrelated_query = "quantum mechanical wavefunctions supermassive black hole stellar dynamics"
    results = retriever.retrieve(
        query=unrelated_query,
        target_condition="Type2_Diabetes",
        recommendation_only=True,
        min_threshold=0.15
    )

    assert results == []
    print("\n[PASS] Test 5 Zero-Evidence Fallback: Unrelated query returned empty list [] (no hallucinated chunk substitution).")


def test_retrieval_test_6_metadata_and_provenance_preserved(retriever):
    """Test 6: All retrieved results preserve complete provenance and 20+ metadata fields."""
    query = "dietary fiber intake 25 g per day whole grains and legumes"
    results = retriever.retrieve(
        query=query,
        target_condition="Prediabetes",
        recommendation_category="dietary_nutrition",
        recommendation_only=True,
        top_k=1
    )

    assert len(results) == 1
    chunk = results[0]

    # Required provenance fields
    required_fields = [
        "chunk_id", "source_id", "chunk_text", "document_title", "publication_year",
        "section", "subsection", "page", "evidence_role", "allowed_condition_scopes",
        "allowed_recommendation_categories", "allowed_intervention_types",
        "prohibited_claim_types", "approved_numerical_anchors",
        "recommendation_generation_allowed", "explanation_generation_allowed",
        "contains_numerical_claim", "contains_recommendation",
        "contains_diagnostic_definition", "contains_microbiome_taxon_reference",
        "taxon_specific_intervention_allowed", "similarity_score"
    ]

    for field in required_fields:
        assert field in chunk, f"Missing required field: {field}"

    assert chunk["chunk_id"] == "WHO_FIBER_2023_CHUNK_02"
    assert chunk["source_id"] == "WHO_CARB_FIBER_2023"
    assert chunk["publication_year"] == 2023
    assert "25 g per day" in chunk["approved_numerical_anchors"] or "25 g/day" in chunk["approved_numerical_anchors"]
    assert chunk["similarity_score"] >= 0.20
    print(f"\n[PASS] Test 6 Metadata Preservation: All {len(required_fields)} metadata fields intact on chunk {chunk['chunk_id']}.")


if __name__ == "__main__":
    r = EvidenceRetriever()
    print("Running Evidence Retrieval Test Suite...")
    test_retrieval_test_1_relevant_query(r)
    test_retrieval_test_2_unauthorized_category_excluded(r)
    test_retrieval_test_3_wrong_condition_scope_excluded(r)
    test_retrieval_test_4_diagnostic_source_restricted(r)
    test_retrieval_test_5_below_threshold_zero_evidence(r)
    test_retrieval_test_6_metadata_and_provenance_preserved(r)
    print("\n[SUCCESS] ALL 6 RETRIEVAL INFRASTRUCTURE TESTS PASSED CONVINCINGLY!")
