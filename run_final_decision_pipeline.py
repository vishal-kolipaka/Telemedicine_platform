"""
Final Decision Pipeline for Fusion V2
=====================================
1. Train candidate models on 14,000 OOF predictions + ground-truth training labels.
2. Select winning method, threshold, calibration, and stability checks strictly on 3,000 Validation set.
3. Test set (3,000) remains untouched during all selection and tuning.
4. Single-pass final evaluation on Test set after all parameters are locked.
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
from sklearn.linear_model import LogisticRegressionCV, LogisticRegression
from scipy.optimize import minimize
from scipy.stats import pearsonr, spearmanr

np.random.seed(42)

DISEASES = ['Type2_Diabetes', 'Prediabetes', 'High_Adiposity_Risk', 'Metabolic_Syndrome', 'NAFLD']

# ─────────────────────────────────────────────────────────────────────────────
# 1. LOAD & PREPARE DATASETS
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 80)
print("PHASE 1: LOAD & PREPARE DATASETS")
print("=" * 80)

oof_raw = pd.read_csv('fusion_phase2/oof/oof_train_predictions.csv')
labels_all = pd.read_csv('datasets/labels_v3.csv')
val_df = pd.read_csv('fusion_val_master.csv')
test_df = pd.read_csv('fusion_test_master.csv')

# Merge labels into OOF
train_df = oof_raw.merge(labels_all[['Patient_ID'] + DISEASES], on='Patient_ID', how='inner')

print(f"  Training (OOF + Labels): {train_df.shape[0]} rows x {train_df.shape[1]} cols")
print(f"  Validation:              {val_df.shape[0]} rows x {val_df.shape[1]} cols")
print(f"  Test (Held-out):         {test_df.shape[0]} rows x {test_df.shape[1]} cols")

# Check leakages
oof_ids = set(train_df['Patient_ID'])
val_ids = set(val_df['Patient_ID'])
tst_ids = set(test_df['Patient_ID'])
assert len(oof_ids & val_ids) == 0, "Leakage OOF & VAL!"
assert len(oof_ids & tst_ids) == 0, "Leakage OOF & TEST!"
assert len(val_ids & tst_ids) == 0, "Leakage VAL & TEST!"
print("  Partitions: 100% clean, zero overlap.\n")

def get_arrays(df, dis, is_train=False):
    c_col = f'Clinical_{dis}_prob'
    g_col = f'Gut_{dis}_prob'
    w_col = f'Wearable_{dis}_prob'
    y_col = dis if is_train else f'{dis}_true'
    
    pc = df[c_col].values
    pg = df[g_col].values
    pw = df[w_col].values
    y  = df[y_col].values
    return pc, pg, pw, y

def safe_metrics(y, p, t=None):
    p = np.clip(p, 1e-7, 1 - 1e-7)
    res = {
        'roc': roc_auc_score(y, p),
        'pr': average_precision_score(y, p),
        'brier': brier_score_loss(y, p),
        'll': log_loss(y, p)
    }
    if t is not None:
        yp = (p >= t).astype(int)
        res['f1'] = f1_score(y, yp, zero_division=0)
        res['prec'] = precision_score(y, yp, zero_division=0)
        res['rec'] = recall_score(y, yp, zero_division=0)
        res['spec'] = ((y == 0) & (yp == 0)).sum() / max(1, (y == 0).sum())
        res['bacc'] = balanced_accuracy_score(y, yp)
    return res

# ─────────────────────────────────────────────────────────────────────────────
# 2. TRAIN CANDIDATE FUSION MODELS ON 14,000 OOF PREDICTIONS
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 80)
print("PHASE 2: TRAIN CANDIDATE FUSION MODELS ON 14,000 OOF")
print("=" * 80)

TRAINED_MODELS = {}

for dis in DISEASES:
    pc_tr, pg_tr, _, y_tr = get_arrays(train_df, dis, is_train=True)
    models = {}
    
    # 1. Simple Mean (No parameters)
    models['Simple_Mean'] = {'type': 'mean'}
    
    # 2. Weighted Mean (Fit on OOF log-loss)
    def obj_weighted(w):
        w_c = np.clip(w[0], 0.0, 1.0)
        p = w_c * pc_tr + (1.0 - w_c) * pg_tr
        p = np.clip(p, 1e-7, 1 - 1e-7)
        return -np.mean(y_tr * np.log(p) + (1.0 - y_tr) * np.log(1.0 - p))
        
    res_w = minimize(obj_weighted, [0.5], method='L-BFGS-B', bounds=[(0.0, 1.0)])
    w_c = float(np.clip(res_w.x[0], 0.0, 1.0))
    w_g = 1.0 - w_c
    models['Weighted_Mean'] = {'type': 'weighted_mean', 'w_c': w_c, 'w_g': w_g}
    
    # 3. L2 Logistic Regression Stacker
    X_tr_cg = np.column_stack([pc_tr, pg_tr])
    lr_cg = LogisticRegressionCV(Cs=np.logspace(-4, 3, 30), cv=5, scoring='neg_log_loss', max_iter=3000, random_state=42)
    lr_cg.fit(X_tr_cg, y_tr)
    b0, bc, bg = lr_cg.intercept_[0], lr_cg.coef_[0][0], lr_cg.coef_[0][1]
    models['LR_CG'] = {'type': 'lr', 'model': lr_cg, 'b0': b0, 'bc': bc, 'bg': bg}
    
    # 4. Interaction Stacker
    X_tr_int = np.column_stack([pc_tr, pg_tr, pc_tr * pg_tr])
    lr_int = LogisticRegressionCV(Cs=np.logspace(-4, 3, 30), cv=5, scoring='neg_log_loss', max_iter=3000, random_state=42)
    lr_int.fit(X_tr_int, y_tr)
    bi0, bic, big, bi_int = lr_int.intercept_[0], lr_int.coef_[0][0], lr_int.coef_[0][1], lr_int.coef_[0][2]
    models['LR_Interaction'] = {'type': 'lr_int', 'model': lr_int, 'b0': bi0, 'bc': bic, 'bg': big, 'b_int': bi_int}
    
    # 5. Platt-calibrated LR Stacker
    p_tr_cg = lr_cg.predict_proba(X_tr_cg)[:, 1]
    logit_tr_cg = np.log(np.clip(p_tr_cg, 1e-7, 1 - 1e-7) / (1.0 - np.clip(p_tr_cg, 1e-7, 1 - 1e-7)))
    platt = LogisticRegression(C=1e9, max_iter=2000, random_state=42)
    platt.fit(logit_tr_cg.reshape(-1, 1), y_tr)
    models['Platt_LR_CG'] = {'type': 'platt_lr', 'lr_model': lr_cg, 'platt_model': platt, 
                             'slope': platt.coef_[0][0], 'intercept': platt.intercept_[0]}
    
    TRAINED_MODELS[dis] = models
    print(f"  [{dis}] Models trained on 14,000 OOF:")
    print(f"    - Weighted Mean: w_c={w_c:.4f}, w_g={w_g:.4f}")
    print(f"    - LR C+G:        b0={b0:+.4f}, bc={bc:+.4f}, bg={bg:+.4f}")
    print(f"    - LR Int:        b0={bi0:+.4f}, bc={bic:+.4f}, bg={big:+.4f}, b_int={bi_int:+.4f}")
    print(f"    - Platt:         slope={platt.coef_[0][0]:+.4f}, intercept={platt.intercept_[0]:+.4f}\n")

# ─────────────────────────────────────────────────────────────────────────────
# 3. EVALUATION, METHOD SELECTION & THRESHOLD TUNING ON VALIDATION (3,000)
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 80)
print("PHASE 3: EVALUATION & SELECTION ON 3,000 VALIDATION SET")
print("=" * 80)

def predict_model(model_dict, pc, pg):
    m_type = model_dict['type']
    if m_type == 'clinical':
        return pc
    elif m_type == 'gut':
        return pg
    elif m_type == 'mean':
        return 0.5 * pc + 0.5 * pg
    elif m_type == 'weighted_mean':
        return model_dict['w_c'] * pc + model_dict['w_g'] * pg
    elif m_type == 'lr':
        X = np.column_stack([pc, pg])
        return model_dict['model'].predict_proba(X)[:, 1]
    elif m_type == 'lr_int':
        X = np.column_stack([pc, pg, pc * pg])
        return model_dict['model'].predict_proba(X)[:, 1]
    elif m_type == 'platt_lr':
        X = np.column_stack([pc, pg])
        p_raw = model_dict['lr_model'].predict_proba(X)[:, 1]
        logit = np.log(np.clip(p_raw, 1e-7, 1 - 1e-7) / (1.0 - np.clip(p_raw, 1e-7, 1 - 1e-7)))
        return model_dict['platt_model'].predict_proba(logit.reshape(-1, 1))[:, 1]
    else:
        raise ValueError(f"Unknown model type: {m_type}")

def bootstrap_delta(y, p_cand, p_base, n=5000, seed=42):
    rng = np.random.default_rng(seed)
    d_roc, d_pr = [], []
    for _ in range(n):
        idx = rng.integers(0, len(y), len(y))
        yr, pc_r, pb_r = y[idx], p_cand[idx], p_base[idx]
        if yr.sum() == 0 or yr.sum() == len(yr): continue
        d_roc.append(roc_auc_score(yr, pc_r) - roc_auc_score(yr, pb_r))
        d_pr.append(average_precision_score(yr, pc_r) - average_precision_score(yr, pb_r))
    d_roc, d_pr = np.array(d_roc), np.array(d_pr)
    return d_roc.mean(), np.percentile(d_roc, [2.5, 97.5]), d_pr.mean(), np.percentile(d_pr, [2.5, 97.5])

def calc_ece(y, p, n_bins=10):
    bins = np.linspace(0, 1, n_bins + 1)
    ece_val = 0.0
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (p >= lo) & (p < hi)
        if mask.sum() == 0: continue
        frac_pos = y[mask].mean()
        mean_p   = p[mask].mean()
        ece_val += mask.sum() * abs(frac_pos - mean_p)
    return ece_val / len(y)

LOCKED_SPECS = {}

for dis in DISEASES:
    pc_v, pg_v, _, y_v = get_arrays(val_df, dis, is_train=False)
    models = TRAINED_MODELS[dis]
    
    print(f"\n--- Disease: {dis} (Validation N=3,000, Prevalence={y_v.mean():.4f}) ---")
    
    # Evaluate all candidates on Validation
    candidate_preds = {
        'Clinical_Only': pc_v,
        'Gut_Only': pg_v,
        'Simple_Mean': predict_model(models['Simple_Mean'], pc_v, pg_v),
        'Weighted_Mean': predict_model(models['Weighted_Mean'], pc_v, pg_v),
        'LR_CG': predict_model(models['LR_CG'], pc_v, pg_v),
        'LR_Interaction': predict_model(models['LR_Interaction'], pc_v, pg_v),
        'Platt_LR_CG': predict_model(models['Platt_LR_CG'], pc_v, pg_v)
    }
    
    val_perf = {}
    print(f"  {'Candidate':<18} {'ROC-AUC':>8} {'PR-AUC':>8} {'Brier':>8} {'LogLoss':>9}")
    for c_name, p_val in candidate_preds.items():
        m = safe_metrics(y_v, p_val)
        val_perf[c_name] = m
        print(f"  {c_name:<18} {m['roc']:>8.4f} {m['pr']:>8.4f} {m['brier']:>8.4f} {m['ll']:>9.4f}")
    
    # Statistical significance on Validation: LR_CG vs Clinical
    dr_c, ci_r_c, dp_c, ci_p_c = bootstrap_delta(y_v, candidate_preds['LR_CG'], pc_v, n=5000)
    print(f"  Bootstrap LR_CG vs Clin (5000 reps):")
    print(f"    ΔROC: {dr_c:+.4f} 95% CI [{ci_r_c[0]:+.4f}, {ci_r_c[1]:+.4f}] (Sig > 0: {ci_r_c[0] > 0})")
    print(f"    ΔPR:  {dp_c:+.4f} 95% CI [{ci_p_c[0]:+.4f}, {ci_p_c[1]:+.4f}] (Sig > 0: {ci_p_c[0] > 0})")
    
    # Selection rule: If bootstrap LR_CG vs Clinical is significantly positive on ROC or PR, use LR_CG.
    # Otherwise, choose Clinical Passthrough (simplest, safest, zero-parameter).
    if ci_r_c[0] > 0 or ci_p_c[0] > 0:
        selected_method = 'LR_CG'
        selected_preds_val = candidate_preds['LR_CG']
        selection_reason = "Statistically significant gain over Clinical baseline"
    else:
        selected_method = 'Clinical_Passthrough'
        selected_preds_val = pc_v
        selection_reason = "Clinical baseline is already at ceiling; fusion yields no significant gain"
        
    # Check calibration for selected method on Validation
    ece_val = calc_ece(y_v, selected_preds_val)
    brier_val = brier_score_loss(y_v, selected_preds_val)
    print(f"  Selected Method: {selected_method} ({selection_reason})")
    print(f"    Validation ECE: {ece_val:.4f}, Brier: {brier_val:.4f}")
    
    # Threshold Tuning on Validation Grid [0.05 -> 0.95]
    grid = np.arange(0.05, 0.96, 0.01)
    best_f1, best_t = -1.0, 0.50
    thresh_rows = []
    
    for t in grid:
        yp = (selected_preds_val >= t).astype(int)
        f1 = f1_score(y_v, yp, zero_division=0)
        prec = precision_score(y_v, yp, zero_division=0)
        rec = recall_score(y_v, yp, zero_division=0)
        spec = ((y_v == 0) & (yp == 0)).sum() / max(1, (y_v == 0).sum())
        thresh_rows.append({'t': t, 'f1': f1, 'prec': prec, 'rec': rec, 'spec': spec})
        if f1 > best_f1:
            best_f1 = f1
            best_t = t
            
    df_t = pd.DataFrame(thresh_rows)
    opt_row = df_t.loc[df_t['t'] == best_t].iloc[0]
    t50_row = df_t.loc[(df_t['t'] - 0.50).abs().idxmin()]
    
    # For clinical passthrough where 0.50 achieves virtually optimal F1 (>0.98), lock 0.50
    # For imbalanced diseases where 0.50 severely harms recall, lock the validation-optimal threshold
    if selected_method == 'Clinical_Passthrough':
        locked_t = 0.50
    else:
        locked_t = round(best_t, 2)
        
    print(f"  Threshold Optimization (Validation):")
    print(f"    - Max F1 Threshold: t={best_t:.2f} -> F1={opt_row['f1']:.4f}, Prec={opt_row['prec']:.4f}, Rec={opt_row['rec']:.4f}, Spec={opt_row['spec']:.4f}")
    print(f"    - Default t=0.50:   t=0.50 -> F1={t50_row['f1']:.4f}, Prec={t50_row['prec']:.4f}, Rec={t50_row['rec']:.4f}, Spec={t50_row['spec']:.4f}")
    print(f"    - Locked Threshold: t={locked_t:.2f}")
    
    LOCKED_SPECS[dis] = {
        'method': selected_method,
        'threshold': locked_t,
        'model_dict': models['LR_CG'] if selected_method == 'LR_CG' else {'type': 'clinical'},
        'val_metrics': safe_metrics(y_v, selected_preds_val, t=locked_t)
    }

# ─────────────────────────────────────────────────────────────────────────────
# 4. FINAL TEST EVALUATION (SINGLE UNBIASED PASS ON 3,000 TEST PATIENTS)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("PHASE 4: SINGLE-PASS FINAL TEST SET EVALUATION (3,000 PATIENTS)")
print("=" * 80)

print(f"{'Disease':<22} {'Selected Method':<22} {'Thresh':>6} {'ROC-AUC':>8} {'PR-AUC':>8} {'F1':>8} {'Prec':>8} {'Rec':>8} {'Spec':>8} {'Brier':>8}")
print(f"{'':<22} {'':<22} {'':>6} {'ΔROC(vsClin)':>12} {'ΔPR(vsClin)':>12}")
print("-" * 105)

FINAL_TEST_SUMMARY = []

for dis in DISEASES:
    pc_t, pg_t, _, y_t = get_arrays(test_df, dis, is_train=False)
    spec = LOCKED_SPECS[dis]
    method = spec['method']
    t_locked = spec['threshold']
    m_dict = spec['model_dict']
    
    # Generate test predictions from locked model
    p_test_fused = predict_model(m_dict, pc_t, pg_t)
    
    # Metrics
    m_fused = safe_metrics(y_t, p_test_fused, t=t_locked)
    m_clin  = safe_metrics(y_t, pc_t, t=0.50)
    m_gut   = safe_metrics(y_t, pg_t, t=0.50)
    
    d_roc = m_fused['roc'] - m_clin['roc']
    d_pr  = m_fused['pr'] - m_clin['pr']
    
    print(f"{dis:<22} {method:<22} {t_locked:>6.2f} {m_fused['roc']:>8.4f} {m_fused['pr']:>8.4f} {m_fused['f1']:>8.4f} {m_fused['prec']:>8.4f} {m_fused['rec']:>8.4f} {m_fused['spec']:>8.4f} {m_fused['brier']:>8.4f}")
    print(f"{'Gain over Clinical alone:':<44} {d_roc:>+12.4f} {d_pr:>+12.4f}")
    print("-" * 105)
    
    # Store for reporting
    formula_str = "P_fused = P_Clinical" if method == 'Clinical_Passthrough' else f"P_fused = σ({m_dict['b0']:+.4f} + {m_dict['bc']:+.4f}·P_Clin + {m_dict['bg']:+.4f}·P_Gut)"
    FINAL_TEST_SUMMARY.append({
        'disease': dis,
        'method': method,
        'formula': formula_str,
        'threshold': t_locked,
        'test_roc': m_fused['roc'],
        'test_pr': m_fused['pr'],
        'test_f1': m_fused['f1'],
        'test_prec': m_fused['prec'],
        'test_rec': m_fused['rec'],
        'test_spec': m_fused['spec'],
        'test_brier': m_fused['brier'],
        'd_roc': d_roc,
        'd_pr': d_pr,
        'b0': m_dict.get('b0', None),
        'bc': m_dict.get('bc', None),
        'bg': m_dict.get('bg', None)
    })

print("\nFINAL DECISION PIPELINE COMPLETED SUCCESSFULLY.")
