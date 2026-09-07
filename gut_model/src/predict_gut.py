"""
predict_gut.py — Gut Microbiome Model Inference (v3)

Inference interface for the 5-label metabolic disease prediction model
trained on CLR-transformed gut microbiome taxa.

Validation rules (all enforced strictly — NO silent fixes):
  - All 21 required raw taxa fields must be present
  - No unexpected/extra fields
  - No NaN, None, or infinite values
  - No negative values
  - Sum of all 21 fields must be within 95.0–105.0 (catches wrong units)

Preprocessing at inference:
  - CLR transform is applied (delta=1e-5) — stateless, no training-time fitting needed
  - Median imputation is NOT applied — inputs with missing values are REJECTED
  - Stored imputation_medians in metadata JSON are for audit/reproducibility only

Suppression rule:
  - If Type2_Diabetes prediction == 1, Prediabetes prediction is forced to 0
  - Raw probabilities are NEVER modified
"""

import os
import json
import math
import numpy as np
import pandas as pd
import xgboost as xgb

# ─────────────────────────────────────────────
# Constants — must match training exactly
# ─────────────────────────────────────────────

LABEL_COLS = [
    "Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk",
    "Metabolic_Syndrome", "NAFLD",
]

RAW_TAXA_COLS = [
    "Akkermansia", "Faecalibacterium", "Roseburia", "Bifidobacterium",
    "Bacteroides", "Prevotella", "Ruminococcus", "Blautia", "Collinsella",
    "Escherichia_Shigella", "Coprococcus", "Alistipes", "Subdoligranulum",
    "Enterococcus", "Eubacterium", "Parabacteroides", "Lactobacillus",
    "Klebsiella", "Streptococcus", "Eggerthella", "Other_Taxa",
]

CLR_FEATURE_COLS = [t + "_CLR" for t in RAW_TAXA_COLS]  # 21 CLR names (must match training)
CLR_DELTA = 1e-5

# Inference sum-to-100 tolerance (catches proportions vs percentages vs raw counts)
SUM_MIN = 95.0
SUM_MAX = 105.0

THRESHOLD = 0.5

# ─────────────────────────────────────────────
# Module-level model cache (load once)
# ─────────────────────────────────────────────
_MODELS_CACHE = {}
_METADATA_CACHE = {}


