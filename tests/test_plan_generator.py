"""
test_plan_generator.py — Phase 4 Governed Recommendation & Plan Assembly Tests

Tests:
1. Actual Value Explanation (preserves exact patient values).
2. No Invented Reference Range (interpretation_unavailable when range absent).
3. Simple English Generation (clear, empathetic, non-technical language).
4. Recommendation Evidence Boundary (zero-evidence fallback when retrieval is empty).
5. Numerical Hallucination (150 min/day rejected by ClaimValidator).
6. Unsupported Medication (GLP-1 prescription rejected).
7. Taxon-Specific Intervention (Akkermansia restoration rejected).
8. Priority Personalization (distinct patient profiles yield distinct priorities).
9. No Overwhelming Recommendation Dump (maximum 2-3 relevant priorities selected).
"""

import os
import sys
import pytest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.recommendations.patient_context_builder import PatientContextBuilder
from src.recommendations.personalization_engine import PersonalizationEngine
from src.recommendations.plan_generator import PlanGenerator
from src.recommendations.claim_validator import ClaimValidator
from src.recommendations.evidence_retriever import EvidenceRetriever


@pytest.fixture
def plan_gen():
    return PlanGenerator()


@pytest.fixture
def sample_t2d_patient():
    features = {
        "Age": 52,
        "BMI": 31.2,
        "Fasting_Blood_Glucose": 150.0,
        "HbA1c": 7.1,
        "Systolic_BP": 138.0,
        "Diastolic_BP": 88.0,
        "Triglycerides": 185.0,
        "Daily_Steps": 4200,
        "Sedentary_Minutes": 540,
        "Moderate_Activity_Minutes": 45,
    }
    disease_results = [
        {"disease": "Type2_Diabetes", "prediction": 1, "probability": 0.85, "risk_level": "High"},
        {"disease": "Prediabetes", "prediction": 0, "probability": 0.05, "risk_level": "Low (Suppressed)"},
        {"disease": "High_Adiposity_Risk", "prediction": 1, "probability": 0.78, "risk_level": "Moderate-High"},
        {"disease": "Metabolic_Syndrome", "prediction": 1, "probability": 0.80, "risk_level": "High"},
        {"disease": "NAFLD", "prediction": 0, "probability": 0.35, "risk_level": "Low"}
    ]
    xai_explanations = {
        "Type2_Diabetes": {
            "risk_drivers": [
                {"feature_name": "Fasting_Blood_Glucose", "actual_value": 150.0, "importance": 0.28},
                {"feature_name": "HbA1c", "actual_value": 7.1, "importance": 0.22},
                {"feature_name": "BMI", "actual_value": 31.2, "importance": 0.15},
                {"feature_name": "Daily_Steps", "actual_value": 4200, "importance": 0.12},
            ],
            "protective_factors": []
        }
    }
    return features, disease_results, xai_explanations


@pytest.fixture
def sample_nafld_patient():
    features = {
        "Age": 45,
        "BMI": 29.5,
        "ALT": 78.0,
        "AST": 52.0,
        "Triglycerides": 210.0,
        "Fasting_Blood_Glucose": 95.0,
        "Daily_Steps": 8200,
        "Moderate_Activity_Minutes": 160
    }
    disease_results = [
        {"disease": "NAFLD", "prediction": 1, "probability": 0.82, "risk_level": "High"},
        {"disease": "Type2_Diabetes", "prediction": 0, "probability": 0.15, "risk_level": "Low"},
        {"disease": "High_Adiposity_Risk", "prediction": 1, "probability": 0.70, "risk_level": "Moderate"},
    ]
    xai_explanations = {
        "NAFLD": {
            "risk_drivers": [
                {"feature_name": "ALT", "actual_value": 78.0, "importance": 0.30},
                {"feature_name": "AST", "actual_value": 52.0, "importance": 0.25},
                {"feature_name": "Triglycerides", "actual_value": 210.0, "importance": 0.18}
            ],
            "protective_factors": []
        }
    }
    return features, disease_results, xai_explanations


def test_plan_test_1_actual_value_explanation(plan_gen, sample_t2d_patient):
    """Test 1: Actual patient values (150 mg/dL) are preserved verbatim without distortion."""
    features, disease_results, xai_explanations = sample_t2d_patient
    plan = plan_gen.generate_personalized_plan(features, xai_explanations, disease_results)

    section_b = plan["sections"]["section_b_what_is_contributing"]
    items = section_b["contributing_items"]
    glucose_item = next(i for i in items if i["parameter"] == "Fasting_Blood_Glucose")

    assert glucose_item["patient_value"] == 150.0
    assert glucose_item["unit"] == "mg/dL"
    assert glucose_item["status"] == "above_expected_range"
    assert "150" in glucose_item["explanation_sentence"]
    assert "above the expected" in glucose_item["explanation_sentence"]
    print(f"\n[PASS] Test 1 Actual Value Explanation: {glucose_item['explanation_sentence']}")


