"""
xai_engine.py — Main XAI Coordination and Explanation Assembly Engine

Orchestrates TreeSHAP local feature attribution, Fusion V2 provenance
deconstruction, dynamic highest-risk selection with clinical tie-breaking,
and decoupled supporting wearable evidence packaging.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional

from .tree_explainer import explain_domain_disease
from .fusion_explainer import (
    explain_provenance,
    build_supporting_wearable_evidence,
    DISEASE_DISPLAY_NAMES,
)

logger = logging.getLogger("XAI.Engine")

DISEASES = [
    "Type2_Diabetes",
    "Prediabetes",
    "High_Adiposity_Risk",
    "Metabolic_Syndrome",
    "NAFLD",
]

# Clinical priority order for tie-breaking identical risk scores
# Higher rank = higher priority when risk scores are tied
TIE_BREAK_PRIORITY: Dict[str, int] = {
    "Type2_Diabetes": 5,
    "Metabolic_Syndrome": 4,
    "NAFLD": 3,
    "High_Adiposity_Risk": 2,
    "Prediabetes": 1,
}


def _extract_domain_feature_dict(contract2: Dict[str, Any], domain: str) -> Optional[Dict[str, float]]:
    """Extract numeric feature dictionary for a given domain from Contract 2."""
    if not isinstance(contract2, dict):
        return None

    domain_obj = contract2.get(domain)
    if not isinstance(domain_obj, dict):
        return None

    values_dict = domain_obj.get("values", {})
    if not isinstance(values_dict, dict) or not values_dict:
        return None

    extracted: Dict[str, float] = {}
    for feat_key, entry in values_dict.items():
        if isinstance(entry, dict) and "canonical_value" in entry:
            val = entry["canonical_value"]
            if val is not None:
                if isinstance(val, bool):
                    extracted[feat_key] = 1.0 if val else 0.0
                elif isinstance(val, (int, float)):
                    extracted[feat_key] = float(val)
                elif isinstance(val, str):
                    val_clean = val.strip().lower()
                    if val_clean in ("male", "m", "yes", "true", "1"):
                        extracted[feat_key] = 1.0
                    elif val_clean in ("female", "f", "no", "false", "0"):
                        extracted[feat_key] = 0.0
                    else:
                        try:
                            extracted[feat_key] = float(val_clean)
                        except ValueError:
                            pass
    return extracted if extracted else None


class XAIEngine:
    """Coordinates patient-facing XAI generation across all 5 disease conditions."""

    def explain_assessment(
        self,
        contract2: Dict[str, Any],
        router_output: Dict[str, Any],
        fusion_output: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Builds the unified, patient-ready XAI explanation payload.

        Parameters:
            contract2: Mapped Contract 2 state
            router_output: Direct output from ModelRouter.route()
            fusion_output: Direct output from Fusion V2 fuse_predictions()

        Returns:
            JSON-serialisable dict containing default_disease and per-disease explanations.
        """
        # 1. Extract feature vectors per domain
        clinical_features = _extract_domain_feature_dict(contract2, "clinical")
        wearable_features = _extract_domain_feature_dict(contract2, "wearable")
        gut_features = _extract_domain_feature_dict(contract2, "gut")

        fusion_diseases = fusion_output.get("diseases", {})
        modality_evidence = fusion_output.get("modality_evidence", {})

        explanations: Dict[str, Any] = {}
        eligible_candidates: List[Dict[str, Any]] = []

        # 2. Process all 5 disease explanations
        for disease in DISEASES:
            dis_info = fusion_diseases.get(disease, {})
            risk_score = dis_info.get("risk_score")
            decision = dis_info.get("decision")
            conf_label = dis_info.get("confidence_label", "INSUFFICIENT_EVIDENCE")
            strategy = dis_info.get("strategy", "insufficient")
            modalities_used = dis_info.get("modalities_used", [])
            is_suppressed = dis_info.get("is_suppressed", False)
            display_name = DISEASE_DISPLAY_NAMES.get(disease, disease)

            # Check eligibility for default highest-risk selection
            if (
                risk_score is not None
                and conf_label != "INSUFFICIENT_EVIDENCE"
                and not is_suppressed
            ):
                eligible_candidates.append({
                    "disease_key": disease,
                    "risk_score": float(risk_score),
                    "priority": TIE_BREAK_PRIORITY.get(disease, 0),
                })

            # Check which Level-0 models actually ran and produced predictions for this disease
            c_ev = (router_output.get("clinical") or modality_evidence.get("clinical") or {})
            w_ev = (router_output.get("wearable") or modality_evidence.get("wearable") or {})
            g_ev = (router_output.get("gut") or modality_evidence.get("gut") or {})

            c_ran = (c_ev.get("status") in ("success", "ran")) and (disease in c_ev.get("probabilities", {}))
            w_ran = (w_ev.get("status") in ("success", "ran")) and (disease in w_ev.get("probabilities", {}))
            g_ran = (g_ev.get("status") in ("success", "ran")) and (disease in g_ev.get("probabilities", {}))

            c_prob = c_ev.get("probabilities", {}).get(disease) if c_ran else None
            c_dec = c_ev.get("predictions", {}).get(disease) if c_ran else None

            w_prob = w_ev.get("probabilities", {}).get(disease) if w_ran else None
            w_dec = w_ev.get("predictions", {}).get(disease) if w_ran else None

            g_prob = g_ev.get("probabilities", {}).get(disease) if g_ran else None
            g_dec = g_ev.get("predictions", {}).get(disease) if g_ran else None

            # Determine modality roles: PRIMARY MATHEMATICAL CONTRIBUTOR vs INDEPENDENT / SUPPORTING SIGNAL
            c_role = "primary_contributor" if "clinical" in modalities_used else "independent_signal"
            w_role = "primary_contributor" if "wearable" in modalities_used else "independent_signal"
            g_role = "primary_contributor" if "gut" in modalities_used else "independent_signal"

            # Compute TreeSHAP drivers for each available modality that successfully predicted
            c_drivers: List[Dict[str, Any]] = []
            c_protective: List[Dict[str, Any]] = []
            if c_ran and clinical_features:
                try:
                    c_xai = explain_domain_disease("clinical", disease, clinical_features, top_n_risk=4, top_n_protective=2)
                    for d in c_xai.get("risk_drivers", []):
                        d_copy = dict(d)
                        d_copy["source_modality"] = "clinical"
                        d_copy["source_role"] = c_role
                        d_copy["source_label"] = "Clinical Model" if c_role == "primary_contributor" else "Clinical Model — Independent Signal"
                        c_drivers.append(d_copy)
                    for p in c_xai.get("protective_factors", []):
                        p_copy = dict(p)
                        p_copy["source_modality"] = "clinical"
                        p_copy["source_role"] = c_role
                        p_copy["source_label"] = "Clinical Model" if c_role == "primary_contributor" else "Clinical Model — Independent Signal"
                        c_protective.append(p_copy)
                except Exception as err:
                    logger.error(f"Clinical TreeSHAP failed for {disease}: {err}")

            w_drivers: List[Dict[str, Any]] = []
            w_protective: List[Dict[str, Any]] = []
            if w_ran and wearable_features:
                try:
                    w_xai = explain_domain_disease("wearable", disease, wearable_features, top_n_risk=4, top_n_protective=2)
                    for d in w_xai.get("risk_drivers", []):
                        d_copy = dict(d)
                        d_copy["source_modality"] = "wearable"
                        d_copy["source_role"] = w_role
                        d_copy["source_label"] = "Wearable Model" if w_role == "primary_contributor" else "Wearable Model — Independent Signal"
                        w_drivers.append(d_copy)
                    for p in w_xai.get("protective_factors", []):
                        p_copy = dict(p)
                        p_copy["source_modality"] = "wearable"
                        p_copy["source_role"] = w_role
                        p_copy["source_label"] = "Wearable Model" if w_role == "primary_contributor" else "Wearable Model — Independent Signal"
                        w_protective.append(p_copy)
                except Exception as err:
                    logger.error(f"Wearable TreeSHAP failed for {disease}: {err}")

            g_drivers: List[Dict[str, Any]] = []
            g_protective: List[Dict[str, Any]] = []
            if g_ran and gut_features:
                try:
                    g_xai = explain_domain_disease("gut", disease, gut_features, top_n_risk=4, top_n_protective=2)
                    for d in g_xai.get("risk_drivers", []):
                        d_copy = dict(d)
                        d_copy["source_modality"] = "gut"
                        d_copy["source_role"] = g_role
                        d_copy["source_label"] = "Gut Model" if g_role == "primary_contributor" else "Gut Model — Independent Signal"
                        g_drivers.append(d_copy)
                    for p in g_xai.get("protective_factors", []):
                        p_copy = dict(p)
                        p_copy["source_modality"] = "gut"
                        p_copy["source_role"] = g_role
                        p_copy["source_label"] = "Gut Model" if g_role == "primary_contributor" else "Gut Model — Independent Signal"
                        g_protective.append(p_copy)
                except Exception as err:
                    logger.error(f"Gut TreeSHAP failed for {disease}: {err}")

            # Build modalities structure for this disease
            modalities_dict: Dict[str, Any] = {}
            available_sources: List[str] = []

            if c_ran:
                available_sources.append("clinical")
                modalities_dict["clinical"] = {
                    "available": True,
                    "predicted": True,
                    "risk_score": c_prob,
                    "risk_percentage": round(c_prob * 100, 1) if c_prob is not None else None,
                    "decision": c_dec,
                    "role": c_role,
                    "role_label": "PRIMARY" if c_role == "primary_contributor" else "INDEPENDENT",
                    "role_description": (
                        "Mathematical contributor to final fused risk score"
                        if c_role == "primary_contributor"
                        else "Independent model signal (not in mathematical fusion formula)"
                    ),
                    "risk_drivers": c_drivers,
                    "protective_factors": c_protective,
                }

            if w_ran:
                available_sources.append("wearable")
                modalities_dict["wearable"] = {
                    "available": True,
                    "predicted": True,
                    "risk_score": w_prob,
                    "risk_percentage": round(w_prob * 100, 1) if w_prob is not None else None,
                    "decision": w_dec,
                    "role": w_role,
                    "role_label": "PRIMARY" if w_role == "primary_contributor" else "INDEPENDENT",
                    "role_description": (
                        "Mathematical contributor to final fused risk score"
                        if w_role == "primary_contributor"
                        else "Independent model signal (not in mathematical fusion formula)"
                    ),
                    "risk_drivers": w_drivers,
                    "protective_factors": w_protective,
                }

            if g_ran:
                available_sources.append("gut")
                modalities_dict["gut"] = {
                    "available": True,
                    "predicted": True,
                    "risk_score": g_prob,
                    "risk_percentage": round(g_prob * 100, 1) if g_prob is not None else None,
                    "decision": g_dec,
                    "role": g_role,
                    "role_label": "PRIMARY" if g_role == "primary_contributor" else "INDEPENDENT",
                    "role_description": (
                        "Mathematical contributor to final fused risk score"
                        if g_role == "primary_contributor"
                        else "Independent model signal (not in mathematical fusion formula)"
                    ),
                    "risk_drivers": g_drivers,
                    "protective_factors": g_protective,
                }

            # Build provenance narrative with dynamic signal awareness
            provenance = explain_provenance(disease, dis_info, modality_evidence, modalities_dict)

            # Handle Insufficient / Suppressed case
            if conf_label == "INSUFFICIENT_EVIDENCE" or risk_score is None or is_suppressed:
                explanations[disease] = {
                    "disease_key": disease,
                    "display_name": display_name,
                    "available": False,
                    "risk_percentage": round(risk_score * 100, 1) if risk_score is not None else None,
                    "decision": decision,
                    "is_suppressed": is_suppressed,
                    "provenance": provenance,
                    "modalities": modalities_dict,
                    "available_sources": available_sources,
                    "risk_drivers": [],
                    "protective_factors": [],
                    "supporting_wearable_evidence": {"available": False},
                    "modality_breakdown": None,
                }
                continue

            # Combine all drivers from available modalities for the unified "All Signals" view
            all_combined_drivers = sorted(
                c_drivers + g_drivers + w_drivers,
                key=lambda x: x.get("shap_value", 0),
                reverse=True,
            )
            all_combined_protective = sorted(
                c_protective + g_protective + w_protective,
                key=lambda x: x.get("shap_value", 0),
                reverse=False,
            )

            combined_risk_drivers = all_combined_drivers[:6]
            combined_protective_factors = all_combined_protective[:4]

            # Modality breakdown for backward compatibility
            modality_breakdown = {
                dom: {
                    "risk_drivers": modalities_dict[dom]["risk_drivers"],
                    "protective_factors": modalities_dict[dom]["protective_factors"],
                }
                for dom in available_sources
            } if available_sources else None

            # Decouple supporting wearable evidence for context card
            supporting_wearable = build_supporting_wearable_evidence(
                disease=disease,
                disease_info=dis_info,
                modality_evidence=modality_evidence,
                wearable_feature_dict=wearable_features,
            )

            explanations[disease] = {
                "disease_key": disease,
                "display_name": display_name,
                "available": True,
                "risk_percentage": round(risk_score * 100, 1),
                "decision": decision,
                "is_suppressed": is_suppressed,
                "provenance": provenance,
                "modalities": modalities_dict,
                "available_sources": available_sources,
                "risk_drivers": combined_risk_drivers,
                "protective_factors": combined_protective_factors,
                "supporting_wearable_evidence": supporting_wearable,
                "modality_breakdown": modality_breakdown,
            }

        # 5. Dynamic Highest-Risk Disease Selection with clinical tie-breaking
        default_disease = None
        if eligible_candidates:
            # Sort by risk_score desc, then priority desc
            sorted_candidates = sorted(
                eligible_candidates,
                key=lambda x: (x["risk_score"], x["priority"]),
                reverse=True,
            )
            default_disease = sorted_candidates[0]["disease_key"]

        return {
            "default_disease": default_disease,
            "has_usable_explanations": bool(default_disease is not None),
            "explanations": explanations,
        }
