"""
predict_fusion.py — Production-Grade Fusion V1 Implementation Module

Implements the frozen multimodal Fusion V1 layer combining raw Level-0 outputs:
  - T2D: Clinical Passthrough (t=0.50)
  - Prediabetes: Clinical Passthrough (t=0.50) + Post-Decision Suppression (if T2D_pred==1 => Pred_pred=0)
  - High Adiposity Risk: Clinical Passthrough (t=0.50)
  - Metabolic Syndrome: Clinical+Gut LR Stacker (-4.3697124012 + 2.5798532189*P_Clin + 1.9638807682*P_Gut)
                         + Platt Scaling (1.5006 + 1.8243*Logit_raw) (t=0.20 post-Platt)
  - NAFLD: Clinical+Gut LR Stacker (-4.7670735247 + 3.7924128668*P_Clin + 2.8339984355*P_Gut) (t=0.50)
  - Wearable: Preserved as Level-0 independent output; excluded from Level-1 fusion.
"""

import os
import json
import warnings
import numpy as np
import pandas as pd
import joblib

warnings.filterwarnings("ignore")

# Frozen Coefficients
METSYN_LR_INTERCEPT = -4.3697124012
METSYN_LR_COEF_CLIN = 2.5798532189
METSYN_LR_COEF_GUT = 1.9638807682

METSYN_PLATT_INTERCEPT = 1.5006
METSYN_PLATT_SLOPE = 1.8243
METSYN_THRESHOLD = 0.20

NAFLD_LR_INTERCEPT = -4.7670735247
NAFLD_LR_COEF_CLIN = 3.7924128668
NAFLD_LR_COEF_GUT = 2.8339984355
NAFLD_THRESHOLD = 0.50

DISEASES = [
    "Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk",
    "Metabolic_Syndrome", "NAFLD"
]

MODALITIES = ["Clinical", "Gut", "Wearable"]


def sigmoid(x):
    """Numerically safe sigmoid function."""
    x_clip = np.clip(x, -50, 50)
    return 1.0 / (1.0 + np.exp(-x_clip))


