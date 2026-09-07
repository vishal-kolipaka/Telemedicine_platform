"""
test_xai_engine.py — Comprehensive Test Suite for the XAI Layer

Verifies:
  1. Feature formatting & taxonomic biological metadata
  2. Level-0 TreeSHAP feature extraction (Clinical, Wearable, Gut)
  3. CLR transformation correctness for Gut XAI
  4. Fusion V2 provenance and strategy deconstruction
  5. Decoupled supporting wearable evidence (non-mathematical attribution)
  6. Dynamic highest-risk selection and clinical tie-breaking policy
  7. Prediabetes suppression handling in XAI
  8. Insufficient data fallback handling
  9. End-to-end integration with ModelRouter and Fusion V2
"""

import pytest
import numpy as np

from src.xai.feature_formatter import (
    get_feature_meta,
    format_feature_value,
    CLINICAL_FEATURE_META,
    WEARABLE_FEATURE_META,
    GUT_TAXA_META,
)
from src.xai.tree_explainer import explain_domain_disease
from src.xai.fusion_explainer import (
    explain_provenance,
    build_supporting_wearable_evidence,
)
from src.xai.xai_engine import XAIEngine, TIE_BREAK_PRIORITY
from src.router.router import ModelRouter
from src.fusion_v2.fusion import fuse_predictions


# ── Sample Synthetic Feature Vectors for Testing ─────────────────────────────

SAMPLE_CLINICAL_FEATURES = {
    "Age": 55.0,
    "Gender": 1.0,
    "Height": 175.0,
    "Weight": 92.0,
    "BMI": 30.0,
    "Waist_Circumference": 102.0,
    "Systolic_BP": 138.0,
    "Diastolic_BP": 88.0,
    "Fasting_Blood_Glucose": 135.0,
    "HbA1c": 7.8,
    "Triglycerides": 210.0,
    "HDL": 38.0,
    "LDL": 145.0,
    "ALT": 42.0,
    "AST": 36.0,
    "Family_History_Diabetes": 1.0,
    "Family_History_Hypertension": 1.0,
    "Family_History_CVD": 0.0,
}

SAMPLE_WEARABLE_FEATURES = {
    "Average_Daily_Steps": 4200.0,
    "Active_Minutes": 18.0,
    "Sedentary_Time_Minutes": 620.0,
    "Resting_Heart_Rate": 76.0,
    "Heart_Rate_Variability_RMSSD": 24.0,
    "Sleep_Duration_Hours": 6.2,
    "Sleep_Efficiency_Score": 74.0,
    "Autonomic_Stress_Score": 68.0,
    "Activity_Energy_Expenditure": 350.0,
    "Exercise_Frequency_Days": 1.0,
    "CGM_Average_Glucose": 152.0,
    "CGM_Glucose_CV": 38.0,
    "CGM_Time_In_Range": 58.0,
    "CGM_Time_Above_Range": 38.0,
    "CGM_Time_Below_Range": 4.0,
}

SAMPLE_GUT_TAXA_FEATURES = {
    "Akkermansia": 1.2,
    "Faecalibacterium": 4.5,
    "Roseburia": 3.1,
    "Bifidobacterium": 2.8,
    "Bacteroides": 18.4,
    "Prevotella": 8.5,
    "Ruminococcus": 5.2,
    "Blautia": 7.3,
    "Collinsella": 6.8,
    "Escherichia_Shigella": 4.2,
    "Coprococcus": 2.1,
    "Alistipes": 3.9,
    "Subdoligranulum": 2.4,
    "Enterococcus": 1.8,
    "Eubacterium": 3.6,
    "Parabacteroides": 2.9,
    "Lactobacillus": 1.5,
    "Klebsiella": 3.8,
    "Streptococcus": 2.7,
    "Eggerthella": 2.1,
    "Other_Taxa": 11.8,
}


# ── Test Suite 1: Feature Formatter & Metadata ───────────────────────────────

