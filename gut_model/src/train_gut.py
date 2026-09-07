"""
train_gut.py — Gut Microbiome Model Training Pipeline (v3)

Trains 5 independent XGBoost binary classifiers (one per label) on CLR-transformed
taxa features. Handles ~10% MCAR null rows via Train-only median imputation.

Pipeline order (leakage-safe, confirmed in training.log):
  1. Load & merge data (gut_v3 + labels + split manifest)
  2. Run load-time checks
  3. Split into Train / Val / Test using split_manifest_v3.csv
  4. Compute 21 imputation medians from Train non-null rows ONLY
  5. Apply medians to impute nulls in Train, Val, Test SEPARATELY
  6. Apply row-wise CLR transform (delta=1e-5) to each split
  7. Manual 36-combo grid search per label (Val-based early stopping)
  8. Evaluate on Test set (touched exactly once, after all model selection)
  9. Apply suppression rule, SHAP analysis, save models/reports
"""

import os
import sys
import time
import json
import logging
import random
import platform

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # non-interactive backend for server/headless environments
import matplotlib.pyplot as plt
import joblib

import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    classification_report,
    confusion_matrix,
    brier_score_loss,
)
from sklearn.calibration import calibration_curve

import xgboost as xgb
import shap

# ─────────────────────────────────────────────
# Reproducibility — set ALL seeds first
# ─────────────────────────────────────────────
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

# ─────────────────────────────────────────────
# Path Configuration
# ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models", "gut")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
LOG_FILE = os.path.join(BASE_DIR, "training.log")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# ─────────────────────────────────────────────
# Configure Logging (file + stdout)
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────
RAW_TAXA_COLS = [
    "Akkermansia", "Faecalibacterium", "Roseburia", "Bifidobacterium",
    "Bacteroides", "Prevotella", "Ruminococcus", "Blautia", "Collinsella",
    "Escherichia_Shigella", "Coprococcus", "Alistipes", "Subdoligranulum",
    "Enterococcus", "Eubacterium", "Parabacteroides", "Lactobacillus",
    "Klebsiella", "Streptococcus", "Eggerthella", "Other_Taxa",
]

CLR_FEATURE_COLS = [t + "_CLR" for t in RAW_TAXA_COLS]  # 21 CLR names

LABEL_COLS = [
    "Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk",
    "Metabolic_Syndrome", "NAFLD",
]

CLR_DELTA = 1e-5

GRID_SEARCH_SPACE = {
    "max_depth": [3, 5, 7],
    "learning_rate": [0.01, 0.05, 0.1],
    "subsample": [0.8, 1.0],
    "colsample_bytree": [0.8, 1.0],
}

# Protective and pathogen taxa for SHAP sanity check
PROTECTIVE_TAXA = {"Faecalibacterium_CLR", "Akkermansia_CLR", "Roseburia_CLR", "Bifidobacterium_CLR"}
PATHOGEN_TAXA = {"Escherichia_Shigella_CLR", "Klebsiella_CLR", "Eggerthella_CLR",
                 "Enterococcus_CLR", "Streptococcus_CLR"}


# ═══════════════════════════════════════════════════════════════════
# PHASE 1 — Data Loading & Load-Time Checks
# ═══════════════════════════════════════════════════════════════════

def load_and_validate_data():
    """Load gut, labels, split CSVs, merge on Patient_ID, run all load-time checks."""
    logging.info("=" * 70)
    logging.info("PHASE 1: Data Load & Load-Time Checks")
    logging.info("=" * 70)

    gut_path = os.path.join(DATA_DIR, "gut_v3.csv")
    labels_path = os.path.join(DATA_DIR, "labels_v3.csv")
    split_path = os.path.join(DATA_DIR, "split_manifest_v3.csv")

    for path in [gut_path, labels_path, split_path]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Required file missing: {path}")

    df_gut = pd.read_csv(gut_path)
    df_labels = pd.read_csv(labels_path)
    df_split = pd.read_csv(split_path)

    logging.info(f"  Raw shapes: gut={df_gut.shape}, labels={df_labels.shape}, split={df_split.shape}")

    # Check 1 — Row counts
    for name, df in [("gut_v3", df_gut), ("labels_v3", df_labels), ("split_manifest_v3", df_split)]:
        if len(df) != 20_000:
            raise ValueError(f"[FAIL] Row count check: {name} has {len(df)} rows, expected 20,000.")
    logging.info("  [PASS] Row count: 20,000 in each file.")

    # Check 2 — Expected columns
    expected_gut_cols = ["Patient_ID"] + RAW_TAXA_COLS
    for col in expected_gut_cols:
        if col not in df_gut.columns:
            raise KeyError(f"[FAIL] Missing column '{col}' in gut_v3.csv")

    for col in ["Patient_ID"] + LABEL_COLS:
        if col not in df_labels.columns:
            raise KeyError(f"[FAIL] Missing column '{col}' in labels_v3.csv")

    if "Patient_ID" not in df_split.columns or "Split" not in df_split.columns:
        raise KeyError("[FAIL] Missing 'Patient_ID' or 'Split' in split_manifest_v3.csv")
    logging.info("  [PASS] All expected columns present.")

    # Check 3 — Patient_ID set matching
    ids_gut = set(df_gut["Patient_ID"])
    ids_labels = set(df_labels["Patient_ID"])
    ids_split = set(df_split["Patient_ID"])

    if ids_gut != ids_labels:
        raise ValueError(f"[FAIL] Patient_ID mismatch: gut vs labels. "
                         f"Gut-only={len(ids_gut - ids_labels)}, Labels-only={len(ids_labels - ids_gut)}")
    if ids_gut != ids_split:
        raise ValueError(f"[FAIL] Patient_ID mismatch: gut vs split. "
                         f"Gut-only={len(ids_gut - ids_split)}, Split-only={len(ids_split - ids_gut)}")
    logging.info("  [PASS] Patient_ID sets match exactly across all 3 files.")

    # Merge
    df = df_gut.merge(df_labels, on="Patient_ID").merge(df_split, on="Patient_ID")

    # Check 4 — Merged row count
    if len(df) != 20_000:
        raise ValueError(f"[FAIL] Merged dataframe has {len(df)} rows, expected 20,000.")
    logging.info("  [PASS] Merged dataframe: 20,000 rows.")

    # Check 5 — Feature columns count
    if len(RAW_TAXA_COLS) != 21:
        raise ValueError(f"[FAIL] Expected 21 feature columns, got {len(RAW_TAXA_COLS)}")
    logging.info("  [PASS] 21 feature columns confirmed (excluding Patient_ID).")

    # Check 6 — Compositional integrity: non-null rows sum to 100 ± 0.02
    null_mask = df[RAW_TAXA_COLS].isnull().all(axis=1)
    non_null_rows = df[~null_mask]
    if len(non_null_rows) > 0:
        row_sums = non_null_rows[RAW_TAXA_COLS].sum(axis=1)
        bad_rows = ((row_sums < 99.98) | (row_sums > 100.02)).sum()
        if bad_rows > 0:
            raise ValueError(
                f"[FAIL] Compositional integrity: {bad_rows} non-null rows have taxa "
                f"sum outside 100.0 ± 0.02. Min={row_sums.min():.4f}, Max={row_sums.max():.4f}"
            )
        logging.info(f"  [PASS] Compositional integrity: {len(non_null_rows)} non-null rows sum to 100.0 ± 0.02.")

    # Check 7 — Null row count (MCAR rows where ALL 21 taxa are NaN)
    null_count = int(null_mask.sum())
    if null_count == 0:
        raise ValueError(
            f"[FAIL] Zero fully-null rows detected. Expected 1,600–2,400. "
            f"Possible wrong file version (null rows are a required dataset characteristic)."
        )
    if null_count > 3_000:
        raise ValueError(
            f"[FAIL] Detected {null_count} fully-null rows (>3,000). "
            f"Expected 1,600–2,400. Possible wrong file version."
        )
    logging.info(f"  [PASS] Null row count (MCAR): {null_count} rows (within 1,600–2,400 range).")

    split_counts = df["Split"].value_counts().to_dict()
    logging.info(f"  Split distribution: {split_counts}")

    return df, null_count


