"""
verify_coefficient_consistency.py — Performs exact side-by-side float comparison across all V1 artifacts
"""

import os
import json
import joblib
import numpy as np

BASE_DIR = r"c:\Users\HP PC\Desktop\telemedicine platform"
PHASE2_DIR = os.path.join(BASE_DIR, "fusion_phase2")
REPORTS_DIR = os.path.join(PHASE2_DIR, "reports")

# 1. Load joblib models
metsyn_joblib = joblib.load(os.path.join(PHASE2_DIR, "models", "fusion_candidates", "stacker_Metabolic_Syndrome_Clinical+Gut.joblib"))
nafld_joblib = joblib.load(os.path.join(PHASE2_DIR, "models", "fusion_candidates", "stacker_NAFLD_Clinical+Gut.joblib"))

# 2. Load JSON manifest
with open(os.path.join(REPORTS_DIR, "fusion_v1_freeze_manifest.json")) as f:
    json_manifest = json.load(f)

# Extract raw floats from joblib
metsyn_joblib_raw = {
    "intercept": float(metsyn_joblib.intercept_[0]),
    "coef_clinical": float(metsyn_joblib.coef_[0][0]),
    "coef_gut": float(metsyn_joblib.coef_[0][1])
}

nafld_joblib_raw = {
    "intercept": float(nafld_joblib.intercept_[0]),
    "coef_clinical": float(nafld_joblib.coef_[0][0]),
    "coef_gut": float(nafld_joblib.coef_[0][1])
}

# Values from approved prompt specification
metsyn_spec = {
    "intercept": -4.3697,
    "coef_clinical": 2.5799,
    "coef_gut": 1.9639,
    "platt_intercept": 1.5006,
    "platt_slope": 1.8243,
    "threshold": 0.20
}

nafld_spec = {
    "intercept": -4.7674,
    "coef_clinical": 3.7924,
    "coef_gut": 2.8340,
    "threshold": 0.50
}

print("=== METSYN COEFFICIENT COMPARISON ===")
print("Approved Spec:      ", metsyn_spec)
print("Joblib Raw Floats:  ", metsyn_joblib_raw)
print("JSON Manifest:      ", json_manifest["fusion_heads"]["Metabolic_Syndrome"]["coefficients"])
print("Diff vs Spec (Intercept):", abs(metsyn_joblib_raw["intercept"] - metsyn_spec["intercept"]))
print("Diff vs Spec (Clin):     ", abs(metsyn_joblib_raw["coef_clinical"] - metsyn_spec["coef_clinical"]))
print("Diff vs Spec (Gut):      ", abs(metsyn_joblib_raw["coef_gut"] - metsyn_spec["coef_gut"]))

print("\n=== NAFLD COEFFICIENT COMPARISON ===")
print("Approved Spec:      ", nafld_spec)
print("Joblib Raw Floats:  ", nafld_joblib_raw)
print("JSON Manifest:      ", json_manifest["fusion_heads"]["NAFLD"]["coefficients"])
print("Diff vs Spec (Intercept):", abs(nafld_joblib_raw["intercept"] - nafld_spec["intercept"]))
print("Diff vs Spec (Clin):     ", abs(nafld_joblib_raw["coef_clinical"] - nafld_spec["coef_clinical"]))
print("Diff vs Spec (Gut):      ", abs(nafld_joblib_raw["coef_gut"] - nafld_spec["coef_gut"]))

# Check if differences are within 4-decimal rounding (0.0001)
metsyn_rounding_ok = (
    round(metsyn_joblib_raw["intercept"], 4) == metsyn_spec["intercept"] and
    round(metsyn_joblib_raw["coef_clinical"], 4) == metsyn_spec["coef_clinical"] and
    round(metsyn_joblib_raw["coef_gut"], 4) == metsyn_spec["coef_gut"]
)

nafld_rounding_ok = (
    round(nafld_joblib_raw["intercept"], 4) == nafld_spec["intercept"] and
    round(nafld_joblib_raw["coef_clinical"], 4) == nafld_spec["coef_clinical"] and
    round(nafld_joblib_raw["coef_gut"], 4) == nafld_spec["coef_gut"]
)

print(f"\nMetSyn Exact 4-Decimal Rounding Match: {metsyn_rounding_ok}")
print(f"NAFLD Exact 4-Decimal Rounding Match: {nafld_rounding_ok}")

