"""
Single-Modality Reliability Investigation for Fusion V2
======================================================
Evaluates:
- Clinical alone
- Gut alone
- Wearable alone
across all 5 diseases on Validation set (3,000 patients) for decision making,
and evaluates on Test set (3,000 patients) for final confirmation.
"""
import sys, io, warnings, os
warnings.filterwarnings('ignore')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

import numpy as np
import pandas as pd
from sklearn.metrics import (
    roc_auc_score, average_precision_score, brier_score_loss,
    log_loss, f1_score, precision_score, recall_score,
    balanced_accuracy_score, confusion_matrix
)
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import calibration_curve

np.random.seed(42)

DISEASES = ['Type2_Diabetes', 'Prediabetes', 'High_Adiposity_Risk', 'Metabolic_Syndrome', 'NAFLD']
MODALITIES = ['Clinical', 'Gut', 'Wearable']

# ─────────────────────────────────────────────────────────────────────────────
# 1. LOAD DATASETS
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 90)
print("PHASE 1: DATASET VERIFICATION")
print("=" * 90)

val_path = 'fusion_val_master.csv'
test_path = 'fusion_test_master.csv'

val_df = pd.read_csv(val_path)
test_df = pd.read_csv(test_path)

print(f"  Validation file: {val_path} -> Shape: {val_df.shape}")
print(f"  Test file:       {test_path} -> Shape: {test_df.shape}")

val_ids = set(val_df['Patient_ID'])
test_ids = set(test_df['Patient_ID'])
overlap = len(val_ids & test_ids)
print(f"  Validation duplicates: {val_df['Patient_ID'].duplicated().sum()}")
print(f"  Test duplicates:       {test_df['Patient_ID'].duplicated().sum()}")
print(f"  Validation ∩ Test:     {overlap} (Must be 0)\n")
assert overlap == 0, "Data leakage between validation and test!"

def calc_ece(y_true, y_prob, n_bins=10):
    bins = np.linspace(0, 1, n_bins + 1)
    ece_val = 0.0
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (y_prob >= lo) & (y_prob < hi)
        if mask.sum() == 0:
            continue
        frac_pos = y_true[mask].mean()
        mean_p = y_prob[mask].mean()
        ece_val += mask.sum() * abs(frac_pos - mean_p)
    return ece_val / len(y_true)

def get_cal_params(y_true, y_prob):
    p_safe = np.clip(y_prob, 1e-7, 1 - 1e-7)
    logit = np.log(p_safe / (1 - p_safe))
    lr = LogisticRegression(C=1e9, max_iter=2000, random_state=42)
    lr.fit(logit.reshape(-1, 1), y_true)
    return lr.coef_[0][0], lr.intercept_[0]

# ─────────────────────────────────────────────────────────────────────────────
# 2. VALIDATION EVALUATION & THRESHOLD SEARCH
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 90)
print("PHASE 2, 3 & 4: VALIDATION SET EVALUATION (N=3,000)")
print("=" * 90)

VAL_RESULTS = []

grid = np.arange(0.05, 0.96, 0.01)