def test_plan_test_2_no_invented_reference_range(plan_gen):
    """Test 2: When no governed reference range exists, status is interpretation_unavailable and high/low is not stated."""
    features = {"Custom_Exploratory_Biomarker_X": 42.5}
    disease_results = [{"disease": "Type2_Diabetes", "prediction": 1, "probability": 0.80, "risk_level": "High"}]
    xai_explanations = {
        "Type2_Diabetes": {
            "risk_drivers": [{"feature_name": "Custom_Exploratory_Biomarker_X", "actual_value": 42.5, "importance": 0.20}],
            "protective_factors": []
        }
    }

    plan = plan_gen.generate_personalized_plan(features, xai_explanations, disease_results)
    items = plan["sections"]["section_b_what_is_contributing"]["contributing_items"]
    custom_item = items[0]

    assert custom_item["status"] == "interpretation_unavailable"
    assert "above" not in custom_item["explanation_sentence"].lower()
    assert "high" not in custom_item["explanation_sentence"].lower()
    assert "abnormal" not in custom_item["explanation_sentence"].lower()
    assert "42.5" in custom_item["explanation_sentence"]
    print(f"\n[PASS] Test 2 No Invented Range: {custom_item['explanation_sentence']}")


def test_plan_test_3_simple_english_generation(plan_gen, sample_t2d_patient):
    """Test 3: Converts technical risk predictions and metrics into clear, non-alarmist English."""
    features, disease_results, xai_explanations = sample_t2d_patient
    plan = plan_gen.generate_personalized_plan(features, xai_explanations, disease_results)

    section_a = plan["sections"]["section_a_your_results"]
    section_c = plan["sections"]["section_c_what_to_focus_on_first"]

    assert "elevated" in section_a["body"].lower()
    assert "not a formal medical diagnosis" in section_a["body"].lower()
    assert "stepwise priority" in section_c["intro"].lower() or "manageable steps" in section_c["intro"].lower()
    print(f"\n[PASS] Test 3 Simple English: Results Summary Section: {section_a['body'][:120]}...")


def test_plan_test_4_recommendation_evidence_boundary(plan_gen):
    """Test 4: Zero evidence retrieval returns deterministic fallback notice without LLM hallucination."""
    # Force mock retriever to return []
    class MockEmptyRetriever(EvidenceRetriever):
        def retrieve(self, *args, **kwargs):
            return []

    empty_gen = PlanGenerator(retriever=MockEmptyRetriever())
    features = {"Fasting_Blood_Glucose": 150.0}
    disease_results = [{"disease": "Type2_Diabetes", "prediction": 1, "probability": 0.80, "risk_level": "High"}]
    xai_explanations = {
        "Type2_Diabetes": {
            "risk_drivers": [{"feature_name": "Fasting_Blood_Glucose", "actual_value": 150.0, "importance": 0.20}],
            "protective_factors": []
        }
    }

    plan = empty_gen.generate_personalized_plan(features, xai_explanations, disease_results)
    recs = plan["sections"]["section_d_personalized_recommendations"]["recommendations"]

    assert len(recs) > 0
    for r in recs:
        assert "We could not retrieve sufficient condition-specific guideline evidence" in r["recommendation_text"]
    print("\n[PASS] Test 4 Evidence Boundary: Zero-evidence fallback strictly returned when retrieval is empty.")


def test_plan_test_5_numerical_hallucination_blocked(plan_gen):
    """Test 5: ClaimValidator rejects numerical frequency hallucination (150 min/day)."""
    claim = {
        "claim_id": "TEST_5_HALLUCINATION",
        "claim_text": "Adults should perform 150 minutes per day of moderate aerobic exercise.",
        "claim_type": "recommendation",
        "category": "physical_activity",
        "supporting_chunk_ids": ["WHO_PA_2020_CHUNK_01"]
    }
    retrieved = ["WHO_PA_2020_CHUNK_01"]
    res = plan_gen.validator.validate_claim(claim, retrieved, "Type2_Diabetes")

    assert res["is_valid"] is False
    assert res["rejection_code"] == "UNGROUNDED_NUMERICAL_CLAIM"
    print("\n[PASS] Test 5 Numerical Hallucination Blocked:", res["reason"])


def test_plan_test_6_unsupported_medication_blocked(plan_gen):
    """Test 6: ClaimValidator rejects unsupported medication prescription (Take GLP-1)."""
    claim = {
        "claim_id": "TEST_6_MEDICATION",
        "claim_text": "Take GLP-1 medication to manage your blood sugar levels.",
        "claim_type": "recommendation",
        "category": "weight_management",
        "supporting_chunk_ids": ["CDC_DPP_2024_CHUNK_01"]
    }
    retrieved = ["CDC_DPP_2024_CHUNK_01"]
    res = plan_gen.validator.validate_claim(claim, retrieved, "Prediabetes")

    assert res["is_valid"] is False
    assert res["rejection_code"] == "PROHIBITED_CLAIM_VIOLATION"
    print("\n[PASS] Test 6 Unsupported Medication Blocked:", res["reason"])


