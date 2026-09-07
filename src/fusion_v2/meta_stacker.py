"""
meta_stacker.py — Late-Fusion Stacking Meta-Model Inference Engine
"""

from __future__ import annotations

import math
from typing import Dict, Any, List
from .pathway_registry import PathwayRegistry, PATHWAY_DISPLAY_NAMES


def _sigmoid(logit: float) -> float:
    """Numerically safe sigmoid with clipping."""
    x = max(-50.0, min(50.0, logit))
    return 1.0 / (1.0 + math.exp(-x))


class MetaStacker:
    """Evaluates late-fusion stackers for any of the 7 pathways."""

    @staticmethod
    def predict_disease(
        pathway_key: str,
        disease: str,
        modality_probs: Dict[str, float],
    ) -> Dict[str, Any]:
        """Predicts calibrated probability and decision for a disease given active modality probabilities.

        Parameters
        ----------
        pathway_key : str
            One of 'C', 'W', 'G', 'C_W', 'C_G', 'W_G', 'C_W_G'.
        disease : str
            One of 'Type2_Diabetes', 'Prediabetes', 'High_Adiposity_Risk', 'Metabolic_Syndrome', 'NAFLD'.
        modality_probs : dict[str, float]
            Dictionary of { 'clinical': float, 'wearable': float, 'gut': float } probabilities for this disease.

        Returns
        -------
        dict[str, Any]
            Inference outcome including calibrated risk score, percentage, decision, threshold, and formula.
        """
        model = PathwayRegistry.get_model_entry(pathway_key, disease)
        
        modalities = [m.lower() for m in model["modalities"]]
        coefs = model["coefficients"]
        intercept = model["intercept"]
        platt = model.get("platt_scaling", {"A": 1.0, "B": 0.0})
        A = platt.get("A", 1.0)
        B = platt.get("B", 0.0)
        threshold = model["threshold"]

        # Validate that all required modalities are provided
        for m in modalities:
            if m not in modality_probs or modality_probs[m] is None:
                raise ValueError(
                    f"Missing required modality '{m}' for pathway '{pathway_key}' in disease '{disease}'"
                )

        if len(modalities) == 1:
            m = modalities[0]
            raw_p = modality_probs[m]
            # Convert single modality probability to logit and apply calibration
            raw_p_c = max(1e-6, min(1.0 - 1e-6, raw_p))
            raw_logit = math.log(raw_p_c / (1.0 - raw_p_c))
            cal_logit = A * raw_logit + B
            cal_prob = _sigmoid(cal_logit)
        else:
            # Multi-modality logistic stacker
            raw_logit = intercept
            for m in modalities:
                raw_logit += coefs[m] * modality_probs[m]
            
            cal_logit = A * raw_logit + B
            cal_prob = _sigmoid(cal_logit)

        decision = bool(cal_prob >= threshold)

        # Confidence label policy:
        # Clinical-containing pathways or valid multi-modality pathways produce FINAL_PREDICTION
        # Single-modality G or W produce REDUCED_MODALITY (or INSUFFICIENT for specific unsupported diseases)
        confidence_label = "FINAL_PREDICTION"
        if pathway_key in ("G", "W"):
            confidence_label = "REDUCED_MODALITY"

        return {
            "risk_score": round(cal_prob, 4),
            "risk_percentage": round(cal_prob * 100.0, 2),
            "decision": decision,
            "threshold_used": threshold,
            "confidence_label": confidence_label,
            "strategy": f"pathway_{pathway_key.lower()}_stacker",
            "pathway": pathway_key,
            "pathway_display": PATHWAY_DISPLAY_NAMES.get(pathway_key, pathway_key),
            "formula": model.get("formula", ""),
            "modalities_used": modalities,
        }