class TestFeatureFormatter:
    def test_clinical_metadata_and_formatting(self):
        meta = get_feature_meta("clinical", "Fasting_Blood_Glucose")
        assert meta["label"] == "Fasting Blood Glucose"
        assert meta["unit"] == "mg/dL"

        formatted = format_feature_value("clinical", "Fasting_Blood_Glucose", 135.4)
        assert formatted == "135 mg/dL"

        formatted_gender = format_feature_value("clinical", "Gender", 1.0)
        assert formatted_gender == "Male"

    def test_wearable_metadata_and_formatting(self):
        meta = get_feature_meta("wearable", "Average_Daily_Steps")
        assert meta["label"] == "Average Daily Steps"
        assert meta["unit"] == "steps/day"

        formatted = format_feature_value("wearable", "Average_Daily_Steps", 8500)
        assert formatted == "8,500 steps/day"

    def test_gut_taxa_metadata_and_clr_handling(self):
        # Base key
        meta = get_feature_meta("gut", "Faecalibacterium")
        assert meta["scientific_name"] == "Faecalibacterium prausnitzii"
        assert "butyrate" in meta["role"].lower()

        # Key with _CLR suffix
        meta_clr = get_feature_meta("gut", "Faecalibacterium_CLR")
        assert meta_clr["scientific_name"] == "Faecalibacterium prausnitzii"


# ── Test Suite 2: Level-0 TreeSHAP Explanations ──────────────────────────────

class TestTreeExplainer:
    @pytest.mark.parametrize("disease", [
        "Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk", "Metabolic_Syndrome", "NAFLD"
    ])
    def test_clinical_shap_all_diseases(self, disease):
        result = explain_domain_disease("clinical", disease, SAMPLE_CLINICAL_FEATURES)
        assert result["domain"] == "clinical"
        assert result["disease"] == disease
        assert "risk_drivers" in result
        assert "protective_factors" in result
        assert len(result["all_features"]) == 18

        # Check positive risk drivers
        for driver in result["risk_drivers"]:
            assert driver["shap_value"] > 0
            assert driver["direction"] == "increases_risk"
            assert "relative_impact_percentage" in driver

        # Check negative protective factors
        for protective in result["protective_factors"]:
            assert protective["shap_value"] < 0
            assert protective["direction"] == "reduces_risk"

    @pytest.mark.parametrize("disease", [
        "Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk", "Metabolic_Syndrome", "NAFLD"
    ])
    def test_wearable_shap_all_diseases(self, disease):
        result = explain_domain_disease("wearable", disease, SAMPLE_WEARABLE_FEATURES)
        assert result["domain"] == "wearable"
        assert len(result["all_features"]) == 15
        assert len(result["risk_drivers"]) <= 4
        assert len(result["protective_factors"]) <= 2

    def test_gut_shap_clr_handling(self):
        # Pass raw taxa (percentage summing to 100) -> TreeExplainer should handle CLR
        result = explain_domain_disease("gut", "Metabolic_Syndrome", SAMPLE_GUT_TAXA_FEATURES)
        assert result["domain"] == "gut"
        assert len(result["all_features"]) == 21
        # Check that display names and scientific names are populated
        feat_sample = result["all_features"][0]
        assert "scientific_name" in feat_sample
        assert feat_sample["scientific_name"] is not None


# ── Test Suite 3: Fusion Provenance and Strategy Deconstruction ──────────────

class TestFusionExplainer:
    def test_cg_lr_stacker_provenance(self):
        dis_info = {
            "risk_score": 0.78,
            "strategy": "pathway_c_g_stacker",
            "modalities_used": ["clinical", "gut"],
            "confidence_label": "FINAL_PREDICTION",
            "is_suppressed": False,
        }
        modality_evidence = {
            "clinical": {"status": "success", "probabilities": {"Metabolic_Syndrome": 0.82}},
            "gut": {"status": "success", "probabilities": {"Metabolic_Syndrome": 0.65}},
        }
        provenance = explain_provenance("Metabolic_Syndrome", dis_info, modality_evidence)
        assert provenance["type"] == "multi_modality_stacker"
        assert "clinical" in provenance["primary_modalities"]
        assert "gut" in provenance["primary_modalities"]

    def test_clinical_passthrough_provenance(self):
        dis_info = {
            "risk_score": 0.85,
            "strategy": "pathway_c_stacker",
            "modalities_used": ["clinical"],
            "confidence_label": "FINAL_PREDICTION",
            "is_suppressed": False,
        }
        modality_evidence = {"clinical": {"status": "success", "probabilities": {"Type2_Diabetes": 0.85}}}
        provenance = explain_provenance("Type2_Diabetes", dis_info, modality_evidence)
        assert provenance["type"] == "single_modality"
        assert provenance["primary_modalities"] == ["clinical"]

    def test_suppressed_prediabetes_provenance(self):
        dis_info = {
            "risk_score": 0.92,
            "strategy": "pathway_c_stacker",
            "modalities_used": ["clinical"],
            "confidence_label": "FINAL_PREDICTION",
            "is_suppressed": True,
        }
        provenance = explain_provenance("Prediabetes", dis_info, {})
        assert provenance["type"] == "suppressed_secondary"
        assert "suppressed" in provenance["headline"].lower()


