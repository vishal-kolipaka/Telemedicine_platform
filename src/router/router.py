"""
router.py — Model Router Module

Adapter and dispatcher that connects Mapper Contract 2 output to Level-0
domain prediction wrappers (Clinical, Wearable, Gut).

Responsibilities:
  - Reads Contract 2 per-domain status.
  - If status == "complete", extracts canonical feature values in authoritative order.
  - Encodes categorical/boolean fields to numeric (0/1) as required by model interfaces.
  - Dispatches to existing prediction wrappers (predict_clinical, predict_wearable, predict_gut).
  - Isolates execution errors per domain (one failure does not stop others).
  - Returns structured results organized strictly by domain key.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

# Authoritative feature definitions
CLINICAL_FEATURES = [
    "Age",
    "Gender",
    "Height",
    "Weight",
    "BMI",
    "Waist_Circumference",
    "Systolic_BP",
    "Diastolic_BP",
    "Fasting_Blood_Glucose",
    "HbA1c",
    "Triglycerides",
    "HDL",
    "LDL",
    "ALT",
    "AST",
    "Family_History_Diabetes",
    "Family_History_Hypertension",
    "Family_History_CVD",
]

WEARABLE_FEATURES = [
    "Average_Daily_Steps",
    "Active_Minutes",
    "Sedentary_Time_Minutes",
    "Resting_Heart_Rate",
    "Heart_Rate_Variability_RMSSD",
    "Sleep_Duration_Hours",
    "Sleep_Efficiency_Score",
    "Autonomic_Stress_Score",
    "Activity_Energy_Expenditure",
    "Exercise_Frequency_Days",
    "CGM_Average_Glucose",
    "CGM_Glucose_CV",
    "CGM_Time_In_Range",
    "CGM_Time_Above_Range",
    "CGM_Time_Below_Range",
]

GUT_RAW_TAXA_FEATURES = [
    "Akkermansia",
    "Faecalibacterium",
    "Roseburia",
    "Bifidobacterium",
    "Bacteroides",
    "Prevotella",
    "Ruminococcus",
    "Blautia",
    "Collinsella",
    "Escherichia_Shigella",
    "Coprococcus",
    "Alistipes",
    "Subdoligranulum",
    "Enterococcus",
    "Eubacterium",
    "Parabacteroides",
    "Lactobacillus",
    "Klebsiella",
    "Streptococcus",
    "Eggerthella",
    "Other_Taxa",
]

logger = logging.getLogger("Router")


def _encode_feature_value(field_name: str, raw_val: Any) -> float:
    """Coerce canonical value to float/int required by model wrappers."""
    if isinstance(raw_val, bool):
        return 1.0 if raw_val else 0.0
    if isinstance(raw_val, (int, float)):
        return float(raw_val)
    if isinstance(raw_val, str):
        val_clean = raw_val.strip().lower()
        if val_clean in ("male", "m", "yes", "true", "1"):
            return 1.0
        if val_clean in ("female", "f", "no", "false", "0"):
            return 0.0
        try:
            return float(val_clean)
        except ValueError:
            raise ValueError(
                f"Cannot encode non-numeric value '{raw_val}' for feature '{field_name}'"
            )
    raise TypeError(
        f"Unsupported feature value type {type(raw_val).__name__} for '{field_name}'"
    )


class ModelRouter:
    """Dispatches complete Contract 2 domains to their corresponding model wrappers."""

    def __init__(
        self,
        predict_clinical_fn: Callable[[dict], dict] | None = None,
        predict_wearable_fn: Callable[[dict], dict] | None = None,
        predict_gut_fn: Callable[[dict], dict] | None = None,
    ) -> None:
        if predict_clinical_fn is not None:
            self._predict_clinical = predict_clinical_fn
        else:
            from clinical_model.src.predict_clinical import predict_clinical
            self._predict_clinical = predict_clinical

        if predict_wearable_fn is not None:
            self._predict_wearable = predict_wearable_fn
        else:
            from wearable_model.src.predict_wearable import predict_wearable
            self._predict_wearable = predict_wearable

        if predict_gut_fn is not None:
            self._predict_gut = predict_gut_fn
        else:
            from gut_model.src.predict_gut import predict_gut
            self._predict_gut = predict_gut

    def route(self, contract2: dict) -> dict:
        """Process Contract 2 and return inference results for each domain."""
        if not isinstance(contract2, dict):
            raise TypeError(f"Contract 2 input must be a dict, got {type(contract2).__name__}")

        results = {
            "clinical": self._process_domain(
                domain_name="clinical",
                domain_state=contract2.get("clinical"),
                expected_features=CLINICAL_FEATURES,
                predict_fn=self._predict_clinical,
            ),
            "wearable": self._process_domain(
                domain_name="wearable",
                domain_state=contract2.get("wearable"),
                expected_features=WEARABLE_FEATURES,
                predict_fn=self._predict_wearable,
            ),
            "gut": self._process_domain(
                domain_name="gut",
                domain_state=contract2.get("gut"),
                expected_features=GUT_RAW_TAXA_FEATURES,
                predict_fn=self._predict_gut,
            ),
        }
        return results

    def _process_domain(
        self,
        domain_name: str,
        domain_state: dict | None,
        expected_features: list[str],
        predict_fn: Callable[[dict], dict],
    ) -> dict:
        if not domain_state or not isinstance(domain_state, dict):
            return {
                "status": "not_run",
                "reason": f"Domain '{domain_name}' is not present in Contract 2",
            }

        status = domain_state.get("status")
        if status != "complete":
            return {
                "status": "not_run",
                "reason": f"Mapper status was '{status}' (expected 'complete')",
            }

        values_dict = domain_state.get("values", {})
        feature_vector: dict[str, float] = {}

        # Extract and validate all required model features
        missing_in_values = []
        for feat in expected_features:
            if feat not in values_dict:
                missing_in_values.append(feat)
                continue
            entry = values_dict[feat]
            if not isinstance(entry, dict) or "canonical_value" not in entry:
                missing_in_values.append(feat)
                continue
            raw_val = entry["canonical_value"]
            if raw_val is None:
                missing_in_values.append(feat)
                continue

            try:
                feature_vector[feat] = _encode_feature_value(feat, raw_val)
            except (ValueError, TypeError) as err:
                logger.error(f"Encoding error for {domain_name}.{feat}: {err}")
                return {
                    "status": "error",
                    "error_type": "contract_error",
                    "error_message": f"Feature '{feat}' value encoding error: {err}",
                }

        if missing_in_values:
            logger.error(
                f"Contract violation: domain '{domain_name}' marked 'complete' but missing features: {missing_in_values}"
            )
            return {
                "status": "error",
                "error_type": "contract_error",
                "error_message": f"Domain marked 'complete' but values missing required features: {missing_in_values}",
            }

        # Dispatch to prediction wrapper with isolated error handling
        try:
            prediction_output = predict_fn(feature_vector)
            return {
                "status": "success",
                "probabilities": prediction_output.get("probabilities", {}),
                "predictions": prediction_output.get("predictions", {}),
                "threshold_used": prediction_output.get("threshold_used", 0.5),
                "suppressed_labels": prediction_output.get("suppressed_labels", []),
            }
        except Exception as exc:
            logger.exception(f"Model wrapper execution failed for domain '{domain_name}': {exc}")
            return {
                "status": "error",
                "error_type": "model_execution_error",
                "error_message": str(exc),
            }


def route_and_predict(contract2: dict) -> dict:
    """Convenience function to route Contract 2 through default ModelRouter."""
    router = ModelRouter()
    return router.route(contract2)
