"""
fusion.py — Adaptive 7-Pathway Late-Fusion Stacking Core Module

Entry point: fuse_predictions(router_output, patient_id) -> dict

Architecture:
-------------
Consumes the dict output from ModelRouter.route() / route_and_predict()
and executes the Adaptive 7-Pathway Late-Fusion Stacking Engine:

  1. Validates router_output and Level-0 probability boundaries strictly.
  2. Resolves active modalities: (C, W, G, C_W, C_G, W_G, C_W_G).
  3. Dispatches inputs to the corresponding OOF-trained Pathway Meta-Stacker.
  4. Applies pathway-specific Platt calibration and validation-optimized thresholds.
  5. Enforces diagnostic hierarchy: active Type 2 Diabetes suppresses intermediate Prediabetes.
  6. Preserves all Level-0 probability outputs in modality_evidence for XAI explainability.
"""

from __future__ import annotations

import math
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from .pathway_registry import PathwayRegistry, PATHWAY_DISPLAY_NAMES
from .meta_stacker import MetaStacker

logger = logging.getLogger("FusionV2")

DISEASES: List[str] = [
    "Type2_Diabetes",
    "Prediabetes",
    "High_Adiposity_Risk",
    "Metabolic_Syndrome",
    "NAFLD",
]


def _validate_probability(value: Any, label: str) -> float:
    """Strict validation of a single incoming Level-0 probability."""
    if isinstance(value, bool):
        raise ValueError(f"{label}: expected numeric float, got bool ({value!r})")
    if not isinstance(value, (int, float)):
        raise ValueError(f"{label}: expected numeric, got {type(value).__name__!r} ({value!r})")
    if math.isnan(value):
        raise ValueError(f"{label}: must be finite, got NaN")
    if math.isinf(value):
        raise ValueError(f"{label}: must be finite, got {'inf' if value > 0 else '-inf'}")
    if value < 0.0 or value > 1.0:
        raise ValueError(f"{label}: must be in [0.0, 1.0], got {value!r}")
    return float(value)


def fuse_predictions(
    router_output: Dict[str, Any],
    patient_id: str = "unknown",
) -> Dict[str, Any]:
    """Executes Adaptive 7-Pathway Late-Fusion on Level-0 predictions.

    Parameters
    ----------
    router_output : dict
        Output from ModelRouter.route() containing results per domain ('clinical', 'wearable', 'gut').
    patient_id : str
        Patient identifier for audit logging.

    Returns
    -------
    dict
        Structured multi-modality health assessment response.
    """
    if not isinstance(router_output, dict):
        raise TypeError(f"router_output must be a dict, got {type(router_output).__name__}")

    timestamp = datetime.now(timezone.utc).isoformat()

    # Step 1: Detect which modalities ran successfully and validate probabilities strictly
    active_modalities: List[str] = []
    level0_probs: Dict[str, Dict[str, float]] = {}
    modality_evidence: Dict[str, Any] = {}

    for dom in ("clinical", "wearable", "gut"):
        res = router_output.get(dom, {})
        modality_evidence[dom] = res
        status = res.get("status")
        
        if status in ("success", "ran"):
            probs = res.get("probabilities")
            if not isinstance(probs, dict):
                raise ValueError(f"{dom}: 'probabilities' must be a dict when status is success/ran")
            
            validated_domain_probs = {}
            for dis in DISEASES:
                if dis not in probs:
                    raise ValueError(f"{dom}: missing required disease probability '{dis}'")
                validated_domain_probs[dis] = _validate_probability(probs[dis], f"{dom}.{dis}")
            
            active_modalities.append(dom)
            level0_probs[dom] = validated_domain_probs

    pathway_key = PathwayRegistry.resolve_pathway_key(active_modalities)

    # Step 2: Handle Insufficient Evidence Case (No valid Level-0 predictions)
    if pathway_key == "insufficient" or not active_modalities:
        logger.warning("Insufficient modalities available to run any fusion pathway.")
        return {
            "patient_id": patient_id,
            "timestamp": timestamp,
            "fusion_case": "none",
            "case_applied": "none",
            "pathway_applied": "insufficient",
            "pathway_display": PATHWAY_DISPLAY_NAMES["insufficient"],
            "has_any_usable_data": False,
            "diseases": {
                dis: {
                    "disease_key": dis,
                    "risk_score": None,
                    "risk_percentage": None,
                    "decision": None,
                    "threshold_used": None,
                    "confidence_label": "INSUFFICIENT_EVIDENCE",
                    "is_suppressed": False,
                    "strategy": "insufficient",
                    "pathway": "insufficient",
                    "modalities_used": [],
                }
                for dis in DISEASES
            },
            "modality_evidence": modality_evidence,
        }

    # Step 3: Execute Pathway Meta-Stacker for each disease
    disease_results: Dict[str, Any] = {}

    for dis in DISEASES:
        # Collect probabilities from active modalities for this disease
        mod_probs_for_dis: Dict[str, float] = {}
        for m in active_modalities:
            if m in level0_probs and dis in level0_probs[m]:
                mod_probs_for_dis[m] = level0_probs[m][dis]

        try:
            pred = MetaStacker.predict_disease(pathway_key, dis, mod_probs_for_dis)
            pred["disease_key"] = dis
            pred["is_suppressed"] = False
            disease_results[dis] = pred
        except Exception as exc:
            logger.error(f"Error predicting {dis} on pathway {pathway_key}: {exc}")
            disease_results[dis] = {
                "disease_key": dis,
                "risk_score": None,
                "risk_percentage": None,
                "decision": None,
                "threshold_used": None,
                "confidence_label": "INSUFFICIENT_EVIDENCE",
                "is_suppressed": False,
                "strategy": "insufficient",
                "pathway": pathway_key,
                "modalities_used": active_modalities,
                "error": str(exc),
            }

    # Step 4: Apply Diagnostic Hierarchy (Prediabetes suppression if T2D is positive)
    t2d_res = disease_results.get("Type2_Diabetes", {})
    if t2d_res.get("decision") is True:
        pre_res = disease_results.get("Prediabetes", {})
        if pre_res:
            pre_res["is_suppressed"] = True
            pre_res["decision"] = None
            pre_res["confidence_label"] = "SUPPRESSED_BY_T2D"
            pre_res["suppression_reason"] = (
                "Diagnostic criteria for Type 2 Diabetes were met. In clinical assessment, "
                "active diabetes supersedes intermediate prediabetes risk."
            )

    # Step 5: Format Case String for backward compatibility
    case_names = {
        "C": "C",
        "W": "W",
        "G": "G",
        "C_W": "C+W",
        "C_G": "C+G",
        "W_G": "W+G",
        "C_W_G": "C+G+W",
    }
    fusion_case_str = case_names.get(pathway_key, pathway_key)

    return {
        "patient_id": patient_id,
        "timestamp": timestamp,
        "fusion_case": fusion_case_str,
        "case_applied": fusion_case_str,
        "pathway_applied": pathway_key,
        "pathway_display": PATHWAY_DISPLAY_NAMES.get(pathway_key, pathway_key),
        "has_any_usable_data": True,
        "active_modalities": active_modalities,
        "diseases": disease_results,
        "modality_evidence": modality_evidence,
    }