# ── Test Suite 4: Wearable Contextual Decoupling ──────────────────────────────

class TestWearableEvidenceDecoupling:
    def test_wearable_decoupled_when_not_mathematical(self):
        # Disease is T2D with clinical passthrough
        dis_info = {
            "risk_score": 0.85,
            "strategy": "pathway_c_stacker",
            "modalities_used": ["clinical"],
            "wearable_evidence": {"raw_score": 0.74, "retained_for_xai": True},
        }
        modality_evidence = {
            "wearable": {"status": "success", "probabilities": {"Type2_Diabetes": 0.74}},
        }
        supporting = build_supporting_wearable_evidence(
            disease="Type2_Diabetes",
            disease_info=dis_info,
            modality_evidence=modality_evidence,
            wearable_feature_dict=SAMPLE_WEARABLE_FEATURES,
        )
        assert supporting["available"] is True
        assert supporting["is_mathematical_contributor"] is False
        assert supporting["raw_wearable_risk_percentage"] == 74.0
        assert len(supporting["top_signals"]) > 0

    def test_wearable_not_decoupled_when_already_primary(self):
        # Disease where wearable is the actual primary predictor
        dis_info = {
            "risk_score": 0.74,
            "strategy": "pathway_w_stacker",
            "modalities_used": ["wearable"],
        }
        supporting = build_supporting_wearable_evidence(
            disease="Type2_Diabetes",
            disease_info=dis_info,
            modality_evidence={},
            wearable_feature_dict=SAMPLE_WEARABLE_FEATURES,
        )
        assert supporting["available"] is False
        assert supporting["is_mathematical_contributor"] is True


# ── Test Suite 5: Dynamic Highest-Risk Selection & Tie-Breaking ──────────────

