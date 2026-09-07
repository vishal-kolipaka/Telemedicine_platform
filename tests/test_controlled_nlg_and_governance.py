"""
test_controlled_nlg_and_governance.py — Controlled NLG Layer & Governance Verification Tests

Tests:
1. Actual value preservation after LLM generation.
2. Parameter/value/unit binding validation.
3. HbA1c and glucose cannot be incorrectly merged.
4. No invented reference ranges (status == interpretation_unavailable).
5. Friendly/simple English generation.
6. Numerical target mutation rejection.
7. Temporal mutation rejection (150 min/week -> 150 min/day).
8. Unsupported medication recommendation rejection (GLP-1).
9. Taxon-specific cure rejection (Akkermansia).
10. Zero-evidence -> LLM bypass.
11. Failed LLM output -> safe conservative fallback.
12. API response remains backward compatible with prediction & XAI intact.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.recommendations.controlled_nlg import ControlledNLG, ParameterBindingValidator
from src.recommendations.plan_generator import PlanGenerator
from src.recommendations.claim_validator import ClaimValidator
from src.recommendations.evidence_retriever import EvidenceRetriever
from api_server import app

client = TestClient(app)


@pytest.fixture
def sample_patient_context():
    return {
        "primary_disease": "Type2_Diabetes",
        "disease_results": [
            {"disease": "Type2_Diabetes", "prediction": 1, "probability": 0.85, "risk_level": "High"},
            {"disease": "High_Adiposity_Risk", "prediction": 1, "probability": 0.78, "risk_level": "Moderate-High"}
        ],
        "contributing_factors": [
            {
                "parameter": "Fasting_Blood_Glucose",
                "friendly_name": "Fasting Blood Glucose",
                "patient_value": 150.0,
                "unit": "mg/dL",
                "status": "above_expected_range",
                "status_label": "above the expected fasting range",
                "importance_score": 0.28,
                "contributes_to": ["Type2_Diabetes"]
            },
            {
                "parameter": "HbA1c",
                "friendly_name": "Glycated Hemoglobin (HbA1c)",
                "patient_value": 7.1,
                "unit": "%",
                "status": "above_expected_range",
                "status_label": "above the expected range",
                "importance_score": 0.22,
                "contributes_to": ["Type2_Diabetes"]
            },
            {
                "parameter": "BMI",
                "friendly_name": "Body Mass Index (BMI)",
                "patient_value": 31.2,
                "unit": "kg/m²",
                "status": "above_expected_range",
                "status_label": "above standard healthy weight range",
                "importance_score": 0.15,
                "contributes_to": ["Type2_Diabetes"]
            }
        ],
        "selected_priorities": [
            {
                "rank": 1,
                "pillar_key": "physical_activity",
                "title": "Physical Activity & Movement",
                "reason": "Regular aerobic movement supports insulin-independent glucose uptake."
            },
            {
                "rank": 2,
                "pillar_key": "dietary_nutrition",
                "title": "Dietary Quality & Carbohydrate Nutrition",
                "reason": "High-fiber whole foods support glycemic regulation."
            }
        ]
    }


def test_nlg_1_actual_value_preservation(sample_patient_context):
    """Test 1: Patient values (150.0 mg/dL, 7.1%, 31.2) are preserved in friendly output."""
    nlg = ControlledNLG()
    plan = nlg.generate_friendly_plan(sample_patient_context)

    items = plan["contributing_items"]
    glucose = next(i for i in items if i["parameter"] == "Fasting_Blood_Glucose")
    hba1c = next(i for i in items if i["parameter"] == "HbA1c")

    assert glucose["patient_value"] == 150.0
    assert "150" in glucose["explanation_sentence"]
    assert "mg/dL" in glucose["explanation_sentence"]

    assert hba1c["patient_value"] == 7.1
    assert "7.1" in hba1c["explanation_sentence"]
    print(f"\n[PASS] Test 1 Actual Value Preservation: {glucose['explanation_sentence']}")


def test_nlg_2_parameter_value_unit_binding_validation():
    """Test 2: ParameterBindingValidator prevents Parameter A from receiving Parameter B's value or unit."""
    other_vals = {"Fasting_Blood_Glucose": 150.0, "HbA1c": 7.1, "BMI": 31.2}

    # Case A: Correct explanation passes
    valid_expl = "Your Fasting Blood Glucose is 150.0 mg/dL, which is higher than the standard target range."
    is_valid, reason = ParameterBindingValidator.validate_factor_explanation(
        parameter_key="Fasting_Blood_Glucose",
        friendly_name="Fasting Blood Glucose",
        patient_value=150.0,
        unit="mg/dL",
        status="above_expected_range",
        explanation_text=valid_expl,
        other_patient_values=other_vals
    )
    assert is_valid is True

    # Case B: Missing actual value fails
    broken_expl = "Your Fasting Blood Glucose is high."
    is_valid, reason = ParameterBindingValidator.validate_factor_explanation(
        parameter_key="Fasting_Blood_Glucose",
        friendly_name="Fasting Blood Glucose",
        patient_value=150.0,
        unit="mg/dL",
        status="above_expected_range",
        explanation_text=broken_expl,
        other_patient_values=other_vals
    )
    assert is_valid is False
    assert "missing" in reason.lower()
    print("\n[PASS] Test 2 Binding Validation: Successfully caught missing parameter value.")