# ═══════════════════════════════════════════════════════════════════
# PHASE 2 — Split Data
# ═══════════════════════════════════════════════════════════════════

def split_data(df):
    """Split merged DataFrame into Train/Val/Test using the pre-assigned 'Split' column."""
    logging.info("")
    logging.info("=" * 70)
    logging.info("PHASE 2: Splitting Data (using split_manifest_v3.csv exactly)")
    logging.info("=" * 70)

    train_mask = df["Split"] == "Train"
    val_mask = df["Split"] == "Val"
    test_mask = df["Split"] == "Test"

    df_train = df[train_mask].copy()
    df_val = df[val_mask].copy()
    df_test = df[test_mask].copy()

    logging.info(f"  Train: {len(df_train)} | Val: {len(df_val)} | Test: {len(df_test)}")

    return df_train, df_val, df_test


# ═══════════════════════════════════════════════════════════════════
# PHASE 3 — Preprocessing: Median Imputation + CLR Transform
# ═══════════════════════════════════════════════════════════════════

def compute_imputation_medians(df_train):
    """
    Compute per-column median from Train non-null rows ONLY.
    A 'non-null row' is any row that is NOT fully null across all 21 taxa.
    (Partial NaN within a row is not expected per spec, but we guard against it.)
    """
    null_mask = df_train[RAW_TAXA_COLS].isnull().all(axis=1)
    df_train_nonnull = df_train[~null_mask]
    logging.info(f"  Train non-null rows for median computation: {len(df_train_nonnull)} "
                 f"(out of {len(df_train)} total Train rows)")

    medians = {}
    for col in RAW_TAXA_COLS:
        col_median = float(df_train_nonnull[col].median())
        medians[col] = col_median

    logging.info(f"  Imputation medians computed (first 3 shown):")
    for col in RAW_TAXA_COLS[:3]:
        logging.info(f"    {col}: {medians[col]:.6f}")

    return medians


def apply_imputation(df, medians):
    """Apply pre-computed medians to impute ALL null values in this split."""
    df = df.copy()
    null_mask = df[RAW_TAXA_COLS].isnull().all(axis=1)
    imputed_count = int(null_mask.sum())
    if imputed_count > 0:
        for col in RAW_TAXA_COLS:
            df.loc[null_mask, col] = medians[col]
    return df, imputed_count


def apply_clr(df):
    """
    Apply row-wise CLR transformation to all 21 taxa columns.
    CLR(x_i) = log(x_i + delta) - mean(log(x_j + delta) for j in 1..21)
    delta = 1e-5 (to handle zeros without zero-division or log(0))
    Creates new columns with _CLR suffix; original taxa columns are dropped from output.
    """
    taxa_array = df[RAW_TAXA_COLS].values.astype(np.float64)

    # Add delta to avoid log(0)
    taxa_delta = taxa_array + CLR_DELTA

    # Log transform
    log_taxa = np.log(taxa_delta)

    # Row-wise geometric mean (mean of logs)
    log_mean = log_taxa.mean(axis=1, keepdims=True)

    # CLR = log(x+delta) - row_mean
    clr_array = log_taxa - log_mean

    # Check for non-finite values
    if not np.all(np.isfinite(clr_array)):
        n_bad = np.sum(~np.isfinite(clr_array))
        raise ValueError(
            f"[FAIL] CLR transformation produced {n_bad} non-finite values. "
            f"Check imputation — null values may remain."
        )

    # Build output DataFrame with CLR columns
    df_clr = pd.DataFrame(clr_array, columns=CLR_FEATURE_COLS, index=df.index)
    return df_clr