def _get_models_dir():
    """Resolve models/gut/ directory relative to this script's location."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "models", "gut")


def _load_gut_models():
    """Load all 5 XGBoost models and their metadata JSONs into module-level cache."""
    global _MODELS_CACHE, _METADATA_CACHE

    if _MODELS_CACHE and _METADATA_CACHE:
        return _MODELS_CACHE, _METADATA_CACHE

    models_dir = _get_models_dir()

    for label in LABEL_COLS:
        model_path = os.path.join(models_dir, f"xgboost_{label}.json")
        meta_path = os.path.join(models_dir, f"xgboost_{label}_metadata.json")

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model file missing for label '{label}': {model_path}. "
                f"Run train_gut.py first."
            )
        if not os.path.exists(meta_path):
            raise FileNotFoundError(
                f"Metadata file missing for label '{label}': {meta_path}. "
                f"Run train_gut.py first."
            )

        model = xgb.XGBClassifier()
        model.load_model(model_path)

        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        _MODELS_CACHE[label] = model
        _METADATA_CACHE[label] = meta

    return _MODELS_CACHE, _METADATA_CACHE


def validate_gut_features(features: dict):
    """
    Strictly validate input features. Raises ValueError/TypeError on any violation.
    Does NOT silently fix or impute any values.

    Checks:
      1. Input is a dict
      2. All 21 required taxa fields are present (no missing)
      3. No unexpected/extra fields
      4. All values are numeric (int/float) — no None, NaN, or infinite
      5. No negative values
      6. Sum of all 21 fields is within 95.0–105.0
    """
    if not isinstance(features, dict):
        raise TypeError(
            f"Input must be a dictionary, got {type(features).__name__}. "
            f"Expected dict with 21 raw taxa relative abundance values."
        )

    # Check 1: Missing required fields
    missing = [col for col in RAW_TAXA_COLS if col not in features]
    if missing:
        raise ValueError(
            f"Missing required taxa field(s): {missing}. "
            f"All 21 raw taxa fields are required. "
            f"Note: median imputation is NOT applied at inference — "
            f"inputs with missing values must be rejected by the caller."
        )

    # Check 2: Unexpected/extra fields
    extra = [k for k in features if k not in RAW_TAXA_COLS]
    if extra:
        raise ValueError(
            f"Unexpected extra field(s): {extra}. "
            f"Only the 21 required taxa fields are accepted. "
            f"Do not pass Patient_ID or any non-taxa field."
        )

    # Check 3: Datatype, NaN, infinite
    for col in RAW_TAXA_COLS:
        val = features[col]

        # None check
        if val is None:
            raise ValueError(
                f"Field '{col}' is None. All taxa values must be numeric. "
                f"Input validation does not impute missing values."
            )

        # Type check: must be numeric
        if not isinstance(val, (int, float, np.integer, np.floating)):
            raise TypeError(
                f"Field '{col}' has type {type(val).__name__}, expected int or float."
            )

        # NaN check (catches float('nan'))
        if math.isnan(float(val)):
            raise ValueError(
                f"Field '{col}' is NaN. Inputs with NaN values are rejected "
                f"(imputation is not applied at inference)."
            )

        # Infinite check
        if math.isinf(float(val)):
            raise ValueError(
                f"Field '{col}' is infinite ({val}). All taxa values must be finite."
            )

    # Check 4: No negative values
    negative_cols = [col for col in RAW_TAXA_COLS if float(features[col]) < 0.0]
    if negative_cols:
        raise ValueError(
            f"Negative value(s) detected in taxa field(s): "
            f"{[(col, features[col]) for col in negative_cols]}. "
            f"Relative abundances must be non-negative."
        )

    # Check 5: Sum-to-100 check (catches wrong units)
    total = sum(float(features[col]) for col in RAW_TAXA_COLS)
    if not (SUM_MIN <= total <= SUM_MAX):
        raise ValueError(
            f"Sum of all 21 taxa values is {total:.4f}, which is outside the "
            f"expected range [{SUM_MIN}, {SUM_MAX}]. "
            f"Values must be relative abundances as percentages (summing to ~100%). "
            f"Possible wrong units: proportions (0–1 range) or raw counts were provided."
        )


def apply_clr_single_row(taxa_values: list) -> list:
    """
    Apply CLR transformation to a single row of 21 taxa values.
    CLR(x_i) = log(x_i + delta) - mean(log(x_j + delta) for j in 1..21)
    This is stateless — no training-time parameters needed.

    Args:
        taxa_values: list of 21 float values in RAW_TAXA_COLS order

    Returns:
        list of 21 CLR-transformed values in CLR_FEATURE_COLS order
    """
    arr = np.array(taxa_values, dtype=np.float64)
    arr_delta = arr + CLR_DELTA
    log_arr = np.log(arr_delta)
    log_mean = log_arr.mean()
    clr_arr = log_arr - log_mean

    if not np.all(np.isfinite(clr_arr)):
        raise ValueError(
            f"CLR transformation produced non-finite values. "
            f"This should not happen after validation — check input values."
        )

    return clr_arr.tolist()


def predict_gut(features: dict) -> dict:
    """
    Predict metabolic disease risk from gut microbiome taxa relative abundances.

    Args:
        features (dict): Dictionary with exactly 21 raw taxa relative abundance
                         values (as percentages summing to ~100%). Keys must match
                         RAW_TAXA_COLS exactly. Patient_ID must NOT be included.

    Returns:
        dict: {
            "probabilities": {"Type2_Diabetes": float, "Prediabetes": float,
                              "High_Adiposity_Risk": float, "Metabolic_Syndrome": float,
                              "NAFLD": float},
            "predictions":   {"Type2_Diabetes": int, "Prediabetes": int,
                              "High_Adiposity_Risk": int, "Metabolic_Syndrome": int,
                              "NAFLD": int},
            "threshold_used": 0.5,
            "suppressed_labels": [list of label names suppressed by the mutual exclusivity rule]
        }

    Raises:
        TypeError: if input is not a dict or any value has wrong type
        ValueError: if any validation rule is violated (missing field, NaN, negative, wrong sum, etc.)
        FileNotFoundError: if trained model files are missing
    """
    # Load models (cached after first call)
    models, metadata = _load_gut_models()

    # Validate input strictly — no silent fixes
    validate_gut_features(features)

    # Verify feature order from metadata agrees with our constants
    reference_features = metadata[LABEL_COLS[0]]["features"]
    if reference_features != CLR_FEATURE_COLS:
        raise ValueError(
            f"Feature order mismatch: metadata expects {reference_features}, "
            f"but inference code expects {CLR_FEATURE_COLS}. "
            f"Retrain the model or update CLR_FEATURE_COLS."
        )

    # Apply CLR transformation — stateless, no medians needed at inference
    taxa_values_ordered = [float(features[col]) for col in RAW_TAXA_COLS]
    clr_values = apply_clr_single_row(taxa_values_ordered)

    # Build DataFrame in correct feature order for model
    df_input = pd.DataFrame([clr_values], columns=CLR_FEATURE_COLS)

    # Verify feature order matches each model's metadata
    for label in LABEL_COLS:
        model_features = metadata[label]["features"]
        if model_features != CLR_FEATURE_COLS:
            raise ValueError(
                f"Feature order mismatch in metadata for label '{label}'. "
                f"Expected: {CLR_FEATURE_COLS}. Got: {model_features}."
            )

    # Generate raw probabilities from all 5 independent models
    raw_probabilities = {}
    raw_predictions = {}

    for label in LABEL_COLS:
        model = models[label]
        prob = float(model.predict_proba(df_input)[0, 1])
        raw_probabilities[label] = prob
        raw_predictions[label] = 1 if prob >= THRESHOLD else 0

    # Apply mutual exclusivity suppression rule (labels only — probs untouched)
    suppressed_labels = []
    final_predictions = dict(raw_predictions)  # copy

    if final_predictions["Type2_Diabetes"] == 1:
        if final_predictions["Prediabetes"] == 1:
            suppressed_labels.append("Prediabetes")
        final_predictions["Prediabetes"] = 0

    return {
        "probabilities": raw_probabilities,
        "predictions": final_predictions,
        "threshold_used": THRESHOLD,
        "suppressed_labels": suppressed_labels,
    }


# ─────────────────────────────────────────────
# CLI demo / smoke test
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("predict_gut.py — Gut Microbiome Model Inference (v3)")
    print("Running quick smoke test with example input...\n")

    # Example patient with healthy microbiome profile (values sum to 100.0)
    example_features = {
        "Akkermansia": 3.5,
        "Faecalibacterium": 10.0,
        "Roseburia": 5.0,
        "Bifidobacterium": 6.0,
        "Bacteroides": 20.0,
        "Prevotella": 5.0,
        "Ruminococcus": 4.0,
        "Blautia": 7.5,
        "Collinsella": 2.0,
        "Escherichia_Shigella": 1.0,
        "Coprococcus": 3.0,
        "Alistipes": 3.5,
        "Subdoligranulum": 2.5,
        "Enterococcus": 0.8,
        "Eubacterium": 4.5,
        "Parabacteroides": 3.2,
        "Lactobacillus": 5.5,
        "Klebsiella": 0.5,
        "Streptococcus": 1.5,
        "Eggerthella": 0.5,
        "Other_Taxa": 10.5,
    }

    total = sum(example_features.values())
    print(f"  Input taxa sum: {total:.2f} (should be ~100)")

    try:
        result = predict_gut(example_features)
        print("\nPrediction result:")
        print(f"  Probabilities:    {result['probabilities']}")
        print(f"  Predictions:      {result['predictions']}")
        print(f"  Threshold:        {result['threshold_used']}")
        print(f"  Suppressed labels: {result['suppressed_labels']}")
    except FileNotFoundError as e:
        print(f"\n[Not yet trained] {e}")
        print("Run train_gut.py first to generate model artifacts.")
    except Exception as e:
        print(f"\n[Error] {type(e).__name__}: {e}")
