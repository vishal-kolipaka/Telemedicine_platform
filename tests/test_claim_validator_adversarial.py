"""
test_claim_validator_adversarial.py — Mandatory Adversarial Validation Test Suite

Validates that ClaimValidator rejects deliberately fabricated, contradictory,
and ungrounded claims citing real evidence chunks.
"""

import os
import sys
import json
import pytest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.recommendations.claim_validator import ClaimValidator


@pytest.fixture
def validator():
    return ClaimValidator()


def test_adversarial_test_a_unrelated_intervention(validator):
    """Test A: Completely Unrelated Intervention (48-hr water fast cited to exercise chunk)."""
    claim = {
        "claim_id": "TEST_A_FASTING",
        "claim_text": "Perform a 48-hour water fast every week to improve metabolic health.",
        "claim_type": "recommendation",
        "category": "physical_activity",
        "supporting_chunk_ids": ["WHO_PA_2020_CHUNK_01"]
    }
    retrieved = ["WHO_PA_2020_CHUNK_01"]
    res = validator.validate_claim(claim, retrieved, "Type2_Diabetes")
    
    assert res["is_valid"] is False
    assert res["rejection_code"] in ("UNSUPPORTED_SEMANTIC_DRIFT", "PROHIBITED_CLAIM_VIOLATION")
    print("\n[PASS] Test A correctly rejected:", res["rejection_code"], "-", res["reason"])


def test_adversarial_test_b_numerical_hallucination(validator):
    """Test B: Numerical Hallucination (50 g fiber daily cited to 25 g chunk)."""
    claim = {
        "claim_id": "TEST_B_NUMERICAL_50G",
        "claim_text": "Consume at least 50 g of dietary fiber every day.",
        "claim_type": "recommendation",
        "category": "dietary_nutrition",
        "supporting_chunk_ids": ["WHO_FIBER_2023_CHUNK_02"]
    }
    retrieved = ["WHO_FIBER_2023_CHUNK_02"]
    res = validator.validate_claim(claim, retrieved, "Type2_Diabetes")
    
    assert res["is_valid"] is False
    assert res["rejection_code"] == "UNGROUNDED_NUMERICAL_CLAIM"
    print("\n[PASS] Test B correctly rejected:", res["rejection_code"], "-", res["reason"])


def test_adversarial_test_c_contradictory_intervention(validator):
    """Test C: Contradictory Intervention (Increase sedentary time cited to sedentary reduction chunk)."""
    claim = {
        "claim_id": "TEST_C_CONTRADICTORY",
        "claim_text": "Increase sedentary time throughout the day to improve metabolic health.",
        "claim_type": "recommendation",
        "category": "physical_activity",
        "supporting_chunk_ids": ["WHO_PA_2020_CHUNK_03"]
    }
    retrieved = ["WHO_PA_2020_CHUNK_03"]
    res = validator.validate_claim(claim, retrieved, "Type2_Diabetes")
    
    assert res["is_valid"] is False
    assert res["rejection_code"] == "UNSUPPORTED_SEMANTIC_DRIFT"
    print("\n[PASS] Test C correctly rejected:", res["rejection_code"], "-", res["reason"])


def test_adversarial_test_d_citation_laundering(validator):
    """Test D: Citation Laundering (GLP-1 prescription cited to CDC DPP lifestyle chunk)."""
    claim = {
        "claim_id": "TEST_D_GLP1_LAUNDERING",
        "claim_text": "Take GLP-1 medication to achieve risk reduction for this prediction.",
        "claim_type": "recommendation",
        "category": "weight_management",
        "supporting_chunk_ids": ["CDC_DPP_2024_CHUNK_01"]
    }
    retrieved = ["CDC_DPP_2024_CHUNK_01"]
    res = validator.validate_claim(claim, retrieved, "Prediabetes")
    
    assert res["is_valid"] is False
    assert res["rejection_code"] == "PROHIBITED_CLAIM_VIOLATION"
    print("\n[PASS] Test D correctly rejected:", res["rejection_code"], "-", res["reason"])


def test_adversarial_test_e_taxon_specific_cure(validator):
    """Test E: Taxon-Specific Cure (Eat food to restore Akkermansia cited to fiber/ISAPP chunk)."""
    claim = {
        "claim_id": "TEST_E_TAXON_CURE",
        "claim_text": "Eat this food to restore Akkermansia and cure your disease.",
        "claim_type": "recommendation",
        "category": "microbiome_support_diet",
        "supporting_chunk_ids": ["WHO_FIBER_2023_CHUNK_02"]
    }
    retrieved = ["WHO_FIBER_2023_CHUNK_02"]
    res = validator.validate_claim(claim, retrieved, "Type2_Diabetes")
    
    assert res["is_valid"] is False
    assert res["rejection_code"] == "PROHIBITED_TAXON_CURE"
    print("\n[PASS] Test E correctly rejected:", res["rejection_code"], "-", res["reason"])


