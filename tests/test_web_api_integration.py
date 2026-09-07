"""
tests/test_web_api_integration.py — End-to-End Web API Integration Tests

Tests the production API endpoints:
  POST /api/analyze
  POST /api/run-assessment
Across Scenario A (All 3 modalities + user answers), Scenario B (Partial data), and Scenario C (Insufficient data).
"""

import os
import sys
import json
import pytest
from fastapi.testclient import TestClient

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from api_server import app

client = TestClient(app)
DATA_DIR = os.path.join(PROJECT_ROOT, "testing datas")


def test_scenario_a_all_three_modalities_with_user_answers():
    """Scenario A: Clinical + Gut + Wearable uploaded, family history answered via user_answers."""
    clin_path = os.path.join(DATA_DIR, "clinical_report.txt")
    gut_path = os.path.join(DATA_DIR, "gut_microbiome_report.txt")
    wear_path = os.path.join(DATA_DIR, "fitbit_wearable_report.txt")

    # 1. Upload documents to /api/analyze
    with open(clin_path, "rb") as f1, open(gut_path, "rb") as f2, open(wear_path, "rb") as f3:
        files = [
            ("files", ("clinical_report.txt", f1, "text/plain")),
            ("files", ("gut_microbiome_report.txt", f2, "text/plain")),
            ("files", ("fitbit_wearable_report.txt", f3, "text/plain")),
        ]
        res_upload = client.post("/api/analyze", files=files)

    assert res_upload.status_code == 200
    upload_data = res_upload.json()
    assert len(upload_data) == 3
    contract2 = upload_data[0]["mapper_output"]
    assert contract2 is not None

    # Before user answers: clinical is incomplete (missing 3 FH fields)
    assert contract2["clinical"]["status"] == "incomplete"
    assert contract2["wearable"]["status"] == "complete"
    assert contract2["gut"]["status"] == "complete"

    # 2. Run assessment with user answers supplied for the 3 family history fields
    user_answers = {
        "Family_History_Diabetes": "Yes",
        "Family_History_Hypertension": "Yes",
        "Family_History_CVD": "No",
    }

    res_assess = client.post(
        "/api/run-assessment",
        json={
            "contract2": contract2,
            "user_answers": user_answers,
            "patient_id": "P001001",
        },
    )

    assert res_assess.status_code == 200
    data = res_assess.json()

    assert data["patient_id"] == "P001001"
    assert data["patient_name"] == "Arjun Mehta"
    assert data["patient_age"] == 47
    assert data["patient_gender"] == "Male"
    assert data["has_any_usable_data"] is True

    # Check 5 diseases
    diseases = {d["key"]: d for d in data["diseases"]}
    assert len(diseases) == 5

    # Check that assessment is available
    for k in ("Type2_Diabetes", "High_Adiposity_Risk", "Metabolic_Syndrome", "NAFLD"):
        assert diseases[k]["status_label"] == "Assessment Available"
        assert diseases[k]["risk_score"] is not None
        assert isinstance(diseases[k]["risk_percentage"], float)

    # Type 2 Diabetes: positive (approx 97.93%)
    assert diseases["Type2_Diabetes"]["decision"] is True
    assert diseases["Type2_Diabetes"]["decision_text"] == "Positive"
    assert diseases["Type2_Diabetes"]["risk_percentage"] == pytest.approx(97.93, abs=1.0)

    # Metabolic Syndrome: positive (approx 39.96%)
    assert diseases["Metabolic_Syndrome"]["decision"] is True
    assert diseases["Metabolic_Syndrome"]["risk_percentage"] == pytest.approx(39.96, abs=1.0)

    # NAFLD: negative (approx 26.43%)
    assert diseases["NAFLD"]["decision"] is False
    assert diseases["NAFLD"]["decision_text"] == "Negative"
    assert diseases["NAFLD"]["risk_percentage"] == pytest.approx(26.43, abs=1.0)

    # XAI Verification
    assert "xai" in data
    assert data["xai"]["has_usable_explanations"] is True
    assert data["xai"]["default_disease"] == "Type2_Diabetes"
    assert len(data["xai"]["explanations"]) == 5
    assert data["xai"]["explanations"]["Type2_Diabetes"]["available"] is True


def test_scenario_b_partial_information_gut_and_wearable_only():
    """Scenario B: Gut + Wearable uploaded, Clinical left unavailable."""
    gut_path = os.path.join(DATA_DIR, "gut_microbiome_report.txt")
    wear_path = os.path.join(DATA_DIR, "fitbit_wearable_report.txt")

    with open(gut_path, "rb") as f1, open(wear_path, "rb") as f2:
        files = [
            ("files", ("gut_microbiome_report.txt", f1, "text/plain")),
            ("files", ("fitbit_wearable_report.txt", f2, "text/plain")),
        ]
        res_upload = client.post("/api/analyze", files=files)

    assert res_upload.status_code == 200
    contract2 = res_upload.json()[0]["mapper_output"]
    assert contract2["clinical"]["status"] == "not_available"
    assert contract2["gut"]["status"] == "complete"
    assert contract2["wearable"]["status"] == "complete"

    # User proceeds without providing any answers
    res_assess = client.post(
        "/api/run-assessment",
        json={
            "contract2": contract2,
            "user_answers": {},
            "patient_id": "P001002",
        },
    )

    assert res_assess.status_code == 200
    data = res_assess.json()
    assert data["has_any_usable_data"] is True

    diseases = {d["key"]: d for d in data["diseases"]}
    # Dual-modality Gut+Wearable stacker produces Assessment Available across available conditions
    assert diseases["Type2_Diabetes"]["status_label"] == "Assessment Available"
    assert diseases["Prediabetes"]["status_label"] == "Assessment Available"
    assert diseases["High_Adiposity_Risk"]["status_label"] == "Assessment Available"
    assert diseases["Metabolic_Syndrome"]["status_label"] == "Assessment Available"
    assert diseases["NAFLD"]["status_label"] == "Assessment Available"

    assert diseases["Type2_Diabetes"]["risk_score"] is not None
    assert diseases["Prediabetes"]["risk_score"] is not None


