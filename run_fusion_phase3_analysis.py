"""
run_fusion_phase3_analysis.py — Fusion Phase 3 Disease-Aware Analysis Script

Executes all numerical calculations, candidate strategy evaluations, difference distributions,
MAX probability strategies, fixed-weight supporting strategies, confidence-aware rules,
calibration diagnostics, and availability scenario comparisons across Validation (n=3,000) and OOF Train (n=14,000).
"""

import os
import json
import warnings
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, rankdata
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
oof_df = pd.read_csv(os.path.join(OOF_DIR, "oof_train_predictions.csv"))

val_labels_df = labels_df[val_mask].reset_index(drop=True)
train_labels_df = labels_df[train_mask].reset_index(drop=True)

# Helper function for evaluation metrics
def get_metrics(y_true, y_prob, threshold=0.5):
    y_pred = (y_prob >= threshold).astype(int)
    roc = roc_auc_score(y_true, y_prob)
    pr = average_precision_score(y_true, y_prob)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    brier = brier_score_loss(y_true, y_prob)
    
    # Calibration slope & intercept via LogisticRegression(prob)
    try:
        eps = 1e-7
        p_clip = np.clip(y_prob, eps, 1 - eps)
        logit_p = np.log(p_clip / (1 - p_clip)).reshape(-1, 1)
        lr_cal = LogisticRegression(penalty=None, solver='lbfgs')
        lr_cal.fit(logit_p, y_true)
        slope = float(lr_cal.coef_[0][0])
        intercept = float(lr_cal.intercept_[0])
    except Exception:
        slope, intercept = np.nan, np.nan
        
    return {
        "ROC-AUC": roc, "PR-AUC": pr, "F1": f1,
        "Precision": prec, "Recall": rec, "Brier": brier,
        "Calib_Slope": slope, "Calib_Intercept": intercept
    }

# ─────────────────────────────────────────────
# 1. Standalone Performance
# ─────────────────────────────────────────────
standalone_rows = []
for lbl in LABEL_COLS:
    y_v = val_labels_df[lbl].values
    for mod in ["Clinical", "Wearable", "Gut"]:
        p_v = val_preds_df[f"{mod}_{lbl}_prob"].values
        m = get_metrics(y_v, p_v)
        m.update({"Disease": lbl, "Modality": mod})
        standalone_rows.append(m)

df_standalone = pd.DataFrame(standalone_rows)

# ─────────────────────────────────────────────
# 2. Sequential Incremental Performance
# ─────────────────────────────────────────────
def get_blend_prob(lbl, mods, method="WeightedAvg"):
    if len(mods) == 1:
        return val_preds_df[f"{mods[0]}_{lbl}_prob"].values
    if method == "WeightedAvg":
        P_oof = np.column_stack([oof_df[f"{m}_{lbl}_prob"].values for m in mods])
        y_oof = train_labels_df[lbl].values
        res = minimize(lambda w: -roc_auc_score(y_oof, np.dot(P_oof, w/np.sum(w))), np.ones(len(mods))/len(mods), method='SLSQP', bounds=[(0,1)]*len(mods), constraints={'type':'eq', 'fun': lambda w: np.sum(w)-1})
        w_opt = res.x / np.sum(res.x)
        P_val = np.column_stack([val_preds_df[f"{m}_{lbl}_prob"].values for m in mods])
        return np.dot(P_val, w_opt)
    elif method == "LRStacker":
        m_path = os.path.join(PHASE2_DIR, "models", "fusion_candidates", f"stacker_{lbl}_{'+'.join(mods)}.joblib")
        P_oof = np.column_stack([oof_df[f"{m}_{lbl}_prob"].values for m in mods])
        y_oof = train_labels_df[lbl].values
        
        if os.path.exists(m_path):
            lr = joblib.load(m_path)
        else:
            lr = LogisticRegression(penalty='l2', C=1.0, random_state=42, max_iter=1000)
            lr.fit(P_oof, y_oof)
            
        P_val = np.column_stack([val_preds_df[f"{m}_{lbl}_prob"].values for m in mods])
        return lr.predict_proba(P_val)[:, 1]

