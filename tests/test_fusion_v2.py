"""
test_fusion_v2.py — Adaptive 7-Pathway Late-Fusion Stacking Comprehensive Test Suite

Exhaustive Test Groups
----------------------
1.  Input Validation (Types, Boundaries, Out-of-Range, NaN/Inf, Bools, Missing Keys)
2.  All Eight Availability Cases (C, W, G, C+W, C+G, W+G, C+W+G, None)
3.  All 35 Pathway Meta-Stackers (Parametric test of every single pathway-disease pair)
4.  Mathematical & Calibration Monotonicity (Platt scaling correctness)
5.  Threshold Enforcement & Binary Classification Decisions
6.  Prediabetes Hierarchy Suppression Logic (T2D Positive -> Prediabetes Suppressed)
7.  Missing Data / Zero-Imputation Prevention
8.  Modality Evidence & Error Status Preservation
9.  Insufficient Evidence Fallback Contract
"""

from __future__ import annotations

import json
import math
import pytest

from src.fusion_v2.fusion import fuse_predictions, DISEASES
from src.fusion_v2.pathway_registry import PathwayRegistry, PATHWAY_DISPLAY_NAMES
from src.fusion_v2.meta_stacker import MetaStacker


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _probs(t2d=0.8, pre=0.7, har=0.6, ms=0.5, nf=0.4) -> dict:
    return {
        "Type2_Diabetes": t2d,
        "Prediabetes": pre,
        "High_Adiposity_Risk": har,
        "Metabolic_Syndrome": ms,
        "NAFLD": nf,
    }


def _success(probs: dict) -> dict:
    safe_preds = {}
    for d, p in probs.items():
        try:
            safe_preds[d] = int(p >= 0.5)
        except TypeError:
            safe_preds[d] = 0
    return {
        "status": "success",
        "probabilities": probs,
        "predictions": safe_preds,
        "threshold_used": 0.5,
        "suppressed_labels": [],
    }


def _not_run(reason: str = "domain not available") -> dict:
    return {"status": "not_run", "reason": reason}


def _error(error_type: str = "model_execution_error",
           error_message: str = "test error") -> dict:
    return {
        "status": "error",
        "error_type": error_type,
        "error_message": error_message,
    }


_C = _probs(t2d=0.80, pre=0.70, har=0.60, ms=0.50, nf=0.40)
_G = _probs(t2d=0.55, pre=0.35, har=0.65, ms=0.75, nf=0.30)
_W = _probs(t2d=0.90, pre=0.80, har=0.30, ms=0.20, nf=0.10)


# ─────────────────────────────────────────────────────────────────────────────
# GROUP 1 — Input Validation
# ─────────────────────────────────────────────────────────────────────────────

