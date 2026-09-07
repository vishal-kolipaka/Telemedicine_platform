import sys, os, time, warnings, json
import numpy as np
import pandas as pd
from scipy.stats import rankdata
from sklearn.metrics import (
    roc_auc_score, average_precision_score, brier_score_loss,
    f1_score, precision_score, recall_score
)
from sklearn.linear_model import LogisticRegression
from scipy.optimize import minimize

warnings.filterwarnings('ignore')
np.random.seed(42)

DISEASES = [
    'Type2_Diabetes',
    'Prediabetes',
    'High_Adiposity_Risk',
    'Metabolic_Syndrome',
    'NAFLD'
]

# Load data
oof_df = pd.read_csv('fusion_phase2/oof/oof_train_predictions.csv')
labels_df = pd.read_csv('datasets/labels_v3.csv')
split_df = pd.read_csv('datasets/split_manifest_v3.csv')

train_pids = split_df[split_df['Split'] == 'Train']['Patient_ID']
train_labels_df = labels_df[labels_df['Patient_ID'].isin(train_pids)].set_index('Patient_ID').loc[oof_df['Patient_ID']].reset_index()

val_df = pd.read_csv('fusion_val_master.csv')
test_df = pd.read_csv('fusion_test_master.csv')

def calc_ece(y_true, y_prob, n_bins=10):
    bins = np.linspace(0, 1, n_bins + 1)
    bin_indices = np.digitize(y_prob, bins) - 1
    bin_indices = np.clip(bin_indices, 0, n_bins - 1)
    
    ece = 0.0
    n = len(y_true)
    for b in range(n_bins):
        mask = (bin_indices == b)
        if np.sum(mask) > 0:
            acc = np.mean(y_true[mask])
            conf = np.mean(y_prob[mask])
            ece += (np.sum(mask) / n) * np.abs(acc - conf)
    return ece

def evaluate_predictions(y_true, y_prob, threshold=0.5):
    y_prob_c = np.clip(y_prob, 1e-7, 1 - 1e-7)
    roc = roc_auc_score(y_true, y_prob_c)
    pr = average_precision_score(y_true, y_prob_c)
    brier = brier_score_loss(y_true, y_prob_c)
    ece = calc_ece(y_true, y_prob_c)
    
    y_pred = (y_prob >= threshold).astype(int)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    tn = np.sum((y_true == 0) & (y_pred == 0))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    spec = tn / max(1, tn + fp)
    
    return {
        'ROC-AUC': roc,
        'PR-AUC': pr,
        'F1': f1,
        'Precision': prec,
        'Recall': rec,
        'Specificity': spec,
        'Brier': brier,
        'ECE': ece,
        'Threshold': threshold
    }

def find_best_threshold(y_true, y_prob):
    best_t = 0.5
    best_f1 = -1
    for t in np.linspace(0.05, 0.95, 91):
        yp = (y_prob >= t).astype(int)
        f = f1_score(y_true, yp, zero_division=0)
        if f > best_f1:
            best_f1 = f
            best_t = t
    return best_t

def fast_auc(y_true, scores):
    pos_mask = (y_true == 1)
    n_pos = np.sum(pos_mask)
    n_neg = len(y_true) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.5
    ranks = rankdata(scores)
    return (np.sum(ranks[pos_mask]) - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)

def run_paired_bootstrap(y_true, p1, p2, n_boot=5000, seed=42):
    rng = np.random.RandomState(seed)
    n = len(y_true)
    boot_idx = rng.choice(n, size=(n_boot, n), replace=True)
    
    auc_diffs = np.zeros(n_boot)
    pr_diffs = np.zeros(n_boot)
    brier_diffs = np.zeros(n_boot)
    
    # We can do exact or fast for AUC
    for i in range(n_boot):
        idx = boot_idx[i]
        y_b = y_true[idx]
        p1_b = p1[idx]
        p2_b = p2[idx]
        
        auc_diffs[i] = fast_auc(y_b, p2_b) - fast_auc(y_b, p1_b)
        brier_diffs[i] = np.mean((p2_b - y_b)**2) - np.mean((p1_b - y_b)**2)
        # calculate PR AUC every 5 bootstrap steps for speed, or on full
        if i % 10 == 0:
            pr_diffs[i] = average_precision_score(y_b, p2_b) - average_precision_score(y_b, p1_b)
        else:
            pr_diffs[i] = pr_diffs[i - 1]
            
    auc_lo, auc_hi = np.percentile(auc_diffs, [2.5, 97.5])
    pr_lo, pr_hi = np.percentile(pr_diffs, [2.5, 97.5])
    br_lo, br_hi = np.percentile(brier_diffs, [2.5, 97.5])
    
    return {
        'delta_roc': np.mean(auc_diffs),
        'roc_ci': (auc_lo, auc_hi),
        'delta_pr': np.mean(pr_diffs),
        'pr_ci': (pr_lo, pr_hi),
        'delta_brier': np.mean(brier_diffs),
        'brier_ci': (br_lo, br_hi),
        'roc_sig': (auc_lo > 0 and auc_hi > 0) or (auc_lo < 0 and auc_hi < 0),
        'pr_sig': (pr_lo > 0 and pr_hi > 0) or (pr_lo < 0 and pr_hi < 0),
    }