incremental_rows = []
for lbl in LABEL_COLS:
    y_v = val_labels_df[lbl].values
    
    p_c = get_blend_prob(lbl, ["Clinical"])
    p_w = get_blend_prob(lbl, ["Wearable"])
    p_g = get_blend_prob(lbl, ["Gut"])
    p_cg_w = get_blend_prob(lbl, ["Clinical", "Gut"], "WeightedAvg")
    p_cg_lr = get_blend_prob(lbl, ["Clinical", "Gut"], "LRStacker")
    p_cw_w = get_blend_prob(lbl, ["Clinical", "Wearable"], "WeightedAvg")
    p_cw_lr = get_blend_prob(lbl, ["Clinical", "Wearable"], "LRStacker")
    p_gw_w = get_blend_prob(lbl, ["Gut", "Wearable"], "WeightedAvg")
    p_full_w = get_blend_prob(lbl, ["Clinical", "Wearable", "Gut"], "WeightedAvg")
    p_full_lr = get_blend_prob(lbl, ["Clinical", "Wearable", "Gut"], "LRStacker")

    auc_c = roc_auc_score(y_v, p_c)
    auc_g = roc_auc_score(y_v, p_g)
    
    incremental_rows.append({
        "Disease": lbl,
        "Clinical": round(auc_c, 4),
        "Clin->Clin+Gut (W)": round(roc_auc_score(y_v, p_cg_w) - auc_c, 4),
        "Clin->Clin+Gut (LR)": round(roc_auc_score(y_v, p_cg_lr) - auc_c, 4),
        "Clin->Clin+Wear (W)": round(roc_auc_score(y_v, p_cw_w) - auc_c, 4),
        "Gut->Gut+Clin (W)": round(roc_auc_score(y_v, p_cg_w) - auc_g, 4),
        "Clin+Gut->Full (W)": round(roc_auc_score(y_v, p_full_w) - roc_auc_score(y_v, p_cg_w), 4),
        "Clin+Gut->Full (LR)": round(roc_auc_score(y_v, p_full_lr) - roc_auc_score(y_v, p_cg_lr), 4),
    })

df_incremental = pd.DataFrame(incremental_rows)

# ─────────────────────────────────────────────
# 3. Probability Difference Distributions (Don't Reduce Strong Output)
# ─────────────────────────────────────────────
diff_rows = []
for lbl in LABEL_COLS:
    p_c = val_preds_df[f"Clinical_{lbl}_prob"].values
    p_w = val_preds_df[f"Wearable_{lbl}_prob"].values
    p_g = val_preds_df[f"Gut_{lbl}_prob"].values
    
    p_strong = np.maximum(np.maximum(p_c, p_w), p_g)
    
    p_cg_lr = get_blend_prob(lbl, ["Clinical", "Gut"], "LRStacker")
    p_full_lr = get_blend_prob(lbl, ["Clinical", "Wearable", "Gut"], "LRStacker")
    
    diff_cg = p_cg_lr - p_strong
    diff_full = p_full_lr - p_strong

    for combo_name, diff_arr in [("Clinical+Gut (LR)", diff_cg), ("Full Fusion (LR)", diff_full)]:
        diff_rows.append({
            "Disease": lbl,
            "Combo": combo_name,
            "Mean Diff": round(np.mean(diff_arr), 4),
            "Median Diff": round(np.median(diff_arr), 4),
            "Std Diff": round(np.std(diff_arr), 4),
            "% Decreased (Fusion < Strongest)": round(np.mean(diff_arr < 0) * 100, 1),
            "% Increased (Fusion > Strongest)": round(np.mean(diff_arr > 0) * 100, 1),
            "% |Diff| > 0.05": round(np.mean(np.abs(diff_arr) > 0.05) * 100, 1),
            "% |Diff| > 0.10": round(np.mean(np.abs(diff_arr) > 0.10) * 100, 1)
        })

df_diff_dist = pd.DataFrame(diff_rows)

