"""
fusion_explainer.py — Fusion V2 Provenance and Modality Attribution for XAI

Translates Fusion V2 decision provenance into transparent, patient-friendly
explanations while strictly separating mathematical contributors from
contextual/supporting evidence (such as Wearable/CGM data).
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional
from .tree_explainer import explain_domain_disease

DISEASE_DISPLAY_NAMES: Dict[str, str] = {
    "Type2_Diabetes": "Type 2 Diabetes",
    "Prediabetes": "Prediabetes",
    "High_Adiposity_Risk": "High Adiposity Risk",
    "Metabolic_Syndrome": "Metabolic Syndrome",
    "NAFLD": "Non-Alcoholic Fatty Liver Disease (NAFLD)",
}


def explain_provenance(
    disease: str,
    disease_info: Dict[str, Any],
    modality_evidence: Dict[str, Any],
    modalities_dict: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Deconstructs Fusion V2 provenance into a clear, patient-facing narrative.
    Dynamically surfaces all available model signals (primary and independent).
    """
    strategy = disease_info.get("strategy", "insufficient")
    modalities_used = disease_info.get("modalities_used", [])
    confidence_label = disease_info.get("confidence_label", "INSUFFICIENT_EVIDENCE")
    is_suppressed = disease_info.get("is_suppressed", False)
    risk_score = disease_info.get("risk_score")

    # Assemble dynamic available signals and modality scores if modalities_dict is provided
    available_signals = []
    dynamic_modality_scores = {}
    if modalities_dict:
        for dom in ("clinical", "gut", "wearable"):
            if dom in modalities_dict and modalities_dict[dom].get("predicted"):
                m_info = modalities_dict[dom]
                available_signals.append({
                    "modality": dom,
                    "name": f"{dom.capitalize()} Model",
                    "role": m_info.get("role_label", "PRIMARY"),
                    "role_label": m_info.get("role_label", "PRIMARY"),
                    "role_description": m_info.get("role_description", ""),
                    "risk_percentage": m_info.get("risk_percentage"),
                    "decision": m_info.get("decision"),
                })
                dynamic_modality_scores[f"{dom}_risk_percentage"] = m_info.get("risk_percentage")

    if is_suppressed:
        return {
            "type": "suppressed_secondary",
            "badge": "Diagnostic Hierarchy Applied",
            "primary_modalities": modalities_used,
            "headline": "Secondary prediabetes assessment suppressed.",
            "description": (
                "Diagnostic criteria for Type 2 Diabetes were met. In clinical assessment, "
                "active diabetes supersedes intermediate prediabetes risk."
            ),
            "modality_scores": dynamic_modality_scores,
            "available_signals": available_signals,
        }

    if confidence_label == "INSUFFICIENT_EVIDENCE" or risk_score is None:
        return {
            "type": "insufficient",
            "badge": "Not Enough Data",
            "primary_modalities": [],
            "headline": "Additional clinical data required.",
            "description": (
                "Essential laboratory biomarkers or physiological measurements are missing. "
                "We cannot form a reliable risk assessment without these key health indicators."
            ),
            "modality_scores": dynamic_modality_scores,
            "available_signals": available_signals,
        }

    # Pathway Stackers and legacy strategies
    primary_modalities = modalities_used if modalities_used else ["clinical", "gut", "wearable"]
    is_multi = len(primary_modalities) > 1

    return {
        "type": "multi_modality_stacker" if is_multi else "single_modality",
        "badge": "Multi-Source Assessment",
        "primary_modalities": primary_modalities,
        "headline": "Synthesized from your multi-source diagnostic markers and predictive model signals.",
        "description": (
            "This assessment integrates your comprehensive health biomarkers, laboratory findings, "
            "and predictive intelligence models to evaluate this health condition."
        ),
        "modality_scores": dynamic_modality_scores,
        "available_signals": available_signals,
    }


def build_supporting_wearable_evidence(
    disease: str,
    disease_info: Dict[str, Any],
    modality_evidence: Dict[str, Any],
    wearable_feature_dict: Optional[Dict[str, float]],
) -> Dict[str, Any]:
    """
    Constructs decoupled contextual Wearable/CGM evidence when wearable was NOT
    a mathematical contributor to the final Fusion V2 score.
    """
    wearable_res = modality_evidence.get("wearable", {})
    w_ok = wearable_res.get("status") == "success"
    w_prob = wearable_res.get("probabilities", {}).get(disease) if w_ok else None

    # Check if wearable was already the primary mathematical contributor
    modalities_used = disease_info.get("modalities_used", [])
    if "wearable" in modalities_used:
        # Wearable was a mathematical contributor; handled in primary explanation
        return {"available": False, "is_mathematical_contributor": True}

    if not w_ok or w_prob is None or not wearable_feature_dict:
        return {"available": False, "is_mathematical_contributor": False}

    # Generate top wearable signals using TreeSHAP on the wearable model
    try:
        w_xai = explain_domain_disease(
            domain="wearable",
            disease=disease,
            feature_dict=wearable_feature_dict,
            top_n_risk=3,
            top_n_protective=2,
        )
        top_signals = (w_xai.get("risk_drivers", []) + w_xai.get("protective_factors", []))[:3]
    except Exception:
        top_signals = []

    return {
        "available": True,
        "is_mathematical_contributor": False,
        "raw_wearable_risk_percentage": round(w_prob * 100, 1),
        "headline": "Additional Context from Wearable & CGM Data",
        "notice": (
            "Your wearable device and continuous monitoring data provide independent corroborating context "
            "alongside your primary clinical assessment."
        ),
        "top_signals": top_signals,
    }
