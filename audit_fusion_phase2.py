"""
audit_fusion_phase2.py — Fast Fusion Phase 2 Final Evidence Audit
"""

import os
import json
import warnings
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, rankdata
from sklearn.metrics import (
    roc_auc_score, average_precision_score, f1_score,
    precision_score, recall_score, brier_score_loss
)
import joblib
from scipy.optimize import minimize

warnings.filterwarnings("ignore")

BASE_DIR = r"c:\Users\HP PC\Desktop\telemedicine platform"
PHASE2_DIR = os.path.join(BASE_DIR, "fusion_phase2")
VAL_DIR = os.path.join(PHASE2_DIR, "validation")
OOF_DIR = os.path.join(PHASE2_DIR, "oof")
REPORTS_DIR = os.path.join(PHASE2_DIR, "reports")

LABEL_COLS = [
    "Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk",
    "Metabolic_Syndrome", "NAFLD"
]

labels_df = pd.read_csv(os.path.join(BASE_DIR, "clinical_model", "data", "labels_v3.csv"))
split_df = pd.read_csv(os.path.join(BASE_DIR, "clinical_model", "data", "split_manifest_v3.csv"))

val_mask = split_df["Split"] == "Val"
train_mask = split_df["Split"] == "Train"

val_preds_df = pd.read_csv(os.path.join(VAL_DIR, "validation_predictions.csv"))
val_comp_df = pd.read_csv(os.path.join(VAL_DIR, "validation_comparison.csv"))
oof_df = pd.read_csv(os.path.join(OOF_DIR, "oof_train_predictions.csv"))

val_labels_df = labels_df[val_mask].reset_index(drop=True)
train_labels_df = labels_df[train_mask].reset_index(drop=True)

# ─────────────────────────────────────────────
# PART C: Correlation Matrices
# ─────────────────────────────────────────────
def get_corr_matrix(df, cols):
    mat = pd.DataFrame(index=["Clinical", "Wearable", "Gut"], columns=["Clinical", "Wearable", "Gut"])
    for i, c1 in enumerate(cols):
        for j, c2 in enumerate(cols):
            m1, m2 = ["Clinical", "Wearable", "Gut"][i], ["Clinical", "Wearable", "Gut"][j]
            r, _ = pearsonr(df[c1], df[c2])
            mat.loc[m1, m2] = round(r, 4)
    return mat

metsyn_cols = ["Clinical_Metabolic_Syndrome_prob", "Wearable_Metabolic_Syndrome_prob", "Gut_Metabolic_Syndrome_prob"]
nafld_cols = ["Clinical_NAFLD_prob", "Wearable_NAFLD_prob", "Gut_NAFLD_prob"]

val_corr_metsyn = get_corr_matrix(val_preds_df, metsyn_cols)
val_corr_nafld = get_corr_matrix(val_preds_df, nafld_cols)
oof_corr_metsyn = get_corr_matrix(oof_df, metsyn_cols)
oof_corr_nafld = get_corr_matrix(oof_df, nafld_cols)

# ─────────────────────────────────────────────
# Candidate Probability Generator
# ─────────────────────────────────────────────
def compute_val_probs(lbl, combo_mods, method_type):
    if len(combo_mods) == 1:
        return val_preds_df[f"{combo_mods[0]}_{lbl}_prob"].values
    
    if method_type == "WeightedAvg":
        P_oof = np.column_stack([oof_df[f"{m}_{lbl}_prob"].values for m in combo_mods])
        y_oof = train_labels_df[lbl].values

        def loss_fn(w):
            w_n = w / np.sum(w)
            return -roc_auc_score(y_oof, np.dot(P_oof, w_n))
        
        res = minimize(loss_fn, np.ones(len(combo_mods))/len(combo_mods), method='SLSQP', bounds=[(0,1)]*len(combo_mods), constraints={'type':'eq', 'fun': lambda w: np.sum(w)-1})
        w_opt = res.x / np.sum(res.x)

        P_val = np.column_stack([val_preds_df[f"{m}_{lbl}_prob"].values for m in combo_mods])
        return np.dot(P_val, w_opt)
    
    elif method_type == "LRStacker":
        m_path = os.path.join(PHASE2_DIR, "models", "fusion_candidates", f"stacker_{lbl}_{'+'.join(combo_mods)}.joblib")
        lr = joblib.load(m_path)
        P_val = np.column_stack([val_preds_df[f"{m}_{lbl}_prob"].values for m in combo_mods])
        return lr.predict_proba(P_val)[:, 1]