# ─────────────────────────────────────────────
# 4. MAX Probability Strategy
# ─────────────────────────────────────────────
max_strategy_rows = []
for lbl in LABEL_COLS:
    y_v = val_labels_df[lbl].values
    p_c = val_preds_df[f"Clinical_{lbl}_prob"].values
    p_w = val_preds_df[f"Wearable_{lbl}_prob"].values
    p_g = val_preds_df[f"Gut_{lbl}_prob"].values
    
    p_max = np.maximum(np.maximum(p_c, p_w), p_g)
    p_cg_w = get_blend_prob(lbl, ["Clinical", "Gut"], "WeightedAvg")
    p_cg_lr = get_blend_prob(lbl, ["Clinical", "Gut"], "LRStacker")
    p_full_w = get_blend_prob(lbl, ["Clinical", "Wearable", "Gut"], "WeightedAvg")
    p_full_lr = get_blend_prob(lbl, ["Clinical", "Wearable", "Gut"], "LRStacker")

    for name, p_arr in [
        ("Clinical (Single)", p_c),
        ("P_max", p_max),
        ("Clin+Gut (Weighted)", p_cg_w),
        ("Clin+Gut (LRStacker)", p_cg_lr),
        ("Full (Weighted)", p_full_w),
        ("Full (LRStacker)", p_full_lr),
    ]:
        m = get_metrics(y_v, p_arr)
        m.update({"Disease": lbl, "Strategy": name})
        max_strategy_rows.append(m)

df_max_strat = pd.DataFrame(max_strategy_rows)

# ─────────────────────────────────────────────
# 5. Dominant Modality + Small Wearable Contribution Strategies
# ─────────────────────────────────────────────
fixed_blend_rows = []
for lbl in LABEL_COLS:
    y_v = val_labels_df[lbl].values
    p_c = val_preds_df[f"Clinical_{lbl}_prob"].values
    p_w = val_preds_df[f"Wearable_{lbl}_prob"].values
    p_g = val_preds_df[f"Gut_{lbl}_prob"].values

    blends = {
        "Strat A (0.50 C + 0.50 G)": 0.50*p_c + 0.50*p_g,
        "Strat B (0.60 C + 0.40 G)": 0.60*p_c + 0.40*p_g,
        "Strat C (0.70 C + 0.30 G)": 0.70*p_c + 0.30*p_g,
        "Strat D (0.55 C + 0.35 G + 0.10 W)": 0.55*p_c + 0.35*p_g + 0.10*p_w,
        "Strat E (0.60 C + 0.30 G + 0.10 W)": 0.60*p_c + 0.30*p_g + 0.10*p_w,
        "Strat F (0.65 C + 0.25 G + 0.10 W)": 0.65*p_c + 0.25*p_g + 0.10*p_w,
        "Strat G (0.65 C + 0.30 G + 0.05 W)": 0.65*p_c + 0.30*p_g + 0.05*p_w,
        "Optimized Clin+Gut LR": get_blend_prob(lbl, ["Clinical", "Gut"], "LRStacker"),
        "Optimized Full LR": get_blend_prob(lbl, ["Clinical", "Wearable", "Gut"], "LRStacker")
    }

    for name, p_arr in blends.items():
        m = get_metrics(y_v, p_arr)
        m.update({"Disease": lbl, "Strategy": name})
        fixed_blend_rows.append(m)

df_fixed_blends = pd.DataFrame(fixed_blend_rows)

# ─────────────────────────────────────────────
# 6. Confidence-Aware Dominant Modality Strategy
# ─────────────────────────────────────────────
conf_aware_rows = []
for lbl in LABEL_COLS:
    y_v = val_labels_df[lbl].values
    p_c = val_preds_df[f"Clinical_{lbl}_prob"].values
    p_w = val_preds_df[f"Wearable_{lbl}_prob"].values
    p_g = val_preds_df[f"Gut_{lbl}_prob"].values
    
    p_base_fusion = get_blend_prob(lbl, ["Clinical", "Gut"], "LRStacker")
    
    # Calculate per-patient max prob and second max prob
    probs_stack = np.column_stack([p_c, p_w, p_g])
    sorted_probs = np.sort(probs_stack, axis=1)
    max_p = sorted_probs[:, 2]
    second_p = sorted_probs[:, 1]
    diff_p = max_p - second_p
    
    for delta in [0.05, 0.10, 0.15, 0.20]:
        # Rule: if max - second >= delta, use max_p; else use base fusion
        p_conf = np.where(diff_p >= delta, max_p, p_base_fusion)
        m = get_metrics(y_v, p_conf)
        m.update({"Disease": lbl, "Delta Threshold": delta, "Strategy": f"ConfAware (delta={delta})"})
        conf_aware_rows.append(m)

