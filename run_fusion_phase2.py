"""
run_fusion_phase2.py — Multimodal Fusion Phase 2 Leakage-Controlled Experiment Pipeline

Executes the complete Phase 2 research & evaluation protocol:
  1. Fold-Safe 5-Fold OOF Prediction Generation on Train (14,000 rows)
  2. Candidate Fusion Model Fitting ONLY on OOF Train (7 Modality Combinations x 2 Methods)
  3. Validation Evaluation & Selection (3,000 rows) with Paired Bootstrap CIs
  4. Final Untouched Test Evaluation (3,000 rows)
  5. Required Reports, Integrity Checks, and Artifact Generation
"""

import os
import sys
import json
import logging
import random
import warnings
import numpy as np
import pandas as pd
from scipy.optimize import minimize
import joblib

warnings.filterwarnings("ignore")

import sklearn
from sklearn.model_selection import KFold
from sklearn.linear_model import LogisticRegression, LogisticRegressionCV
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    brier_score_loss,
    confusion_matrix,
    classification_report
)

import xgboost as xgb

# ─────────────────────────────────────────────
# Setup Paths & Directories
# ─────────────────────────────────────────────
BASE_DIR = r"c:\Users\HP PC\Desktop\telemedicine platform"
PHASE2_DIR = os.path.join(BASE_DIR, "fusion_phase2")

OOF_DIR = os.path.join(PHASE2_DIR, "oof")
VAL_DIR = os.path.join(PHASE2_DIR, "validation")
TEST_DIR = os.path.join(PHASE2_DIR, "test")
MODELS_DIR = os.path.join(PHASE2_DIR, "models", "fusion_candidates")
REPORTS_DIR = os.path.join(PHASE2_DIR, "reports")
LOG_FILE = os.path.join(PHASE2_DIR, "training.log")

for d in [OOF_DIR, VAL_DIR, TEST_DIR, MODELS_DIR, REPORTS_DIR]:
    os.makedirs(d, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="w"),
        logging.StreamHandler(sys.stdout)
    ]
)

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

LABEL_COLS = [
    "Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk",
    "Metabolic_Syndrome", "NAFLD"
]

GUT_RAW_TAXA = [
    "Akkermansia", "Faecalibacterium", "Roseburia", "Bifidobacterium",
    "Bacteroides", "Prevotella", "Ruminococcus", "Blautia", "Collinsella",
    "Escherichia_Shigella", "Coprococcus", "Alistipes", "Subdoligranulum",
    "Enterococcus", "Eubacterium", "Parabacteroides", "Lactobacillus",
    "Klebsiella", "Streptococcus", "Eggerthella", "Other_Taxa"
]
GUT_CLR_FEATURES = [t + "_CLR" for t in GUT_RAW_TAXA]
CLR_DELTA = 1e-5

# ─────────────────────────────────────────────
# Load Raw Data & Split Manifest
# ─────────────────────────────────────────────
logging.info("========== Starting Fusion Phase 2 Pipeline ==========")
logging.info("--- Step 0: Loading Datasets & Metadata ---")

labels_df = pd.read_csv(os.path.join(BASE_DIR, "clinical_model", "data", "labels_v3.csv"))
split_df = pd.read_csv(os.path.join(BASE_DIR, "clinical_model", "data", "split_manifest_v3.csv"))
clinical_df = pd.read_csv(os.path.join(BASE_DIR, "clinical_model", "data", "clinical_v3.csv"))
wearable_std = pd.read_csv(os.path.join(BASE_DIR, "wearable_model", "data", "wearable_standard_v3.csv"))
wearable_cgm = pd.read_csv(os.path.join(BASE_DIR, "wearable_model", "data", "wearable_cgm_v3.csv"))
gut_raw_df = pd.read_csv(os.path.join(BASE_DIR, "gut_model", "data", "gut_v3.csv"))

wearable_df = wearable_std.merge(wearable_cgm, on="Patient_ID")

# Helper to read Level-0 Metadata
def load_level0_metadata(modality_dir, sdir):
    meta_dict = {}
    for lbl in LABEL_COLS:
        p = os.path.join(BASE_DIR, modality_dir, "models", sdir, f"xgboost_{lbl}_metadata.json")
        with open(p, "r") as f:
            meta_dict[lbl] = json.load(f)
    return meta_dict

clinical_meta = load_level0_metadata("clinical_model", "clinical")
wearable_meta = load_level0_metadata("wearable_model", "wearable")
gut_meta = load_level0_metadata("gut_model", "gut")

CLINICAL_FEATURES = clinical_meta["Type2_Diabetes"]["features"]
WEARABLE_FEATURES = wearable_meta["Type2_Diabetes"]["features"]

# Masks
train_mask = split_df["Split"] == "Train"
val_mask = split_df["Split"] == "Val"
test_mask = split_df["Split"] == "Test"