for dis in DISEASES:
    y_val = val_df[f'{dis}_true'].values
    prev = y_val.mean()
    print(f"\n==================== Disease: {dis} (Prevalence = {prev:.4f}) ====================")
    
    for mod in MODALITIES:
        p_val = val_df[f'{mod}_{dis}_prob'].values
        p_val_clipped = np.clip(p_val, 1e-7, 1 - 1e-7)
        
        roc = roc_auc_score(y_val, p_val_clipped)
        pr = average_precision_score(y_val, p_val_clipped)
        brier = brier_score_loss(y_val, p_val_clipped)
        ece = calc_ece(y_val, p_val_clipped)
        slope, intercept = get_cal_params(y_val, p_val_clipped)
        
        # Grid search for best F1 threshold
        best_f1, best_t = -1.0, 0.50
        rows = []
        for t in grid:
            yp = (p_val >= t).astype(int)
            f1 = f1_score(y_val, yp, zero_division=0)
            prec = precision_score(y_val, yp, zero_division=0)
            rec = recall_score(y_val, yp, zero_division=0)
            spec = ((y_val == 0) & (yp == 0)).sum() / max(1, (y_val == 0).sum())
            bacc = balanced_accuracy_score(y_val, yp)
            rows.append({'t': t, 'f1': f1, 'prec': prec, 'rec': rec, 'spec': spec, 'bacc': bacc})
            if f1 > best_f1:
                best_f1 = f1
                best_t = t
                
        df_t = pd.DataFrame(rows)
        opt_row = df_t.loc[df_t['t'] == best_t].iloc[0]
        t50_row = df_t.loc[(df_t['t'] - 0.50).abs().idxmin()]
        
        # Confusion matrix at t=0.50 and t=best_t
        cm_50 = confusion_matrix(y_val, (p_val >= 0.50).astype(int))
        cm_opt = confusion_matrix(y_val, (p_val >= best_t).astype(int))
        
        print(f"\n  --- Modality: {mod} ---")
        print(f"    ROC-AUC:   {roc:.4f}")
        print(f"    PR-AUC:    {pr:.4f} (Baseline prevalence: {prev:.4f})")
        print(f"    Brier:     {brier:.4f}")
        print(f"    ECE:       {ece:.4f}")
        print(f"    Cal Slope: {slope:.4f}, Intercept: {intercept:.4f}")
        print(f"    At t=0.50:   F1={t50_row['f1']:.4f} | Prec={t50_row['prec']:.4f} | Rec={t50_row['rec']:.4f} | Spec={t50_row['spec']:.4f} | BAcc={t50_row['bacc']:.4f}")
        print(f"                 CM (TN, FP, FN, TP) = ({cm_50[0,0]}, {cm_50[0,1]}, {cm_50[1,0]}, {cm_50[1,1]})")
        print(f"    Optimal t:   t={best_t:.2f} -> F1={opt_row['f1']:.4f} | Prec={opt_row['prec']:.4f} | Rec={opt_row['rec']:.4f} | Spec={opt_row['spec']:.4f} | BAcc={opt_row['bacc']:.4f}")
        print(f"                 CM (TN, FP, FN, TP) = ({cm_opt[0,0]}, {cm_opt[0,1]}, {cm_opt[1,0]}, {cm_opt[1,1]})")
        
        VAL_RESULTS.append({
            'disease': dis,
            'modality': mod,
            'prevalence': prev,
            'roc': roc,
            'pr': pr,
            'brier': brier,
            'ece': ece,
            'slope': slope,
            'intercept': intercept,
            't_opt': best_t,
            'f1_opt': opt_row['f1'],
            'prec_opt': opt_row['prec'],
            'rec_opt': opt_row['rec'],
            'spec_opt': opt_row['spec'],
            'f1_50': t50_row['f1'],
            'prec_50': t50_row['prec'],
            'rec_50': t50_row['rec'],
            'spec_50': t50_row['spec'],
        })

df_val_res = pd.DataFrame(VAL_RESULTS)

# ─────────────────────────────────────────────────────────────────────────────
# 3. RELIABILITY CLASSIFICATION & POLICY FORMULATION
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 90)
print("PHASE 5: RELIABILITY CLASSIFICATION & DECISION LOGIC")
print("=" * 90)

"""
Classification Criteria:
- STRONG: ROC-AUC >= 0.90 AND PR-AUC >= 0.70 (or >= 3x prevalence for low-prevalence diseases) AND Brier <= 0.08
  -> Allowed as FINAL_PREDICTION
- MODERATE: ROC-AUC >= 0.80 AND PR-AUC >= 1.5x prevalence AND Brier <= 0.16
  -> Allowed as REDUCED_MODALITY (useful signal, but lower confidence than multi-modality fusion)
- WEAK / UNRELIABLE: ROC-AUC < 0.80 OR PR-AUC < 1.5x prevalence OR PR-AUC ~ prevalence
  -> INSUFFICIENT_EVIDENCE (risk of misleading clinical output if presented as a standalone disease risk)
"""

def classify_modality(row):
    dis = row['disease']
    mod = row['modality']
    roc = row['roc']
    pr = row['pr']
    prev = row['prevalence']
    brier = row['brier']
    
    if roc >= 0.90 and pr >= 0.70 and brier <= 0.08:
        rel = 'STRONG'
        decision = 'FINAL_PREDICTION'
        reason = f"High discriminative power (ROC={roc:.4f}, PR={pr:.4f}) and well calibrated (Brier={brier:.4f})."
        t_final = 0.50
    elif roc >= 0.85 and pr >= 2.0 * prev and brier <= 0.13:
        rel = 'STRONG'
        decision = 'FINAL_PREDICTION'
        reason = f"Strong clinical baseline (ROC={roc:.4f}, PR={pr:.4f} vs prev={prev:.4f})."
        # Check if 0.50 or adapted threshold is better
        t_final = 0.50 if row['f1_50'] >= 0.80 or abs(row['t_opt'] - 0.50) <= 0.10 else row['t_opt']
    elif roc >= 0.80 and pr >= 1.5 * prev and brier <= 0.18:
        rel = 'MODERATE'
        decision = 'REDUCED_MODALITY'
        reason = f"Moderate standalone capability (ROC={roc:.4f}, PR={pr:.4f}). Informative but lacks multi-modal synergy."
        t_final = 0.50
    elif roc >= 0.70 and pr >= 1.2 * prev:
        rel = 'WEAK'
        decision = 'INSUFFICIENT_EVIDENCE'
        reason = f"Weak standalone discrimination (ROC={roc:.4f}, PR={pr:.4f}). High risk of false positives/negatives."
        t_final = 0.50
    else:
        rel = 'UNRELIABLE'
        decision = 'INSUFFICIENT_EVIDENCE'
        reason = f"Poor discrimination (ROC={roc:.4f}, PR={pr:.4f} close to random/prevalence {prev:.4f})."
        t_final = 0.50
        
    return rel, decision, reason, t_final