def fit_and_predict_strategies(dis):
    y_train = train_labels_df[dis].values
    y_val = val_df[f'{dis}_true'].values
    y_test = test_df[f'{dis}_true'].values
    
    c_oof = oof_df[f'Clinical_{dis}_prob'].values
    g_oof = oof_df[f'Gut_{dis}_prob'].values
    w_oof = oof_df[f'Wearable_{dis}_prob'].values
    
    c_val = val_df[f'Clinical_{dis}_prob'].values
    g_val = val_df[f'Gut_{dis}_prob'].values
    w_val = val_df[f'Wearable_{dis}_prob'].values
    
    c_test = test_df[f'Clinical_{dis}_prob'].values
    g_test = test_df[f'Gut_{dis}_prob'].values
    w_test = test_df[f'Wearable_{dis}_prob'].values
    
    results = {}
    
    # 1. Single Modalities
    results['C'] = {'val_prob': c_val, 'test_prob': c_test, 'formula': 'P_c', 'type': 'Single Modality'}
    results['G'] = {'val_prob': g_val, 'test_prob': g_test, 'formula': 'P_g', 'type': 'Single Modality'}
    results['W'] = {'val_prob': w_val, 'test_prob': w_test, 'formula': 'P_w', 'type': 'Single Modality'}
    
    # Pairs and Triplets
    combos = {
        'C+G': (['Clinical', 'Gut'], [c_oof, g_oof], [c_val, g_val], [c_test, g_test]),
        'C+W': (['Clinical', 'Wearable'], [c_oof, w_oof], [c_val, w_val], [c_test, w_test]),
        'G+W': (['Gut', 'Wearable'], [g_oof, w_oof], [g_val, w_val], [g_test, w_test]),
        'C+G+W': (['Clinical', 'Gut', 'Wearable'], [c_oof, g_oof, w_oof], [c_val, g_val, w_val], [c_test, g_test, w_test]),
    }
    
    for cname, (mod_names, oof_list, val_list, test_list) in combos.items():
        X_oof = np.column_stack(oof_list)
        X_val = np.column_stack(val_list)
        X_test = np.column_stack(test_list)
        
        # A. Simple Average
        val_sa = np.mean(X_val, axis=1)
        test_sa = np.mean(X_test, axis=1)
        results[f'{cname}_SimpleAvg'] = {
            'val_prob': val_sa, 'test_prob': test_sa,
            'formula': f"({' + '.join([m[0] for m in mod_names])}) / {len(mod_names)}",
            'type': 'Simple Average'
        }
        
        # B. Weighted Average (Learned on Train/OOF via Brier minimization)
        def loss_weights(w):
            w = np.array(w)
            w = w / np.sum(w)
            p = np.dot(X_oof, w)
            return brier_score_loss(y_train, p)
        
        init_w = np.ones(len(mod_names)) / len(mod_names)
        bounds = [(0, 1)] * len(mod_names)
        cons = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0})
        res_w = minimize(loss_weights, init_w, method='SLSQP', bounds=bounds, constraints=cons)
        best_w = res_w.x / np.sum(res_w.x)
        
        val_wa = np.dot(X_val, best_w)
        test_wa = np.dot(X_test, best_w)
        w_str = ' + '.join([f"{best_w[i]:.3f}*{mod_names[i][0]}" for i in range(len(mod_names))])
        results[f'{cname}_WeightedAvg'] = {
            'val_prob': val_wa, 'test_prob': test_wa,
            'formula': w_str,
            'weights': best_w,
            'type': 'Weighted Average'
        }
        
        # C. Logistic Stacker (L2)
        lr = LogisticRegression(penalty='l2', C=1.0, solver='lbfgs', random_state=42)
        lr.fit(X_oof, y_train)
        val_lr = lr.predict_proba(X_val)[:, 1]
        test_lr = lr.predict_proba(X_test)[:, 1]
        coef_str = f"sigmoid({lr.intercept_[0]:.3f} + " + ' + '.join([f"{lr.coef_[0][i]:.3f}*{mod_names[i][0]}" for i in range(len(mod_names))]) + ")"
        results[f'{cname}_Logistic'] = {
            'val_prob': val_lr, 'test_prob': test_lr,
            'formula': coef_str,
            'coefs': lr.coef_[0],
            'intercept': lr.intercept_[0],
            'type': 'Logistic Stacker'
        }
        
        # D. Logistic Stacker with Non-Negative Bounds
        def loss_logistic_nonneg(params):
            b0 = params[0]
            w = params[1:]
            logit = b0 + np.dot(X_oof, w)
            p = 1.0 / (1.0 + np.exp(-np.clip(logit, -50, 50)))
            p = np.clip(p, 1e-7, 1 - 1e-7)
            bce = -np.mean(y_train * np.log(p) + (1 - y_train) * np.log(1 - p))
            l2 = 0.5 * 1.0 * np.sum(w**2)
            return bce + l2
        
        init_p = np.array([0.0] + [0.5]*len(mod_names))
        bnds = [(None, None)] + [(0.0, None)]*len(mod_names)
        res_nn = minimize(loss_logistic_nonneg, init_p, method='L-BFGS-B', bounds=bnds)
        b0_nn = res_nn.x[0]
        w_nn = res_nn.x[1:]
        val_nn = 1.0 / (1.0 + np.exp(-np.clip(b0_nn + np.dot(X_val, w_nn), -50, 50)))
        test_nn = 1.0 / (1.0 + np.exp(-np.clip(b0_nn + np.dot(X_test, w_nn), -50, 50)))
        coef_nn_str = f"sigmoid({b0_nn:.3f} + " + ' + '.join([f"{w_nn[i]:.3f}*{mod_names[i][0]}" for i in range(len(mod_names))]) + ")"
        results[f'{cname}_LogisticNonNeg'] = {
            'val_prob': val_nn, 'test_prob': test_nn,
            'formula': coef_nn_str,
            'coefs': w_nn,
            'intercept': b0_nn,
            'type': 'NonNeg Logistic Stacker'
        }
        
        # E. Interaction Candidate
        if len(mod_names) == 2:
            X_oof_int = np.column_stack([X_oof, X_oof[:, 0] * X_oof[:, 1]])
            X_val_int = np.column_stack([X_val, X_val[:, 0] * X_val[:, 1]])
            X_test_int = np.column_stack([X_test, X_test[:, 0] * X_test[:, 1]])
            lr_int = LogisticRegression(penalty='l2', C=1.0, solver='lbfgs', random_state=42)
            lr_int.fit(X_oof_int, y_train)
            val_int = lr_int.predict_proba(X_val_int)[:, 1]
            test_int = lr_int.predict_proba(X_test_int)[:, 1]
            int_str = f"sigmoid({lr_int.intercept_[0]:.3f} + {lr_int.coef_[0][0]:.3f}*{mod_names[0][0]} + {lr_int.coef_[0][1]:.3f}*{mod_names[1][0]} + {lr_int.coef_[0][2]:.3f}*{mod_names[0][0]}*{mod_names[1][0]})"
            results[f'{cname}_Interaction'] = {
                'val_prob': val_int, 'test_prob': test_int,
                'formula': int_str,
                'type': 'Interaction Stacker'
            }
        elif len(mod_names) == 3:
            X_oof_int = np.column_stack([
                X_oof,
                X_oof[:, 0] * X_oof[:, 1], # C*G
                X_oof[:, 0] * X_oof[:, 2], # C*W
                X_oof[:, 1] * X_oof[:, 2]  # G*W
            ])
            X_val_int = np.column_stack([
                X_val,
                X_val[:, 0] * X_val[:, 1],
                X_val[:, 0] * X_val[:, 2],
                X_val[:, 1] * X_val[:, 2]
            ])
            X_test_int = np.column_stack([
                X_test,
                X_test[:, 0] * X_test[:, 1],
                X_test[:, 0] * X_test[:, 2],
                X_test[:, 1] * X_test[:, 2]
            ])
            lr_int = LogisticRegression(penalty='l2', C=1.0, solver='lbfgs', random_state=42)
            lr_int.fit(X_oof_int, y_train)
            val_int = lr_int.predict_proba(X_val_int)[:, 1]
            test_int = lr_int.predict_proba(X_test_int)[:, 1]
            int_str = f"sigmoid({lr_int.intercept_[0]:.3f} + {lr_int.coef_[0][0]:.3f}*C + {lr_int.coef_[0][1]:.3f}*G + {lr_int.coef_[0][2]:.3f}*W + {lr_int.coef_[0][3]:.3f}*CG + {lr_int.coef_[0][4]:.3f}*CW + {lr_int.coef_[0][5]:.3f}*GW)"
            results[f'{cname}_Interaction'] = {
                'val_prob': val_int, 'test_prob': test_int,
                'formula': int_str,
                'type': 'Interaction Stacker'
            }
            
    return results