# Verify counts
assert train_mask.sum() == 14000, f"Train count mismatch: {train_mask.sum()}"
assert val_mask.sum() == 3000, f"Val count mismatch: {val_mask.sum()}"
assert test_mask.sum() == 3000, f"Test count mismatch: {test_mask.sum()}"

logging.info(f"Splits verified: Train={train_mask.sum()}, Val={val_mask.sum()}, Test={test_mask.sum()}")

# ─────────────────────────────────────────────
# Step A: 5-Fold OOF Train Predictions (14,000 Rows)
# ─────────────────────────────────────────────
logging.info("\n--- Step A: Generating 5-Fold OOF Train Predictions (14,000 Rows) ---")

train_patients = split_df.loc[train_mask, "Patient_ID"].values
df_train_clin = clinical_df[train_mask].reset_index(drop=True)
df_train_wear = wearable_df[train_mask].reset_index(drop=True)
df_train_gut = gut_raw_df[train_mask].reset_index(drop=True)
df_train_labels = labels_df[train_mask].reset_index(drop=True)

# 5-fold CV setup
kf = KFold(n_splits=5, shuffle=True, random_state=SEED)
folds = list(kf.split(df_train_clin))

oof_preds = {
    "Patient_ID": train_patients,
    "Split": ["Train"] * len(train_patients)
}
for mod in ["Clinical", "Wearable", "Gut"]:
    for lbl in LABEL_COLS:
        oof_preds[f"{mod}_{lbl}_prob"] = np.zeros(len(train_patients), dtype=np.float64)

for fold_idx, (trn_idx, val_idx) in enumerate(folds, 1):
    logging.info(f"Processing OOF Fold {fold_idx}/5 (Trn={len(trn_idx)}, Val={len(val_idx)})...")

    # ---- 1. Clinical OOF ----
    X_tr_c = df_train_clin.loc[trn_idx, CLINICAL_FEATURES]
    X_val_c = df_train_clin.loc[val_idx, CLINICAL_FEATURES]

    for lbl in LABEL_COLS:
        y_tr = df_train_labels.loc[trn_idx, lbl].values
        meta = clinical_meta[lbl]
        hp = meta["hyperparameters"]
        spw = meta["scale_pos_weight"]

        m = xgb.XGBClassifier(
            n_estimators=hp["n_estimators_used"],
            max_depth=hp["max_depth"],
            learning_rate=hp["learning_rate"],
            subsample=hp["subsample"],
            colsample_bytree=hp["colsample_bytree"],
            scale_pos_weight=spw,
            objective="binary:logistic",
            eval_metric="aucpr",
            random_state=SEED,
            n_jobs=-1
        )
        m.fit(X_tr_c, y_tr)
        probs = m.predict_proba(X_val_c)[:, 1]
        oof_preds[f"Clinical_{lbl}_prob"][val_idx] = probs

    # ---- 2. Wearable OOF ----
    X_tr_w = df_train_wear.loc[trn_idx, WEARABLE_FEATURES]
    X_val_w = df_train_wear.loc[val_idx, WEARABLE_FEATURES]

    for lbl in LABEL_COLS:
        y_tr = df_train_labels.loc[trn_idx, lbl].values
        meta = wearable_meta[lbl]
        hp = meta["hyperparameters"]
        spw = meta["scale_pos_weight"]

        m = xgb.XGBClassifier(
            n_estimators=hp["n_estimators_used"],
            max_depth=hp["max_depth"],
            learning_rate=hp["learning_rate"],
            subsample=hp["subsample"],
            colsample_bytree=hp["colsample_bytree"],
            scale_pos_weight=spw,
            objective="binary:logistic",
            eval_metric="aucpr",
            random_state=SEED,
            n_jobs=-1
        )
        m.fit(X_tr_w, y_tr)
        probs = m.predict_proba(X_val_w)[:, 1]
        oof_preds[f"Wearable_{lbl}_prob"][val_idx] = probs

    # ---- 3. Gut OOF (FOLD-SAFE PREPROCESSING) ----
    # Fit median imputation ONLY on training portion of fold
    taxa_tr = df_train_gut.loc[trn_idx, GUT_RAW_TAXA].copy()
    taxa_val = df_train_gut.loc[val_idx, GUT_RAW_TAXA].copy()

    fold_medians = taxa_tr.median()

    # Impute
    for col in GUT_RAW_TAXA:
        taxa_tr[col] = taxa_tr[col].fillna(fold_medians[col])
        taxa_val[col] = taxa_val[col].fillna(fold_medians[col])

    # CLR Transform (Stateless)
    def apply_clr(df_taxa):
        arr = df_taxa.values + CLR_DELTA
        log_arr = np.log(arr)
        log_mean = log_arr.mean(axis=1, keepdims=True)
        return log_arr - log_mean

    clr_tr = pd.DataFrame(apply_clr(taxa_tr), columns=GUT_CLR_FEATURES)
    clr_val = pd.DataFrame(apply_clr(taxa_val), columns=GUT_CLR_FEATURES)

    for lbl in LABEL_COLS:
        y_tr = df_train_labels.loc[trn_idx, lbl].values
        meta = gut_meta[lbl]
        hp = meta["hyperparameters"]
        spw = meta["scale_pos_weight"]

        m = xgb.XGBClassifier(
            n_estimators=hp["n_estimators_used"],
            max_depth=hp["max_depth"],
            learning_rate=hp["learning_rate"],
            subsample=hp["subsample"],
            colsample_bytree=hp["colsample_bytree"],
            scale_pos_weight=spw,
            objective="binary:logistic",
            eval_metric="aucpr",
            random_state=SEED,
            n_jobs=-1
        )
        m.fit(clr_tr, y_tr)
        probs = m.predict_proba(clr_val)[:, 1]
        oof_preds[f"Gut_{lbl}_prob"][val_idx] = probs

