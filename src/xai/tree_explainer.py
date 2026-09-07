"""
tree_explainer.py — TreeSHAP Explanation Engine for Level-0 XGBoost Models

Computes exact local TreeSHAP feature contributions for a single patient vector
against the authoritative Level-0 XGBoost models (Clinical, Wearable, Gut).
Caches shap.TreeExplainer instances in memory for sub-millisecond live evaluation.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
import shap

from .feature_formatter import get_feature_meta, format_feature_value

logger = logging.getLogger("XAI.TreeExplainer")

# In-memory explainer instance cache: key = f"{domain}:{disease}"
_EXPLAINER_CACHE: Dict[str, shap.TreeExplainer] = {}


def _get_or_create_explainer(domain: str, disease: str, model_obj: Any) -> shap.TreeExplainer:
    """Retrieve cached shap.TreeExplainer or create and cache a new instance."""
    cache_key = f"{domain}:{disease}"
    if cache_key in _EXPLAINER_CACHE:
        return _EXPLAINER_CACHE[cache_key]

    try:
        explainer = shap.TreeExplainer(model_obj)
        _EXPLAINER_CACHE[cache_key] = explainer
        return explainer
    except Exception as exc:
        logger.error(f"Failed to create TreeExplainer for {cache_key}: {exc}")
        raise


def explain_domain_disease(
    domain: str,
    disease: str,
    feature_dict: Dict[str, float],
    top_n_risk: int = 4,
    top_n_protective: int = 2,
) -> Dict[str, Any]:
    """
    Computes exact TreeSHAP local feature attribution for a single patient vector.

    Parameters:
        domain: "clinical" | "wearable" | "gut"
        disease: "Type2_Diabetes" | "Prediabetes" | "High_Adiposity_Risk" |
                 "Metabolic_Syndrome" | "NAFLD"
        feature_dict: Raw numeric feature dictionary passed to model
        top_n_risk: Max number of positive risk-increasing features to return (default 4)
        top_n_protective: Max number of negative/protective features to return (default 2)

    Returns:
        Structured dict containing risk_drivers, protective_factors, and all_features.
    """
    if domain == "clinical":
        from clinical_model.src.predict_clinical import _load_clinical_models
        models, metadata = _load_clinical_models()
        feature_order = metadata[disease]["features"]
        model = models[disease]
        
        # Prepare 1-row DataFrame matching training column order
        values = [float(feature_dict[col]) for col in feature_order]
        df_input = pd.DataFrame([values], columns=feature_order)
        raw_feature_map = feature_dict

    elif domain == "wearable":
        from wearable_model.src.predict_wearable import _load_wearable_models
        models, metadata = _load_wearable_models()
        feature_order = metadata[disease]["features"]
        model = models[disease]
        
        values = [float(feature_dict[col]) for col in feature_order]
        df_input = pd.DataFrame([values], columns=feature_order)
        raw_feature_map = feature_dict

    elif domain == "gut":
        from gut_model.src.predict_gut import _load_gut_models, apply_clr_single_row, RAW_TAXA_COLS, CLR_FEATURE_COLS
        models, metadata = _load_gut_models()
        feature_order = CLR_FEATURE_COLS  # 21 CLR names
        model = models[disease]
        
        # If feature_dict contains raw taxa, apply CLR transform
        if any(col in feature_dict for col in RAW_TAXA_COLS):
            raw_values = [float(feature_dict[col]) for col in RAW_TAXA_COLS]
            clr_values = apply_clr_single_row(raw_values)
            df_input = pd.DataFrame([clr_values], columns=feature_order)
            raw_feature_map = {k: feature_dict.get(k) for k in RAW_TAXA_COLS}
        else:
            # Already CLR transformed
            clr_values = [float(feature_dict[col]) for col in feature_order]
            df_input = pd.DataFrame([clr_values], columns=feature_order)
            raw_feature_map = feature_dict
    else:
        raise ValueError(f"Unknown domain '{domain}' for XAI explanation")

    # Run TreeSHAP
    explainer = _get_or_create_explainer(domain, disease, model)
    shap_res = explainer(df_input)

    # Extract 1D array of SHAP values for the single patient
    if hasattr(shap_res, "values"):
        vals_arr = shap_res.values
    else:
        vals_arr = shap_res

    if len(vals_arr.shape) == 3:
        # Multi-class output [n_samples, n_features, n_classes] -> take positive class (index 1)
        shap_vector = vals_arr[0, :, 1]
    elif len(vals_arr.shape) == 2:
        shap_vector = vals_arr[0, :]
    else:
        shap_vector = np.array(vals_arr).flatten()

    # Base value (expected value)
    base_val = getattr(shap_res, "base_values", 0.0)
    if isinstance(base_val, np.ndarray):
        if base_val.ndim > 1:
            base_val = float(base_val[0, 1]) if base_val.shape[-1] > 1 else float(base_val[0, 0])
        elif len(base_val) > 0:
            base_val = float(base_val[0])
    base_val = float(base_val) if isinstance(base_val, (int, float, np.floating)) else 0.0

    # Assemble structured feature impacts
    feature_entries: List[Dict[str, Any]] = []
    max_abs_shap = 1e-6

    for idx, feat_name in enumerate(feature_order):
        s_val = float(shap_vector[idx])
        abs_s_val = abs(s_val)
        if abs_s_val > max_abs_shap:
            max_abs_shap = abs_s_val

        # Get original raw/formatted value
        meta = get_feature_meta(domain, feat_name)
        base_name = feat_name.replace("_CLR", "")
        raw_val = raw_feature_map.get(base_name, feature_dict.get(feat_name))
        formatted_val = format_feature_value(domain, base_name, raw_val)

        direction = "increases_risk" if s_val > 1e-5 else ("reduces_risk" if s_val < -1e-5 else "neutral")

        entry = {
            "feature_key": base_name,
            "display_name": meta.get("label", base_name),
            "scientific_name": meta.get("scientific_name"),
            "role_description": meta.get("role") or meta.get("description", ""),
            "raw_value": raw_val,
            "formatted_value": formatted_val,
            "shap_value": round(s_val, 4),
            "abs_shap_value": round(abs_s_val, 4),
            "direction": direction,
            "normal_range": meta.get("normal_range", ""),
        }
        feature_entries.append(entry)

    # Calculate relative bar percentages (0 to 100) based on max_abs_shap in this prediction
    for item in feature_entries:
        rel_pct = int(round((item["abs_shap_value"] / max_abs_shap) * 100))
        item["relative_impact_percentage"] = min(100, max(5, rel_pct))

    # Partition into positive risk drivers (descending) and protective factors (ascending/most negative)
    positive_drivers = sorted(
        [f for f in feature_entries if f["direction"] == "increases_risk"],
        key=lambda x: x["shap_value"],
        reverse=True,
    )
    protective_factors = sorted(
        [f for f in feature_entries if f["direction"] == "reduces_risk"],
        key=lambda x: x["shap_value"],
        reverse=False,
    )

    top_risk_drivers = positive_drivers[:top_n_risk]
    top_protective = protective_factors[:top_n_protective]

    return {
        "domain": domain,
        "disease": disease,
        "base_value": round(base_val, 4),
        "risk_drivers": top_risk_drivers,
        "protective_factors": top_protective,
        "all_features": feature_entries,
    }
