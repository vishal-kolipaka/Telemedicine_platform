"""
test_router.py — Verification suite for Model Router (Section 19 / Phase 2)

Covers:
  1. All three complete -> all models execute and return results
  2. Clinical only -> only clinical executes; others not_run
  3. Wearable only -> only wearable executes; 15 features, no Age/Gender passed
  4. Gut only -> only gut executes; 21 raw taxa passed, CLR executed internally by wrapper
  5. One model failure -> isolated error; remaining independent domains succeed
  6. Invalid complete contract -> missing field in 'complete' domain yields contract_error
  7. Output organization -> strictly keyed by domain name ('clinical', 'wearable', 'gut')
  8. Type/value encodings -> categorical 'Male'/'Female' and booleans encode properly
"""

import pytest
from src.router.router import (
    ModelRouter,
    route_and_predict,
    CLINICAL_FEATURES,
    WEARABLE_FEATURES,
    GUT_RAW_TAXA_FEATURES,
)


# Fixtures for realistic complete domain payloads
@pytest.fixture
def complete_clinical_values():
    return {
        "Age": {"canonical_value": 45, "canonical_unit": "years"},
        "Gender": {"canonical_value": "Male", "canonical_unit": ""},
        "Height": {"canonical_value": 175.0, "canonical_unit": "cm"},
        "Weight": {"canonical_value": 80.0, "canonical_unit": "kg"},
        "BMI": {"canonical_value": 26.1, "canonical_unit": "kg/m2"},
        "Waist_Circumference": {"canonical_value": 90.0, "canonical_unit": "cm"},
        "Systolic_BP": {"canonical_value": 120.0, "canonical_unit": "mmHg"},
        "Diastolic_BP": {"canonical_value": 80.0, "canonical_unit": "mmHg"},
        "Fasting_Blood_Glucose": {"canonical_value": 100.0, "canonical_unit": "mg/dL"},
        "HbA1c": {"canonical_value": 5.6, "canonical_unit": "%"},
        "Triglycerides": {"canonical_value": 150.0, "canonical_unit": "mg/dL"},
        "HDL": {"canonical_value": 50.0, "canonical_unit": "mg/dL"},
        "LDL": {"canonical_value": 100.0, "canonical_unit": "mg/dL"},
        "ALT": {"canonical_value": 25.0, "canonical_unit": "U/L"},
        "AST": {"canonical_value": 22.0, "canonical_unit": "U/L"},
        "Family_History_Diabetes": {"canonical_value": False, "canonical_unit": ""},
        "Family_History_Hypertension": {"canonical_value": False, "canonical_unit": ""},
        "Family_History_CVD": {"canonical_value": False, "canonical_unit": ""},
    }


@pytest.fixture
def complete_wearable_values():
    return {
        "Average_Daily_Steps": {"canonical_value": 8000.0, "canonical_unit": "steps/day"},
        "Active_Minutes": {"canonical_value": 45.0, "canonical_unit": "minutes/day"},
        "Sedentary_Time_Minutes": {"canonical_value": 600.0, "canonical_unit": "minutes/day"},
        "Resting_Heart_Rate": {"canonical_value": 70.0, "canonical_unit": "bpm"},
        "Heart_Rate_Variability_RMSSD": {"canonical_value": 45.0, "canonical_unit": "ms"},
        "Sleep_Duration_Hours": {"canonical_value": 7.5, "canonical_unit": "hours"},
        "Sleep_Efficiency_Score": {"canonical_value": 85.0, "canonical_unit": "score"},
        "Autonomic_Stress_Score": {"canonical_value": 3.2, "canonical_unit": "score"},
        "Activity_Energy_Expenditure": {"canonical_value": 2200.0, "canonical_unit": "kcal/day"},
        "Exercise_Frequency_Days": {"canonical_value": 4.0, "canonical_unit": "days/week"},
        "CGM_Average_Glucose": {"canonical_value": 105.0, "canonical_unit": "mg/dL"},
        "CGM_Glucose_CV": {"canonical_value": 18.0, "canonical_unit": "% CV"},
        "CGM_Time_In_Range": {"canonical_value": 90.0, "canonical_unit": "%"},
        "CGM_Time_Above_Range": {"canonical_value": 6.0, "canonical_unit": "%"},
        "CGM_Time_Below_Range": {"canonical_value": 4.0, "canonical_unit": "%"},
    }


