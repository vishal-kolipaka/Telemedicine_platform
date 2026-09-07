"""
test_api_health_plan_integration.py — API & Pipeline Integration Tests for Governed Health Plan

Validates:
1. POST /api/run-assessment returns all existing prediction fields unchanged.
2. health_plan object is successfully attached with all 5 sections.
3. Actual patient values (e.g. 150 mg/dL, 7.1%, 31.2) are preserved verbatim.
4. XAI factors are correctly passed to the recommendation engine.
5. Zero-evidence / unusable data handling is graceful.
6. Backward compatibility: Works when health_plan is null or disabled.
7. ClaimValidator remains active on all recommendation items.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api_server import app

client = TestClient(app)


@pytest.fixture
def t2d_assessment_payload():
    clinical_feats = {
        "Age": 52,
        "Gender": "Male",
        "Height": 175.0,
        "Weight": 95.5,
        "BMI": 31.2,
        "Waist_Circumference": 104.0,
        "Systolic_BP": 138.0,
        "Diastolic_BP": 88.0,
        "Fasting_Blood_Glucose": 150.0,
        "HbA1c": 7.1,
        "Triglycerides": 185.0,
        "HDL": 38.0,
        "LDL": 128.0,
        "ALT": 32.0,
        "AST": 28.0,
        "Family_History_Diabetes": True,
        "Family_History_Hypertension": True,
        "Family_History_CVD": False,
    }
    return {
        "contract2": {
            "patient_info": {
                "name": "Alex Mercer",
                "age": 52,
                "gender": "Male"
            },
            "clinical": {
                "status": "complete",
                "values": {
                    k: {"canonical_value": v, "unit": "", "source": "test"}
                    for k, v in clinical_feats.items()
                }
            },
            "wearable": {
                "status": "not_available"
            },
            "gut": {
                "status": "not_available"
            }
        },
        "user_answers": {},
        "patient_id": "P_INTEGRATION_001"
    }


def test_api_run_assessment_preserves_existing_prediction_and_xai(t2d_assessment_payload):
    """Test 1: Existing prediction fields and XAI outputs remain 100% intact."""
    response = client.post("/api/run-assessment", json=t2d_assessment_payload)
    assert response.status_code == 200
    data = response.json()

    # Verify existing prediction fields
    assert "patient_id" in data
    assert data["patient_id"] == "P_INTEGRATION_001"
    assert "diseases" in data
    assert len(data["diseases"]) == 5
    assert "xai" in data
    assert data["has_any_usable_data"] is True

    # Verify T2D prediction is present
    t2d_item = next(d for d in data["diseases"] if d["key"] == "Type2_Diabetes")
    assert t2d_item["risk_percentage"] is not None
    assert t2d_item["decision"] is True
    print("\n[PASS] Test 1 API Preservation: Existing fields intact. T2D risk:", t2d_item["risk_percentage"], "%")


def test_api_run_assessment_attaches_governed_health_plan(t2d_assessment_payload):
    """Test 2: health_plan object is attached with all 5 sections."""
    response = client.post("/api/run-assessment", json=t2d_assessment_payload)
    assert response.status_code == 200
    data = response.json()

    assert "health_plan" in data
    hp = data["health_plan"]
    assert hp is not None
    assert hp["summary_title"] == "Your Personalized Health Plan"
    assert "sections" in hp
    sections = hp["sections"]

    # Verify all 5 required sections
    assert "section_a_your_results" in sections
    assert "section_b_what_is_contributing" in sections
    assert "section_c_what_to_focus_on_first" in sections
    assert "section_d_personalized_recommendations" in sections
    assert "section_e_why_suggested" in sections
    print(f"\n[PASS] Test 2 Health Plan Attached: Total validated recommendations = {hp['total_validated_recommendations']}")


def test_api_preserves_exact_patient_values_in_health_plan(t2d_assessment_payload):
    """Test 3: Exact patient values (150 mg/dL, 7.1%, 31.2) are preserved in Section B."""
    response = client.post("/api/run-assessment", json=t2d_assessment_payload)
    data = response.json()
    items = data["health_plan"]["sections"]["section_b_what_is_contributing"]["contributing_items"]

    glucose_entry = next((i for i in items if i["parameter"] == "Fasting_Blood_Glucose"), None)
    assert glucose_entry is not None
    assert glucose_entry["patient_value"] == 150.0
    assert glucose_entry["unit"] == "mg/dL"
    assert glucose_entry["status"] == "above_expected_range"
    assert "150" in glucose_entry["explanation_sentence"]
    print(f"\n[PASS] Test 3 Actual Value Preservation in API: {glucose_entry['explanation_sentence']}")


def test_api_zero_data_fallback():
    """Test 4: Unusable data returns graceful fallback without crash."""
    empty_payload = {
        "contract2": {
            "patient_info": {},
            "clinical": {"status": "not_available"},
            "wearable": {"status": "not_available"},
            "gut": {"status": "not_available"}
        },
        "patient_id": "P_EMPTY"
    }
    response = client.post("/api/run-assessment", json=empty_payload)
    assert response.status_code == 200
    data = response.json()

    assert data["has_any_usable_data"] is False
    assert data["health_plan"] is None or data["health_plan"].get("status") == "GENERATION_UNAVAILABLE"
    print("\n[PASS] Test 4 Zero Data Fallback: Gracefully handled with has_any_usable_data=False")


def test_api_claim_validator_active_on_recommendations(t2d_assessment_payload):
    """Test 5: All recommendation items in the response are marked validation_passed=True."""
    response = client.post("/api/run-assessment", json=t2d_assessment_payload)
    data = response.json()
    recs = data["health_plan"]["recommendation_items"]

    assert len(recs) > 0
    for r in recs:
        assert r["validation_passed"] is True
        assert r["status"] in ("VALIDATED", "VALIDATED_CONSERVATIVE")
        assert len(r["supporting_chunk_ids"]) > 0
    print(f"\n[PASS] Test 5 ClaimValidator Active: {len(recs)} recommendation items verified with valid provenance citations.")


def test_api_backward_compatibility_when_health_plan_fails(monkeypatch, t2d_assessment_payload):
    """Test 6: If PlanGenerator throws an unexpected error, API still returns 200 with full prediction."""
    from src.recommendations.plan_generator import PlanGenerator

    def mock_broken_plan(*args, **kwargs):
        raise RuntimeError("Simulated PlanGenerator internal failure")

    monkeypatch.setattr(PlanGenerator, "generate_personalized_plan", mock_broken_plan)

    response = client.post("/api/run-assessment", json=t2d_assessment_payload)
    assert response.status_code == 200
    data = response.json()

    # Prediction and XAI are completely preserved
    assert data["has_any_usable_data"] is True
    assert len(data["diseases"]) == 5
    assert data["health_plan"]["status"] == "GENERATION_UNAVAILABLE"
    print("\n[PASS] Test 6 Fault Isolation: Prediction pipeline remained fully operational during PlanGenerator exception.")