class TestHighestRiskSelection:
    def test_highest_risk_selection_clear_winner(self):
        engine = XAIEngine()
        contract2 = {
            "clinical": {"status": "complete", "values": {k: {"canonical_value": v} for k, v in SAMPLE_CLINICAL_FEATURES.items()}}
        }
        router = ModelRouter()
        router_out = router.route(contract2)
        fusion_out = fuse_predictions(router_out, patient_id="test_pat")

        xai_out = engine.explain_assessment(contract2, router_out, fusion_out)
        assert xai_out["has_usable_explanations"] is True
        assert xai_out["default_disease"] in ["Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk", "Metabolic_Syndrome", "NAFLD"]

    def test_suppressed_prediabetes_skipped_in_highest_risk(self):
        engine = XAIEngine()
        # Mock fusion output where Prediabetes risk is 99% but suppressed because T2D is positive (85%)
        fusion_out = {
            "diseases": {
                "Type2_Diabetes": {"risk_score": 0.85, "decision": True, "confidence_label": "FINAL_PREDICTION", "strategy": "pathway_c_stacker", "modalities_used": ["clinical"], "is_suppressed": False},
                "Prediabetes": {"risk_score": 0.99, "decision": False, "confidence_label": "FINAL_PREDICTION", "strategy": "pathway_c_stacker", "modalities_used": ["clinical"], "is_suppressed": True},
                "High_Adiposity_Risk": {"risk_score": 0.30, "decision": False, "confidence_label": "FINAL_PREDICTION", "strategy": "pathway_c_stacker", "modalities_used": ["clinical"], "is_suppressed": False},
                "Metabolic_Syndrome": {"risk_score": 0.40, "decision": False, "confidence_label": "FINAL_PREDICTION", "strategy": "pathway_c_stacker", "modalities_used": ["clinical"], "is_suppressed": False},
                "NAFLD": {"risk_score": 0.25, "decision": False, "confidence_label": "FINAL_PREDICTION", "strategy": "pathway_c_stacker", "modalities_used": ["clinical"], "is_suppressed": False},
            },
            "modality_evidence": {
                "clinical": {"status": "success", "probabilities": {"Type2_Diabetes": 0.85, "Prediabetes": 0.99, "High_Adiposity_Risk": 0.30, "Metabolic_Syndrome": 0.40, "NAFLD": 0.25}},
            }
        }
        contract2 = {
            "clinical": {"status": "complete", "values": {k: {"canonical_value": v} for k, v in SAMPLE_CLINICAL_FEATURES.items()}}
        }
        router_out = {"clinical": {"status": "success", "probabilities": {"Type2_Diabetes": 0.85, "Prediabetes": 0.99, "High_Adiposity_Risk": 0.30, "Metabolic_Syndrome": 0.40, "NAFLD": 0.25}}}

        xai_out = engine.explain_assessment(contract2, router_out, fusion_out)
        # Even though Prediabetes is 99%, T2D (85%) must be selected because Prediabetes is suppressed
        assert xai_out["default_disease"] == "Type2_Diabetes"

    def test_tie_breaking_order(self):
        engine = XAIEngine()
        # Mock identical scores for T2D and MetSyn (both 0.80)
        fusion_out = {
            "diseases": {
                "Type2_Diabetes": {"risk_score": 0.80, "decision": True, "confidence_label": "FINAL_PREDICTION", "strategy": "pathway_c_stacker", "modalities_used": ["clinical"], "is_suppressed": False},
                "Metabolic_Syndrome": {"risk_score": 0.80, "decision": True, "confidence_label": "FINAL_PREDICTION", "strategy": "pathway_c_stacker", "modalities_used": ["clinical"], "is_suppressed": False},
                "NAFLD": {"risk_score": 0.50, "decision": True, "confidence_label": "FINAL_PREDICTION", "strategy": "pathway_c_stacker", "modalities_used": ["clinical"], "is_suppressed": False},
                "High_Adiposity_Risk": {"risk_score": 0.30, "decision": False, "confidence_label": "FINAL_PREDICTION", "strategy": "pathway_c_stacker", "modalities_used": ["clinical"], "is_suppressed": False},
                "Prediabetes": {"risk_score": 0.20, "decision": False, "confidence_label": "FINAL_PREDICTION", "strategy": "pathway_c_stacker", "modalities_used": ["clinical"], "is_suppressed": False},
            },
            "modality_evidence": {
                "clinical": {"status": "success", "probabilities": {"Type2_Diabetes": 0.80, "Metabolic_Syndrome": 0.80, "NAFLD": 0.50, "High_Adiposity_Risk": 0.30, "Prediabetes": 0.20}},
            }
        }
        contract2 = {
            "clinical": {"status": "complete", "values": {k: {"canonical_value": v} for k, v in SAMPLE_CLINICAL_FEATURES.items()}}
        }
        xai_out = engine.explain_assessment(contract2, {}, fusion_out)
        # Priority order: T2D (priority 5) > MetSyn (priority 4) -> T2D wins tie
        assert xai_out["default_disease"] == "Type2_Diabetes"


# ── Test Suite 6: Full End-to-End Pipeline Integration ───────────────────────

