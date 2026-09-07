"""
create_freeze_manifest.py — Computes SHA-256 hashes for all 15 Level-0 XGBoost models and 2 Level-1 stackers
"""

import os
import json
import hashlib
import sys
import numpy as np
import pandas as pd
import sklearn
import xgboost
import joblib

BASE_DIR = r"c:\Users\HP PC\Desktop\telemedicine platform"
PHASE2_DIR = os.path.join(BASE_DIR, "fusion_phase2")
REPORTS_DIR = os.path.join(PHASE2_DIR, "reports")

def file_sha256(filepath):
    if not os.path.exists(filepath):
        return "FILE_NOT_FOUND"
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

LABEL_COLS = ["Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk", "Metabolic_Syndrome", "NAFLD"]

artifact_hashes = {}

# Level-0 XGBoost hashes
for dir_name, mod_key in [("clinical_model", "clinical"), ("wearable_model", "wearable"), ("gut_model", "gut")]:
    for lbl in LABEL_COLS:
        p = os.path.join(BASE_DIR, dir_name, "models", mod_key, f"xgboost_{lbl}.json")
        artifact_hashes[f"{mod_key}_xgboost_{lbl}"] = file_sha256(p)

# Level-1 Stacker hashes
metsyn_stacker_path = os.path.join(PHASE2_DIR, "models", "fusion_candidates", "stacker_Metabolic_Syndrome_Clinical+Gut.joblib")
nafld_stacker_path = os.path.join(PHASE2_DIR, "models", "fusion_candidates", "stacker_NAFLD_Clinical+Gut.joblib")

artifact_hashes["metsyn_stacker_joblib"] = file_sha256(metsyn_stacker_path)
artifact_hashes["nafld_stacker_joblib"] = file_sha256(nafld_stacker_path)

runtime_env = {
    "python_version": sys.version.split()[0],
    "scikit_learn_version": sklearn.__version__,
    "xgboost_version": xgboost.__version__,
    "joblib_version": joblib.__version__,
    "pandas_version": pd.__version__,
    "numpy_version": np.__version__
}

lr_metsyn = joblib.load(metsyn_stacker_path)
lr_nafld = joblib.load(nafld_stacker_path)

metsyn_params = {
    "intercept": float(lr_metsyn.intercept_[0]),
    "coef_clinical": float(lr_metsyn.coef_[0][0]),
    "coef_gut": float(lr_metsyn.coef_[0][1]),
    "platt_intercept": 1.5006,
    "platt_slope": 1.8243,
    "threshold": 0.20
}

nafld_params = {
    "intercept": float(lr_nafld.intercept_[0]),
    "coef_clinical": float(lr_nafld.coef_[0][0]),
    "coef_gut": float(lr_nafld.coef_[0][1]),
    "threshold": 0.50
}

manifest_dict = {
    "manifest_version": "1.0.0",
    "timestamp_utc": pd.Timestamp.now(tz="UTC").isoformat(),
    "architecture_name": "Fusion V1 Frozen Architecture",
    "status": "FROZEN_LOCKED",
    "seed": 42,
    "runtime_environment": runtime_env,
    "artifact_hashes": artifact_hashes,
    "level0_models": {
        "Clinical": {"version": "v4", "features": 18, "passthrough_labels": ["Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk"]},
        "Wearable": {"version": "v3", "features": 15, "status": "Independent Level-0 Modality Only (Excluded from Level-1 Fusion)"},
        "Gut": {"version": "v3", "features": 21, "transform": "CLR (delta=1e-5)", "imputation": "Train-only median"}
    },
    "fusion_heads": {
        "Type2_Diabetes": {"type": "Clinical Passthrough", "threshold": 0.50, "suppression": None},
        "Prediabetes": {"type": "Clinical Passthrough", "threshold": 0.50, "suppression": "IF T2D_pred == 1 THEN Prediabetes_pred = 0"},
        "High_Adiposity_Risk": {"type": "Clinical Passthrough", "threshold": 0.50, "suppression": None},
        "Metabolic_Syndrome": {
            "type": "Clinical + Gut L2 Logistic Regression Stacker",
            "coefficients": metsyn_params,
            "calibration": "Platt Scaling (Slope=1.8243, Intercept=1.5006)",
            "decision_threshold": 0.20,
            "threshold_provenance": "Selected on OOF Train predictions only; evaluated on Validation"
        },
        "NAFLD": {
            "type": "Clinical + Gut L2 Logistic Regression Stacker",
            "coefficients": nafld_params,
            "calibration": None,
            "decision_threshold": 0.50,
            "threshold_provenance": "Default 0.50"
        }
    },
    "test_isolation": "Test data HAS NOT been used for final evaluation in this freeze operation.",
    "future_v2_research": [
        "Real-world missingness patterns",
        "Modality reliability & quality scoring",
        "Modality conflict detection",
        "Uncertainty quantification (UQ)",
        "Decision-curve / clinical-utility analysis",
        "Subgroup & fairness analysis",
        "Longitudinal multimodal modeling",
        "Calibration drift monitoring",
        "Constrained non-negative Wearable experiment",
        "External real-world clinical validation",
        "Future Wearable reintegration if real-world evidence supports it"
    ]
}

os.makedirs(REPORTS_DIR, exist_ok=True)
json_manifest_path = os.path.join(REPORTS_DIR, "fusion_v1_freeze_manifest.json")
with open(json_manifest_path, "w", encoding="utf-8") as f:
    json.dump(manifest_dict, f, indent=2)

print(f"[OK] Immutable JSON Manifest updated at: {json_manifest_path}")