def test_plan_test_7_taxon_specific_intervention_blocked(plan_gen):
    """Test 7: ClaimValidator rejects taxon restoration claim (Eat food to restore Akkermansia)."""
    claim = {
        "claim_id": "TEST_7_TAXON",
        "claim_text": "Eat this prebiotic food to restore Akkermansia and cure your disease.",
        "claim_type": "recommendation",
        "category": "microbiome_support_diet",
        "supporting_chunk_ids": ["WHO_FIBER_2023_CHUNK_02"]
    }
    retrieved = ["WHO_FIBER_2023_CHUNK_02"]
    res = plan_gen.validator.validate_claim(claim, retrieved, "Type2_Diabetes")

    assert res["is_valid"] is False
    assert res["rejection_code"] == "PROHIBITED_TAXON_CURE"
    print("\n[PASS] Test 7 Taxon-Specific Intervention Blocked:", res["reason"])


def test_plan_test_8_priority_personalization(plan_gen, sample_t2d_patient, sample_nafld_patient):
    """Test 8: Distinct patient contexts produce distinct, tailored recommendation priorities."""
    # Patient 1: T2D with high glucose & low activity
    t2d_feat, t2d_dis, t2d_xai = sample_t2d_patient
    plan_t2d = plan_gen.generate_personalized_plan(t2d_feat, t2d_xai, t2d_dis)
    t2d_priorities = [p["pillar_key"] for p in plan_t2d["selected_priorities"]]

    # Patient 2: NAFLD with high ALT/AST enzymes
    nafld_feat, nafld_dis, nafld_xai = sample_nafld_patient
    plan_nafld = plan_gen.generate_personalized_plan(nafld_feat, nafld_xai, nafld_dis)
    nafld_priorities = [p["pillar_key"] for p in plan_nafld["selected_priorities"]]

    assert t2d_priorities != nafld_priorities
    assert "physical_activity" in t2d_priorities
    assert "dietary_nutrition" in nafld_priorities or "weight_management" in nafld_priorities
    print(f"\n[PASS] Test 8 Priority Personalization: T2D Priorities={t2d_priorities} vs NAFLD Priorities={nafld_priorities}")


def test_plan_test_9_no_overwhelming_dump(plan_gen, sample_t2d_patient):
    """Test 9: System selects at most 3 relevant priority pillars instead of dumping every category."""
    features, disease_results, xai_explanations = sample_t2d_patient
    plan = plan_gen.generate_personalized_plan(features, xai_explanations, disease_results)

    priorities = plan["selected_priorities"]
    recs = plan["recommendation_items"]

    assert 1 <= len(priorities) <= 3
    assert 1 <= len(recs) <= 3
    print(f"\n[PASS] Test 9 Controlled Recommendations: Generated exactly {len(recs)} targeted recommendations (no dump).")


if __name__ == "__main__":
    pg = PlanGenerator()
    print("Running Phase 4 Plan Generator Tests...")
    t2d_p = (
        {"Fasting_Blood_Glucose": 150.0, "BMI": 31.2, "Daily_Steps": 4200},
        [{"disease": "Type2_Diabetes", "prediction": 1, "probability": 0.85, "risk_level": "High"}],
        {"Type2_Diabetes": {"risk_drivers": [{"feature_name": "Fasting_Blood_Glucose", "actual_value": 150.0, "importance": 0.28}]}}
    )
    nafld_p = (
        {"ALT": 78.0, "AST": 52.0, "BMI": 29.5},
        [{"disease": "NAFLD", "prediction": 1, "probability": 0.82, "risk_level": "High"}],
        {"NAFLD": {"risk_drivers": [{"feature_name": "ALT", "actual_value": 78.0, "importance": 0.30}]}}
    )
    test_plan_test_1_actual_value_explanation(pg, t2d_p)
    test_plan_test_2_no_invented_reference_range(pg)
    test_plan_test_3_simple_english_generation(pg, t2d_p)
    test_plan_test_4_recommendation_evidence_boundary(pg)
    test_plan_test_5_numerical_hallucination_blocked(pg)
    test_plan_test_6_unsupported_medication_blocked(pg)
    test_plan_test_7_taxon_specific_intervention_blocked(pg)
    test_plan_test_8_priority_personalization(pg, t2d_p, nafld_p)
    test_plan_test_9_no_overwhelming_dump(pg, t2d_p)
    print("\n[SUCCESS] ALL 9 PHASE 4 TESTS PASSED FLAWLESSLY!")