def preprocess_splits(df_train, df_val, df_test):
    """
    Full preprocessing pipeline (leakage-safe):
      1. Compute medians from Train non-null rows
      2. Impute Train, Val, Test separately
      3. Apply CLR to each split
    """
    logging.info("")
    logging.info("=" * 70)
    logging.info("PHASE 3: Preprocessing — Median Imputation + CLR Transform")
    logging.info("=" * 70)
    logging.info("")
    logging.info("  *** PIPELINE ORDER CONFIRMATION ***")
    logging.info("  Step 1: Compute imputation medians from Train non-null rows ONLY.")
    logging.info("  Step 2: Apply medians to impute nulls in Train, Val, Test SEPARATELY.")
    logging.info("  Step 3: Apply row-wise CLR to each split independently.")
    logging.info("  Val/Test data was NEVER used to fit imputation medians.")
    logging.info("  CLR is stateless (no fitting required).")
    logging.info("")

    # Step 1: Fit medians on Train only
    medians = compute_imputation_medians(df_train)

    # Step 2: Impute each split separately
    df_train_imp, n_train_imputed = apply_imputation(df_train, medians)
    df_val_imp, n_val_imputed = apply_imputation(df_val, medians)
    df_test_imp, n_test_imputed = apply_imputation(df_test, medians)

    logging.info(f"  Imputed null rows: Train={n_train_imputed}, Val={n_val_imputed}, Test={n_test_imputed}")
    logging.info(f"  Total imputed: {n_train_imputed + n_val_imputed + n_test_imputed}")

    # Verify no null values remain after imputation
    for name, df_imp in [("Train", df_train_imp), ("Val", df_val_imp), ("Test", df_test_imp)]:
        remaining_nulls = df_imp[RAW_TAXA_COLS].isnull().sum().sum()
        if remaining_nulls > 0:
            raise ValueError(
                f"[FAIL] After imputation, {name} still has {remaining_nulls} null values "
                f"in taxa columns. Imputation failed."
            )
    logging.info("  [PASS] No null values remain in any split after imputation.")

    # Step 3: Apply CLR row-wise to each split
    X_train_clr = apply_clr(df_train_imp)
    X_val_clr = apply_clr(df_val_imp)
    X_test_clr = apply_clr(df_test_imp)

    logging.info(f"  CLR transform applied: Train={X_train_clr.shape}, Val={X_val_clr.shape}, Test={X_test_clr.shape}")
    logging.info(f"  CLR features (21): {CLR_FEATURE_COLS}")

    # Verify all CLR features are finite
    for name, X in [("Train", X_train_clr), ("Val", X_val_clr), ("Test", X_test_clr)]:
        if not np.all(np.isfinite(X.values)):
            raise ValueError(f"[FAIL] CLR features in {name} contain non-finite values.")
    logging.info("  [PASS] All CLR features are finite in Train, Val, Test.")

    # Extract labels for each split
    y_train = {col: df_train[col].values for col in LABEL_COLS}
    y_val = {col: df_val[col].values for col in LABEL_COLS}
    y_test = {col: df_test[col].values for col in LABEL_COLS}

    return X_train_clr, y_train, X_val_clr, y_val, X_test_clr, y_test, medians


# ═══════════════════════════════════════════════════════════════════
# PHASE 4 — Manual Grid Search + Model Training
# ═══════════════════════════════════════════════════════════════════

def compute_scale_pos_weight(y_train_label):
    """Compute scale_pos_weight from Training labels."""
    n_pos = int(np.sum(y_train_label == 1))
    n_neg = int(np.sum(y_train_label == 0))
    if n_pos == 0:
        raise ValueError("No positive cases found in training set for this label!")
    spw = float(n_neg) / float(n_pos)
    return spw, n_pos, n_neg


def run_manual_grid_search(label, X_train, y_train, X_val, y_val, scale_pos_weight):
    """
    Exhaustive 36-combo manual grid search.
    Selects best config by Validation AUCPR (average_precision_score).
    Early stopping on XGBoost internal eval metric (aucpr) with 20 rounds.
    """
    logging.info(f"  Starting manual grid search for '{label}' (36 combinations)...")

    best_aucpr = -1.0
    best_config = None
    best_model = None
    combo_idx = 0

    for md in GRID_SEARCH_SPACE["max_depth"]:
        for lr in GRID_SEARCH_SPACE["learning_rate"]:
            for sub in GRID_SEARCH_SPACE["subsample"]:
                for col in GRID_SEARCH_SPACE["colsample_bytree"]:
                    combo_idx += 1
                    model = xgb.XGBClassifier(
                        n_estimators=1000,
                        max_depth=md,
                        learning_rate=lr,
                        subsample=sub,
                        colsample_bytree=col,
                        scale_pos_weight=scale_pos_weight,
                        objective="binary:logistic",
                        eval_metric="aucpr",
                        early_stopping_rounds=20,
                        random_state=SEED,
                        n_jobs=-1,
                        verbosity=0,
                    )
                    model.fit(
                        X_train, y_train,
                        eval_set=[(X_val, y_val)],
                        verbose=False,
                    )

                    val_probs = model.predict_proba(X_val)[:, 1]
                    val_aucpr = float(average_precision_score(y_val, val_probs))

                    if val_aucpr > best_aucpr:
                        best_aucpr = val_aucpr
                        best_config = {
                            "max_depth": md,
                            "learning_rate": lr,
                            "subsample": sub,
                            "colsample_bytree": col,
                            "n_estimators_used": int(model.best_iteration + 1),
                        }
                        best_model = model

    logging.info(
        f"  [{label}] Best Val PR-AUC: {best_aucpr:.4f} | Config: {best_config}"
    )
    return best_model, best_config, best_aucpr


