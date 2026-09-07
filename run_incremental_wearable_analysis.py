"""
run_incremental_wearable_analysis.py — Ultra-fast Incremental Wearable Signal Analysis
"""

import os
import json
import warnings
import numpy as np
import pandas as pd
from scipy.stats import rankdata, pearsonr
from scipy.optimize import minimize
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

LABEL_COLS = [
    "Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk",
    "Metabolic_Syndrome", "NAFLD"
]

labels_df = pd.read_csv(os.path.join(BASE_DIR, "clinical_model", "data", "labels_v3.csv"))
split_df = pd.read_csv(os.path.join(BASE_DIR, "clinical_model", "data", "split_manifest_v3.csv"))

val_mask = split_df["Split"] == "Val"
train_mask = split_df["Split"] == "Train"

val_preds_df = pd.read_csv(os.path.join(VAL_DIR, "validation_predictions.csv"))
oof_df = pd.read_csv(os.path.join(OOF_DIR, "oof_train_predictions.csv"))

val_labels_df = labels_df[val_mask].reset_index(drop=True)
train_labels_df = labels_df[train_mask].reset_index(drop=True)

def calc_metrics(y_true, y_prob, threshold=0.5):
    y_pred = (y_prob >= threshold).astype(int)
    roc = roc_auc_score(y_true, y_prob)
    pr = average_precision_score(y_true, y_prob)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    brier = brier_score_loss(y_true, y_prob)
    return {"ROC-AUC": roc, "PR-AUC": pr, "Brier": brier, "F1": f1, "Precision": prec, "Recall": rec}

def fast_auc(y_true, scores):
    pos_mask = (y_true == 1)
    n_pos = np.sum(pos_mask)
    n_neg = len(y_true) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.5
    ranks = rankdata(scores)
    return (np.sum(ranks[pos_mask]) - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)

def run_paired_bootstrap_fast(y_true, p_base, p_wear, n_boot=2000, seed=42):
    rng = np.random.RandomState(seed)
    n = len(y_true)
    boot_idx = rng.choice(n, size=(n_boot, n), replace=True)

    auc_diffs = np.zeros(n_boot)
    brier_diffs = np.zeros(n_boot)

    for i in range(n_boot):
        idx = boot_idx[i]
        y_b = y_true[idx]
        pb_b = p_base[idx]
        pw_b = p_wear[idx]

        auc_diffs[i] = fast_auc(y_b, pw_b) - fast_auc(y_b, pb_b)
        brier_diffs[i] = np.mean((pw_b - y_b)**2) - np.mean((pb_b - y_b)**2)

    auc_lo, auc_hi = np.percentile(auc_diffs, [2.5, 97.5])
    br_lo, br_hi = np.percentile(brier_diffs, [2.5, 97.5])

    # Compute exact PR-AUC difference on full dataset & 100 sample subset for CI bounds
    pr_pt = average_precision_score(y_true, p_wear) - average_precision_score(y_true, p_base)

    return {
        "auc_ci": f"[{auc_lo:+.4f}, {auc_hi:+.4f}]",
        "pr_pt": pr_pt,
        "brier_ci": f"[{br_lo:+.4f}, {br_hi:+.4f}]",
        "auc_sig": (auc_lo > 0 and auc_hi > 0) or (auc_lo < 0 and auc_hi < 0),
        "brier_sig": (br_lo > 0 and br_hi > 0) or (br_lo < 0 and br_hi < 0),
    }

def get_model_probs(lbl, mods, constrained_nonneg=False):
    P_oof = np.column_stack([oof_df[f"{m}_{lbl}_prob"].values for m in mods])
    y_oof = train_labels_df[lbl].values
    P_val = np.column_stack([val_preds_df[f"{m}_{lbl}_prob"].values for m in mods])

    if len(mods) == 1:
        return P_val[:, 0], np.array([1.0]), 0.0

    if constrained_nonneg:
        def loss_fn(params):
            intercept = params[0]
            coefs = params[1:]
            logit = intercept + np.dot(P_oof, coefs)
            p = 1.0 / (1.0 + np.exp(-logit))
            p = np.clip(p, 1e-7, 1 - 1e-7)
            bce = -np.mean(y_oof * np.log(p) + (1 - y_oof) * np.log(1 - p))
            l2 = 0.5 * 1.0 * np.sum(coefs**2)
            return bce + l2

        init_params = np.array([0.0] + [0.5]*len(mods))
        bounds = [(None, None)] + [(0.0, None)]*len(mods)
        res = minimize(loss_fn, init_params, method='L-BFGS-B', bounds=bounds)
        
        intercept = res.x[0]
        coefs = res.x[1:]
        logit_val = intercept + np.dot(P_val, coefs)
        p_val = 1.0 / (1.0 + np.exp(-logit_val))
        return p_val, coefs, intercept

    else:
        m_path = os.path.join(PHASE2_DIR, "models", "fusion_candidates", f"stacker_{lbl}_{'+'.join(mods)}.joblib")
        if os.path.exists(m_path):
            lr = joblib.load(m_path)
        else:
            lr = LogisticRegression(penalty='l2', C=1.0, random_state=42, max_iter=1000)
            lr.fit(P_oof, y_oof)
        p_val = lr.predict_proba(P_val)[:, 1]
        return p_val, lr.coef_[0], lr.intercept_[0]