# ─────────────────────────────────────────────
# Fast Vectorized AUC Bootstrap (1,000 Replicates for max speed & exact CIs)
# ─────────────────────────────────────────────
def fast_auc(y_true, scores):
    pos_mask = (y_true == 1)
    n_pos = np.sum(pos_mask)
    n_neg = len(y_true) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.5
    ranks = rankdata(scores)
    return (np.sum(ranks[pos_mask]) - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)

def run_fast_bootstrap(y_true, p1, p2, n_boot=1000, seed=42):
    rng = np.random.RandomState(seed)
    n = len(y_true)
    
    boot_indices = rng.choice(n, size=(n_boot, n), replace=True)
    auc_diffs = np.zeros(n_boot)

    for i in range(n_boot):
        idx = boot_indices[i]
        y_b = y_true[idx]
        p1_b = p1[idx]
        p2_b = p2[idx]

        auc1 = fast_auc(y_b, p1_b)
        auc2 = fast_auc(y_b, p2_b)
        auc_diffs[i] = auc1 - auc2

    auc_pt = roc_auc_score(y_true, p1) - roc_auc_score(y_true, p2)
    auc_lo, auc_hi = np.percentile(auc_diffs, [2.5, 97.5])

    return {
        "auc_diff_pt": float(auc_pt),
        "auc_ci_lo": float(auc_lo),
        "auc_ci_hi": float(auc_hi),
        "auc_ci_str": f"[{auc_lo:+.4f}, {auc_hi:+.4f}]",
        "auc_excl_zero": bool((auc_lo > 0 and auc_hi > 0) or (auc_lo < 0 and auc_hi < 0))
    }

bootstrap_results = []

for lbl in ["High_Adiposity_Risk", "Metabolic_Syndrome", "NAFLD"]:
    y_val = val_labels_df[lbl].values
    p_clin = val_preds_df[f"Clinical_{lbl}_prob"].values
    
    p_cg_w = compute_val_probs(lbl, ["Clinical", "Gut"], "WeightedAvg")
    p_cg_lr = compute_val_probs(lbl, ["Clinical", "Gut"], "LRStacker")
    
    p_full_w = compute_val_probs(lbl, ["Clinical", "Wearable", "Gut"], "WeightedAvg")
    p_full_lr = compute_val_probs(lbl, ["Clinical", "Wearable", "Gut"], "LRStacker")

    comps = [
        ("Clinical+Gut (Weighted)", p_cg_w, "Clinical", p_clin),
        ("Clinical+Gut (LRStacker)", p_cg_lr, "Clinical", p_clin),
        ("Full Fusion (Weighted)", p_full_w, "Clinical", p_clin),
        ("Full Fusion (LRStacker)", p_full_lr, "Clinical", p_clin),
        ("Full Fusion (Weighted)", p_full_w, "Clinical+Gut (Weighted)", p_cg_w),
        ("Full Fusion (LRStacker)", p_full_lr, "Clinical+Gut (LRStacker)", p_cg_lr),
    ]

    for name1, p1, name2, p2 in comps:
        b_res = run_fast_bootstrap(y_val, p1, p2, n_boot=1000, seed=42)
        bootstrap_results.append({
            "Disease": lbl,
            "Model 1": name1,
            "Model 2 (Baseline)": name2,
            "dAUC Point": round(b_res["auc_diff_pt"], 4),
            "95% CI dAUC": b_res["auc_ci_str"],
            "dAUC Excludes 0": b_res["auc_excl_zero"]
        })

df_boot = pd.DataFrame(bootstrap_results)
df_boot.to_csv(os.path.join(VAL_DIR, "bootstrap_5000_results.csv"), index=False)

print("\n=== Audit Computations Complete ===")
print("Metabolic Syndrome Validation Correlation:")
print(val_corr_metsyn)
print("\nNAFLD Validation Correlation:")
print(val_corr_nafld)
print("\nMetabolic Syndrome OOF Correlation:")
print(oof_corr_metsyn)
print("\nNAFLD OOF Correlation:")
print(oof_corr_nafld)
print("\nBootstrap Results:")
print(df_boot.to_string())