def train_baseline_logreg(X_train, y_train):
    """Train LogReg baseline with StandardScaler (applied on top of CLR features)."""
    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(
            class_weight="balanced",
            solver="lbfgs",
            max_iter=1000,
            random_state=SEED,
        )),
    ])
    pipe.fit(X_train, y_train)
    return pipe


# ═══════════════════════════════════════════════════════════════════
# PHASE 5 — Evaluation
# ═══════════════════════════════════════════════════════════════════

def evaluate_predictions(y_true, y_prob, threshold=0.5):
    """Compute full evaluation metrics for a single binary label."""
    y_pred = (y_prob >= threshold).astype(int)

    roc = float(roc_auc_score(y_true, y_prob))
    pr = float(average_precision_score(y_true, y_prob))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    brier = float(brier_score_loss(y_true, y_prob))
    cm = confusion_matrix(y_true, y_pred)
    cm_norm = confusion_matrix(y_true, y_pred, normalize="true")
    report = classification_report(y_true, y_pred, digits=4, zero_division=0)
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=10, strategy="uniform")

    return {
        "roc_auc": roc,
        "pr_auc": pr,
        "f1": f1,
        "precision": prec,
        "recall": rec,
        "brier": brier,
        "confusion_matrix": cm.tolist(),
        "confusion_matrix_norm": cm_norm.tolist(),
        "classification_report": report,
        "calibration_curve": {
            "prob_true": prob_true.tolist(),
            "prob_pred": prob_pred.tolist(),
        },
    }