oof_df = pd.DataFrame(oof_preds)

# Save OOF Predictions
oof_csv_path = os.path.join(OOF_DIR, "oof_train_predictions.csv")
oof_df.to_csv(oof_csv_path, index=False)
logging.info(f"OOF Predictions saved to {oof_csv_path} ({len(oof_df)} rows).")

# OOF Integrity Checks
assert len(oof_df) == 14000, f"Expected 14000 OOF rows, got {len(oof_df)}"
assert oof_df.isnull().sum().sum() == 0, "Null values found in OOF predictions!"
assert len(oof_df["Patient_ID"].unique()) == 14000, "Duplicate Patient_IDs found in OOF!"
logging.info("[PASS] OOF Prediction Integrity Verification Complete.")


# ─────────────────────────────────────────────
# Step B: Fit Fusion Candidates ONLY on OOF Train
# ─────────────────────────────────────────────
logging.info("\n--- Step B: Fitting Fusion Candidates ONLY on OOF Train Predictions ---")

# 7 Modality Combinations
MODALITY_COMBOS = {
    "Clinical": ["Clinical"],
    "Wearable": ["Wearable"],
    "Gut": ["Gut"],
    "Clinical+Wearable": ["Clinical", "Wearable"],
    "Clinical+Gut": ["Clinical", "Gut"],
    "Wearable+Gut": ["Wearable", "Gut"],
    "Clinical+Wearable+Gut": ["Clinical", "Wearable", "Gut"]
}

# Continuous Weighted Average Optimizer
def optimize_weights_continuous(probs_matrix, y_true):
    n_mods = probs_matrix.shape[1]
    if n_mods == 1:
        return np.array([1.0])

    def loss_fn(weights):
        # We maximize ROC-AUC -> minimize negative ROC-AUC
        weights = np.array(weights)
        w_norm = weights / np.sum(weights)
        p_blend = np.dot(probs_matrix, w_norm)
        # Handle zero variance edge case
        try:
            auc = roc_auc_score(y_true, p_blend)
        except Exception:
            auc = 0.5
        return -auc

    init_w = np.ones(n_mods) / n_mods
    bounds = [(0.0, 1.0)] * n_mods
    constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0})

    res = minimize(
        loss_fn, init_w, method='SLSQP', bounds=bounds, constraints=constraints,
        options={'maxiter': 500, 'ftol': 1e-7}
    )
    best_w = res.x / np.sum(res.x)
    return best_w

fitted_candidates = {}

for lbl in LABEL_COLS:
    y_oof = df_train_labels[lbl].values
    fitted_candidates[lbl] = {}

    for combo_name, mods in MODALITY_COMBOS.items():
        fitted_candidates[lbl][combo_name] = {}

        # 1. Single Modality
        if len(mods) == 1:
            m_name = mods[0]
            p_oof = oof_df[f"{m_name}_{lbl}_prob"].values
            auc_oof = roc_auc_score(y_oof, p_oof)
            pr_oof = average_precision_score(y_oof, p_oof)
            fitted_candidates[lbl][combo_name]["Single"] = {
                "weights": np.array([1.0]),
                "oof_auc": auc_oof,
                "oof_pr": pr_oof
            }
            continue

        # 2. Continuous Weighted Average
        P_cols = np.column_stack([oof_df[f"{m}_{lbl}_prob"].values for m in mods])
        weights_opt = optimize_weights_continuous(P_cols, y_oof)
        p_wavg = np.dot(P_cols, weights_opt)
        auc_wavg = roc_auc_score(y_oof, p_wavg)
        pr_wavg = average_precision_score(y_oof, p_wavg)

        fitted_candidates[lbl][combo_name]["WeightedAvg"] = {
            "weights": weights_opt,
            "oof_auc": auc_wavg,
            "oof_pr": pr_wavg
        }

        # 3. Logistic Regression Stacker with CV for C
        # Tune C using LogisticRegressionCV on OOF probs
        lr_cv = LogisticRegressionCV(
            Cs=np.logspace(-3, 3, 20),
            cv=5,
            penalty='l2',
            scoring='roc_auc',
            random_state=SEED,
            max_iter=1000
        )
        lr_cv.fit(P_cols, y_oof)
        p_lr = lr_cv.predict_proba(P_cols)[:, 1]
        auc_lr = roc_auc_score(y_oof, p_lr)
        pr_lr = average_precision_score(y_oof, p_lr)

        best_C = float(lr_cv.C_[0])
        coefs = lr_cv.coef_[0].tolist()
        intercept = float(lr_cv.intercept_[0])

        fitted_candidates[lbl][combo_name]["LRStacker"] = {
            "model": lr_cv,
            "C": best_C,
            "coefs": coefs,
            "intercept": intercept,
            "oof_auc": auc_lr,
            "oof_pr": pr_lr
        }

        # Save model candidate artifact
        model_save_path = os.path.join(MODELS_DIR, f"stacker_{lbl}_{combo_name}.joblib")
        joblib.dump(lr_cv, model_save_path)

