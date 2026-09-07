"""
audit_metsyn_policy.py — Pre-Freeze Correction Audit for Metabolic Syndrome Policy

Fits Platt scaling (Logistic Regression calibration) and Isotonic Regression on OOF Train predictions (n=14,000),
evaluates calibration metrics on Validation (n=3,000), and tunes decision threshold strictly on OOF Train.
"""

import os
import json
import warnings
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.isotonic import IsotonicRegression
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

lbl = "Metabolic_Syndrome"
y_oof = train_labels_df[lbl].values
y_val = val_labels_df[lbl].values

# Load fitted Clin+Gut LR Stacker
lr_stacker = joblib.load(os.path.join(PHASE2_DIR, "models", "fusion_candidates", f"stacker_{lbl}_Clinical+Gut.joblib"))

# Compute raw stacker probabilities
P_oof_cg = oof_df[[f"Clinical_{lbl}_prob", f"Gut_{lbl}_prob"]].values
P_val_cg = val_preds_df[[f"Clinical_{lbl}_prob", f"Gut_{lbl}_prob"]].values

p_oof_raw = lr_stacker.predict_proba(P_oof_cg)[:, 1]
p_val_raw = lr_stacker.predict_proba(P_val_cg)[:, 1]

print("=== 1. RAW STACKER PERFORMANCE ===")
print(f"OOF Train ROC-AUC: {roc_auc_score(y_oof, p_oof_raw):.4f}, PR-AUC: {average_precision_score(y_oof, p_oof_raw):.4f}")
print(f"Val Set ROC-AUC:   {roc_auc_score(y_val, p_val_raw):.4f}, PR-AUC:   {average_precision_score(y_val, p_val_raw):.4f}")

# Threshold Grid Search on OOF Train (Strictly train-only selection)
best_t_oof = 0.5
best_f1_oof = 0.0
threshold_grid = np.linspace(0.01, 0.50, 50)

print("\n--- OOF Train Threshold Search ---")
for t in threshold_grid:
    y_pred_oof = (p_oof_raw >= t).astype(int)
    f1_t = f1_score(y_oof, y_pred_oof, zero_division=0)
    if f1_t > best_f1_oof:
        best_f1_oof = f1_t
        best_t_oof = t

print(f"Optimal Decision Threshold Selected on OOF Train: t* = {best_t_oof:.4f} (OOF F1 = {best_f1_oof:.4f})")

# Evaluate OOF-selected threshold on Validation (Decision-blind selection)
y_pred_val_t = (p_val_raw >= best_t_oof).astype(int)
val_f1 = f1_score(y_val, y_pred_val_t, zero_division=0)
val_prec = precision_score(y_val, y_pred_val_t, zero_division=0)
val_rec = recall_score(y_val, y_pred_val_t, zero_division=0)

print("\n--- Validation Performance at OOF-Selected Threshold (t* = {:.4f}) ---".format(best_t_oof))
print(f"Val F1: {val_f1:.4f}, Precision: {val_prec:.4f}, Recall: {val_rec:.4f}, Positive Count: {np.sum(y_pred_val_t)}")

# ─────────────────────────────────────────────
# 2. PLATT SCALING RECALIBRATION ON OOF TRAIN
# ─────────────────────────────────────────────
print("\n=== 2. PLATT SCALING RECALIBRATION ===")
# Fit Platt scaling (Logistic Regression on logit of raw probabilities) on OOF Train
eps = 1e-7
logit_oof = np.log(np.clip(p_oof_raw, eps, 1-eps) / np.clip(1-p_oof_raw, eps, 1-eps)).reshape(-1, 1)
logit_val = np.log(np.clip(p_val_raw, eps, 1-eps) / np.clip(1-p_val_raw, eps, 1-eps)).reshape(-1, 1)

platt_calibrator = LogisticRegression(penalty=None, solver='lbfgs')
platt_calibrator.fit(logit_oof, y_oof)

p_oof_platt = platt_calibrator.predict_proba(logit_oof)[:, 1]
p_val_platt = platt_calibrator.predict_proba(logit_val)[:, 1]

print(f"Platt Calibrator Parameters (fit on OOF Train): Slope = {platt_calibrator.coef_[0][0]:.4f}, Intercept = {platt_calibrator.intercept_[0]:.4f}")

brier_raw_val = brier_score_loss(y_val, p_val_raw)
brier_platt_val = brier_score_loss(y_val, p_val_platt)

print(f"Raw Stacker Val Brier Score:   {brier_raw_val:.4f}")
print(f"Platt Calibrated Val Brier:   {brier_platt_val:.4f}")
print(f"Val ROC-AUC after Platt:       {roc_auc_score(y_val, p_val_platt):.4f} (Unchanged, as Platt is strictly monotonic)")
print(f"Val PR-AUC after Platt:        {average_precision_score(y_val, p_val_platt):.4f}")

# Threshold on Platt Calibrated probabilities (OOF Train tuning)
best_t_platt_oof = 0.5
best_f1_platt_oof = 0.0
for t in threshold_grid:
    y_pred_platt_oof = (p_oof_platt >= t).astype(int)
    f1_p = f1_score(y_oof, y_pred_platt_oof, zero_division=0)
    if f1_p > best_f1_platt_oof:
        best_f1_platt_oof = f1_p
        best_t_platt_oof = t

y_pred_val_platt = (p_val_platt >= best_t_platt_oof).astype(int)
print(f"Optimal Threshold on Platt-Calibrated OOF Train: t_platt* = {best_t_platt_oof:.4f}")
print(f"Val Performance (Platt @ t_platt*): F1 = {f1_score(y_val, y_pred_val_platt):.4f}, Prec = {precision_score(y_val, y_pred_val_platt):.4f}, Rec = {recall_score(y_val, y_pred_val_platt):.4f}")

# ─────────────────────────────────────────────
# 3. NAFLD Calibration & Threshold Verification
# ─────────────────────────────────────────────
print("\n=== 3. NAFLD STACKER POLICY VERIFICATION ===")
lbl_n = "NAFLD"
lr_nafld = joblib.load(os.path.join(PHASE2_DIR, "models", "fusion_candidates", f"stacker_{lbl_n}_Clinical+Gut.joblib"))
p_val_nafld = lr_nafld.predict_proba(val_preds_df[[f"Clinical_{lbl_n}_prob", f"Gut_{lbl_n}_prob"]].values)[:, 1]
y_val_nafld = val_labels_df[lbl_n].values

brier_nafld = brier_score_loss(y_val_nafld, p_val_nafld)
y_pred_nafld_05 = (p_val_nafld >= 0.5).astype(int)

print(f"NAFLD Clin+Gut LR Stacker (Threshold = 0.50):")
print(f"  ROC-AUC: {roc_auc_score(y_val_nafld, p_val_nafld):.4f}")
print(f"  PR-AUC:  {average_precision_score(y_val_nafld, p_val_nafld):.4f}")
print(f"  F1:      {f1_score(y_val_nafld, y_pred_nafld_05):.4f}")
print(f"  Prec:    {precision_score(y_val_nafld, y_pred_nafld_05):.4f}")
print(f"  Rec:     {recall_score(y_val_nafld, y_pred_nafld_05):.4f}")
print(f"  Brier:   {brier_nafld:.4f}")