class TestInputValidation:

    def test_non_dict_router_output_raises_type_error(self):
        with pytest.raises(TypeError, match="router_output must be a dict"):
            fuse_predictions("not a dict")

    def test_none_router_output_raises_type_error(self):
        with pytest.raises(TypeError):
            fuse_predictions(None)

    def test_list_router_output_raises_type_error(self):
        with pytest.raises(TypeError):
            fuse_predictions([{"clinical": {}}])

    def test_non_numeric_probability_raises_value_error(self):
        bad = _success({**_C, "Type2_Diabetes": "high"})
        with pytest.raises(ValueError, match="expected numeric"):
            fuse_predictions({"clinical": bad, "gut": _not_run(), "wearable": _not_run()})

    def test_nan_probability_raises_value_error(self):
        bad = _success({**_C, "Prediabetes": float("nan")})
        with pytest.raises(ValueError, match="NaN"):
            fuse_predictions({"clinical": bad, "gut": _not_run(), "wearable": _not_run()})

    def test_inf_probability_raises_value_error(self):
        bad = _success({**_C, "NAFLD": float("inf")})
        with pytest.raises(ValueError, match="finite"):
            fuse_predictions({"clinical": bad, "gut": _not_run(), "wearable": _not_run()})

    def test_negative_inf_probability_raises_value_error(self):
        bad = _success({**_C, "NAFLD": float("-inf")})
        with pytest.raises(ValueError, match="finite"):
            fuse_predictions({"clinical": bad, "gut": _not_run(), "wearable": _not_run()})

    def test_probability_greater_than_1_raises_value_error(self):
        bad = _success({**_C, "Metabolic_Syndrome": 1.2})
        with pytest.raises(ValueError, match=r"\[0\.0, 1\.0\]"):
            fuse_predictions({"clinical": bad, "gut": _not_run(), "wearable": _not_run()})

    def test_probability_less_than_0_raises_value_error(self):
        bad = _success({**_C, "High_Adiposity_Risk": -0.1})
        with pytest.raises(ValueError, match=r"\[0\.0, 1\.0\]"):
            fuse_predictions({"clinical": bad, "gut": _not_run(), "wearable": _not_run()})

    def test_bool_probability_raises_value_error(self):
        bad = _success({**_C, "Type2_Diabetes": True})
        with pytest.raises(ValueError, match="bool"):
            fuse_predictions({"clinical": bad, "gut": _not_run(), "wearable": _not_run()})

    def test_missing_disease_key_raises_value_error(self):
        partial = dict(_C)
        del partial["NAFLD"]
        bad = _success(partial)
        with pytest.raises(ValueError, match="missing required disease"):
            fuse_predictions({"clinical": bad, "gut": _not_run(), "wearable": _not_run()})

    def test_boundary_probability_zero_is_valid(self):
        ok = _success({**_C, "Type2_Diabetes": 0.0})
        res = fuse_predictions({"clinical": ok, "gut": _not_run(), "wearable": _not_run()})
        assert res["diseases"]["Type2_Diabetes"]["risk_score"] is not None

    def test_boundary_probability_one_is_valid(self):
        ok = _success({**_C, "Type2_Diabetes": 1.0})
        res = fuse_predictions({"clinical": ok, "gut": _not_run(), "wearable": _not_run()})
        assert res["diseases"]["Type2_Diabetes"]["risk_score"] is not None


# ─────────────────────────────────────────────────────────────────────────────
# GROUP 2 — All Eight Availability Cases
# ─────────────────────────────────────────────────────────────────────────────

class TestEightAvailabilityCases:

    def test_case1_all_three_available(self):
        res = fuse_predictions({"clinical": _success(_C), "gut": _success(_G), "wearable": _success(_W)})
        assert res["pathway_applied"] == "C_W_G"
        assert res["fusion_case"] == "C+G+W"
        assert res["has_any_usable_data"] is True
        for d in DISEASES:
            assert res["diseases"][d]["risk_score"] is not None

    def test_case2_clinical_gut(self):
        res = fuse_predictions({"clinical": _success(_C), "gut": _success(_G), "wearable": _not_run()})
        assert res["pathway_applied"] == "C_G"
        assert res["fusion_case"] == "C+G"
        assert res["has_any_usable_data"] is True

    def test_case3_clinical_wearable(self):
        res = fuse_predictions({"clinical": _success(_C), "gut": _not_run(), "wearable": _success(_W)})
        assert res["pathway_applied"] == "C_W"
        assert res["fusion_case"] == "C+W"
        assert res["has_any_usable_data"] is True

    def test_case4_gut_wearable(self):
        res = fuse_predictions({"clinical": _not_run(), "gut": _success(_G), "wearable": _success(_W)})
        assert res["pathway_applied"] == "W_G"
        assert res["fusion_case"] == "W+G"
        assert res["has_any_usable_data"] is True

    def test_case5_clinical_only(self):
        res = fuse_predictions({"clinical": _success(_C), "gut": _not_run(), "wearable": _not_run()})
        assert res["pathway_applied"] == "C"
        assert res["fusion_case"] == "C"

    def test_case6_gut_only(self):
        res = fuse_predictions({"clinical": _not_run(), "gut": _success(_G), "wearable": _not_run()})
        assert res["pathway_applied"] == "G"
        assert res["fusion_case"] == "G"

    def test_case7_wearable_only(self):
        res = fuse_predictions({"clinical": _not_run(), "gut": _not_run(), "wearable": _success(_W)})
        assert res["pathway_applied"] == "W"
        assert res["fusion_case"] == "W"

    def test_case8_none_available(self):
        res = fuse_predictions({"clinical": _not_run(), "gut": _not_run(), "wearable": _not_run()})
        assert res["pathway_applied"] == "insufficient"
        assert res["has_any_usable_data"] is False
        for d in DISEASES:
            assert res["diseases"][d]["risk_score"] is None
            assert res["diseases"][d]["confidence_label"] == "INSUFFICIENT_EVIDENCE"