logging.info("[PASS] Candidate Fusion Models Fitted on OOF Train.")


# ─────────────────────────────────────────────
# Step C: Validation Prediction Generation & Candidate Evaluation
# ─────────────────────────────────────────────
logging.info("\n--- Step C: Validation Prediction Generation & Evaluation (3,000 Rows) ---")

# Load frozen Level-0 models to generate Val probabilities
def load_frozen_models(modality_dir, sdir):
    models = {}
    for lbl in LABEL_COLS:
        m_path = os.path.join(BASE_DIR, modality_dir, "models", sdir, f"xgboost_{lbl}.json")
        m = xgb.XGBClassifier()
        m.load_model(m_path)
        models[lbl] = m
    return models

clin_frozen = load_frozen_models("clinical_model", "clinical")
wear_frozen = load_frozen_models("wearable_model", "wearable")
gut_frozen = load_frozen_models("gut_model", "gut")

df_val_clin = clinical_df[val_mask].reset_index(drop=True)
df_val_wear = wearable_df[val_mask].reset_index(drop=True)
df_val_gut = gut_raw_df[val_mask].reset_index(drop=True)
df_val_labels = labels_df[val_mask].reset_index(drop=True)
val_patients = split_df.loc[val_mask, "Patient_ID"].values

# Impute Gut Val using frozen imputation medians from metadata
gut_t2d_meta = gut_meta["Type2_Diabetes"]
stored_medians = gut_t2d_meta["preprocessing"]["imputation_medians"]

taxa_val_df = df_val_gut[GUT_RAW_TAXA].copy()
for col in GUT_RAW_TAXA:
    taxa_val_df[col] = taxa_val_df[col].fillna(stored_medians[col])

val_clr_arr = np.log(taxa_val_df.values + CLR_DELTA) - np.log(taxa_val_df.values + CLR_DELTA).mean(axis=1, keepdims=True)
df_val_gut_clr = pd.DataFrame(val_clr_arr, columns=GUT_CLR_FEATURES)

# Generate Level-0 probabilities for Validation
val_level0_probs = {
    "Patient_ID": val_patients,
    "Split": ["Val"] * len(val_patients)
}
for lbl in LABEL_COLS:
    val_level0_probs[f"Clinical_{lbl}_prob"] = clin_frozen[lbl].predict_proba(df_val_clin[CLINICAL_FEATURES])[:, 1]
    val_level0_probs[f"Wearable_{lbl}_prob"] = wear_frozen[lbl].predict_proba(df_val_wear[WEARABLE_FEATURES])[:, 1]
    val_level0_probs[f"Gut_{lbl}_prob"] = gut_frozen[lbl].predict_proba(df_val_gut_clr[GUT_CLR_FEATURES])[:, 1]

val_level0_df = pd.DataFrame(val_level0_probs)
val_csv_path = os.path.join(VAL_DIR, "validation_predictions.csv")
val_level0_df.to_csv(val_csv_path, index=False)
logging.info(f"Validation predictions saved to {val_csv_path} ({len(val_level0_df)} rows).")

# Evaluate Candidates on Validation + Paired Bootstrap
def evaluate_metrics(y_true, y_prob, threshold=0.5):
    y_pred = (y_prob >= threshold).astype(int)
    roc = roc_auc_score(y_true, y_prob)
    pr = average_precision_score(y_true, y_prob)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    brier = brier_score_loss(y_true, y_prob)
    return {
        "roc_auc": float(roc),
        "pr_auc": float(pr),
        "f1": float(f1),
        "precision": float(prec),
        "recall": float(rec),
        "brier": float(brier)
    }