@pytest.fixture
def complete_gut_values():
    return {
        "Akkermansia": {"canonical_value": 4.8, "canonical_unit": "relative abundance %"},
        "Faecalibacterium": {"canonical_value": 11.6, "canonical_unit": "relative abundance %"},
        "Roseburia": {"canonical_value": 5.1, "canonical_unit": "relative abundance %"},
        "Bifidobacterium": {"canonical_value": 7.4, "canonical_unit": "relative abundance %"},
        "Bacteroides": {"canonical_value": 9.2, "canonical_unit": "relative abundance %"},
        "Prevotella": {"canonical_value": 6.4, "canonical_unit": "relative abundance %"},
        "Ruminococcus": {"canonical_value": 3.5, "canonical_unit": "relative abundance %"},
        "Blautia": {"canonical_value": 4.0, "canonical_unit": "relative abundance %"},
        "Collinsella": {"canonical_value": 2.3, "canonical_unit": "relative abundance %"},
        "Escherichia_Shigella": {"canonical_value": 1.2, "canonical_unit": "relative abundance %"},
        "Coprococcus": {"canonical_value": 1.8, "canonical_unit": "relative abundance %"},
        "Alistipes": {"canonical_value": 3.0, "canonical_unit": "relative abundance %"},
        "Subdoligranulum": {"canonical_value": 2.1, "canonical_unit": "relative abundance %"},
        "Enterococcus": {"canonical_value": 0.9, "canonical_unit": "relative abundance %"},
        "Eubacterium": {"canonical_value": 3.3, "canonical_unit": "relative abundance %"},
        "Parabacteroides": {"canonical_value": 2.7, "canonical_unit": "relative abundance %"},
        "Lactobacillus": {"canonical_value": 1.5, "canonical_unit": "relative abundance %"},
        "Klebsiella": {"canonical_value": 0.6, "canonical_unit": "relative abundance %"},
        "Streptococcus": {"canonical_value": 2.8, "canonical_unit": "relative abundance %"},
        "Eggerthella": {"canonical_value": 1.0, "canonical_unit": "relative abundance %"},
        "Other_Taxa": {"canonical_value": 24.8, "canonical_unit": "relative abundance %"},
    }


# ────────────────────────────────────────────────────────────
# TEST 1: ALL THREE COMPLETE
# ────────────────────────────────────────────────────────────
def test_all_three_complete(complete_clinical_values, complete_wearable_values, complete_gut_values):
    contract2 = {
        "clinical": {"status": "complete", "values": complete_clinical_values},
        "wearable": {"status": "complete", "values": complete_wearable_values},
        "gut": {"status": "complete", "values": complete_gut_values},
        "patient_info": {"Name": "Rahul Sharma", "Age": 45, "Gender": "Male"},
    }

    results = route_and_predict(contract2)

    assert set(results.keys()) == {"clinical", "wearable", "gut"}
    for domain in ("clinical", "wearable", "gut"):
        assert results[domain]["status"] == "success"
        assert "probabilities" in results[domain]
        assert "predictions" in results[domain]
        assert "threshold_used" in results[domain]
        assert "suppressed_labels" in results[domain]
        assert len(results[domain]["predictions"]) == 5


# ────────────────────────────────────────────────────────────
# TEST 2: CLINICAL ONLY
# ────────────────────────────────────────────────────────────
def test_clinical_only(complete_clinical_values):
    contract2 = {
        "clinical": {"status": "complete", "values": complete_clinical_values},
        "wearable": {"status": "incomplete", "values": {}},
        "gut": {"status": "not_available", "values": {}},
        "patient_info": {"Name": "Rahul Sharma"},
    }

    results = route_and_predict(contract2)

    assert results["clinical"]["status"] == "success"
    assert results["wearable"]["status"] == "not_run"
    assert results["gut"]["status"] == "not_run"
    assert "probabilities" in results["clinical"]
    assert "probabilities" not in results["wearable"]
    assert "probabilities" not in results["gut"]


# ────────────────────────────────────────────────────────────
# TEST 3: WEARABLE ONLY (NO Age/Gender passed)
# ────────────────────────────────────────────────────────────
def test_wearable_only(complete_wearable_values):
    passed_features = None

    def mock_predict_wearable(feat_dict):
        nonlocal passed_features
        passed_features = feat_dict
        return {"probabilities": {}, "predictions": {}, "threshold_used": 0.5, "suppressed_labels": []}

    router = ModelRouter(predict_wearable_fn=mock_predict_wearable)

    contract2 = {
        "clinical": {"status": "incomplete", "values": {}},
        "wearable": {"status": "complete", "values": complete_wearable_values},
        "gut": {"status": "not_available", "values": {}},
    }

    results = router.route(contract2)

    assert results["wearable"]["status"] == "success"
    assert results["clinical"]["status"] == "not_run"
    assert results["gut"]["status"] == "not_run"

    assert len(passed_features) == 15
    assert set(passed_features.keys()) == set(WEARABLE_FEATURES)
    assert "Age" not in passed_features
    assert "Gender" not in passed_features
    assert passed_features["Sleep_Efficiency_Score"] == 85.0