def test_scenario_c_insufficient_information_non_medical_document():
    """Scenario C / Situation D: Non-medical document uploaded, all domains unavailable, proceed anyway."""
    non_med_path = os.path.join(DATA_DIR, "non_medical_doc.txt")

    with open(non_med_path, "rb") as f1:
        files = [("files", ("non_medical_doc.txt", f1, "text/plain"))]
        res_upload = client.post("/api/analyze", files=files)

    assert res_upload.status_code == 200
    contract2 = res_upload.json()[0]["mapper_output"]
    assert contract2["clinical"]["status"] == "not_available"
    assert contract2["gut"]["status"] == "not_available"
    assert contract2["wearable"]["status"] == "not_available"

    res_assess = client.post(
        "/api/run-assessment",
        json={
            "contract2": contract2,
            "user_answers": {},
            "patient_id": "P001003",
        },
    )

    assert res_assess.status_code == 200
    data = res_assess.json()
    assert data["has_any_usable_data"] is False
    assert "Insufficient" in data["summary_message"]

    for d in data["diseases"]:
        assert d["status_label"] == "Not Enough Information"
        assert d["risk_score"] is None
        assert d["risk_percentage"] is None
        assert d["decision"] is None
        assert d["decision_text"] == "N/A"


def test_situation_a_clinical_incomplete_without_answers_proceed_anyway():
    """Situation A: Clinical document uploaded, but 3 family history questions remain unanswered.
    User chooses to proceed anyway without completing the closest category.
    Backend Router marks clinical as incomplete -> not_run.
    Fusion V2 returns Not Enough Information for all 5 diseases without fake scores.
    """
    clin_path = os.path.join(DATA_DIR, "clinical_report.txt")

    with open(clin_path, "rb") as f1:
        files = [("files", ("clinical_report.txt", f1, "text/plain"))]
        res_upload = client.post("/api/analyze", files=files)

    assert res_upload.status_code == 200
    contract2 = res_upload.json()[0]["mapper_output"]
    assert contract2["clinical"]["status"] == "incomplete"
    assert len(contract2["clinical"]["missing_fields"]) == 3

    # User proceeds anyway without supplying answers
    res_assess = client.post(
        "/api/run-assessment",
        json={
            "contract2": contract2,
            "user_answers": {},
            "patient_id": "P001004",
        },
    )

    assert res_assess.status_code == 200
    data = res_assess.json()
    assert data["has_any_usable_data"] is False

    for d in data["diseases"]:
        assert d["status_label"] == "Not Enough Information"
        assert d["risk_score"] is None
        assert d["risk_percentage"] is None
        assert d["decision"] is None


def test_situation_b_single_category_gut_only():
    """Situation B: Exactly one category is complete (Gut only).
    Case 6 single-modality policy runs:
    T2D, HAR, MetSyn, NAFLD receive Limited Data Assessment.
    Prediabetes receives Not Enough Information.
    """
    gut_path = os.path.join(DATA_DIR, "gut_microbiome_report.txt")

    with open(gut_path, "rb") as f1:
        files = [("files", ("gut_microbiome_report.txt", f1, "text/plain"))]
        res_upload = client.post("/api/analyze", files=files)

    assert res_upload.status_code == 200
    contract2 = res_upload.json()[0]["mapper_output"]
    assert contract2["gut"]["status"] == "complete"
    assert contract2["clinical"]["status"] == "not_available"
    assert contract2["wearable"]["status"] == "not_available"

    res_assess = client.post(
        "/api/run-assessment",
        json={
            "contract2": contract2,
            "user_answers": {},
            "patient_id": "P001005",
        },
    )

    assert res_assess.status_code == 200
    data = res_assess.json()
    assert data["has_any_usable_data"] is True

    diseases = {d["key"]: d for d in data["diseases"]}
    assert diseases["Type2_Diabetes"]["status_label"] == "Limited Data Assessment"
    assert diseases["High_Adiposity_Risk"]["status_label"] == "Limited Data Assessment"
    assert diseases["Metabolic_Syndrome"]["status_label"] == "Limited Data Assessment"
    assert diseases["NAFLD"]["status_label"] == "Limited Data Assessment"
    assert diseases["Prediabetes"]["status_label"] == "Not Enough Information"