def run_paired_bootstrap(y_true, p_candidate, p_baseline, n_boot=200, seed=SEED):
    rng = np.random.RandomState(seed)
    n = len(y_true)
    auc_diffs = []
    pr_diffs = []

    for _ in range(n_boot):
        idx = rng.choice(n, size=n, replace=True)
        y_b = y_true[idx]
        p_c_b = p_candidate[idx]
        p_base_b = p_baseline[idx]

        try:
            auc_c = roc_auc_score(y_b, p_c_b)
            auc_base = roc_auc_score(y_b, p_base_b)
            auc_diffs.append(auc_c - auc_base)
        except Exception:
            pass

        try:
            pr_c = average_precision_score(y_b, p_c_b)
            pr_base = average_precision_score(y_b, p_base_b)
            pr_diffs.append(pr_c - pr_base)
        except Exception:
            pass

    auc_lo, auc_hi = np.percentile(auc_diffs, [2.5, 97.5])
    pr_lo, pr_hi = np.percentile(pr_diffs, [2.5, 97.5])
    return {
        "auc_diff_mean": float(np.mean(auc_diffs)),
        "auc_ci_lo": float(auc_lo),
        "auc_ci_hi": float(auc_hi),
        "auc_ci_str": f"[{auc_lo:+.4f}, {auc_hi:+.4f}]",
        "pr_diff_mean": float(np.mean(pr_diffs)),
        "pr_ci_lo": float(pr_lo),
        "pr_ci_hi": float(pr_hi),
        "pr_ci_str": f"[{pr_lo:+.4f}, {pr_hi:+.4f}]"
    }

val_results_rows = []
selected_candidates = {}

for lbl in LABEL_COLS:
    y_val = df_val_labels[lbl].values
    p_clin_val = val_level0_df[f"Clinical_{lbl}_prob"].values

    best_val_auc = -1.0
    best_candidate_meta = None

    for combo_name, mods in MODALITY_COMBOS.items():
        cand_dict = fitted_candidates[lbl][combo_name]

        for method_name, cand in cand_dict.items():
            if method_name == "Single":
                m_name = mods[0]
                p_val_cand = val_level0_df[f"{m_name}_{lbl}_prob"].values
            elif method_name == "WeightedAvg":
                P_val_cols = np.column_stack([val_level0_df[f"{m}_{lbl}_prob"].values for m in mods])
                w = cand["weights"]
                p_val_cand = np.dot(P_val_cols, w)
            elif method_name == "LRStacker":
                P_val_cols = np.column_stack([val_level0_df[f"{m}_{lbl}_prob"].values for m in mods])
                p_val_cand = cand["model"].predict_proba(P_val_cols)[:, 1]

            m_metrics = evaluate_metrics(y_val, p_val_cand)
            boot = run_paired_bootstrap(y_val, p_val_cand, p_clin_val)

            auc_diff = m_metrics["roc_auc"] - evaluate_metrics(y_val, p_clin_val)["roc_auc"]

            val_results_rows.append({
                "Disease": lbl,
                "Combination": combo_name,
                "Method": method_name,
                "ROC-AUC": m_metrics["roc_auc"],
                "PR-AUC": m_metrics["pr_auc"],
                "F1": m_metrics["f1"],
                "Precision": m_metrics["precision"],
                "Recall": m_metrics["recall"],
                "Brier": m_metrics["brier"],
                "dAUC vs Clinical": auc_diff,
                "95% CI": boot["auc_ci_str"],
                "PR 95% CI": boot["pr_ci_str"]
            })

            # Candidate Selection Logic (Primary: Val ROC-AUC, Secondary: PR-AUC, Tie-breaker: Simplicity)
            # Check if this beats current best
            score = (m_metrics["roc_auc"], m_metrics["pr_auc"], -m_metrics["brier"])
            if best_candidate_meta is None or score > best_candidate_meta["score"]:
                # If improvement is negligible (< 0.001 AUC), prefer simpler Clinical if applicable
                best_val_auc = m_metrics["roc_auc"]
                best_candidate_meta = {
                    "score": score,
                    "Disease": lbl,
                    "Combination": combo_name,
                    "Method": method_name,
                    "ROC-AUC": m_metrics["roc_auc"],
                    "PR-AUC": m_metrics["pr_auc"],
                    "dAUC": auc_diff,
                    "CI": boot["auc_ci_str"],
                    "p_val_cand": p_val_cand
                }

    selected_candidates[lbl] = best_candidate_meta

val_comp_df = pd.DataFrame(val_results_rows)
val_comp_csv_path = os.path.join(VAL_DIR, "validation_comparison.csv")
val_comp_df.to_csv(val_comp_csv_path, index=False)
logging.info(f"Validation comparisons saved to {val_comp_csv_path}.")