class TestXAIEndToEndIntegration:
    def test_full_c_g_w_pipeline(self):
        engine = XAIEngine()
        router = ModelRouter()

        contract2 = {
            "clinical": {"status": "complete", "values": {k: {"canonical_value": v} for k, v in SAMPLE_CLINICAL_FEATURES.items()}},
            "wearable": {"status": "complete", "values": {k: {"canonical_value": v} for k, v in SAMPLE_WEARABLE_FEATURES.items()}},
            "gut": {"status": "complete", "values": {k: {"canonical_value": v} for k, v in SAMPLE_GUT_TAXA_FEATURES.items()}},
        }

        router_out = router.route(contract2)
        fusion_out = fuse_predictions(router_out, patient_id="pat_full_e2e")
        xai_out = engine.explain_assessment(contract2, router_out, fusion_out)

        assert xai_out["has_usable_explanations"] is True
        assert xai_out["default_disease"] is not None
        assert len(xai_out["explanations"]) == 5

        # Check MetSyn (combined C+G+W pathway stacker with all 3 modalities contributing)
        metsyn = xai_out["explanations"]["Metabolic_Syndrome"]
        assert metsyn["available"] is True
        assert metsyn["provenance"]["type"] == "multi_modality_stacker"
        assert metsyn["modalities"] is not None
        assert set(metsyn["modalities"].keys()) == {"clinical", "wearable", "gut"}
        assert metsyn["modalities"]["clinical"]["role"] == "primary_contributor"
        assert metsyn["modalities"]["gut"]["role"] == "primary_contributor"
        assert metsyn["modalities"]["wearable"]["role"] == "primary_contributor"

        # Verify Clinical TreeSHAP drivers exist and are non-empty for Metabolic Syndrome
        assert len(metsyn["modalities"]["clinical"]["risk_drivers"]) > 0
        assert len(metsyn["modalities"]["gut"]["risk_drivers"]) > 0
        assert len(metsyn["modalities"]["wearable"]["risk_drivers"]) > 0

        # Check Available Signals in Provenance
        sig_names = [s["name"] for s in metsyn["provenance"]["available_signals"]]
        assert "Clinical Model" in sig_names
        assert "Gut Model" in sig_names
        assert "Wearable Model" in sig_names

    def test_all_7_modality_combinations_roles_and_filters(self):
        engine = XAIEngine()
        router = ModelRouter()

        c_state = {"status": "complete", "values": {k: {"canonical_value": v} for k, v in SAMPLE_CLINICAL_FEATURES.items()}}
        w_state = {"status": "complete", "values": {k: {"canonical_value": v} for k, v in SAMPLE_WEARABLE_FEATURES.items()}}
        g_state = {"status": "complete", "values": {k: {"canonical_value": v} for k, v in SAMPLE_GUT_TAXA_FEATURES.items()}}

        combos = [
            ("1_clinical_only", {"clinical": c_state}, ["clinical"]),
            ("2_gut_only", {"gut": g_state}, ["gut"]),
            ("3_wearable_only", {"wearable": w_state}, ["wearable"]),
            ("4_clinical_gut", {"clinical": c_state, "gut": g_state}, ["clinical", "gut"]),
            ("5_clinical_wearable", {"clinical": c_state, "wearable": w_state}, ["clinical", "wearable"]),
            ("6_gut_wearable", {"gut": g_state, "wearable": w_state}, ["gut", "wearable"]),
            ("7_clinical_gut_wearable", {"clinical": c_state, "gut": g_state, "wearable": w_state}, ["clinical", "gut", "wearable"]),
        ]

        for name, c2, exp_mods in combos:
            r_out = router.route(c2)
            f_out = fuse_predictions(r_out, patient_id=f"test_{name}")
            x_out = engine.explain_assessment(c2, r_out, f_out)

            metsyn_exp = x_out["explanations"]["Metabolic_Syndrome"]
            if metsyn_exp["available"]:
                assert set(metsyn_exp["available_sources"]) == set(exp_mods), f"Failed for {name}"
                assert set(metsyn_exp["modalities"].keys()) == set(exp_mods), f"Failed for {name}"

                for m in exp_mods:
                    mod_info = metsyn_exp["modalities"][m]
                    assert mod_info["role"] == "primary_contributor", f"Expected primary for {m} in {name}"
                    assert mod_info["role_label"] == "PRIMARY"

    def test_insufficient_evidence_case(self):
        # Empty contract 2
        contract2 = {}
        router = ModelRouter()
        router_out = router.route(contract2)
        fusion_out = fuse_predictions(router_out, patient_id="pat_insufficient")

        engine = XAIEngine()
        xai_out = engine.explain_assessment(contract2, router_out, fusion_out)

        assert xai_out["has_usable_explanations"] is False
        assert xai_out["default_disease"] is None
        for dis_key, exp in xai_out["explanations"].items():
            assert exp["available"] is False
            assert exp["provenance"]["type"] == "insufficient"
