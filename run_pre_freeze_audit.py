"""
run_pre_freeze_audit.py — Final Pre-Freeze Audit Script

Audits:
  - MetSyn LR stacker F1=0 at threshold 0.5 (probability distribution breakdown)
  - Monotonicity & finiteness of Clin+Gut LR stacker probabilities for MetSyn and NAFLD
  - Calibration breakdown: Discrimination (AUC/PR) vs Probability Error (Brier) vs Reliability (Slope/Intercept)
  - Verification of paired bootstrap CIs from saved artifacts
"""

import os
import json
import warnings
import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    roc_auc_score, average_precision_score, f1_score,
    precision_score, recall_score, brier_score_loss
)
import joblib

warnings.filterwarnings("ignore")

BASE_DIR = r"c:\Users\HP PC\Desktop\telemedicine platform"
PHASE2_DIR = os.path.join(BASE_DIR, "fusion_phase2")
VAL_DIR = os.path.join(PHASE2_DIR, "validation")
OOF_DIR = os.path.join(PHASE2_DIR, "oof")

labels_df = pd.read_csv(os.path.join(BASE_DIR, "clinical_model", "data", "labels_v3.csv"))
split_df = pd.read_csv(os.path.join(BASE_DIR, "clinical_model", "data", "split_manifest_v3.csv"))

val_mask = split_df["Split"] == "Val"
train_mask = split_df["Split"] == "Train"

val_preds_df = pd.read_csv(os.path.join(VAL_DIR, "validation_predictions.csv"))
oof_df = pd.read_csv(os.path.join(OOF_DIR, "oof_train_predictions.csv"))

val_labels_df = labels_df[val_mask].reset_index(drop=True)
train_labels_df = labels_df[train_mask].reset_index(drop=True)

print("=== 1. MetSyn LR Stacker Probability Audit ===")
y_val_metsyn = val_labels_df["Metabolic_Syndrome"].values
lr_metsyn = joblib.load(os.path.join(PHASE2_DIR, "models", "fusion_candidates", "stacker_Metabolic_Syndrome_Clinical+Gut.joblib"))

P_val_metsyn = val_preds_df[["Clinical_Metabolic_Syndrome_prob", "Gut_Metabolic_Syndrome_prob"]].values
probs_metsyn = lr_metsyn.predict_proba(P_val_metsyn)[:, 1]

print(f"MetSyn Prevalence in Val: {np.mean(y_val_metsyn)*100:.2f}% ({np.sum(y_val_metsyn)} / {len(y_val_metsyn)})")
print(f"MetSyn LR Intercept: {lr_metsyn.intercept_[0]:.4f}")
print(f"MetSyn LR Coefficients: Clin = {lr_metsyn.coef_[0][0]:.4f}, Gut = {lr_metsyn.coef_[0][1]:.4f}")
print(f"Probability Summary (Min, 25%, 50%, 75%, Max):")
print(f"  Min: {np.min(probs_metsyn):.4f}")
print(f"  25%: {np.percentile(probs_metsyn, 25):.4f}")
print(f"  50%: {np.median(probs_metsyn):.4f}")
print(f"  75%: {np.percentile(probs_metsyn, 75):.4f}")
print(f"  Max: {np.max(probs_metsyn):.4f}")
print(f"  Count >= 0.5: {np.sum(probs_metsyn >= 0.5)} / {len(probs_metsyn)}")
print(f"  Max probability achieved: {np.max(probs_metsyn):.4f}")

# Threshold analysis for MetSyn
print("\nMetSyn Performance at Various Thresholds:")
for t in [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]:
    y_pred = (probs_metsyn >= t).astype(int)
    f1 = f1_score(y_val_metsyn, y_pred, zero_division=0)
    prec = precision_score(y_val_metsyn, y_pred, zero_division=0)
    rec = recall_score(y_val_metsyn, y_pred, zero_division=0)
    print(f"  Threshold {t:.2f} -> F1: {f1:.4f}, Prec: {prec:.4f}, Rec: {rec:.4f}, Positive Preds: {np.sum(y_pred)}")

print("\n=== 2. Monotonicity & Finiteness Check ===")
for lbl in ["Metabolic_Syndrome", "NAFLD"]:
    lr = joblib.load(os.path.join(PHASE2_DIR, "models", "fusion_candidates", f"stacker_{lbl}_Clinical+Gut.joblib"))
    P_val = val_preds_df[[f"Clinical_{lbl}_prob", f"Gut_{lbl}_prob"]].values
    p_out = lr.predict_proba(P_val)[:, 1]
    
    is_finite = np.all(np.isfinite(p_out))
    in_range = np.all((p_out >= 0.0) & (p_out <= 1.0))
    
    # Monotonicity check: derivative w.r.t input probabilities
    w_clin, w_gut = lr.coef_[0]
    is_monotonic = (w_clin > 0) and (w_gut > 0)
    
    print(f"{lbl} Clin+Gut LR Stacker:")
    print(f"  Finite: {is_finite}")
    print(f"  Bounded [0, 1]: {in_range}")
    print(f"  Monotonic w.r.t Inputs (Weights > 0): {is_monotonic} (Clin: {w_clin:+.4f}, Gut: {w_gut:+.4f})")

print("\n=== 3. Calibration Audit Breakdown ===")
def audit_calibration(y_true, y_prob):
    eps = 1e-7
    p_clip = np.clip(y_prob, eps, 1 - eps)
    logit_p = np.log(p_clip / (1 - p_clip)).reshape(-1, 1)
    lr_cal = LogisticRegression(penalty=None, solver='lbfgs')
    lr_cal.fit(logit_p, y_true)
    slope = float(lr_cal.coef_[0][0])
    intercept = float(lr_cal.intercept_[0])
    brier = brier_score_loss(y_true, y_prob)
    roc = roc_auc_score(y_true, y_prob)
    pr = average_precision_score(y_true, y_prob)
    return roc, pr, brier, slope, intercept

for lbl in ["Metabolic_Syndrome", "NAFLD"]:
    y_v = val_labels_df[lbl].values
    p_clin = val_preds_df[f"Clinical_{lbl}_prob"].values
    lr = joblib.load(os.path.join(PHASE2_DIR, "models", "fusion_candidates", f"stacker_{lbl}_Clinical+Gut.joblib"))
    p_cg = lr.predict_proba(val_preds_df[[f"Clinical_{lbl}_prob", f"Gut_{lbl}_prob"]].values)[:, 1]

    roc_c, pr_c, br_c, sl_c, ic_c = audit_calibration(y_v, p_clin)
    roc_cg, pr_cg, br_cg, sl_cg, ic_cg = audit_calibration(y_v, p_cg)

    print(f"\n--- {lbl} Calibration Audit ---")
    print(f"  Clinical Single -> ROC: {roc_c:.4f}, PR: {pr_c:.4f}, Brier: {br_c:.4f}, Calib Slope: {sl_c:.4f}, Intercept: {ic_c:.4f}")
    print(f"  Clin+Gut LR     -> ROC: {roc_cg:.4f}, PR: {pr_cg:.4f}, Brier: {br_cg:.4f}, Calib Slope: {sl_cg:.4f}, Intercept: {ic_cg:.4f}")