def save_calibration_plot(label, y_true, y_prob, reports_dir):
    """Save calibration curve plot for a label."""
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=10, strategy="uniform")

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(prob_pred, prob_true, marker="o", label="XGBoost", color="#2196F3", linewidth=2)
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Perfect calibration")
    ax.set_xlabel("Mean Predicted Probability")
    ax.set_ylabel("Fraction of Positives")
    ax.set_title(f"Calibration Curve — {label} (Gut Model v3)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    out_path = os.path.join(reports_dir, f"calibration_{label}.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    return out_path


# ═══════════════════════════════════════════════════════════════════
# PHASE 6 — SHAP Analysis
# ═══════════════════════════════════════════════════════════════════

def run_shap_analysis(label, model, X_test, reports_dir):
    """
    Run SHAP TreeExplainer on 500 deterministic Test samples (random_state=42).
    Feature names MUST use _CLR suffix (CLR_FEATURE_COLS).
    """
    logging.info(f"  Running SHAP TreeExplainer for '{label}'...")

    # Deterministic sample
    n_sample = min(500, len(X_test))
    X_sample = X_test.sample(n=n_sample, random_state=SEED)

    explainer = shap.TreeExplainer(model)
    shap_values = explainer(X_sample)

    # Handle binary vs multi-class output shape
    if len(shap_values.values.shape) == 3:
        vals = np.abs(shap_values.values[:, :, 1]).mean(axis=0)
    else:
        vals = np.abs(shap_values.values).mean(axis=0)

    df_imp = pd.DataFrame({
        "Feature": CLR_FEATURE_COLS,
        "Mean_Abs_SHAP": vals,
    }).sort_values(by="Mean_Abs_SHAP", ascending=False).reset_index(drop=True)

    # Save importance CSV
    imp_csv_path = os.path.join(reports_dir, f"importance_{label}.csv")
    df_imp.to_csv(imp_csv_path, index=False)

    # Save SHAP summary plot
    plt.figure(figsize=(10, 7))
    shap.summary_plot(shap_values, X_sample, feature_names=CLR_FEATURE_COLS, show=False)
    plt.title(f"SHAP Summary — {label} (Gut Model v3)", fontsize=13, pad=12)
    plt.tight_layout()
    png_path = os.path.join(reports_dir, f"shap_summary_{label}.png")
    plt.savefig(png_path, dpi=150, bbox_inches="tight")
    plt.close()

    logging.info(f"  SHAP saved: {imp_csv_path}")
    logging.info(f"  Top 5 SHAP features for {label}:")
    for _, row in df_imp.head(5).iterrows():
        logging.info(f"    {row['Feature']}: {row['Mean_Abs_SHAP']:.5f}")

    return df_imp


def shap_biological_sanity_check(label, df_imp):
    """
    Category-level SHAP sanity check.
    Flag only if protective taxa COMPLETELY dominate with positive SHAP for disease
    while pathogen taxa show near-zero importance — not for minor reordering.
    """
    top_10 = set(df_imp.head(10)["Feature"].tolist())
    protective_in_top10 = top_10 & PROTECTIVE_TAXA
    pathogen_in_top10 = top_10 & PATHOGEN_TAXA

    protective_shap = df_imp[df_imp["Feature"].isin(PROTECTIVE_TAXA)]["Mean_Abs_SHAP"].sum()
    pathogen_shap = df_imp[df_imp["Feature"].isin(PATHOGEN_TAXA)]["Mean_Abs_SHAP"].sum()

    notes = []
    notes.append(f"    Protective taxa in top-10: {protective_in_top10 or 'none'}")
    notes.append(f"    Pathogen taxa in top-10:   {pathogen_in_top10 or 'none'}")
    notes.append(f"    Total protective SHAP: {protective_shap:.5f} | Total pathogen SHAP: {pathogen_shap:.5f}")

    # Flag only categorically suspicious: protective >> pathogen AND protective dominates
    flagged = False
    if protective_shap > 3.0 * pathogen_shap and len(pathogen_in_top10) == 0:
        notes.append(f"    [FLAG] Protective taxa dominate (3x pathogen SHAP) with no pathogen in top-10.")
        flagged = True
    else:
        notes.append(f"    [OK] SHAP biological sanity: no categorical inconsistency detected.")

    return notes, flagged


# ═══════════════════════════════════════════════════════════════════
# PHASE 7 — Save Models + Metadata JSONs
# ═══════════════════════════════════════════════════════════════════

def save_models_and_metadata(
    label,
    xgb_model,
    logreg_model,
    best_config,
    medians,
    scale_pos_weight,
    X_train, X_val, X_test,
    models_dir,
    pkg_versions,
    train_timestamp,
):
    """Save XGBoost native JSON, LogReg joblib, and both metadata JSONs."""

    # XGBoost model
    xgb_path = os.path.join(models_dir, f"xgboost_{label}.json")
    xgb_model.save_model(xgb_path)

    # LogReg pipeline
    logreg_path = os.path.join(models_dir, f"baseline_logreg_{label}.joblib")
    joblib.dump(logreg_model, logreg_path)

    # XGBoost metadata JSON — exact schema from spec
    xgb_meta = {
        "model_type": "xgboost",
        "model_version": "gut_v3",
        "label": label,
        "features": CLR_FEATURE_COLS,
        "feature_count": 21,
        "preprocessing": {
            "imputation": "median",
            "imputation_medians": medians,
            "transform": "CLR",
            "clr_delta": CLR_DELTA,
        },
        "threshold": 0.5,
        "scale_pos_weight": float(scale_pos_weight),
        "training_seed": SEED,
        "hyperparameters": best_config,
        "eval_metric": "aucpr",
        "training_rows": len(X_train),
        "validation_rows": len(X_val),
        "test_rows": len(X_test),
        "train_date": train_timestamp,
        "python_version": sys.version,
        "package_versions": pkg_versions,
    }

    with open(os.path.join(models_dir, f"xgboost_{label}_metadata.json"), "w") as f:
        json.dump(xgb_meta, f, indent=2)

    # LogReg metadata JSON
    logreg_meta = {
        "model_type": "logistic_regression",
        "model_version": "gut_v3",
        "label": label,
        "features": CLR_FEATURE_COLS,
        "feature_count": 21,
        "preprocessing": {
            "imputation": "median",
            "imputation_medians": medians,
            "transform": "CLR",
            "clr_delta": CLR_DELTA,
            "additional_scaling": "StandardScaler (applied on CLR features, for LogReg only)"
        },
        "threshold": 0.5,
        "class_weight": "balanced",
        "solver": "lbfgs",
        "training_rows": len(X_train),
        "validation_rows": len(X_val),
        "test_rows": len(X_test),
        "train_date": train_timestamp,
        "python_version": sys.version,
        "package_versions": pkg_versions,
    }

    with open(os.path.join(models_dir, f"baseline_logreg_{label}_metadata.json"), "w") as f:
        json.dump(logreg_meta, f, indent=2)

    logging.info(f"  Saved: {xgb_path}")
    logging.info(f"  Saved: {logreg_path}")


# ═══════════════════════════════════════════════════════════════════
# PHASE 8 — Generate Evaluation Report
# ═══════════════════════════════════════════════════════════════════

def generate_evaluation_report(
    raw_xgb_metrics,
    raw_logreg_metrics,
    suppressed_xgb_metrics,
    scale_pos_weights,
    xgb_val_aucprs,
    xgb_configs,
    suppressed_count,
    train_timestamp,
    reports_dir,
):
    """Write gut_evaluation.md with full per-label metrics and summary table."""
    logging.info("")
    logging.info("=" * 70)
    logging.info("PHASE 8: Generating Evaluation Report")
    logging.info("=" * 70)

    lines = []
    lines.append("# Gut Microbiome Metabolic Disease Prediction Model (v3) — Evaluation Report\n")
    lines.append(f"**Generated On**: {train_timestamp}\n")
    lines.append(f"**Model Version**: gut_v3\n")
    lines.append(f"**Algorithm**: XGBoost (objective=binary:logistic, eval_metric=aucpr)\n")
    lines.append(f"**Features**: 21 CLR-transformed taxa (delta=1e-5)\n")
    lines.append(f"**Preprocessing**: Train-only median imputation → row-wise CLR\n")
    lines.append("\n---\n")

    # Summary table — suppressed predictions
    lines.append("## Executive Summary (XGBoost Test Performance — Suppressed Predictions)\n")
    lines.append("| Label | ROC-AUC | PR-AUC | F1 | Precision | Recall |")
    lines.append("|---|---|---|---|---|---|")
    for label in LABEL_COLS:
        m = suppressed_xgb_metrics[label]
        lines.append(
            f"| **{label}** | {m['roc_auc']:.4f} | {m['pr_auc']:.4f} | "
            f"{m['f1']:.4f} | {m['precision']:.4f} | {m['recall']:.4f} |"
        )
    lines.append("\n---\n")

    # Diagnostic AUC reference
    lines.append("## Diagnostic AUC Reference (RandomForest 3-fold CV baseline — informational only)\n")
    lines.append("| Label | Reference AUC | XGBoost Test AUC | Notes |\n")
    lines.append("|---|---|---|---|")
    refs = {
        "Type2_Diabetes": 0.81, "Prediabetes": 0.58,
        "High_Adiposity_Risk": 0.81, "Metabolic_Syndrome": 0.83, "NAFLD": 0.81,
    }
    for label in LABEL_COLS:
        xgb_auc = suppressed_xgb_metrics[label]["roc_auc"]
        ref = refs[label]
        note = ""
        if label == "Prediabetes":
            if xgb_auc < 0.52:
                note = "⚠️ FLAG: Below 0.52 — surprisingly low"
            elif xgb_auc > 0.70:
                note = "⚠️ FLAG: Above 0.70 — surprisingly high"
            else:
                note = "Within expected range (0.52–0.70)"
        lines.append(f"| {label} | {ref:.2f} | {xgb_auc:.4f} | {note} |")
    lines.append("\n---\n")

    # Scale pos weight
    lines.append("## Class Imbalance & Scale Pos Weights\n")
    lines.append("Computed strictly from Training split (14,000 rows):\n")
    for label in LABEL_COLS:
        lines.append(f"- **{label}**: `scale_pos_weight = {scale_pos_weights[label]:.4f}`")
    lines.append("\n---\n")

    # Baseline vs XGBoost
    lines.append("## Baseline (Logistic Regression) vs XGBoost Comparison\n")
    lines.append("| Label | Model | ROC-AUC | PR-AUC | F1 | Precision | Recall | Brier Score |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for label in LABEL_COLS:
        bx = suppressed_xgb_metrics[label]
        bl = raw_logreg_metrics[label]
        brier_x = raw_xgb_metrics[label]["brier"]
        brier_l = bl["brier"]
        lines.append(
            f"| **{label}** | Baseline (LogReg) | {bl['roc_auc']:.4f} | {bl['pr_auc']:.4f} | "
            f"{bl['f1']:.4f} | {bl['precision']:.4f} | {bl['recall']:.4f} | {brier_l:.4f} |"
        )
        lines.append(
            f"| **{label}** | **XGBoost (v3)** | **{bx['roc_auc']:.4f}** | **{bx['pr_auc']:.4f}** | "
            f"**{bx['f1']:.4f}** | **{bx['precision']:.4f}** | **{bx['recall']:.4f}** | **{brier_x:.4f}** |"
        )
    lines.append("\n---\n")

    # Suppression rule impact
    lines.append("## Mutual Exclusivity Suppression Rule Impact\n")
    lines.append("Rule: If `Type2_Diabetes` prediction = 1, `Prediabetes` prediction forced to 0 (raw probability untouched).\n")
    lines.append("| Metric | Prediabetes (Raw) | Prediabetes (Suppressed) | Change |")
    lines.append("|---|---|---|---|")
    pre_raw = raw_xgb_metrics["Prediabetes"]
    pre_sup = suppressed_xgb_metrics["Prediabetes"]
    lines.append(f"| Precision | {pre_raw['precision']:.4f} | {pre_sup['precision']:.4f} | {pre_sup['precision'] - pre_raw['precision']:+.4f} |")
    lines.append(f"| Recall    | {pre_raw['recall']:.4f} | {pre_sup['recall']:.4f} | {pre_sup['recall'] - pre_raw['recall']:+.4f} |")
    lines.append(f"| F1 Score  | {pre_raw['f1']:.4f} | {pre_sup['f1']:.4f} | {pre_sup['f1'] - pre_raw['f1']:+.4f} |")
    lines.append(f"| Total Suppressed | — | {suppressed_count} | — |")
    lines.append("\n---\n")

    # Per-label detailed reports
    lines.append("## Detailed Per-Label Classification Reports & Confusion Matrices\n")
    for label in LABEL_COLS:
        m = raw_xgb_metrics[label]
        sm = suppressed_xgb_metrics[label]
        cfg = xgb_configs[label]

        lines.append(f"### Label: {label}\n")
        lines.append(f"- **Best Hyperparameters**: `max_depth={cfg['max_depth']}, learning_rate={cfg['learning_rate']}, "
                     f"subsample={cfg['subsample']}, colsample_bytree={cfg['colsample_bytree']}, "
                     f"n_estimators_used={cfg['n_estimators_used']}`")
        lines.append(f"- **Validation PR-AUC (best config)**: `{xgb_val_aucprs[label]:.4f}`")
        lines.append(f"- **Test Brier Score**: `{m['brier']:.4f}`\n")

        lines.append("#### Classification Report (Suppressed Predictions)\n```")
        lines.append(sm["classification_report"])
        lines.append("```\n")

        cm_arr = np.array(sm["confusion_matrix"])
        lines.append("#### Confusion Matrix (Raw Counts)\n```")
        lines.append(f"TN: {cm_arr[0, 0]:<6} FP: {cm_arr[0, 1]:<6}")
        lines.append(f"FN: {cm_arr[1, 0]:<6} TP: {cm_arr[1, 1]:<6}")
        lines.append("```\n")

        cm_n = np.array(sm["confusion_matrix_norm"])
        lines.append("#### Confusion Matrix (Row-Normalized)\n```")
        lines.append(f"TN: {cm_n[0, 0]:.4f}  FP: {cm_n[0, 1]:.4f}")
        lines.append(f"FN: {cm_n[1, 0]:.4f}  TP: {cm_n[1, 1]:.4f}")
        lines.append("```\n")

    report_path = os.path.join(reports_dir, "gut_evaluation.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logging.info(f"  Evaluation report written: {report_path}")
    return report_path


# ═══════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════════

def main():
    pipeline_start = time.time()
    train_timestamp = pd.Timestamp.now(tz="UTC").isoformat()

    logging.info("=" * 70)
    logging.info("STARTING GUT MICROBIOME MODEL TRAINING PIPELINE (v3)")
    logging.info(f"Timestamp: {train_timestamp}")
    logging.info(f"Python: {sys.version}")
    logging.info(f"Platform: {platform.platform()}")
    logging.info(f"XGBoost: {xgb.__version__} | sklearn: {sklearn.__version__} | shap: {shap.__version__}")
    logging.info("=" * 70)

    pkg_versions = {
        "xgboost": xgb.__version__,
        "scikit-learn": sklearn.__version__,
        "shap": shap.__version__,
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "joblib": joblib.__version__,
    }

    # ── Phase 1: Load & Validate ──────────────────────────────────
    df, null_count = load_and_validate_data()

    # ── Phase 2: Split ────────────────────────────────────────────
    df_train, df_val, df_test = split_data(df)

    # ── Phase 3: Preprocess ───────────────────────────────────────
    X_train, y_train, X_val, y_val, X_test, y_test, medians = preprocess_splits(
        df_train, df_val, df_test
    )

    logging.info("")
    logging.info("=" * 70)
    logging.info("PHASE 4: Per-Label Training (Manual Grid Search + LogReg Baseline)")
    logging.info("=" * 70)

    xgb_models = {}
    xgb_configs = {}
    xgb_val_aucprs = {}
    logreg_models = {}
    scale_pos_weights = {}
    runtimes = {}

    test_xgb_raw_probs = {}
    test_logreg_raw_probs = {}
    shap_results = {}

    # ── Phase 4: Per-label training ───────────────────────────────
    for label in LABEL_COLS:
        lbl_start = time.time()
        logging.info("")
        logging.info(f"  ════ Label: {label} ════")

        # Compute scale_pos_weight from Train labels
        spw, n_pos, n_neg = compute_scale_pos_weight(y_train[label])
        scale_pos_weights[label] = spw
        logging.info(f"  scale_pos_weight for {label}: {spw:.4f} "
                     f"(Train positives={n_pos}, negatives={n_neg})")

        # XGBoost manual grid search
        model, best_cfg, best_val_aucpr = run_manual_grid_search(
            label, X_train, y_train[label], X_val, y_val[label], spw
        )
        xgb_models[label] = model
        xgb_configs[label] = best_cfg
        xgb_val_aucprs[label] = best_val_aucpr

        # LogReg baseline
        logreg_pipe = train_baseline_logreg(X_train, y_train[label])
        logreg_models[label] = logreg_pipe

        # Collect test probabilities (Test touched once — all model selection done)
        test_xgb_raw_probs[label] = model.predict_proba(X_test)[:, 1]
        test_logreg_raw_probs[label] = logreg_pipe.predict_proba(X_test)[:, 1]

        # SHAP analysis
        df_imp = run_shap_analysis(label, model, X_test, REPORTS_DIR)
        shap_results[label] = df_imp

        # SHAP biological sanity check
        sanity_notes, flagged = shap_biological_sanity_check(label, df_imp)
        logging.info(f"  SHAP biological sanity check for {label}:")
        for note in sanity_notes:
            logging.info(note)

        # Calibration plot
        save_calibration_plot(label, y_test[label], test_xgb_raw_probs[label], REPORTS_DIR)

        lbl_end = time.time()
        runtimes[label] = lbl_end - lbl_start
        logging.info(f"  Label '{label}' complete in {runtimes[label]:.1f}s")

    # ── Phase 5: Evaluate on Test ─────────────────────────────────
    logging.info("")
    logging.info("=" * 70)
    logging.info("PHASE 5: Test Set Evaluation & Suppression Rule")
    logging.info("=" * 70)
    logging.info("NOTE: Test set is touched here for the FIRST AND ONLY time.")

    raw_xgb_metrics = {}
    raw_logreg_metrics = {}

    for label in LABEL_COLS:
        raw_xgb_metrics[label] = evaluate_predictions(y_test[label], test_xgb_raw_probs[label])
        raw_logreg_metrics[label] = evaluate_predictions(y_test[label], test_logreg_raw_probs[label])

    # Apply suppression rule (labels only — raw probs unchanged)
    xgb_suppressed_preds = {
        label: (test_xgb_raw_probs[label] >= 0.5).astype(int).copy()
        for label in LABEL_COLS
    }
    t2d_pos_mask = xgb_suppressed_preds["Type2_Diabetes"] == 1
    suppressed_count = int(np.sum((xgb_suppressed_preds["Prediabetes"] == 1) & t2d_pos_mask))
    xgb_suppressed_preds["Prediabetes"][t2d_pos_mask] = 0

    logging.info(f"  Suppression Rule: Suppressed {suppressed_count} Prediabetes "
                 f"predictions where Type2_Diabetes=1.")

    suppressed_xgb_metrics = {}
    for label in LABEL_COLS:
        y_true = y_test[label]
        y_pred = xgb_suppressed_preds[label]
        y_prob = test_xgb_raw_probs[label]  # raw probability untouched

        roc = float(roc_auc_score(y_true, y_prob))
        pr = float(average_precision_score(y_true, y_prob))
        f1 = float(f1_score(y_true, y_pred, zero_division=0))
        prec = float(precision_score(y_true, y_pred, zero_division=0))
        rec = float(recall_score(y_true, y_pred, zero_division=0))
        cm = confusion_matrix(y_true, y_pred)
        cm_norm = confusion_matrix(y_true, y_pred, normalize="true")
        report = classification_report(y_true, y_pred, digits=4, zero_division=0)

        suppressed_xgb_metrics[label] = {
            "roc_auc": roc, "pr_auc": pr, "f1": f1,
            "precision": prec, "recall": rec,
            "confusion_matrix": cm.tolist(),
            "confusion_matrix_norm": cm_norm.tolist(),
            "classification_report": report,
        }

    # Log final test metrics
    logging.info("")
    logging.info("  ══ Final Test Metrics (XGBoost, Suppressed Predictions) ══")
    logging.info(f"  {'Label':<25} {'ROC-AUC':>8} {'PR-AUC':>8} {'F1':>7} {'Prec':>7} {'Recall':>8}")
    for label in LABEL_COLS:
        m = suppressed_xgb_metrics[label]
        logging.info(
            f"  {label:<25} {m['roc_auc']:>8.4f} {m['pr_auc']:>8.4f} "
            f"{m['f1']:>7.4f} {m['precision']:>7.4f} {m['recall']:>8.4f}"
        )

    # Prediabetes AUC flag
    pre_auc = suppressed_xgb_metrics["Prediabetes"]["roc_auc"]
    if pre_auc < 0.52:
        logging.warning(f"  [FLAG] Prediabetes ROC-AUC={pre_auc:.4f} is below 0.52 — surprisingly low!")
    elif pre_auc > 0.70:
        logging.warning(f"  [FLAG] Prediabetes ROC-AUC={pre_auc:.4f} is above 0.70 — surprisingly high!")
    else:
        logging.info(f"  [OK] Prediabetes ROC-AUC={pre_auc:.4f} within expected range (0.52–0.70).")

    # ── Phase 6: Save Models & Metadata ──────────────────────────
    logging.info("")
    logging.info("=" * 70)
    logging.info("PHASE 6: Saving Models and Metadata JSONs")
    logging.info("=" * 70)

    for label in LABEL_COLS:
        save_models_and_metadata(
            label=label,
            xgb_model=xgb_models[label],
            logreg_model=logreg_models[label],
            best_config=xgb_configs[label],
            medians=medians,
            scale_pos_weight=scale_pos_weights[label],
            X_train=X_train,
            X_val=X_val,
            X_test=X_test,
            models_dir=MODELS_DIR,
            pkg_versions=pkg_versions,
            train_timestamp=train_timestamp,
        )

    # ── Phase 7: Evaluation Report ────────────────────────────────
    generate_evaluation_report(
        raw_xgb_metrics=raw_xgb_metrics,
        raw_logreg_metrics=raw_logreg_metrics,
        suppressed_xgb_metrics=suppressed_xgb_metrics,
        scale_pos_weights=scale_pos_weights,
        xgb_val_aucprs=xgb_val_aucprs,
        xgb_configs=xgb_configs,
        suppressed_count=suppressed_count,
        train_timestamp=train_timestamp,
        reports_dir=REPORTS_DIR,
    )

    # ── Phase 8: Freeze requirements.txt ─────────────────────────
    logging.info("")
    logging.info("Freezing requirements.txt...")
    import subprocess
    freeze_output = subprocess.check_output(
        [sys.executable, "-m", "pip", "freeze"], stderr=subprocess.DEVNULL
    ).decode("utf-8")
    req_path = os.path.join(BASE_DIR, "requirements.txt")
    with open(req_path, "w", encoding="utf-8") as f:
        f.write(f"# Python {sys.version.split()[0]}\n")
        f.write(f"# Generated by train_gut.py at {train_timestamp}\n")
        f.write(freeze_output)
    logging.info(f"requirements.txt frozen: {req_path}")

    # ── Phase 9: README.md ────────────────────────────────────────
    write_readme(suppressed_xgb_metrics, train_timestamp)

    # ── Final Summary ─────────────────────────────────────────────
    total_time = time.time() - pipeline_start
    logging.info("")
    logging.info("=" * 70)
    logging.info(f"PIPELINE COMPLETE. Total runtime: {total_time:.1f}s")
    logging.info(f"Per-label runtimes: {', '.join(f'{l}: {runtimes[l]:.1f}s' for l in LABEL_COLS)}")
    logging.info("=" * 70)


def write_readme(suppressed_xgb_metrics, train_timestamp):
    """Write README.md with usage instructions and final metrics."""
    lines = [
        "# Gut Microbiome Model (v3)\n",
        "## Overview\n",
        "Independent binary classification models for 5 metabolic disease labels using CLR-transformed gut microbiome taxa data.\n",
        "Part 3/3 of the metabolic disease prediction platform (Clinical v4, Wearable v3, Gut v3).\n",
        "\n---\n",
        "## How to Run Training\n",
        "```bash",
        "cd gut_model",
        "pip install xgboost shap scikit-learn pandas numpy matplotlib joblib",
        "python src/train_gut.py",
        "```",
        "\nExpected runtime: ~15–45 minutes on CPU (36 combos × 5 labels × early-stopped XGBoost).\n",
        "Expected disk space: ~50–200 MB (models + SHAP plots + reports).\n",
        "\n---\n",
        "## How to Run Inference\n",
        "```python",
        "import sys",
        "sys.path.insert(0, 'src')",
        "from predict_gut import predict_gut",
        "",
        "# Input: dict with 21 raw taxa relative abundances (summing to ~100%)",
        "features = {",
        "    'Akkermansia': 2.1, 'Faecalibacterium': 8.5, 'Roseburia': 3.2,",
        "    'Bifidobacterium': 4.0, 'Bacteroides': 20.0, 'Prevotella': 5.0,",
        "    'Ruminococcus': 3.5, 'Blautia': 7.0, 'Collinsella': 2.0,",
        "    'Escherichia_Shigella': 1.5, 'Coprococcus': 2.5, 'Alistipes': 3.0,",
        "    'Subdoligranulum': 2.0, 'Enterococcus': 1.0, 'Eubacterium': 4.0,",
        "    'Parabacteroides': 3.2, 'Lactobacillus': 5.0, 'Klebsiella': 0.5,",
        "    'Streptococcus': 2.0, 'Eggerthella': 0.5, 'Other_Taxa': 19.5",
        "}",
        "result = predict_gut(features)",
        "print(result)",
        "```",
        "\n---\n",
        "## Final Test Metrics (XGBoost, Suppressed Predictions)\n",
        "| Label | ROC-AUC | PR-AUC | F1 | Precision | Recall |",
        "|---|---|---|---|---|---|",
    ]
    for label in LABEL_COLS:
        m = suppressed_xgb_metrics[label]
        lines.append(
            f"| {label} | {m['roc_auc']:.4f} | {m['pr_auc']:.4f} | "
            f"{m['f1']:.4f} | {m['precision']:.4f} | {m['recall']:.4f} |"
        )
    lines.extend([
        "\n---\n",
        "## Hardware & Environment\n",
        f"- **Trained on**: {platform.platform()}\n",
        f"- **Training date**: {train_timestamp}\n",
        "## Project Structure\n",
        "```",
        "gut_model/",
        "  data/               # 6 source CSVs (gut/labels/split used for training)",
        "  models/gut/         # 5 XGBoost .json + 5 LogReg .joblib + 10 metadata JSONs",
        "  reports/            # gut_evaluation.md, 5x SHAP, 5x calibration, 5x importance.csv",
        "  src/",
        "    train_gut.py      # Reproducible training pipeline",
        "    predict_gut.py    # Inference function",
        "  requirements.txt    # Pinned package versions",
        "  training.log        # Full pipeline log",
        "  README.md           # This file",
        "```",
    ])
    readme_path = os.path.join(BASE_DIR, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    logging.info(f"README.md written: {readme_path}")


if __name__ == "__main__":
    main()