def test_adversarial_test_f_correct_claim_direct(validator):
    """Test F: Correct Claim (150-300 min moderate aerobic activity cited to WHO PA chunk)."""
    claim = {
        "claim_id": "TEST_F_CORRECT_DIRECT",
        "claim_text": "Adults should do at least 150–300 minutes of moderate-intensity aerobic physical activity throughout the week.",
        "claim_type": "recommendation",
        "category": "physical_activity",
        "supporting_chunk_ids": ["WHO_PA_2020_CHUNK_01"]
    }
    retrieved = ["WHO_PA_2020_CHUNK_01"]
    res = validator.validate_claim(claim, retrieved, "Type2_Diabetes")
    
    assert res["is_valid"] is True
    assert res["support_type"] in ("DIRECT", "DERIVED_LOGICAL")
    assert res["verified_chunk_id"] == "WHO_PA_2020_CHUNK_01"
    print("\n[PASS] Test F correctly approved:", res["support_type"], "-", res["reason"])


def test_adversarial_test_g_legitimate_derived_claim(validator):
    """Test G: Legitimate Derived Claim (30 min brisk walking 5 days/wk for 150 min goal)."""
    claim = {
        "claim_id": "TEST_G_DERIVED_LOGICAL",
        "claim_text": "Accumulate 30 minutes a day of moderate-intensity brisk walking 5 days a week to reach the 150 minutes weekly physical activity target.",
        "claim_type": "recommendation",
        "category": "physical_activity",
        "supporting_chunk_ids": ["CDC_DPP_2024_CHUNK_02"]
    }
    retrieved = ["CDC_DPP_2024_CHUNK_02"]
    res = validator.validate_claim(claim, retrieved, "Prediabetes")
    
    assert res["is_valid"] is True
    assert res["support_type"] in ("DIRECT", "DERIVED_LOGICAL")
    print("\n[PASS] Test G correctly approved:", res["support_type"], "-", res["reason"])


def test_adversarial_test_h_diagnostic_source_intervention_laundering(validator):
    """Test H: Diagnostic Source Laundering (AHA Metsyn 2005 cited for diet recommendation)."""
    claim = {
        "claim_id": "TEST_H_METSYN_LAUNDERING",
        "claim_text": "Follow a low sodium dietary plan to lower blood pressure below 130/85 mmHg.",
        "claim_type": "recommendation",
        "category": "dietary_nutrition",
        "supporting_chunk_ids": ["AHA_METSYN_2005_CHUNK_01"]
    }
    retrieved = ["AHA_METSYN_2005_CHUNK_01"]
    res = validator.validate_claim(claim, retrieved, "Metabolic_Syndrome")
    
    assert res["is_valid"] is False
    assert res["rejection_code"] in ("UNAUTHORIZED_SOURCE_ROLE", "UNAUTHORIZED_CHUNK_ROLE", "CATEGORY_MISMATCH")
    print("\n[PASS] Test H correctly rejected:", res["rejection_code"], "-", res["reason"])


def test_adversarial_test_i_unretrieved_chunk(validator):
    """Test I: Unretrieved Citation Fabricated by LLM."""
    claim = {
        "claim_id": "TEST_I_UNRETRIEVED",
        "claim_text": "Consume at least 25 g of dietary fiber per day.",
        "claim_type": "recommendation",
        "category": "dietary_nutrition",
        "supporting_chunk_ids": ["WHO_FIBER_2023_CHUNK_02"]
    }
    # WHO_FIBER_2023_CHUNK_02 was NOT retrieved in this session
    retrieved = ["WHO_PA_2020_CHUNK_01", "CDC_DPP_2024_CHUNK_01"]
    res = validator.validate_claim(claim, retrieved, "Type2_Diabetes")
    
    assert res["is_valid"] is False
    assert res["rejection_code"] == "UNRETRIEVED_CHUNK_CITATION"
    print("\n[PASS] Test I correctly rejected:", res["rejection_code"], "-", res["reason"])


def test_adversarial_test_j_temporal_unit_shift(validator):
    """Test J: Unit/temporal shift (150 minutes per day vs 150 minutes per week)."""
    claim = {
        "claim_id": "TEST_J_TEMPORAL_SHIFT",
        "claim_text": "Adults should perform at least 150 minutes per day of moderate-intensity aerobic physical activity.",
        "claim_type": "recommendation",
        "category": "physical_activity",
        "supporting_chunk_ids": ["WHO_PA_2020_CHUNK_01"]
    }
    retrieved = ["WHO_PA_2020_CHUNK_01"]
    res = validator.validate_claim(claim, retrieved, "Type2_Diabetes")
    
    assert res["is_valid"] is False
    assert res["rejection_code"] == "UNGROUNDED_NUMERICAL_CLAIM"
    assert "Temporal unit shift" in res["reason"]
    print("\n[PASS] Test J correctly rejected:", res["rejection_code"], "-", res["reason"])