print('========================================================================')
print('  STARTING MULTI-MODALITY COMBINATION CONTRIBUTION INVESTIGATION')
print('========================================================================')

all_investigation_data = {}

for dis in DISEASES:
    print(f'\n>>> Processing Disease: {dis} ...')
    y_val = val_df[f'{dis}_true'].values
    y_test = test_df[f'{dis}_true'].values
    
    strategies = fit_and_predict_strategies(dis)
    
    dis_data = {
        'val_metrics': {},
        'test_metrics': {},
        'thresholds': {},
        'formulas': {},
        'bootstrap': {}
    }
    
    # 1. Evaluate on Validation & Find Best Threshold
    for sname, sdata in strategies.items():
        v_prob = sdata['val_prob']
        best_t = find_best_threshold(y_val, v_prob)
        v_metrics = evaluate_predictions(y_val, v_prob, threshold=best_t)
        
        dis_data['val_metrics'][sname] = v_metrics
        dis_data['thresholds'][sname] = best_t
        dis_data['formulas'][sname] = sdata.get('formula', '')
        
        # Test evaluation with frozen threshold
        t_prob = sdata['test_prob']
        t_metrics = evaluate_predictions(y_test, t_prob, threshold=best_t)
        dis_data['test_metrics'][sname] = t_metrics
        
    # 2. Bootstrap comparisons on Validation (5,000 replicates)
    # Target comparisons
    comparisons = [
        ('C', 'C+G_Logistic', 'Add G to C'),
        ('C', 'C+W_Logistic', 'Add W to C'),
        ('G', 'G+W_Logistic', 'Add W to G'),
        ('W', 'C+W_Logistic', 'Add C to W'),
        ('C+G_Logistic', 'C+G+W_Logistic', 'Add W to C+G'),
        ('C+W_Logistic', 'C+G+W_Logistic', 'Add G to C+W'),
        ('G+W_Logistic', 'C+G+W_Logistic', 'Add C to G+W'),
        ('C+G_Logistic', 'C+G+W_LogisticNonNeg', 'Add W to C+G (NonNeg)'),
    ]
    
    for base_key, cand_key, comp_name in comparisons:
        if base_key in strategies and cand_key in strategies:
            p_base = strategies[base_key]['val_prob']
            p_cand = strategies[cand_key]['val_prob']
            boot_res = run_paired_bootstrap(y_val, p_base, p_cand, n_boot=5000)
            dis_data['bootstrap'][comp_name] = boot_res
            
    all_investigation_data[dis] = dis_data

# Save results to json for detailed extraction
with open('investigation_results.json', 'w') as f:
    # Convert numpy / tuple objects for json
    def convert(o):
        if isinstance(o, (np.float32, np.float64, np.int32, np.int64)): return float(o)
        if isinstance(o, np.ndarray): return o.tolist()
        if isinstance(o, tuple): return list(o)
        if isinstance(o, (np.bool_, bool)): return bool(o)
        return str(o)
    json.dump(all_investigation_data, f, indent=2, default=convert)

print('\nInvestigation complete! Data saved to investigation_results.json.')
