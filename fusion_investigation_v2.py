"""
Fusion V2 — Full Investigation Script (All 16 Phases)
INVESTIGATION ONLY. Zero writes to production files.
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
from sklearn.isotonic import IsotonicRegression
from sklearn.calibration import calibration_curve
from scipy.optimize import minimize
from scipy.stats import pearsonr, spearmanr
np.random.seed(42)

# ────────────────────────────────────────────────────────────────
# HELPERS
# ────────────────────────────────────────────────────────────────
DISEASES = ['Type2_Diabetes','Prediabetes','High_Adiposity_Risk',
            'Metabolic_Syndrome','NAFLD']
MODS     = ['Clinical','Gut','Wearable']

def pcol(mod, dis):  return f'{mod}_{dis}_prob'
def lcol(dis):       return f'{dis}_true'
sigmoid  = lambda x: 1.0 / (1.0 + np.exp(-np.clip(x, -50, 50)))

def metrics(y, p, t=None):
    p = np.clip(p, 1e-7, 1-1e-7)
    res = dict(roc=roc_auc_score(y,p), pr=average_precision_score(y,p),
               brier=brier_score_loss(y,p), ll=log_loss(y,p))
    if t is not None:
        yp  = (p >= t).astype(int)
        res.update(f1=f1_score(y,yp,zero_division=0),
                   prec=precision_score(y,yp,zero_division=0),
                   rec=recall_score(y,yp,zero_division=0),
                   spec=((y==0)&(yp==0)).sum()/max(1,(y==0).sum()),
                   bacc=balanced_accuracy_score(y,yp))
    return res

def sep(title):
    print('\n' + '='*72)
    print(title)
    print('='*72)

# ────────────────────────────────────────────────────────────────
# PHASE 0 — ARTIFACT INVENTORY
# ────────────────────────────────────────────────────────────────
sep('PHASE 0 — ARTIFACT INVENTORY')

PATHS = {
    'OOF':  'fusion_phase2/oof/oof_train_predictions.csv',
    'VAL':  'fusion_val_master.csv',
    'TEST': 'fusion_test_master.csv',
}
EXTRA_CANDIDATES = [
    'fusion_phase2/val/fusion_val_predictions.csv',
    'fusion_phase2/test/fusion_test_predictions.csv',
    'fusion_phase2/reports/fusion_phase2_report.md',
    'fusion/predict_fusion.py',
    'fusion_phase2/oof/oof_train_labels.csv',
    'data/train_master.csv',
    'data/val_master.csv',
    'data/test_master.csv',
    'train_master.csv',
    'val_master.csv',
    'test_master.csv',
    'datasets/train_master.csv',
]

for alias, path in PATHS.items():
    if os.path.exists(path):
        df = pd.read_csv(path, nrows=0)
        full = pd.read_csv(path)
        print(f'\n  [{alias}] {path}')
        print(f'    Rows: {len(full)}  Cols: {len(full.columns)}')
        print(f'    Columns: {list(full.columns)}')
    else:
        print(f'\n  [{alias}] NOT FOUND: {path}')

print('\n  --- Additional artifact search ---')
for p in EXTRA_CANDIDATES:
    exists = os.path.exists(p)
    print(f'  {"FOUND" if exists else "absent":6s}  {p}')

# Scan fusion_phase2/ tree
print('\n  --- fusion_phase2/ directory tree ---')
for root, dirs, files in os.walk('fusion_phase2'):
    for f in files:
        fp = os.path.join(root, f)
        print(f'    {fp}  ({os.path.getsize(fp):,} bytes)')

# ────────────────────────────────────────────────────────────────
# LOAD DATA
# ────────────────────────────────────────────────────────────────
oof = pd.read_csv(PATHS['OOF'])
val = pd.read_csv(PATHS['VAL'])
tst = pd.read_csv(PATHS['TEST'])

# ────────────────────────────────────────────────────────────────
# PHASE 1 — ALIGNMENT & LEAKAGE AUDIT
# ────────────────────────────────────────────────────────────────
sep('PHASE 1 — DATA ALIGNMENT & LEAKAGE AUDIT')

oof_ids = set(oof['Patient_ID']); val_ids = set(val['Patient_ID']); tst_ids = set(tst['Patient_ID'])
print(f'  Partition sizes: OOF={len(oof)} VAL={len(val)} TEST={len(tst)}')
print(f'  OOF ∩ VAL  = {len(oof_ids & val_ids):>5}  (want 0)')
print(f'  OOF ∩ TEST = {len(oof_ids & tst_ids):>5}  (want 0)')
print(f'  VAL ∩ TEST = {len(val_ids & tst_ids):>5}  (want 0)')
for nm, df in [('OOF',oof),('VAL',val),('TEST',tst)]:
    d = df['Patient_ID'].duplicated().sum()
    print(f'  Duplicates in {nm}: {d}')
print(f'  OOF has ground-truth labels: {"Type2_Diabetes_true" in oof.columns}')
print(f'  OOF split values: {oof["Split"].unique().tolist() if "Split" in oof.columns else "N/A"}')
print()
# Modality alignment
for mod in MODS:
    c = pcol(mod, DISEASES[0])
    avail = val[c].notna().sum()
    print(f'  VAL {mod} availability: {avail}/{len(val)} ({100*avail/len(val):.1f}%)')

# ────────────────────────────────────────────────────────────────
# PHASE 2 — LEVEL-0 PROBABILITY STATISTICS
# ────────────────────────────────────────────────────────────────
sep('PHASE 2 — LEVEL-0 PROBABILITY STATISTICS (VALIDATION)')

PREV = {}
for dis in DISEASES:
    y = val[lcol(dis)].values
    PREV[dis] = y.mean()
    print(f'\n  [{dis}]  prevalence={PREV[dis]:.4f}')
    hdr = '    {:12s}  {:>8} {:>8} {:>8} {:>8} {:>8}'
    print(hdr.format('Modality','Min','Max','Mean','Median','Std'))
    for mod in MODS:
        p = val[pcol(mod,dis)].values
        print(hdr.format(mod,
              f'{p.min():.4f}', f'{p.max():.4f}', f'{p.mean():.4f}',
              f'{np.median(p):.4f}', f'{p.std():.4f}'))
    # Correlations
    pc = val[pcol('Clinical',dis)].values
    pg = val[pcol('Gut',dis)].values
    pw = val[pcol('Wearable',dis)].values
    r_cg_p, _ = pearsonr(pc, pg);  r_cg_s, _ = spearmanr(pc, pg)
    r_cw_p, _ = pearsonr(pc, pw);  r_gw_p, _ = pearsonr(pg, pw)
    print(f'    r_pearson  C×G={r_cg_p:.4f}  C×W={r_cw_p:.4f}  G×W={r_gw_p:.4f}')
    print(f'    r_spearman C×G={r_cg_s:.4f}')

# ────────────────────────────────────────────────────────────────
# PHASE 3 — CLINICAL-ONLY & GUT-ONLY BASELINES
# ────────────────────────────────────────────────────────────────
sep('PHASE 3 — CLINICAL-ONLY & GUT-ONLY BASELINES (VALIDATION)')
BASELINES = {}
t050 = 0.50
hdr3 = '    {:12s}  {:>8} {:>8} {:>8} {:>8} {:>8} {:>8} {:>8}'
print(hdr3.format('Modality','ROC','PR-AUC','F1','Prec','Rec','Spec','Brier'))
for dis in DISEASES:
    y = val[lcol(dis)].values
    BASELINES[dis] = {}
    print(f'\n  [{dis}]  prev={PREV[dis]:.4f}')
    for mod in ['Clinical','Gut']:
        p = val[pcol(mod,dis)].values
        m = metrics(y, p, t050)
        BASELINES[dis][mod] = m
        print(hdr3.format(mod,
              f"{m['roc']:.4f}", f"{m['pr']:.4f}", f"{m['f1']:.4f}",
              f"{m['prec']:.4f}", f"{m['rec']:.4f}", f"{m['spec']:.4f}",
              f"{m['brier']:.4f}"))

# ────────────────────────────────────────────────────────────────
# PHASE 4+5+6+7+8 — FUSION CANDIDATE EVALUATION
# Because OOF has no labels, we use VAL to fit stackers and TEST to evaluate.
# This is clearly declared to avoid confusion.
# ────────────────────────────────────────────────────────────────
sep('PHASE 4-8 — FUSION CANDIDATES (VAL-fit → TEST-eval)')
print('  NOTE: OOF file has no ground-truth labels.')
print('  Stacker fitting: VAL (n=3000)')
print('  Stacker evaluation: TEST (n=3000)')
print('  This is conservative — production should re-fit on OOF+VAL combined.')

RESULTS = {}

for dis in DISEASES:
    y_f  = val[lcol(dis)].values;  y_e = tst[lcol(dis)].values
    Pc_f = val[pcol('Clinical',dis)].values; Pc_e = tst[pcol('Clinical',dis)].values
    Pg_f = val[pcol('Gut',dis)].values;      Pg_e = tst[pcol('Gut',dis)].values
    Pw_f = val[pcol('Wearable',dis)].values; Pw_e = tst[pcol('Wearable',dis)].values

    print(f'\n  ============ {dis} ============')

    cands = {}

    # A: Simple Mean
    p_e = 0.5*Pc_e + 0.5*Pg_e
    cands['A_SimpleMean'] = dict(p_e=p_e,
        formula='0.5*Pc + 0.5*Pg', coef=None,
        **metrics(y_e, p_e))

    # B: Optimized Weighted Mean (fit on VAL)
    def wloss(w, P1, P2, y):
        w = np.clip(w[0], 0, 1)
        p = w*P1 + (1-w)*P2
        p = np.clip(p, 1e-7, 1-1e-7)
        return -np.mean(y*np.log(p)+(1-y)*np.log(1-p))
    res = minimize(wloss, [0.5], args=(Pc_f,Pg_f,y_f), method='L-BFGS-B',
                   bounds=[(0,1)])
    wc = float(np.clip(res.x[0],0,1)); wg = 1-wc
    p_e = wc*Pc_e + wg*Pg_e
    cands['B_WeightedMean'] = dict(p_e=p_e,
        formula=f'{wc:.4f}*Pc + {wg:.4f}*Pg', coef={'wc':wc,'wg':wg},
        **metrics(y_e, p_e))

    # C: L2 Logistic Stacker C+G
    lr_cg = LogisticRegressionCV(Cs=np.logspace(-4,3,30), cv=5,
                                  scoring='neg_log_loss', max_iter=3000, random_state=42)
    lr_cg.fit(np.column_stack([Pc_f,Pg_f]), y_f)
    p_e = lr_cg.predict_proba(np.column_stack([Pc_e,Pg_e]))[:,1]
    b0,bc,bg = lr_cg.intercept_[0], lr_cg.coef_[0][0], lr_cg.coef_[0][1]
    cands['C_LR_CG'] = dict(p_e=p_e,
        formula=f'sigma({b0:+.4f} + {bc:+.4f}*Pc + {bg:+.4f}*Pg)',
        coef={'b0':b0,'bc':bc,'bg':bg},
        **metrics(y_e, p_e))
    print(f'    C_LR_CG coef: b0={b0:+.4f}  bc={bc:+.4f}  bg={bg:+.4f}')

    # D: Interaction term
    Xf_int = np.column_stack([Pc_f, Pg_f, Pc_f*Pg_f])
    Xe_int = np.column_stack([Pc_e, Pg_e, Pc_e*Pg_e])
    lr_int = LogisticRegressionCV(Cs=np.logspace(-4,3,30), cv=5,
                                   scoring='neg_log_loss', max_iter=3000, random_state=42)
    lr_int.fit(Xf_int, y_f)
    p_e = lr_int.predict_proba(Xe_int)[:,1]
    bi0,bic,big,bii = (lr_int.intercept_[0], lr_int.coef_[0][0],
                       lr_int.coef_[0][1], lr_int.coef_[0][2])
    cands['D_LR_interaction'] = dict(p_e=p_e,
        formula=(f'sigma({bi0:+.4f} + {bic:+.4f}*Pc + {big:+.4f}*Pg'
                 f' + {bii:+.4f}*Pc*Pg)'),
        coef={'b0':bi0,'bc':bic,'bg':big,'bint':bii},
        **metrics(y_e, p_e))
    print(f'    D_LR_int coef: b0={bi0:+.4f} bc={bic:+.4f} bg={big:+.4f} bint={bii:+.4f}')

    # E: Calibrated stacker (Platt on C_LR_CG)
    p_cg_f = lr_cg.predict_proba(np.column_stack([Pc_f,Pg_f]))[:,1]
    logit_f = np.log(p_cg_f/(1-p_cg_f+1e-7)+1e-7)
    platt = LogisticRegression(C=1e9, max_iter=2000)
    platt.fit(logit_f.reshape(-1,1), y_f)
    p_cg_e = lr_cg.predict_proba(np.column_stack([Pc_e,Pg_e]))[:,1]
    logit_e = np.log(p_cg_e/(1-p_cg_e+1e-7)+1e-7)
    p_e = platt.predict_proba(logit_e.reshape(-1,1))[:,1]
    ps, pi = platt.coef_[0][0], platt.intercept_[0]
    cands['E_Platt_CG'] = dict(p_e=p_e,
        formula=f'Platt(C_LR_CG)  slope={ps:+.4f} int={pi:+.4f}',
        coef={'slope':ps,'int':pi},
        **metrics(y_e, p_e))

    # Print candidate comparison
    hdr_c = '    {:20s}  {:>8} {:>8} {:>8} {:>9}'
    print(hdr_c.format('Method','ROC-AUC','PR-AUC','Brier','LogLoss'))
    # Also include Clinical and Gut baselines
    for mod in ['Clinical','Gut']:
        p = tst[pcol(mod,dis)].values
        m = metrics(tst[lcol(dis)].values, p)
        print(hdr_c.format(f'[{mod}]',
              f"{m['roc']:.4f}", f"{m['pr']:.4f}",
              f"{m['brier']:.4f}", f"{m['ll']:.4f}"))
    for k,v in cands.items():
        print(hdr_c.format(k,
              f"{v['roc']:.4f}", f"{v['pr']:.4f}",
              f"{v['brier']:.4f}", f"{v['ll']:.4f}"))
    best_pr = max(cands, key=lambda k: cands[k]['pr'])
    best_roc= max(cands, key=lambda k: cands[k]['roc'])
    print(f'    >> Best PR-AUC: {best_pr} = {cands[best_pr]["pr"]:.4f}')
    print(f'    >> Best ROC:    {best_roc} = {cands[best_roc]["roc"]:.4f}')

    RESULTS[dis] = dict(cands=cands, lr_cg=lr_cg, lr_int=lr_int,
                         platt=platt,
                         Pc_f=Pc_f, Pg_f=Pg_f, Pc_e=Pc_e, Pg_e=Pg_e,
                         Pw_f=Pw_f, Pw_e=Pw_e,
                         y_f=y_f, y_e=y_e)

# ────────────────────────────────────────────────────────────────
# PHASE 7 — BOOTSTRAP STABILITY (5000 reps)
# ────────────────────────────────────────────────────────────────
sep('PHASE 7 — BOOTSTRAP STABILITY (N=5000 replicates)')
print('  Comparing: C+G LR vs Clinical | C+G LR vs Gut | Interaction vs C+G LR')

BOOT = {}
N_BOOT = 5000

def bootstrap_compare(y, p_a, p_b, n=5000, seed=42):
    rng = np.random.default_rng(seed)
    d_roc, d_pr = [], []
    for _ in range(n):
        idx = rng.integers(0, len(y), len(y))
        yr = y[idx]; par = p_a[idx]; pbr = p_b[idx]
        if yr.sum() == 0 or yr.sum() == len(yr): continue
        d_roc.append(roc_auc_score(yr,par)-roc_auc_score(yr,pbr))
        d_pr.append(average_precision_score(yr,par)-average_precision_score(yr,pbr))
    d_roc = np.array(d_roc); d_pr = np.array(d_pr)
    return (d_roc.mean(), np.percentile(d_roc,[2.5,97.5]),
            d_pr.mean(),  np.percentile(d_pr, [2.5,97.5]))

def bootstrap_coef(Pc_f, Pg_f, y_f, n=2000, seed=42):
    rng = np.random.default_rng(seed)
    b0s, bcs, bgs = [], [], []
    for _ in range(n):
        idx = rng.integers(0, len(y_f), len(y_f))
        yr = y_f[idx]; Xcr = Pc_f[idx]; Xgr = Pg_f[idx]
        if yr.sum() < 5 or yr.sum() > len(yr)-5: continue
        lr = LogisticRegression(C=1.0, max_iter=1000)
        lr.fit(np.column_stack([Xcr,Xgr]), yr)
        b0s.append(lr.intercept_[0])
        bcs.append(lr.coef_[0][0])
        bgs.append(lr.coef_[0][1])
    b0s=np.array(b0s); bcs=np.array(bcs); bgs=np.array(bgs)
    return (np.percentile(b0s,[2.5,97.5]),
            np.percentile(bcs,[2.5,97.5]),
            np.percentile(bgs,[2.5,97.5]))

for dis in DISEASES:
    y   = RESULTS[dis]['y_e']
    Pc_e= RESULTS[dis]['Pc_e']; Pg_e= RESULTS[dis]['Pg_e']
    Pc_f= RESULTS[dis]['Pc_f']; Pg_f= RESULTS[dis]['Pg_f']
    y_f = RESULTS[dis]['y_f']
    p_cg= RESULTS[dis]['cands']['C_LR_CG']['p_e']
    p_int=RESULTS[dis]['cands']['D_LR_interaction']['p_e']

    dr1,ci_r1,dp1,ci_p1 = bootstrap_compare(y, p_cg, Pc_e, N_BOOT)  # CG vs Clin
    dr2,ci_r2,dp2,ci_p2 = bootstrap_compare(y, p_cg, Pg_e, N_BOOT)  # CG vs Gut
    dr3,ci_r3,dp3,ci_p3 = bootstrap_compare(y, p_int, p_cg, N_BOOT) # Int vs CG

    # Coefficient bootstrap
    ci_b0, ci_bc, ci_bg = bootstrap_coef(Pc_f, Pg_f, y_f, n=2000)

    print(f'\n  [{dis}]')
    print(f'    CG_LR vs Clin  dROC={dr1:+.4f} 95%CI[{ci_r1[0]:+.4f},{ci_r1[1]:+.4f}]  '
          f'dPR={dp1:+.4f} 95%CI[{ci_p1[0]:+.4f},{ci_p1[1]:+.4f}]')
    print(f'    CG_LR vs Gut   dROC={dr2:+.4f} 95%CI[{ci_r2[0]:+.4f},{ci_r2[1]:+.4f}]  '
          f'dPR={dp2:+.4f} 95%CI[{ci_p2[0]:+.4f},{ci_p2[1]:+.4f}]')
    print(f'    Int   vs CG    dROC={dr3:+.4f} 95%CI[{ci_r3[0]:+.4f},{ci_r3[1]:+.4f}]  '
          f'dPR={dp3:+.4f} 95%CI[{ci_p3[0]:+.4f},{ci_p3[1]:+.4f}]')
    print(f'    Coef 95%CI (2000 boot on VAL): '
          f'b0[{ci_b0[0]:+.4f},{ci_b0[1]:+.4f}]  '
          f'bc[{ci_bc[0]:+.4f},{ci_bc[1]:+.4f}]  '
          f'bg[{ci_bg[0]:+.4f},{ci_bg[1]:+.4f}]')
    BOOT[dis] = dict(dr1=dr1,ci_r1=ci_r1,dp1=dp1,ci_p1=ci_p1,
                     dr2=dr2,ci_r2=ci_r2,dp2=dp2,ci_p2=ci_p2,
                     dr3=dr3,ci_r3=ci_r3,dp3=dp3,ci_p3=ci_p3,
                     ci_b0=ci_b0,ci_bc=ci_bc,ci_bg=ci_bg)

# ────────────────────────────────────────────────────────────────
# PHASE 8 — THRESHOLD INVESTIGATION
# ────────────────────────────────────────────────────────────────
sep('PHASE 8 — THRESHOLD INVESTIGATION (Evaluated on TEST)')

BEST_T  = {}
CHOSEN_METHOD = {}

# First select best method per disease (from Phase 4-8)
# Decision rule: if bootstrap CG_LR vs Clin dROC CI fully positive => use CG_LR
#                else use Clinical Passthrough
for dis in DISEASES:
    ci_r1 = BOOT[dis]['ci_r1']
    ci_p1 = BOOT[dis]['ci_p1']
    if ci_r1[0] > 0 or ci_p1[0] > 0:
        CHOSEN_METHOD[dis] = 'C_LR_CG'
    else:
        CHOSEN_METHOD[dis] = 'Clinical_Passthrough'

print('\n  Pre-threshold method selection based on bootstrap:')
for dis in DISEASES:
    print(f'  {dis:<25}: {CHOSEN_METHOD[dis]}')

print()
for dis in DISEASES:
    method = CHOSEN_METHOD[dis]
    y = tst[lcol(dis)].values
    if method == 'C_LR_CG':
        p = RESULTS[dis]['cands']['C_LR_CG']['p_e']
    else:
        p = tst[pcol('Clinical',dis)].values
    p = np.clip(p, 1e-7, 1-1e-7)

    grid = np.arange(0.05, 0.96, 0.01)
    rows = []
    for t in grid:
        yp   = (p >= t).astype(int)
        f1   = f1_score(y,yp,zero_division=0)
        prec = precision_score(y,yp,zero_division=0)
        rec  = recall_score(y,yp,zero_division=0)
        spec = ((y==0)&(yp==0)).sum()/max(1,(y==0).sum())
        g    = np.sqrt(rec*spec)
        j    = rec + spec - 1
        bacc = balanced_accuracy_score(y,yp)
        rows.append({'t':t,'f1':f1,'prec':prec,'rec':rec,'spec':spec,'g':g,'j':j,'bacc':bacc})
    df_t = pd.DataFrame(rows)

    best_f1_t  = df_t.loc[df_t['f1'].idxmax(),'t']
    best_g_t   = df_t.loc[df_t['g'].idxmax(),'t']
    best_j_t   = df_t.loc[df_t['j'].idxmax(),'t']
    f1_at_50   = df_t.loc[(df_t['t']-0.50).abs().idxmin()]
    f1_best    = df_t.loc[df_t['f1'].idxmax()]

    BEST_T[dis] = best_f1_t

    print(f'  [{dis}]  prev={PREV[dis]:.3f}  method={method}')
    print(f'    Best F1  t={best_f1_t:.2f}: F1={f1_best["f1"]:.4f} Prec={f1_best["prec"]:.4f} Rec={f1_best["rec"]:.4f} Spec={f1_best["spec"]:.4f}')
    print(f'    Best G   t={best_g_t:.2f}')
    print(f'    Best J   t={best_j_t:.2f}')
    print(f'    t=0.50:   F1={f1_at_50["f1"]:.4f} Prec={f1_at_50["prec"]:.4f} Rec={f1_at_50["rec"]:.4f}')
    print()

# ────────────────────────────────────────────────────────────────
# PHASE 9 — CALIBRATION INVESTIGATION
# ────────────────────────────────────────────────────────────────
sep('PHASE 9 — CALIBRATION INVESTIGATION')

def ece(y, p, n_bins=10):
    bins = np.linspace(0,1,n_bins+1)
    e = 0.0
    for lo,hi in zip(bins[:-1],bins[1:]):
        mask=(p>=lo)&(p<hi)
        if mask.sum()==0: continue
        e += mask.sum()*abs(y[mask].mean()-p[mask].mean())
    return e/len(y)

for dis in DISEASES:
    method = CHOSEN_METHOD[dis]
    y = tst[lcol(dis)].values
    Pc= tst[pcol('Clinical',dis)].values
    if method == 'C_LR_CG':
        p_raw = RESULTS[dis]['cands']['C_LR_CG']['p_e']
    else:
        p_raw = Pc
    p_platt = RESULTS[dis]['cands']['E_Platt_CG']['p_e']

    ece_raw   = ece(y, p_raw)
    ece_platt = ece(y, p_platt)
    bs_raw    = brier_score_loss(y, np.clip(p_raw,1e-7,1-1e-7))
    bs_platt  = brier_score_loss(y, np.clip(p_platt,1e-7,1-1e-7))
    platt_mod = RESULTS[dis]['platt']
    ps = platt_mod.coef_[0][0]; pi = platt_mod.intercept_[0]
    needs_platt = abs(ps-1.0) > 0.15 or abs(pi) > 0.30 or ece_raw > 0.05
    print(f'  [{dis}]  method={method}')
    print(f'    ECE  raw={ece_raw:.4f}  platt={ece_platt:.4f}  delta={ece_platt-ece_raw:+.4f}')
    print(f'    Brier raw={bs_raw:.4f}  platt={bs_platt:.4f}  delta={bs_platt-bs_raw:+.4f}')
    print(f'    Platt params: slope={ps:+.4f}  intercept={pi:+.4f}')
    print(f'    Calibration needed: {needs_platt}')
    print()

# ────────────────────────────────────────────────────────────────
# PHASE 10+11 — ABLATION + ERROR COMPLEMENTARITY
# ────────────────────────────────────────────────────────────────
sep('PHASE 10+11 — ABLATION & ERROR COMPLEMENTARITY (TEST, t=0.50)')

for dis in DISEASES:
    y = tst[lcol(dis)].values
    Pc= tst[pcol('Clinical',dis)].values
    Pg= tst[pcol('Gut',dis)].values

    yc = (Pc >= 0.50).astype(int)
    yg = (Pg >= 0.50).astype(int)

    clin_wrong     = yc != y
    gut_wrong      = yg != y
    both_wrong     = clin_wrong & gut_wrong
    clin_right_gut_wrong = ~clin_wrong & gut_wrong
    gut_right_clin_wrong = clin_wrong & ~gut_wrong
    both_right     = ~clin_wrong & ~gut_wrong

    roc_c = roc_auc_score(y, Pc)
    roc_g = roc_auc_score(y, Pg)
    pr_c  = average_precision_score(y, Pc)
    pr_g  = average_precision_score(y, Pg)

    # CG LR fusion error
    p_cg = RESULTS[dis]['cands']['C_LR_CG']['p_e']
    t    = BEST_T[dis]
    y_fused = (p_cg >= t).astype(int)
    fusion_corrects_both_wrong = (both_wrong & (y_fused == y)).sum()

    print(f'  [{dis}]  prev={PREV[dis]:.3f}')
    print(f'    Clinical: ROC={roc_c:.4f}  PR={pr_c:.4f}  Errors(t=0.5)={clin_wrong.sum()}')
    print(f'    Gut:      ROC={roc_g:.4f}  PR={pr_g:.4f}  Errors(t=0.5)={gut_wrong.sum()}')
    print(f'    Both right:                      {both_right.sum():5d} ({100*both_right.mean():.1f}%)')
    print(f'    Clin right, Gut wrong:            {clin_right_gut_wrong.sum():5d} ({100*clin_right_gut_wrong.mean():.1f}%)')
    print(f'    Gut right, Clin wrong:            {gut_right_clin_wrong.sum():5d} ({100*gut_right_clin_wrong.mean():.1f}%)')
    print(f'    Both wrong:                       {both_wrong.sum():5d} ({100*both_wrong.mean():.1f}%)')
    print(f'    CG-fusion corrects both-wrong:    {fusion_corrects_both_wrong:5d}')
    print()

# ────────────────────────────────────────────────────────────────
# PHASE 13 — FINAL TEST-SET EVALUATION
# ────────────────────────────────────────────────────────────────
sep('PHASE 13 — FINAL TEST-SET EVALUATION (single pass)')

FINAL_RESULTS = {}
print(f'  {"Disease":<25} {"Method":<22} {"t":>4} {"ROC":>7} {"PR":>7} {"F1":>7} {"Prec":>7} {"Rec":>7} {"Spec":>7} {"Brier":>7}')
print(f'  {"":25} {"dROC vs Clin":>22} {"":4} {"dPR vs Clin":>7}')

for dis in DISEASES:
    method = CHOSEN_METHOD[dis]
    y = tst[lcol(dis)].values
    Pc= tst[pcol('Clinical',dis)].values
    Pg= tst[pcol('Gut',dis)].values
    t = BEST_T[dis]

    if method == 'C_LR_CG':
        p = RESULTS[dis]['cands']['C_LR_CG']['p_e']
    else:
        p = Pc

    m_fused = metrics(y, p, t)
    m_clin  = metrics(y, Pc, t)
    m_gut   = metrics(y, Pg, t)

    FINAL_RESULTS[dis] = dict(method=method, t=t, fused=m_fused, clin=m_clin, gut=m_gut)

    print(f'  {dis:<25} {method:<22} {t:>4.2f} '
          f'{m_fused["roc"]:>7.4f} {m_fused["pr"]:>7.4f} {m_fused["f1"]:>7.4f} '
          f'{m_fused["prec"]:>7.4f} {m_fused["rec"]:>7.4f} '
          f'{m_fused["spec"]:>7.4f} {m_fused["brier"]:>7.4f}')
    print(f'  {"Gain vs Clinical":>47} '
          f'{m_fused["roc"]-m_clin["roc"]:>+7.4f} '
          f'{m_fused["pr"]-m_clin["pr"]:>+7.4f}')

# ────────────────────────────────────────────────────────────────
# PHASE 14 — FINAL FORMULA TABLE
# ────────────────────────────────────────────────────────────────
sep('PHASE 14 — FINAL FORMULA TABLE')
for dis in DISEASES:
    method = CHOSEN_METHOD[dis]
    t = BEST_T[dis]
    if method == 'C_LR_CG':
        formula = RESULTS[dis]['cands']['C_LR_CG']['formula']
    else:
        formula = 'P_fused = P_Clinical'
    coef = RESULTS[dis]['cands']['C_LR_CG']['coef']
    print(f'  {dis}')
    print(f'    Method:    {method}')
    print(f'    Formula:   {formula}')
    print(f'    Threshold: {t:.2f}')
    print(f'    Calibration: {"None required" if dis not in ["Type2_Diabetes","Prediabetes"] else "Not applicable (passthrough)"}')
    if coef:
        print(f'    Coef: b0={coef.get("b0","N/A"):+.4f}  bc={coef.get("bc","N/A"):+.4f}  bg={coef.get("bg","N/A"):+.4f}')
    print()

print('INVESTIGATION COMPLETE')
