import os
import json
import math
import numpy as np
import pandas as pd
import xgboost as xgb

LABEL_COLS = [
    "Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk",
    "Metabolic_Syndrome", "NAFLD"
]

FEATURE_RANGES = {
    "Average_Daily_Steps": (0.0, 100000.0),
    "Active_Minutes": (0.0, 1440.0),
    "Sedentary_Time_Minutes": (0.0, 1440.0),
    "Resting_Heart_Rate": (30.0, 220.0),
    "Heart_Rate_Variability_RMSSD": (0.0, 300.0),
    "Sleep_Duration_Hours": (0.0, 24.0),
    "Sleep_Efficiency_Score": (0.0, 100.0),
    "Autonomic_Stress_Score": (0.0, 100.0),
    "Activity_Energy_Expenditure": (0.0, 10000.0),
    "Exercise_Frequency_Days": (0.0, 7.0),
    "CGM_Average_Glucose": (40.0, 500.0),
    "CGM_Glucose_CV": (0.0, 150.0),
    "CGM_Time_In_Range": (0.0, 100.0),
    "CGM_Time_Above_Range": (0.0, 100.0),
    "CGM_Time_Below_Range": (0.0, 100.0)
}

# Module-level model cache to avoid re-loading on every invocation
_MODELS_CACHE = {}
_METADATA_CACHE = {}

def _load_wearable_models():
    global _MODELS_CACHE, _METADATA_CACHE
    if _MODELS_CACHE and _METADATA_CACHE:
        return _MODELS_CACHE, _METADATA_CACHE

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    models_dir = os.path.join(base_dir, "models", "wearable")

    for label in LABEL_COLS:
        model_path = os.path.join(models_dir, f"xgboost_{label}.json")
        meta_path = os.path.join(models_dir, f"xgboost_{label}_metadata.json")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file missing for '{label}': {model_path}")
        if not os.path.exists(meta_path):
            raise FileNotFoundError(f"Metadata file missing for '{label}': {meta_path}")

        model = xgb.XGBClassifier()
        model.load_model(model_path)

        with open(meta_path, "r") as f:
            meta = json.load(f)

        _MODELS_CACHE[label] = model
        _METADATA_CACHE[label] = meta

    return _MODELS_CACHE, _METADATA_CACHE

def validate_wearable_features(features: dict, expected_features: list):
    if not isinstance(features, dict):
        raise TypeError(f"Input features must be a dictionary, got {type(features)}")

    # 1. Missing fields check
    missing = set(expected_features) - set(features.keys())
    if missing:
        raise ValueError(f"Missing required wearable feature(s): {sorted(list(missing))}")

    # 2. Extra unexpected fields check
    extra = set(features.keys()) - set(expected_features)
    if extra:
        raise ValueError(f"Unexpected extra feature(s) provided: {sorted(list(extra))}")

    # 3. Datatype and NaN checks, Range validation
    for col in expected_features:
        val = features[col]
        if val is None or (isinstance(val, float) and math.isnan(val)):
            raise ValueError(f"Feature '{col}' cannot be None or NaN")

        if not isinstance(val, (int, float, np.integer, np.floating)):
            raise TypeError(f"Feature '{col}' must be numeric (int/float), got {type(val).__name__}")

        min_val, max_val = FEATURE_RANGES[col]
        if not (min_val <= float(val) <= max_val):
            raise ValueError(
                f"Feature '{col}' value {val} is outside valid plausible range [{min_val}, {max_val}]"
            )

def predict_wearable(features: dict) -> dict:
    """
    Predicts metabolic disease risk for a single patient across 5 independent labels using wearable features.

    Parameters:
        features (dict): Dictionary of 15 wearable feature key-value pairs.

    Returns:
        dict: {
            "probabilities": {label: raw_float, ...},
            "predictions": {label: 0/1, ...},
            "threshold_used": 0.5,
            "suppressed_labels": [label_names]
        }
    """
    models, metadata = _load_wearable_models()

    # Reference feature order from metadata of first model
    reference_features = metadata[LABEL_COLS[0]]["features"]

    # Validate input dictionary strictly
    validate_wearable_features(features, reference_features)

    # Verify all 5 models agree on expected feature order
    for label in LABEL_COLS:
        if metadata[label]["features"] != reference_features:
            raise ValueError(f"Feature order mismatch in metadata for label '{label}'")

    # Construct DataFrame with explicit column order matching metadata
    feature_values = [float(features[col]) for col in reference_features]
    df_input = pd.DataFrame([feature_values], columns=reference_features)

    raw_probabilities = {}
    raw_predictions = {}
    threshold = 0.5

    # Make 5 independent predictions
    for label in LABEL_COLS:
        model = models[label]
        prob = float(model.predict_proba(df_input)[0, 1])
        raw_probabilities[label] = prob
        raw_predictions[label] = 1 if prob >= threshold else 0

    # Apply Mutual Exclusivity Suppression Rule on predictions
    suppressed_labels = []
    final_predictions = raw_predictions.copy()

    if final_predictions["Type2_Diabetes"] == 1:
        if final_predictions["Prediabetes"] == 1:
            suppressed_labels.append("Prediabetes")
        final_predictions["Prediabetes"] = 0

    return {
        "probabilities": raw_probabilities,
        "predictions": final_predictions,
        "threshold_used": threshold,
        "suppressed_labels": suppressed_labels
    }