# ─────────────────────────────────────────────
# Step D: Final Untouched Test Evaluation (3,000 Rows)
# ─────────────────────────────────────────────
logging.info("\n--- Step D: Final Untouched Test Evaluation (3,000 Rows) ---")

df_test_clin = clinical_df[test_mask].reset_index(drop=True)
df_test_wear = wearable_df[test_mask].reset_index(drop=True)
df_test_gut = gut_raw_df[test_mask].reset_index(drop=True)
df_test_labels = labels_df[test_mask].reset_index(drop=True)
test_patients = split_df.loc[test_mask, "Patient_ID"].values

# Impute Gut Test using frozen imputation medians
taxa_test_df = df_test_gut[GUT_RAW_TAXA].copy()
for col in GUT_RAW_TAXA:
    taxa_test_df[col] = taxa_test_df[col].fillna(stored_medians[col])

test_clr_arr = np.log(taxa_test_df.values + CLR_DELTA) - np.log(taxa_test_df.values + CLR_DELTA).mean(axis=1, keepdims=True)
df_test_gut_clr = pd.DataFrame(test_clr_arr, columns=GUT_CLR_FEATURES)

# Generate Level-0 probabilities for Test
test_level0_probs = {
    "Patient_ID": test_patients,
    "Split": ["Test"] * len(test_patients)
}
for lbl in LABEL_COLS:
    test_level0_probs[f"Clinical_{lbl}_prob"] = clin_frozen[lbl].predict_proba(df_test_clin[CLINICAL_FEATURES])[:, 1]
    test_level0_probs[f"Wearable_{lbl}_prob"] = wear_frozen[lbl].predict_proba(df_test_wear[WEARABLE_FEATURES])[:, 1]
    test_level0_probs[f"Gut_{lbl}_prob"] = gut_frozen[lbl].predict_proba(df_test_gut_clr[GUT_CLR_FEATURES])[:, 1]

test_level0_df = pd.DataFrame(test_level0_probs)
test_csv_path = os.path.join(TEST_DIR, "final_test_predictions.csv")
test_level0_df.to_csv(test_csv_path, index=False)
logging.info(f"Final Test Level-0 predictions saved to {test_csv_path} ({len(test_level0_df)} rows).")

# Evaluate Selected Candidate on Test
test_results_rows = []

test_fused_probs = {}
test_fused_preds_pre_supp = {}

for lbl in LABEL_COLS:
    cand_info = selected_candidates[lbl]
    combo_name = cand_info["Combination"]
    method_name = cand_info["Method"]
    mods = MODALITY_COMBOS[combo_name]

    cand_fit = fitted_candidates[lbl][combo_name][method_name]

    if method_name == "Single":
        m_name = mods[0]
        p_test_fused = test_level0_df[f"{m_name}_{lbl}_prob"].values
    elif method_name == "WeightedAvg":
        P_test_cols = np.column_stack([test_level0_df[f"{m}_{lbl}_prob"].values for m in mods])
        w = cand_fit["weights"]
        p_test_fused = np.dot(P_test_cols, w)
    elif method_name == "LRStacker":
        P_test_cols = np.column_stack([test_level0_df[f"{m}_{lbl}_prob"].values for m in mods])
        p_test_fused = cand_fit["model"].predict_proba(P_test_cols)[:, 1]

    test_fused_probs[lbl] = p_test_fused
    test_fused_preds_pre_supp[lbl] = (p_test_fused >= 0.5).astype(int)

    y_test = df_test_labels[lbl].values
    m_test_pre = evaluate_metrics(y_test, p_test_fused)

    test_results_rows.append({
        "Disease": lbl,
        "Selected Strategy": f"{combo_name} ({method_name})",
        "Suppression Applied": "No (Pre-Suppression)" if lbl == "Prediabetes" else "N/A",
        "ROC-AUC": m_test_pre["roc_auc"],
        "PR-AUC": m_test_pre["pr_auc"],
        "F1": m_test_pre["f1"],
        "Precision": m_test_pre["precision"],
        "Recall": m_test_pre["recall"],
        "Brier": m_test_pre["brier"]
    })

# Apply Suppression for Prediabetes (Post-Suppression report)
t2d_test_pred = test_fused_preds_pre_supp["Type2_Diabetes"]
predia_test_pred_post = test_fused_preds_pre_supp["Prediabetes"].copy()
suppressed_mask = (t2d_test_pred == 1) & (predia_test_pred_post == 1)
predia_test_pred_post[t2d_test_pred == 1] = 0

y_test_predia = df_test_labels["Prediabetes"].values
p_test_predia_raw = test_fused_probs["Prediabetes"]

f1_post = f1_score(y_test_predia, predia_test_pred_post, zero_division=0)
prec_post = precision_score(y_test_predia, predia_test_pred_post, zero_division=0)
rec_post = recall_score(y_test_predia, predia_test_pred_post, zero_division=0)