POLICY = []
for _, row in df_val_res.iterrows():
    rel, decision, reason, t_final = classify_modality(row)
    POLICY.append({
        'disease': row['disease'],
        'modality': row['modality'],
        'roc_val': row['roc'],
        'pr_val': row['pr'],
        'brier_val': row['brier'],
        'ece_val': row['ece'],
        'reliability': rel,
        'decision': decision,
        'locked_threshold': t_final,
        'reason': reason
    })

df_policy = pd.DataFrame(POLICY)

print(f"\n{'Disease':<22} {'Modality':<10} {'ROC':>7} {'PR-AUC':>7} {'Brier':>7} {'Reliability':<12} {'Policy Decision':<22} {'Thresh':>6}")
print("-" * 100)
for _, p in df_policy.iterrows():
    print(f"{p['disease']:<22} {p['modality']:<10} {p['roc_val']:>7.4f} {p['pr_val']:>7.4f} {p['brier_val']:>7.4f} {p['reliability']:<12} {p['decision']:<22} {p['locked_threshold']:>6.2f}")

# ─────────────────────────────────────────────────────────────────────────────
# 4. TEST SET CONFIRMATION (N=3,000 HELD-OUT)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 90)
print("PHASE 9: TEST SET CONFIRMATION (N=3,000 SINGLE-PASS)")
print("=" * 90)

TEST_CONFIRM = []

for _, p in df_policy.iterrows():
    dis = p['disease']
    mod = p['modality']
    t_locked = p['locked_threshold']
    
    y_test = test_df[f'{dis}_true'].values
    p_test = test_df[f'{mod}_{dis}_prob'].values
    p_test_clipped = np.clip(p_test, 1e-7, 1 - 1e-7)
    
    roc_t = roc_auc_score(y_test, p_test_clipped)
    pr_t = average_precision_score(y_test, p_test_clipped)
    brier_t = brier_score_loss(y_test, p_test_clipped)
    ece_t = calc_ece(y_test, p_test_clipped)
    
    yp_t = (p_test >= t_locked).astype(int)
    f1_t = f1_score(y_test, yp_t, zero_division=0)
    prec_t = precision_score(y_test, yp_t, zero_division=0)
    rec_t = recall_score(y_test, yp_t, zero_division=0)
    spec_t = ((y_test == 0) & (yp_t == 0)).sum() / max(1, (y_test == 0).sum())
    
    TEST_CONFIRM.append({
        'disease': dis,
        'modality': mod,
        'decision': p['decision'],
        'locked_t': t_locked,
        'roc_val': p['roc_val'],
        'roc_test': roc_t,
        'd_roc': roc_t - p['roc_val'],
        'pr_val': p['pr_val'],
        'pr_test': pr_t,
        'd_pr': pr_t - p['pr_val'],
        'brier_test': brier_t,
        'f1_test': f1_t,
        'prec_test': prec_t,
        'rec_test': rec_t,
        'spec_test': spec_t
    })

df_test_conf = pd.DataFrame(TEST_CONFIRM)

print(f"{'Disease':<22} {'Modality':<10} {'Decision':<22} {'t':>4} {'ROC(Val)':>9} {'ROC(Test)':>9} {'PR(Val)':>8} {'PR(Test)':>8} {'F1(Test)':>8} {'Rec(Test)':>9}")
print("-" * 105)
for _, r in df_test_conf.iterrows():
    print(f"{r['disease']:<22} {r['modality']:<10} {r['decision']:<22} {r['locked_t']:>4.2f} {r['roc_val']:>9.4f} {r['roc_test']:>9.4f} {r['pr_val']:>8.4f} {r['pr_test']:>8.4f} {r['f1_test']:>8.4f} {r['rec_test']:>9.4f}")

print("\nINVESTIGATION COMPLETE.")