def test_nlg_3_glucose_and_hba1c_merge_rejected():
    """Test 3: Compound merge (e.g., 'fasting glucose/hba1c is 150 mg/dL') is rejected by validator."""
    other_vals = {"Fasting_Blood_Glucose": 150.0, "HbA1c": 7.1}
    bad_merged_text = "Your Fasting Blood Glucose/HbA1c is 150.0 mg/dL."

    is_valid, reason = ParameterBindingValidator.validate_factor_explanation(
        parameter_key="Fasting_Blood_Glucose",
        friendly_name="Fasting Blood Glucose",
        patient_value=150.0,
        unit="mg/dL",
        status="above_expected_range",
        explanation_text=bad_merged_text,
        other_patient_values=other_vals
    )
    assert is_valid is False
    assert "forbidden merge" in reason.lower()
    print(f"\n[PASS] Test 3 Merge Rejection: {reason}")


def test_nlg_4_no_invented_reference_ranges():
    """Test 4: Status 'interpretation_unavailable' forbids adjectives like high/low/abnormal/dangerous."""
    other_vals = {"Exploratory_Metabolite_Y": 42.5}
    bad_hallucinated_text = "Your Exploratory Metabolite Y is 42.5, which is dangerously high."

    is_valid, reason = ParameterBindingValidator.validate_factor_explanation(
        parameter_key="Exploratory_Metabolite_Y",
        friendly_name="Exploratory Metabolite Y",
        patient_value=42.5,
        unit="",
        status="interpretation_unavailable",
        explanation_text=bad_hallucinated_text,
        other_patient_values=other_vals
    )
    assert is_valid is False
    assert "invented interpretation" in reason.lower()
    print(f"\n[PASS] Test 4 No Invented Ranges: {reason}")


def test_nlg_5_friendly_conversational_english(sample_patient_context):
    """Test 5: Controlled NLG produces friendly, warm, conversational sentences."""
    nlg = ControlledNLG()
    plan = nlg.generate_friendly_plan(sample_patient_context)

    sec_a = plan["section_a_summary"]
    assert "health information" in sec_a.lower()
    assert "steady changes" in sec_a.lower() or "really help you" in sec_a.lower() or "healthy habit changes" in sec_a.lower()
    print(f"\n[PASS] Test 5 Friendly English Summary: {sec_a[:100]}...")


