"""
patient_context_builder.py — Structured Patient Explanation Context Layer

Transforms raw patient inputs, model predictions, and XAI feature attributions
into a clinically governed explanation context.

Features:
- Associates exact patient values with approved reference ranges and units.
- Evaluates clinical status:
    'above_expected_range' | 'below_expected_range' | 'within_expected_range' | 'interpretation_unavailable'
- Classifies attribution contribution ('major', 'moderate', 'protective').
- Prohibits inventing clinical normal ranges if governed reference data is absent.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional
from ..xai.feature_formatter import (
    CLINICAL_FEATURE_META,
    WEARABLE_FEATURE_META,
    GUT_TAXA_META,
)

# Governed numerical boundaries for standard clinical & wearable parameters
GOVERNED_REFERENCE_RANGES: Dict[str, Dict[str, Any]] = {
    # Clinical Biomarkers
    "Fasting_Blood_Glucose": {
        "unit": "mg/dL",
        "normal_min": 70.0,
        "normal_max": 99.0,
        "description": "70–99 mg/dL (Normal fasting glycemic range)",
        "high_label": "above the expected fasting range",
        "low_label": "below the expected fasting range",
        "normal_label": "within the expected fasting range"
    },
    "HbA1c": {
        "unit": "%",
        "normal_min": 4.0,
        "normal_max": 5.6,
        "description": "< 5.7% (Normal glycated hemoglobin)",
        "high_label": "above the expected range (indicates elevated 2–3 month blood sugar)",
        "low_label": "below the standard reference range",
        "normal_label": "within the expected healthy range"
    },
    "BMI": {
        "unit": "kg/m²",
        "normal_min": 18.5,
        "normal_max": 24.9,
        "description": "18.5–24.9 kg/m² (Standard healthy weight range)",
        "high_label": "above the standard healthy weight range",
        "low_label": "below the standard healthy weight range",
        "normal_label": "within the standard healthy weight range"
    },
    "Waist_Circumference": {
        "unit": "cm",
        "normal_min": 50.0,
        "normal_max": 94.0,  # General baseline; refined by sex if present
        "description": "< 94 cm for men, < 80 cm for women",
        "high_label": "above the recommended abdominal circumference target",
        "low_label": "within lean range",
        "normal_label": "within recommended abdominal target"
    },
    "Systolic_BP": {
        "unit": "mmHg",
        "normal_min": 90.0,
        "normal_max": 120.0,
        "description": "< 120 mmHg (Normal resting systolic blood pressure)",
        "high_label": "above the standard resting blood pressure target",
        "low_label": "below standard resting blood pressure",
        "normal_label": "within the standard resting target"
    },
    "Diastolic_BP": {
        "unit": "mmHg",
        "normal_min": 60.0,
        "normal_max": 80.0,
        "description": "< 80 mmHg (Normal resting diastolic blood pressure)",
        "high_label": "above the standard resting diastolic target",
        "low_label": "below standard resting diastolic level",
        "normal_label": "within the standard resting target"
    },
    "Triglycerides": {
        "unit": "mg/dL",
        "normal_min": 0.0,
        "normal_max": 149.0,
        "description": "< 150 mg/dL (Normal fasting lipid concentration)",
        "high_label": "above the recommended fasting lipid target",
        "low_label": "within optimal range",
        "normal_label": "within the recommended lipid target"
    },
    "HDL": {
        "unit": "mg/dL",
        "normal_min": 40.0,
        "normal_max": 100.0,
        "description": "> 40 mg/dL for men, > 50 mg/dL for women",
        "high_label": "optimal protective level",
        "low_label": "lower than the protective cardiovascular target",
        "normal_label": "within protective target range"
    },
    "LDL": {
        "unit": "mg/dL",
        "normal_min": 0.0,
        "normal_max": 99.0,
        "description": "< 100 mg/dL (Optimal LDL cholesterol target)",
        "high_label": "above the optimal cholesterol target",
        "low_label": "within optimal target",
        "normal_label": "within optimal target"
    },
    "ALT": {
        "unit": "U/L",
        "normal_min": 7.0,
        "normal_max": 56.0,
        "description": "7–56 U/L (Standard hepatic enzyme range)",
        "high_label": "above the standard liver enzyme reference range",
        "low_label": "within reference range",
        "normal_label": "within the standard reference range"
    },
    "AST": {
        "unit": "U/L",
        "normal_min": 10.0,
        "normal_max": 40.0,
        "description": "10–40 U/L (Standard liver enzyme range)",
        "high_label": "above the standard liver enzyme range",
        "low_label": "within standard range",
        "normal_label": "within the standard reference range"
    },

    # Wearable Lifestyle Metrics
    "Daily_Steps": {
        "unit": "steps/day",
        "normal_min": 7500.0,
        "normal_max": 25000.0,
        "description": ">= 7,500–10,000 steps/day (Active lifestyle baseline)",
        "high_label": "active daily movement level",
        "low_label": "lower than general daily activity guidelines",
        "normal_label": "meeting active daily movement targets"
    },
    "Sedentary_Minutes": {
        "unit": "min/day",
        "normal_min": 0.0,
        "normal_max": 480.0,
        "description": "< 480 min/day (<= 8 hours sedentary sitting time)",
        "high_label": "higher than recommended daily sedentary time",
        "low_label": "low sedentary time",
        "normal_label": "within acceptable sedentary limits"
    },
    "Moderate_Activity_Minutes": {
        "unit": "min/week",
        "normal_min": 150.0,
        "normal_max": 600.0,
        "description": ">= 150–300 minutes/week (WHO Physical Activity Target)",
        "high_label": "meeting or exceeding weekly aerobic targets",
        "low_label": "lower than the recommended weekly 150-minute aerobic target",
        "normal_label": "meeting the recommended weekly aerobic target"
    },
    "Sleep_Duration": {
        "unit": "hours/night",
        "normal_min": 7.0,
        "normal_max": 9.0,
        "description": "7–9 hours/night (Recommended adult sleep range)",
        "high_label": "above standard sleep duration",
        "low_label": "shorter than the recommended 7–9 hours of restorative sleep",
        "normal_label": "within the recommended 7–9 hour restorative range"
    }
}


class PatientContextBuilder:
    """Constructs governed, patient-friendly explanation contexts."""

    @staticmethod
    def build_context(
        patient_features: Dict[str, Any],
        xai_explanations: Dict[str, Any],
        disease_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Assembles the complete patient explanation context.

        Parameters
        ----------
        patient_features : dict
            Merged raw/mapped clinical, wearable, and gut feature values.
        xai_explanations : dict
            Local feature attributions ('explanations' dictionary from XAIEngine).
        disease_results : list[dict]
            Output list of disease predictions and risk levels.

        Returns
        -------
        dict
            Structured patient explanation context.
        """
        contributing_factors = []
        protective_factors = []

        # Find the highest-risk or primary disease context
        positive_diseases = [d for d in disease_results if d.get("prediction") == 1]
        primary_disease = positive_diseases[0]["disease"] if positive_diseases else (
            disease_results[0]["disease"] if disease_results else "Type2_Diabetes"
        )

        # Process XAI drivers across all evaluated diseases
        processed_features = set()

        for d_obj in disease_results:
            d_name = d_obj["disease"]
            d_expl = xai_explanations.get(d_name, {})

            # 1. Process Risk Drivers (Positive SHAP attributions)
            for driver in d_expl.get("risk_drivers", []):
                feat_name = driver.get("feature_name") or driver.get("feature_key") or ""
                if not feat_name or feat_name in processed_features:
                    continue
                processed_features.add(feat_name)

                raw_val = driver.get("actual_value")
                if raw_val is None:
                    raw_val = driver.get("raw_value", patient_features.get(feat_name))

                imp_score = driver.get("importance")
                if imp_score is None:
                    imp_score = driver.get("abs_shap_value", driver.get("shap_value", 0.0))

                entry = PatientContextBuilder._build_feature_entry(
                    feature_name=feat_name,
                    raw_val=raw_val,
                    contribution_role="risk_driver",
                    importance_score=float(imp_score or 0.0),
                    contributes_to=[d_name]
                )
                contributing_factors.append(entry)

            # 2. Process Protective Factors (Negative SHAP attributions)
            for factor in d_expl.get("protective_factors", []):
                feat_name = factor.get("feature_name") or factor.get("feature_key") or ""
                if not feat_name or feat_name in processed_features:
                    continue
                processed_features.add(feat_name)

                raw_val = factor.get("actual_value")
                if raw_val is None:
                    raw_val = factor.get("raw_value", patient_features.get(feat_name))

                imp_score = factor.get("importance")
                if imp_score is None:
                    imp_score = factor.get("abs_shap_value", factor.get("shap_value", 0.0))

                entry = PatientContextBuilder._build_feature_entry(
                    feature_name=feat_name,
                    raw_val=raw_val,
                    contribution_role="protective_factor",
                    importance_score=float(imp_score or 0.0),
                    contributes_to=[d_name]
                )
                protective_factors.append(entry)

        # Sort factors by importance descending
        contributing_factors.sort(key=lambda x: x.get("importance_score", 0.0), reverse=True)
        protective_factors.sort(key=lambda x: x.get("importance_score", 0.0), reverse=True)

        return {
            "primary_disease": primary_disease,
            "disease_results": disease_results,
            "contributing_factors": contributing_factors,
            "protective_factors": protective_factors,
            "raw_patient_features": patient_features
        }

    @staticmethod
    def _build_feature_entry(
        feature_name: str,
        raw_val: Any,
        contribution_role: str,
        importance_score: float,
        contributes_to: List[str],
    ) -> Dict[str, Any]:
        """Builds a single parameter entry with governed reference interpretation."""
        # Find friendly label & unit
        meta = (
            CLINICAL_FEATURE_META.get(feature_name)
            or WEARABLE_FEATURE_META.get(feature_name)
            or GUT_TAXA_META.get(feature_name)
            or {"label": feature_name.replace("_", " "), "unit": "", "description": ""}
        )

        friendly_label = meta.get("label", feature_name.replace("_", " "))
        unit = meta.get("unit", "")
        ref_rule = GOVERNED_REFERENCE_RANGES.get(feature_name)

        status = "interpretation_unavailable"
        status_label = ""
        ref_desc = "Standard reference range not established"

        # Evaluate reference range if governed rule exists and value is numeric
        if ref_rule is not None and isinstance(raw_val, (int, float)):
            val_float = float(raw_val)
            ref_desc = ref_rule.get("description", "")
            n_min = ref_rule.get("normal_min", 0.0)
            n_max = ref_rule.get("normal_max", 1e9)

            if feature_name == "HDL":
                # For HDL, higher is protective
                if val_float < 40.0:
                    status = "below_expected_range"
                    status_label = ref_rule.get("low_label", "lower than target")
                else:
                    status = "within_expected_range"
                    status_label = ref_rule.get("normal_label", "within target")
            elif val_float > n_max:
                status = "above_expected_range"
                status_label = ref_rule.get("high_label", "above expected range")
            elif val_float < n_min:
                status = "below_expected_range"
                status_label = ref_rule.get("low_label", "below expected range")
            else:
                status = "within_expected_range"
                status_label = ref_rule.get("normal_label", "within expected range")

        # Classify contribution strength
        contribution = "major" if abs(importance_score) >= 0.10 else (
            "moderate" if abs(importance_score) >= 0.03 else "mild"
        )
        if contribution_role == "protective_factor":
            contribution = "protective"

        return {
            "parameter": feature_name,
            "friendly_name": friendly_label,
            "patient_value": raw_val,
            "unit": unit,
            "reference_range": {
                "description": ref_desc
            },
            "status": status,
            "status_label": status_label,
            "contribution": contribution,
            "contribution_role": contribution_role,
            "importance_score": round(importance_score, 4),
            "contributes_to": contributes_to
        }