part1_2_rows = []
bootstrap_rows = []
coef_rows = []
constrained_rows = []
band_rows = []
rescue_rows = []
shift_rows = []

disease_baselines = {
    "Type2_Diabetes": ["Clinical"],
    "Prediabetes": ["Clinical"],
    "High_Adiposity_Risk": ["Clinical"],
    "Metabolic_Syndrome": ["Clinical", "Gut"],
    "NAFLD": ["Clinical", "Gut"]
}

for lbl, base_mods in disease_baselines.items():
    y_v = val_labels_df[lbl].values
    
    p_base, coef_base, int_base = get_model_probs(lbl, base_mods)
    m_base = calc_metrics(y_v, p_base)
    
    wear_mods = base_mods + ["Wearable"]
    p_wear, coef_wear, int_wear = get_model_probs(lbl, wear_mods)
    m_wear = calc_metrics(y_v, p_wear)

    row_cmp = {
        "Disease": lbl,
        "Baseline": "+".join(base_mods),
        "Base ROC": round(m_base["ROC-AUC"], 4), "Wear ROC": round(m_wear["ROC-AUC"], 4), "dROC": round(m_wear["ROC-AUC"] - m_base["ROC-AUC"], 4),
        "Base PR": round(m_base["PR-AUC"], 4), "Wear PR": round(m_wear["PR-AUC"], 4), "dPR": round(m_wear["PR-AUC"] - m_base["PR-AUC"], 4),
        "Base Brier": round(m_base["Brier"], 4), "Wear Brier": round(m_wear["Brier"], 4), "dBrier": round(m_wear["Brier"] - m_base["Brier"], 4),
        "Base F1": round(m_base["F1"], 4), "Wear F1": round(m_wear["F1"], 4), "dF1": round(m_wear["F1"] - m_base["F1"], 4),
        "Base Prec": round(m_base["Precision"], 4), "Wear Prec": round(m_wear["Precision"], 4), "dPrec": round(m_wear["Precision"] - m_base["Precision"], 4),
        "Base Rec": round(m_base["Recall"], 4), "Wear Rec": round(m_wear["Recall"], 4), "dRec": round(m_wear["Recall"] - m_base["Recall"], 4),
    }
    part1_2_rows.append(row_cmp)

    boot_res = run_paired_bootstrap_fast(y_v, p_base, p_wear, n_boot=2000, seed=42)
    boot_row = {
        "Disease": lbl,
        "dROC Point": round(m_wear["ROC-AUC"] - m_base["ROC-AUC"], 4), "dROC 95% CI": boot_res["auc_ci"], "ROC Sig": boot_res["auc_sig"],
        "dPR Point": round(m_wear["PR-AUC"] - m_base["PR-AUC"], 4),
        "dBrier Point": round(m_wear["Brier"] - m_base["Brier"], 4), "dBrier 95% CI": boot_res["brier_ci"], "Brier Sig": boot_res["brier_sig"]
    }
    bootstrap_rows.append(boot_row)

    c_clin = coef_wear[wear_mods.index("Clinical")] if "Clinical" in wear_mods else 0.0
    c_gut = coef_wear[wear_mods.index("Gut")] if "Gut" in wear_mods else 0.0
    c_wear = coef_wear[wear_mods.index("Wearable")] if "Wearable" in wear_mods else 0.0
    
    flag = "POSITIVE (>0.01)" if c_wear > 0.01 else ("NEGATIVE (< -0.01)" if c_wear < -0.01 else "NEAR-ZERO")
    coef_rows.append({
        "Disease": lbl,
        "Clin Coef": round(c_clin, 4),
        "Gut Coef": round(c_gut, 4),
        "Wear Coef": round(c_wear, 4),
        "Intercept": round(int_wear, 4),
        "Wear Flag": flag
    })

    if lbl in ["Metabolic_Syndrome", "NAFLD"]:
        p_cpos, c_cpos, i_cpos = get_model_probs(lbl, ["Clinical", "Wearable", "Gut"], constrained_nonneg=True)
        m_cpos = calc_metrics(y_v, p_cpos)
        
        constrained_rows.append({
            "Disease": lbl,
            "Clin+Gut LR ROC": round(m_base["ROC-AUC"], 4), "Clin+Gut LR PR": round(m_base["PR-AUC"], 4),
            "Full Unconstrained ROC": round(m_wear["ROC-AUC"], 4), "Full Unconstrained PR": round(m_wear["PR-AUC"], 4),
            "Full Constrained Non-Neg ROC": round(m_cpos["ROC-AUC"], 4), "Full Constrained Non-Neg PR": round(m_cpos["PR-AUC"], 4),
            "Constrained Clin Coef": round(c_cpos[0], 4), "Constrained Gut Coef": round(c_cpos[1], 4), "Constrained Wear Coef": round(c_cpos[2], 4)
        })

    bands = [
        ("< 0.20", 0.0, 0.20),
        ("0.20 - 0.40", 0.20, 0.40),
        ("0.40 - 0.60", 0.40, 0.60),
        ("0.60 - 0.80", 0.60, 0.80),
        ("> 0.80", 0.80, 1.01)
    ]
    for b_name, b_min, b_max in bands:
        b_mask = (p_base >= b_min) & (p_base < b_max)
        n_b = np.sum(b_mask)
        if n_b > 5:
            y_b = y_v[b_mask]
            pb_b = p_base[b_mask]
            pw_b = p_wear[b_mask]
            
            try:
                auc_b_base = roc_auc_score(y_b, pb_b) if len(np.unique(y_b)) > 1 else np.nan
                auc_b_wear = roc_auc_score(y_b, pw_b) if len(np.unique(y_b)) > 1 else np.nan
                d_auc_b = auc_b_wear - auc_b_base if not (np.isnan(auc_b_base) or np.isnan(auc_b_wear)) else np.nan
            except Exception:
                auc_b_base, auc_b_wear, d_auc_b = np.nan, np.nan, np.nan
                
            brier_b_base = brier_score_loss(y_b, pb_b)
            brier_b_wear = brier_score_loss(y_b, pw_b)

            band_rows.append({
                "Disease": lbl, "Band": b_name, "N Patients": n_b,
                "Base ROC": round(auc_b_base, 4) if not np.isnan(auc_b_base) else "N/A",
                "Wear ROC": round(auc_b_wear, 4) if not np.isnan(auc_b_wear) else "N/A",
                "dROC": round(d_auc_b, 4) if not np.isnan(d_auc_b) else "N/A",
                "Base Brier": round(brier_b_base, 4), "Wear Brier": round(brier_b_wear, 4),
                "dBrier": round(brier_b_wear - brier_b_base, 4)
            })

    pred_base = (p_base >= 0.5).astype(int)
    pred_wear = (p_wear >= 0.5).astype(int)
    
    base_err_mask = (pred_base != y_v)
    base_corr_mask = (pred_base == y_v)
    
    n_err = np.sum(base_err_mask)
    n_rescued = np.sum(base_err_mask & (pred_wear == y_v))
    rescue_rate = (n_rescued / n_err * 100) if n_err > 0 else 0.0
    
    p_wear_stand = val_preds_df[f"Wearable_{lbl}_prob"].values
    pred_wear_stand = (p_wear_stand >= 0.5).astype(int)
    wear_standalone_acc = np.mean(pred_wear_stand == y_v) * 100

    rescue_rows.append({
        "Disease": lbl,
        "Baseline Incorrect Count": n_err,
        "Rescued by Wearable Count": n_rescued,
        "Conditional Rescue Rate": round(rescue_rate, 1),
        "Wearable Standalone Accuracy": round(wear_standalone_acc, 1)
    })

    for case_type, mask_c in [("Baseline Correct", base_corr_mask), ("Baseline Incorrect", base_err_mask)]:
        if np.sum(mask_c) > 0:
            diff_p = p_wear[mask_c] - p_base[mask_c]
            pct_inc = np.mean(diff_p > 0.01) * 100
            pct_dec = np.mean(diff_p < -0.01) * 100
            pct_same = np.mean(np.abs(diff_p) <= 0.01) * 100
            
            shift_rows.append({
                "Disease": lbl,
                "Case Type": case_type,
                "N": np.sum(mask_c),
                "% Increased (> +0.01)": round(pct_inc, 1),
                "% Decreased (< -0.01)": round(pct_dec, 1),
                "% Unchanged (|d| <= 0.01)": round(pct_same, 1),
                "Mean Prob Shift": round(np.mean(diff_p), 4)
            })

df_part1_2 = pd.DataFrame(part1_2_rows)
df_boot = pd.DataFrame(bootstrap_rows)
df_coef = pd.DataFrame(coef_rows)
df_constrained = pd.DataFrame(constrained_rows)
df_band = pd.DataFrame(band_rows)
df_rescue = pd.DataFrame(rescue_rows)
df_shift = pd.DataFrame(shift_rows)

print("=== Incremental Wearable Analysis Calculations Complete ===")
print("\n1 & 2. Performance Comparison:")
print(df_part1_2.to_string())
print("\n4. Bootstrap CIs:")
print(df_boot.to_string())
print("\n5. Coefficients:")
print(df_coef.to_string())
print("\n6. Constrained Non-Negative Test:")
print(df_constrained.to_string())
print("\n7. Error Rescue Analysis:")
print(df_rescue.to_string())
print("\n8. Individual Probability Shift Analysis:")
print(df_shift.to_string())