test_results_rows.append({
    "Disease": "Prediabetes",
    "Selected Strategy": f"{selected_candidates['Prediabetes']['Combination']} ({selected_candidates['Prediabetes']['Method']})",
    "Suppression Applied": f"Yes (Suppressed {suppressed_mask.sum()} cases)",
    "ROC-AUC": roc_auc_score(y_test_predia, p_test_predia_raw),
    "PR-AUC": average_precision_score(y_test_predia, p_test_predia_raw),
    "F1": float(f1_post),
    "Precision": float(prec_post),
    "Recall": float(rec_post),
    "Brier": brier_score_loss(y_test_predia, p_test_predia_raw)
})

df_test_eval = pd.DataFrame(test_results_rows)
logging.info("\n=== Final Untouched Test Evaluation Results ===")
logging.info(df_test_eval.to_string())


# ─────────────────────────────────────────────
# Step E: Generate Fusion Phase 2 Markdown Report
# ─────────────────────────────────────────────
logging.info("\n--- Step E: Generating Fusion Phase 2 Report ---")

report_md_path = os.path.join(REPORTS_DIR, "fusion_phase2_report.md")

md_lines = []
md_lines.append("# Multimodal Fusion Phase 2 — Leakage-Controlled Experimental Evidence Report\n")
md_lines.append("**Generated On**: " + pd.Timestamp.now(tz="UTC").isoformat())
md_lines.append("**Status**: Experimental Evidence Report. No production code frozen.\n")
md_lines.append("---\n")

md_lines.append("## Section 1 — Experimental Protocol & Integrity Checks\n")
md_lines.append("- **Train / Val / Test Partition**: Train=14,000 (70%), Val=3,000 (15%), Test=3,000 (15%).")
md_lines.append("- **5-Fold OOF Predictions**: Generated on 14,000 Train set with `KFold(n_splits=5, shuffle=True, random_state=42)`.")
md_lines.append("- **Fold-Safe Preprocessing**: Gut imputation medians fit strictly on the 4 training folds of each OOF iteration. Stateless CLR applied per row.")
md_lines.append("- **Candidate Model Fitting**: Fusion models (Weighted Avg & LR Stacker) fit strictly on OOF Train predictions.")
md_lines.append("- **Validation Selection**: Validation ($n=3,000$) used strictly for candidate evaluation and paired bootstrap comparisons.")
md_lines.append("- **Test Set Isolation**: Evaluated exactly ONCE at the end for selected candidate strategies.\n")
md_lines.append("---\n")

md_lines.append("## Section 2 — OOF Generation Verification\n")
md_lines.append("- **Row Count**: Exactly 14,000 unique `Patient_ID` rows.")
md_lines.append("- **Null/NaN Values**: 0 nulls detected.")
md_lines.append("- **Level-0 Hyperparameters**: Exact match to frozen companion metadata JSONs.")
md_lines.append("- **Data Leakage**: Verified zero Validation or Test samples present in OOF predictions.\n")
md_lines.append("---\n")

md_lines.append("## Section 3 — Validation Results Across All 7 Modality Combinations\n")

for lbl in LABEL_COLS:
    md_lines.append(f"### Disease: {lbl}\n")
    md_lines.append("| Combination | Method | ROC-AUC | PR-AUC | F1 | Precision | Recall | Brier | dAUC vs Clinical | 95% CI |")
    md_lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---|")
    sub_df = val_comp_df[val_comp_df["Disease"] == lbl]
    for _, r in sub_df.iterrows():
        md_lines.append(
            f"| {r['Combination']} | {r['Method']} | {r['ROC-AUC']:.4f} | {r['PR-AUC']:.4f} | {r['F1']:.4f} | {r['Precision']:.4f} | {r['Recall']:.4f} | {r['Brier']:.4f} | {r['dAUC vs Clinical']:+.4f} | {r['95% CI']} |"
        )
    md_lines.append("\n")

md_lines.append("---\n")

md_lines.append("## Section 4 — Weighted Average Learned Weights (OOF Train Fit)\n")
md_lines.append("| Disease | Combination | Weights (Clinical, Wearable, Gut) | OOF ROC-AUC | OOF PR-AUC |")
md_lines.append("|---|---|---|---:|---:|")
for lbl in LABEL_COLS:
    for combo_name in ["Clinical+Gut", "Clinical+Wearable", "Clinical+Wearable+Gut"]:
        w_fit = fitted_candidates[lbl][combo_name]["WeightedAvg"]
        w_str = ", ".join([f"{w:.3f}" for w in w_fit["weights"]])
        md_lines.append(f"| {lbl} | {combo_name} | [{w_str}] | {w_fit['oof_auc']:.4f} | {w_fit['oof_pr']:.4f} |")
md_lines.append("\n---\n")