class FusionV1Predictor:
    def __init__(self, models_dir=None):
        self.models_dir = models_dir
        self.metsyn_stacker = None
        self.nafld_stacker = None
        self._load_artifacts()

    def _load_artifacts(self):
        if self.models_dir and os.path.exists(self.models_dir):
            ms_path = os.path.join(self.models_dir, "stacker_Metabolic_Syndrome_Clinical+Gut.joblib")
            if os.path.exists(ms_path):
                try:
                    self.metsyn_stacker = joblib.load(ms_path)
                except Exception:
                    pass

            nf_path = os.path.join(self.models_dir, "stacker_NAFLD_Clinical+Gut.joblib")
            if os.path.exists(nf_path):
                try:
                    self.nafld_stacker = joblib.load(nf_path)
                except Exception:
                    pass

    def predict(self, clinical_df=None, gut_df=None, wearable_df=None, master_df=None):
        """
        Executes Fusion V1 predictions using explicit Patient_ID matching.

        Accepts either individual modality dataframes (clinical_df, gut_df, wearable_df)
        or a single aligned master_df containing Patient_ID and raw Level-0 probabilities.
        """
        if master_df is not None:
            df_merged = master_df.copy()
        else:
            if clinical_df is None:
                raise ValueError("clinical_df must be provided if master_df is None.")
            
            df_merged = clinical_df.copy()
            if "Patient_ID" not in df_merged.columns:
                raise ValueError("Patient_ID column missing from clinical_df!")

            if gut_df is not None:
                if "Patient_ID" not in gut_df.columns:
                    raise ValueError("Patient_ID column missing from gut_df!")
                df_merged = pd.merge(df_merged, gut_df, on="Patient_ID", how="left", suffixes=("", "_gut"))

            if wearable_df is not None:
                if "Patient_ID" not in wearable_df.columns:
                    raise ValueError("Patient_ID column missing from wearable_df!")
                df_merged = pd.merge(df_merged, wearable_df, on="Patient_ID", how="left", suffixes=("", "_wearable"))

        # Verify Patient_ID presence
        if "Patient_ID" not in df_merged.columns:
            raise ValueError("Patient_ID column missing from merged data!")

        # Normalize column names if needed
        # Expected column format: P_Clinical_<Disease> or Clinical_<Disease>_prob
        prob_cols = {}
        for mod in MODALITIES:
            for dis in DISEASES:
                target_key = f"P_{mod}_{dis}"
                alt_key1 = f"{mod}_{dis}_prob"
                alt_key2 = f"P_{mod}_{dis}"
                
                if alt_key1 in df_merged.columns:
                    prob_cols[target_key] = df_merged[alt_key1].values
                elif alt_key2 in df_merged.columns:
                    prob_cols[target_key] = df_merged[alt_key2].values
                else:
                    # Default 0.0 if modality is missing (e.g. standalone test)
                    prob_cols[target_key] = np.zeros(len(df_merged))

        # Output Dataframe Initialization
        out = pd.DataFrame({"Patient_ID": df_merged["Patient_ID"]})

        # Preserve Level-0 Raw Probabilities
        for k, v in prob_cols.items():
            out[k] = v

        # ─────────────────────────────────────────────
        # 1. Type 2 Diabetes Head (Clinical Passthrough, t=0.50)
        # ─────────────────────────────────────────────
        p_c_t2d = prob_cols["P_Clinical_Type2_Diabetes"]
        out["P_Fused_Type2_Diabetes"] = p_c_t2d
        out["Pred_Type2_Diabetes"] = (p_c_t2d >= 0.50).astype(int)
        out["Threshold_Type2_Diabetes"] = 0.50

        # ─────────────────────────────────────────────
        # 2. Prediabetes Head (Clinical Passthrough, t=0.50 + Suppression)
        # ─────────────────────────────────────────────
        p_c_pred = prob_cols["P_Clinical_Prediabetes"]
        out["P_Fused_Prediabetes"] = p_c_pred
        
        pred_pred_raw = (p_c_pred >= 0.50).astype(int)
        # Post-Decision Suppression Rule: if Pred_T2D == 1 => Pred_Prediabetes = 0
        pred_t2d = out["Pred_Type2_Diabetes"].values
        suppressed_mask = (pred_t2d == 1) & (pred_pred_raw == 1)
        pred_pred_final = np.where(pred_t2d == 1, 0, pred_pred_raw)

        out["Pred_Prediabetes_Raw"] = pred_pred_raw
        out["Pred_Prediabetes"] = pred_pred_final
        out["Prediabetes_Suppressed"] = suppressed_mask.astype(int)
        out["Threshold_Prediabetes"] = 0.50

        # ─────────────────────────────────────────────
        # 3. High Adiposity Risk Head (Clinical Passthrough, t=0.50)
        # ─────────────────────────────────────────────
        p_c_har = prob_cols["P_Clinical_High_Adiposity_Risk"]
        out["P_Fused_High_Adiposity_Risk"] = p_c_har
        out["Pred_High_Adiposity_Risk"] = (p_c_har >= 0.50).astype(int)
        out["Threshold_High_Adiposity_Risk"] = 0.50

        # ─────────────────────────────────────────────
        # 4. Metabolic Syndrome Head (Clinical+Gut LR Stacker + Platt Scaling, t=0.20)
        # ─────────────────────────────────────────────
        p_c_ms = prob_cols["P_Clinical_Metabolic_Syndrome"]
        p_g_ms = prob_cols["P_Gut_Metabolic_Syndrome"]

        if self.metsyn_stacker is not None:
            # Use loaded joblib artifact
            P_ms = np.column_stack([p_c_ms, p_g_ms])
            logit_raw_ms = self.metsyn_stacker.intercept_[0] + np.dot(P_ms, self.metsyn_stacker.coef_[0])
        else:
            # Use frozen exact float parameters
            logit_raw_ms = METSYN_LR_INTERCEPT + METSYN_LR_COEF_CLIN * p_c_ms + METSYN_LR_COEF_GUT * p_g_ms

        p_raw_ms = sigmoid(logit_raw_ms)

        # Platt Calibration
        logit_platt_ms = METSYN_PLATT_INTERCEPT + METSYN_PLATT_SLOPE * logit_raw_ms
        p_cal_ms = sigmoid(logit_platt_ms)

        out["P_Raw_LR_Metabolic_Syndrome"] = p_raw_ms
        out["P_Fused_Metabolic_Syndrome"] = p_cal_ms
        out["Pred_Metabolic_Syndrome"] = (p_cal_ms >= METSYN_THRESHOLD).astype(int)
        out["Threshold_Metabolic_Syndrome"] = METSYN_THRESHOLD

        # ─────────────────────────────────────────────
        # 5. NAFLD Head (Clinical+Gut LR Stacker, t=0.50)
        # ─────────────────────────────────────────────
        p_c_nf = prob_cols["P_Clinical_NAFLD"]
        p_g_nf = prob_cols["P_Gut_NAFLD"]

        if self.nafld_stacker is not None:
            P_nf = np.column_stack([p_c_nf, p_g_nf])
            logit_nf = self.nafld_stacker.intercept_[0] + np.dot(P_nf, self.nafld_stacker.coef_[0])
        else:
            logit_nf = NAFLD_LR_INTERCEPT + NAFLD_LR_COEF_CLIN * p_c_nf + NAFLD_LR_COEF_GUT * p_g_nf

        p_fused_nf = sigmoid(logit_nf)

        out["P_Fused_NAFLD"] = p_fused_nf
        out["Pred_NAFLD"] = (p_fused_nf >= NAFLD_THRESHOLD).astype(int)
        out["Threshold_NAFLD"] = NAFLD_THRESHOLD

        # Final numerical safety check: ensure all fused probabilities sit in [0.0, 1.0]
        fused_prob_cols = [
            "P_Fused_Type2_Diabetes", "P_Fused_Prediabetes",
            "P_Fused_High_Adiposity_Risk", "P_Fused_Metabolic_Syndrome",
            "P_Fused_NAFLD"
        ]
        for col in fused_prob_cols:
            out[col] = np.clip(out[col], 0.0, 1.0)

        return out


def predict_fusion_v1(master_df, models_dir=None):
    """Convenience functional wrapper for Fusion V1 prediction."""
    predictor = FusionV1Predictor(models_dir=models_dir)
    return predictor.predict(master_df=master_df)