def test_adversarial_test_k_wrong_condition_scope(validator):
    """Test K: Correct evidence but wrong condition scope (EASL MASLD chunk applied to T2D)."""
    claim = {
        "claim_id": "TEST_K_WRONG_CONDITION",
        "claim_text": "A weight loss of at least 5% of body weight is recommended.",
        "claim_type": "recommendation",
        "category": "weight_management",
        "supporting_chunk_ids": ["EASL_MASLD_2024_CHUNK_01"]
    }
    retrieved = ["EASL_MASLD_2024_CHUNK_01"]
    # EASL_MASLD_2024_CHUNK_01 allowed scopes: ['NAFLD', 'Metabolic_Syndrome', 'High_Adiposity_Risk']
    # We attempt to apply it to 'Type2_Diabetes'
    res = validator.validate_claim(claim, retrieved, "Type2_Diabetes")
    
    assert res["is_valid"] is False
    assert res["rejection_layer"] == "LAYER_2_ROLE_PERMISSIONS"
    assert res["rejection_code"] == "UNAUTHORIZED_CONDITION_SCOPE"
    print("\n[PASS] Test K correctly rejected at Layer 2:", res["rejection_code"], "-", res["reason"])


def test_adversarial_test_l_evidence_combination_laundering(validator):
    """Test L: Evidence combination / claim laundering (Combining exercise & fiber into unsupported fasting intervention)."""
    # Scenario 1: Category specified -> Layer 2 detects category mismatch on second cited chunk
    claim = {
        "claim_id": "TEST_L_CLAIM_LAUNDERING_CAT",
        "claim_text": "Engage in 150 minutes of physical activity specifically while water fasting on 25 g of fiber to reverse disease.",
        "claim_type": "recommendation",
        "category": "physical_activity",
        "supporting_chunk_ids": ["WHO_PA_2020_CHUNK_01", "WHO_FIBER_2023_CHUNK_02"]
    }
    retrieved = ["WHO_PA_2020_CHUNK_01", "WHO_FIBER_2023_CHUNK_02"]
    res = validator.validate_claim(claim, retrieved, "Type2_Diabetes")
    
    assert res["is_valid"] is False
    assert res["rejection_code"] in ("CATEGORY_MISMATCH", "PROHIBITED_CLAIM_VIOLATION", "UNSUPPORTED_SEMANTIC_DRIFT")
    print("\n[PASS] Test L (with category) correctly rejected at Layer 2:", res["rejection_code"], "-", res["reason"])

    # Scenario 2: Category omitted -> Detected as UNGROUNDED_NUMERICAL_CLAIM (numbers cross-cited) or PROHIBITED_CLAIM_VIOLATION
    claim_no_cat = {
        "claim_id": "TEST_L_CLAIM_LAUNDERING_NOCAT",
        "claim_text": "Engage in 150 minutes of physical activity specifically while water fasting on 25 g of fiber to reverse disease.",
        "claim_type": "recommendation",
        "category": "",
        "supporting_chunk_ids": ["WHO_PA_2020_CHUNK_01", "WHO_FIBER_2023_CHUNK_02"]
    }
    res_no_cat = validator.validate_claim(claim_no_cat, retrieved, "Type2_Diabetes")
    assert res_no_cat["is_valid"] is False
    assert res_no_cat["rejection_code"] in ("UNGROUNDED_NUMERICAL_CLAIM", "PROHIBITED_CLAIM_VIOLATION", "UNSUPPORTED_SEMANTIC_DRIFT")
    print("[PASS] Test L (without category) correctly rejected at Layer 3/4/5:", res_no_cat["rejection_code"], "-", res_no_cat["reason"])


if __name__ == "__main__":
    v = ClaimValidator()
    print("Running comprehensive adversarial validation test suite (A through L)...")
    test_adversarial_test_a_unrelated_intervention(v)
    test_adversarial_test_b_numerical_hallucination(v)
    test_adversarial_test_c_contradictory_intervention(v)
    test_adversarial_test_d_citation_laundering(v)
    test_adversarial_test_e_taxon_specific_cure(v)
    test_adversarial_test_f_correct_claim_direct(v)
    test_adversarial_test_g_legitimate_derived_claim(v)
    test_adversarial_test_h_diagnostic_source_intervention_laundering(v)
    test_adversarial_test_i_unretrieved_chunk(v)
    test_adversarial_test_j_temporal_unit_shift(v)
    test_adversarial_test_k_wrong_condition_scope(v)
    test_adversarial_test_l_evidence_combination_laundering(v)
    print("\n[SUCCESS] ALL 12 ADVERSARIAL TESTS (A-L) PASSED WITH 100% ACCURACY!")