def test_nlg_6_numerical_mutation_rejection():
    """Test 6: ClaimValidator rejects numerical mutation (e.g. 50 g/day fibre instead of 25 g/day)."""
    validator = ClaimValidator()
    mutated_claim = {
        "claim_id": "TEST_MUTATED_FIBER",
        "claim_text": "Consume at least 50 g per day of dietary fibre in foods.",
        "claim_type": "recommendation",
        "category": "dietary_nutrition",
        "supporting_chunk_ids": ["WHO_FIBER_2023_CHUNK_01"]
    }
    retrieved = ["WHO_FIBER_2023_CHUNK_01"]
    res = validator.validate_claim(mutated_claim, retrieved, "Type2_Diabetes")

    assert res["is_valid"] is False
    assert res["rejection_code"] == "UNGROUNDED_NUMERICAL_CLAIM"
    print(f"\n[PASS] Test 6 Numerical Mutation Rejection: {res['reason']}")


def test_nlg_7_temporal_mutation_rejection():
    """Test 7: ClaimValidator rejects temporal shift (150 min/week -> 150 min/day)."""
    validator = ClaimValidator()
    mutated_claim = {
        "claim_id": "TEST_TEMPORAL_SHIFT",
        "claim_text": "Adults should do at least 150 minutes of aerobic activity per day.",
        "claim_type": "recommendation",
        "category": "physical_activity",
        "supporting_chunk_ids": ["WHO_PA_2020_CHUNK_01"]
    }
    retrieved = ["WHO_PA_2020_CHUNK_01"]
    res = validator.validate_claim(mutated_claim, retrieved, "Type2_Diabetes")

    assert res["is_valid"] is False
    assert res["rejection_code"] == "UNGROUNDED_NUMERICAL_CLAIM"
    print(f"\n[PASS] Test 7 Temporal Mutation Rejection: {res['reason']}")


def test_nlg_8_unsupported_medication_rejection():
    """Test 8: Prescribing GLP-1 or metformin without approved chunk is rejected by ClaimValidator."""
    validator = ClaimValidator()
    med_claim = {
        "claim_id": "TEST_MED_CLAIM",
        "claim_text": "Start taking GLP-1 receptor agonist medication immediately.",
        "claim_type": "recommendation",
        "category": "weight_management",
        "supporting_chunk_ids": ["CDC_DPP_2024_CHUNK_01"]
    }
    retrieved = ["CDC_DPP_2024_CHUNK_01"]
    res = validator.validate_claim(med_claim, retrieved, "Type2_Diabetes")

    assert res["is_valid"] is False
    assert res["rejection_code"] == "PROHIBITED_CLAIM_VIOLATION"
    print(f"\n[PASS] Test 8 Unsupported Medication Rejection: {res['reason']}")


def test_nlg_9_taxon_specific_cure_rejection():
    """Test 9: Taxon restoration claims are prohibited by ClaimValidator."""
    validator = ClaimValidator()
    taxon_claim = {
        "claim_id": "TEST_TAXON_CURE",
        "claim_text": "Consume this prebiotic supplement to restore Akkermansia abundance.",
        "claim_type": "recommendation",
        "category": "microbiome_support_diet",
        "supporting_chunk_ids": ["WHO_FIBER_2023_CHUNK_02"]
    }
    retrieved = ["WHO_FIBER_2023_CHUNK_02"]
    res = validator.validate_claim(taxon_claim, retrieved, "Type2_Diabetes")

    assert res["is_valid"] is False
    assert res["rejection_code"] == "PROHIBITED_TAXON_CURE"
    print(f"\n[PASS] Test 9 Taxon Cure Rejection: {res['reason']}")


def test_nlg_10_zero_evidence_llm_bypass():
    """Test 10: When retriever returns [], LLM is bypassed and deterministic fallback is returned."""
    class MockEmptyRetriever(EvidenceRetriever):
        def retrieve(self, *args, **kwargs):
            return []

    pg = PlanGenerator(retriever=MockEmptyRetriever())
    features = {"Fasting_Blood_Glucose": 150.0}
    disease_results = [{"disease": "Type2_Diabetes", "prediction": 1, "probability": 0.85, "risk_level": "High"}]
    xai_exps = {"Type2_Diabetes": {"risk_drivers": [{"feature_name": "Fasting_Blood_Glucose", "actual_value": 150.0, "importance": 0.28}]}}

    plan = pg.generate_personalized_plan(features, xai_exps, disease_results)
    recs = plan["recommendation_items"]

    assert len(recs) > 0
    for r in recs:
        assert "We could not retrieve sufficient condition-specific guideline evidence" in r["actionable_recommendation"]
    print("\n[PASS] Test 10 Zero Evidence Bypass: Deterministic notice strictly returned without LLM hallucination.")