# ────────────────────────────────────────────────────────────
# TEST 4: GUT ONLY (RAW taxa passed, CLR handled internally)
# ────────────────────────────────────────────────────────────
def test_gut_only(complete_gut_values):
    passed_features = None

    def mock_predict_gut(feat_dict):
        nonlocal passed_features
        passed_features = feat_dict
        # Call real predict_gut to ensure end-to-end wrapper correctness
        from gut_model.src.predict_gut import predict_gut
        return predict_gut(feat_dict)

    router = ModelRouter(predict_gut_fn=mock_predict_gut)

    contract2 = {
        "clinical": {"status": "not_available", "values": {}},
        "wearable": {"status": "incomplete", "values": {}},
        "gut": {"status": "complete", "values": complete_gut_values},
    }

    results = router.route(contract2)

    assert results["gut"]["status"] == "success"
    assert len(passed_features) == 21
    assert set(passed_features.keys()) == set(GUT_RAW_TAXA_FEATURES)
    assert not any(k.endswith("_CLR") for k in passed_features.keys())


# ────────────────────────────────────────────────────────────
# TEST 5: ONE MODEL FAILURE (Isolation)
# ────────────────────────────────────────────────────────────
def test_one_model_failure_isolation(complete_clinical_values, complete_wearable_values, complete_gut_values):
    def broken_clinical(_feat):
        raise RuntimeError("Simulated XGBoost CUDA / Memory Error")

    router = ModelRouter(predict_clinical_fn=broken_clinical)

    contract2 = {
        "clinical": {"status": "complete", "values": complete_clinical_values},
        "wearable": {"status": "complete", "values": complete_wearable_values},
        "gut": {"status": "complete", "values": complete_gut_values},
    }

    results = router.route(contract2)

    # Clinical failed
    assert results["clinical"]["status"] == "error"
    assert results["clinical"]["error_type"] == "model_execution_error"
    assert "Simulated XGBoost" in results["clinical"]["error_message"]

    # Wearable and Gut still succeeded
    assert results["wearable"]["status"] == "success"
    assert results["gut"]["status"] == "success"


# ────────────────────────────────────────────────────────────
# TEST 6: INVALID COMPLETE CONTRACT (Missing field in values)
# ────────────────────────────────────────────────────────────
def test_invalid_complete_contract(complete_clinical_values):
    # Invalidate by removing a required field
    corrupted_values = complete_clinical_values.copy()
    del corrupted_values["Systolic_BP"]

    called = False
    def mock_predict(_feat):
        nonlocal called
        called = True
        return {}

    router = ModelRouter(predict_clinical_fn=mock_predict)

    contract2 = {
        "clinical": {"status": "complete", "values": corrupted_values},
        "wearable": {"status": "not_available", "values": {}},
        "gut": {"status": "not_available", "values": {}},
    }

    results = router.route(contract2)

    assert results["clinical"]["status"] == "error"
    assert results["clinical"]["error_type"] == "contract_error"
    assert "missing required features" in results["clinical"]["error_message"]
    assert not called  # Model must NOT be called with incomplete vector


# ────────────────────────────────────────────────────────────
# TEST 7: OUTPUT ORGANIZATION & TOP-LEVEL KEYS
# ────────────────────────────────────────────────────────────
def test_output_organization(complete_clinical_values):
    contract2 = {
        "gut": {"status": "not_available", "values": {}},
        "wearable": {"status": "incomplete", "values": {}},
        "clinical": {"status": "complete", "values": complete_clinical_values},
    }

    results = route_and_predict(contract2)

    # Must always have exact domain keys
    assert list(results.keys()) == ["clinical", "wearable", "gut"]


# ────────────────────────────────────────────────────────────
# TEST 8: TYPE AND CATEGORICAL ENCODING
# ────────────────────────────────────────────────────────────
def test_categorical_and_boolean_encoding(complete_clinical_values):
    passed_features = None

    def mock_predict_clinical(feat_dict):
        nonlocal passed_features
        passed_features = feat_dict
        return {"probabilities": {}, "predictions": {}}

    router = ModelRouter(predict_clinical_fn=mock_predict_clinical)

    values = complete_clinical_values.copy()
    values["Gender"] = {"canonical_value": "Female"}
    values["Family_History_Diabetes"] = {"canonical_value": True}
    values["Family_History_Hypertension"] = {"canonical_value": "No"}
    values["Family_History_CVD"] = {"canonical_value": 0}

    contract2 = {
        "clinical": {"status": "complete", "values": values},
        "wearable": {"status": "not_available", "values": {}},
        "gut": {"status": "not_available", "values": {}},
    }

    results = router.route(contract2)

    assert results["clinical"]["status"] == "success"
    assert passed_features["Gender"] == 0.0
    assert passed_features["Family_History_Diabetes"] == 1.0
    assert passed_features["Family_History_Hypertension"] == 0.0
    assert passed_features["Family_History_CVD"] == 0.0