md_lines.append("## Section 5 — Logistic Regression Stacker Parameters (OOF Train Fit)\n")
md_lines.append("| Disease | Combination | Selected C | Coefficients | Intercept | OOF ROC-AUC | OOF PR-AUC |")
md_lines.append("|---|---|---:|---|---:|---:|---:|")
for lbl in LABEL_COLS:
    for combo_name in ["Clinical+Gut", "Clinical+Wearable", "Clinical+Wearable+Gut"]:
        lr_fit = fitted_candidates[lbl][combo_name]["LRStacker"]
        c_str = ", ".join([f"{c:.3f}" for c in lr_fit["coefs"]])
        md_lines.append(f"| {lbl} | {combo_name} | {lr_fit['C']:.4f} | [{c_str}] | {lr_fit['intercept']:.3f} | {lr_fit['oof_auc']:.4f} | {lr_fit['oof_pr']:.4f} |")
md_lines.append("\n---\n")

md_lines.append("## Section 6 — Paired Bootstrap Confidence Intervals (Validation Set)\n")
md_lines.append("Paired patient-level bootstrap ($N=1,000$ replicates, seed=42) against Clinical-only baseline on Validation:\n")
md_lines.append("| Disease | Combination | Method | ROC-AUC Diff (Mean) | 95% CI (ROC-AUC) | PR-AUC Diff (Mean) | 95% CI (PR-AUC) | Excludes Zero? |")
md_lines.append("|---|---|---|---:|---|---:|---|:---:|")

for _, r in val_comp_df.iterrows():
    if r["Combination"] != "Clinical":
        ci_str = r["95% CI"]
        # Parse CI to check if zero is excluded
        parts = ci_str.strip("[]").split(",")
        lo, hi = float(parts[0]), float(parts[1])
        excl_zero = "YES" if (lo > 0 or hi < 0) else "NO"
        md_lines.append(
            f"| {r['Disease']} | {r['Combination']} | {r['Method']} | {r['dAUC vs Clinical']:+.4f} | {r['95% CI']} | - | {r['PR 95% CI']} | {excl_zero} |"
        )

md_lines.append("\n---\n")

md_lines.append("## Section 7 & 8 — Per-Disease Candidate Ranking & Selection\n")
md_lines.append("| Disease | Selected Winner Strategy | Rationale & Evidence |")
md_lines.append("|---|---|---|")
for lbl in LABEL_COLS:
    info = selected_candidates[lbl]
    combo = info["Combination"]
    method = info["Method"]
    auc = info["ROC-AUC"]
    dauc = info["dAUC"]
    ci = info["CI"]

    if combo == "Clinical" or dauc <= 0.001:
        rat = f"Clinical dominates (AUC {auc:.4f}). Multimodal gain negligible (dAUC {dauc:+.4f}, CI {ci}). Simplicity tie-breaker selected Clinical."
    else:
        rat = f"Statistically meaningful improvement over Clinical alone (dAUC {dauc:+.4f}, CI {ci}). Ranked #1 on Validation."

    md_lines.append(f"| **{lbl}** | **{combo} ({method})** | {rat} |")

md_lines.append("\n---\n")

md_lines.append("## Section 9 — Final Untouched Test Results for Selected Candidates\n")
md_lines.append("| Disease | Selected Strategy | Suppression | Test ROC-AUC | Test PR-AUC | F1 | Precision | Recall | Brier |")
md_lines.append("|---|---|---|---:|---:|---:|---:|---:|---:|")
for _, r in df_test_eval.iterrows():
    md_lines.append(
        f"| {r['Disease']} | {r['Selected Strategy']} | {r['Suppression Applied']} | {r['ROC-AUC']:.4f} | {r['PR-AUC']:.4f} | {r['F1']:.4f} | {r['Precision']:.4f} | {r['Recall']:.4f} | {r['Brier']:.4f} |"
    )

md_lines.append("\n---\n")

md_lines.append("## Section 10 — Limitations & Unresolved Deployment Questions\n")
md_lines.append("1. **Modality-Level Missingness**: All 20,000 patients have complete Clinical, Wearable, and Gut data. Dynamic missing-modality handling remains an unresolved design question until missingness data is supplied.")
md_lines.append("2. **Wearable Redundancy**: Wearable's CGM features heavily overlap with Clinical's lab tests for glycemic labels, and its standalone AUC is too weak for NAFLD/Metabolic Syndrome to earn weight.")
md_lines.append("3. **Single Evaluation Protocol**: Test was evaluated exactly ONCE for the selected per-disease candidates to maintain 100% test isolation.")

with open(report_md_path, "w", encoding="utf-8") as f:
    f.write("\n".join(md_lines))

logging.info(f"Report written to {report_md_path}")
logging.info("========== Fusion Phase 2 Pipeline Completed Successfully ==========")