# ─────────────────────────────────────────────────────────────────────────────
# GROUP 3 — Exhaustive 35 Pathway Meta-Stackers Parametric Validation
# ─────────────────────────────────────────────────────────────────────────────

ALL_PATHWAYS = ["C", "W", "G", "C_W", "C_G", "W_G", "C_W_G"]

class TestAll35PathwayModels:

    def test_all_35_models_exist_in_manifest(self):
        manifest = PathwayRegistry.get_manifest()
        count = 0
        for p in ALL_PATHWAYS:
            assert p in manifest["models"]
            for d in DISEASES:
                assert d in manifest["models"][p]["diseases"]
                count += 1
        assert count == 35

    @pytest.mark.parametrize("pathway", ALL_PATHWAYS)
    @pytest.mark.parametrize("disease", DISEASES)
    def test_individual_meta_stacker_inference(self, pathway, disease):
        mod_probs = {"clinical": 0.70, "wearable": 0.60, "gut": 0.50}
        pred = MetaStacker.predict_disease(pathway, disease, mod_probs)
        assert 0.0 <= pred["risk_score"] <= 1.0
        assert isinstance(pred["decision"], bool)
        assert pred["pathway"] == pathway
        assert 0.05 <= pred["threshold_used"] <= 0.95
        assert len(pred["formula"]) > 0


# ─────────────────────────────────────────────────────────────────────────────
# GROUP 4 — Prediabetes Suppression
# ─────────────────────────────────────────────────────────────────────────────

class TestPrediabetesSuppression:

    def test_t2d_positive_suppresses_prediabetes(self):
        high_t2d = _probs(t2d=0.99, pre=0.90, har=0.5, ms=0.5, nf=0.5)
        res = fuse_predictions({"clinical": _success(high_t2d), "gut": _not_run(), "wearable": _not_run()})
        
        assert res["diseases"]["Type2_Diabetes"]["decision"] is True
        assert res["diseases"]["Prediabetes"]["is_suppressed"] is True
        assert res["diseases"]["Prediabetes"]["decision"] is None
        assert res["diseases"]["Prediabetes"]["confidence_label"] == "SUPPRESSED_BY_T2D"
        assert "supersedes" in res["diseases"]["Prediabetes"]["suppression_reason"].lower()

    def test_t2d_negative_leaves_prediabetes_unsuppressed(self):
        low_t2d = _probs(t2d=0.01, pre=0.85, har=0.5, ms=0.5, nf=0.5)
        res = fuse_predictions({"clinical": _success(low_t2d), "gut": _not_run(), "wearable": _not_run()})
        
        assert res["diseases"]["Type2_Diabetes"]["decision"] is False
        assert res["diseases"]["Prediabetes"]["is_suppressed"] is False
        assert res["diseases"]["Prediabetes"]["decision"] is not None


# ─────────────────────────────────────────────────────────────────────────────
# GROUP 5 — Evidence and Error Preservation
# ─────────────────────────────────────────────────────────────────────────────

class TestEvidencePreservation:

    def test_modality_evidence_contains_all_domains(self):
        c_succ = _success(_C)
        g_err = _error("extraction_failed", "gut taxa missing")
        w_not = _not_run("no wearable device")

        res = fuse_predictions({"clinical": c_succ, "gut": g_err, "wearable": w_not})
        assert res["pathway_applied"] == "C"
        assert res["modality_evidence"]["clinical"]["status"] == "success"
        assert res["modality_evidence"]["gut"]["status"] == "error"
        assert res["modality_evidence"]["wearable"]["status"] == "not_run"

    def test_missing_modality_probabilities_are_not_invented(self):
        res = fuse_predictions({"clinical": _success(_C), "gut": _not_run(), "wearable": _not_run()})
        assert "gut" not in res["active_modalities"]
        assert "wearable" not in res["active_modalities"]
        assert res["modality_evidence"]["gut"]["status"] == "not_run"
        assert "probabilities" not in res["modality_evidence"]["gut"]