df_conf_aware = pd.DataFrame(conf_aware_rows)

# ─────────────────────────────────────────────
# 7. Modality Availability Scenarios (Cases 1-7)
# ─────────────────────────────────────────────
avail_rows = []
for lbl in LABEL_COLS:
    y_v = val_labels_df[lbl].values
    p_c = val_preds_df[f"Clinical_{lbl}_prob"].values
    p_w = val_preds_df[f"Wearable_{lbl}_prob"].values
    p_g = val_preds_df[f"Gut_{lbl}_prob"].values

    # Case 4: Clin + Gut
    p_cg_w = get_blend_prob(lbl, ["Clinical", "Gut"], "WeightedAvg")
    p_cg_lr = get_blend_prob(lbl, ["Clinical", "Gut"], "LRStacker")
    p_max_cg = np.maximum(p_c, p_g)

    # Case 5: Clin + Wear
    p_cw_w = get_blend_prob(lbl, ["Clinical", "Wearable"], "WeightedAvg")
    p_cw_lr = get_blend_prob(lbl, ["Clinical", "Wearable"], "LRStacker")
    p_max_cw = np.maximum(p_c, p_w)

    # Case 6: Gut + Wear
    p_gw_w = get_blend_prob(lbl, ["Gut", "Wearable"], "WeightedAvg")
    p_gw_lr = get_blend_prob(lbl, ["Gut", "Wearable"], "LRStacker")
    p_max_gw = np.maximum(p_g, p_w)

    # Case 7: All 3
    p_full_lr = get_blend_prob(lbl, ["Clinical", "Wearable", "Gut"], "LRStacker")
    p_max_all = np.maximum(np.maximum(p_c, p_w), p_g)

    scenarios = [
        ("Case 1: Clin Only", "Clinical Passthrough", p_c),
        ("Case 2: Gut Only", "Gut Passthrough", p_g),
        ("Case 3: Wear Only", "Wearable Passthrough", p_w),
        ("Case 4: Clin+Gut", "Clinical Single", p_c),
        ("Case 4: Clin+Gut", "Gut Single", p_g),
        ("Case 4: Clin+Gut", "Clin+Gut LRStacker", p_cg_lr),
        ("Case 4: Clin+Gut", "MAX(Clin, Gut)", p_max_cg),
        ("Case 5: Clin+Wear", "Clinical Single", p_c),
        ("Case 5: Clin+Wear", "Wearable Single", p_w),
        ("Case 5: Clin+Wear", "Clin+Wear LRStacker", p_cw_lr),
        ("Case 5: Clin+Wear", "MAX(Clin, Wear)", p_max_cw),
        ("Case 6: Gut+Wear", "Gut Single", p_g),
        ("Case 6: Gut+Wear", "Wearable Single", p_w),
        ("Case 6: Gut+Wear", "Gut+Wear LRStacker", p_gw_lr),
        ("Case 6: Gut+Wear", "MAX(Gut, Wear)", p_max_gw),
        ("Case 7: All 3", "Clinical Single", p_c),
        ("Case 7: All 3", "Clin+Gut LRStacker", p_cg_lr),
        ("Case 7: All 3", "Full LRStacker", p_full_lr),
        ("Case 7: All 3", "MAX(All 3)", p_max_all),
    ]

    for sc_name, strat_name, p_arr in scenarios:
        m = get_metrics(y_v, p_arr)
        m.update({"Disease": lbl, "Scenario": sc_name, "Candidate": strat_name})
        avail_rows.append(m)

df_avail = pd.DataFrame(avail_rows)

print("=== Phase 3 Computations Complete ===")
print("Generated standalone, incremental, difference distribution, MAX, fixed blend, confidence aware, and availability scenario tables.")