def test_nlg_11_failed_llm_output_safe_fallback():
    """Test 11: If LLM output fails parameter binding or claim validation, safe fallback is used."""
    class BrokenNLG(ControlledNLG):
        def _synthesize_conversational_plan(self, context):
            return {
                "summary_title": "Your Personalized Health Plan",
                "contributing_explanations": {
                    # Purposely omit actual value to trigger binding failure
                    "Fasting_Blood_Glucose": "Your glucose was high without numbers."
                },
                "recommendation_texts": {
                    # Purposely mutate numbers to trigger claim validation failure
                    "physical_activity": "Do 150 minutes per day of intense exercise."
                }
            }

    pg = PlanGenerator(nlg=BrokenNLG())
    features = {"Fasting_Blood_Glucose": 150.0}
    disease_results = [{"disease": "Type2_Diabetes", "prediction": 1, "probability": 0.85, "risk_level": "High"}]
    xai_exps = {"Type2_Diabetes": {"risk_drivers": [{"feature_name": "Fasting_Blood_Glucose", "actual_value": 150.0, "importance": 0.28}]}}

    plan = pg.generate_personalized_plan(features, xai_exps, disease_results)

    # Contributing factor fell back to governed text containing 150.0 mg/dL
    glucose_item = next(i for i in plan["sections"]["section_b_what_is_contributing"]["contributing_items"] if i["parameter"] == "Fasting_Blood_Glucose")
    assert "150.0" in glucose_item["explanation_sentence"]

    # Recommendation fell back to conservative chunk text
    recs = plan["recommendation_items"]
    assert len(recs) > 0
    assert all(r["validation_passed"] for r in recs)
    print("\n[PASS] Test 11 Safe Fallback: Both parameter binding and claim validation safely degraded to governed truth.")


def test_nlg_12_api_backward_compatibility():
    """Test 12: API response maintains all existing keys with prediction and XAI intact."""
    payload = {
        "contract2": {
            "patient_info": {"name": "Alex Mercer", "age": 52, "gender": "Male"},
            "clinical": {
                "status": "complete",
                "values": {
                    "Age": {"canonical_value": 52},
                    "Gender": {"canonical_value": "Male"},
                    "Height": {"canonical_value": 175.0},
                    "Weight": {"canonical_value": 95.5},
                    "BMI": {"canonical_value": 31.2},
                    "Waist_Circumference": {"canonical_value": 104.0},
                    "Systolic_BP": {"canonical_value": 138.0},
                    "Diastolic_BP": {"canonical_value": 88.0},
                    "Fasting_Blood_Glucose": {"canonical_value": 150.0},
                    "HbA1c": {"canonical_value": 7.1},
                    "Triglycerides": {"canonical_value": 185.0},
                    "HDL": {"canonical_value": 38.0},
                    "LDL": {"canonical_value": 128.0},
                    "ALT": {"canonical_value": 32.0},
                    "AST": {"canonical_value": 28.0},
                    "Family_History_Diabetes": {"canonical_value": True},
                    "Family_History_Hypertension": {"canonical_value": True},
                    "Family_History_CVD": {"canonical_value": False}
                }
            },
            "wearable": {"status": "not_available"},
            "gut": {"status": "not_available"}
        },
        "user_answers": {},
        "patient_id": "P_COMPATIBILITY_CHECK"
    }
    response = client.post("/api/run-assessment", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["has_any_usable_data"] is True
    assert len(data["diseases"]) == 5
    assert "xai" in data
    assert "health_plan" in data
    assert data["health_plan"]["total_validated_recommendations"] >= 1
    print("\n[PASS] Test 12 API Compatibility: Complete prediction, XAI, and Health Plan returned seamlessly.")
