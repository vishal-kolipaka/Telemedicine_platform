import os
import sys
import time
import json
import logging
import random
import numpy as np
import pandas as pd
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
    brier_score_loss
)
from sklearn.calibration import calibration_curve

import xgboost as xgb
import shap

# Set fixed random seeds for reproducibility
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

# Paths configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models", "clinical")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
LOG_FILE = os.path.join(BASE_DIR, "training.log")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="w"),
        logging.StreamHandler(sys.stdout)
    ]
)

FEATURE_COLS = [
    "Age", "Gender", "Height", "Weight", "BMI", "Waist_Circumference",
    "Systolic_BP", "Diastolic_BP", "Fasting_Blood_Glucose", "HbA1c",
    "Triglycerides", "HDL", "LDL", "ALT", "AST",
    "Family_History_Diabetes", "Family_History_Hypertension", "Family_History_CVD"
]

LABEL_COLS = [
    "Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk",
    "Metabolic_Syndrome", "NAFLD"
]

GRID_SEARCH_SPACE = {
    "max_depth": [3, 5, 7],
    "learning_rate": [0.01, 0.05, 0.1],
    "subsample": [0.8, 1.0],
    "colsample_bytree": [0.8, 1.0]
}

def load_and_validate_data():
    logging.info("--- Phase 1: Data Load & Lightweight Quality Checks ---")
    clinical_path = os.path.join(DATA_DIR, "clinical_v3.csv")
    labels_path = os.path.join(DATA_DIR, "labels_v3.csv")
    split_path = os.path.join(DATA_DIR, "split_manifest_v3.csv")

    for path in [clinical_path, labels_path, split_path]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Required dataset file missing: {path}")

    df_clinical = pd.read_csv(clinical_path)
    df_labels = pd.read_csv(labels_path)
    df_split = pd.read_csv(split_path)

    # 1. Row count validation
    if len(df_clinical) != 20000 or len(df_labels) != 20000 or len(df_split) != 20000:
        raise ValueError(
            f"Row count mismatch! Expected 20,000 each. Got: "
            f"clinical={len(df_clinical)}, labels={len(df_labels)}, split={len(df_split)}"
        )

    # 2. Expected columns present
    for col in ["Patient_ID"] + FEATURE_COLS:
        if col not in df_clinical.columns:
            raise KeyError(f"Missing column '{col}' in clinical_v3.csv")

    for col in ["Patient_ID"] + LABEL_COLS:
        if col not in df_labels.columns:
            raise KeyError(f"Missing column '{col}' in labels_v3.csv")

    if "Patient_ID" not in df_split.columns or "Split" not in df_split.columns:
        raise KeyError("Missing 'Patient_ID' or 'Split' in split_manifest_v3.csv")

    # 3. Patient_ID set matching
    set_c = set(df_clinical["Patient_ID"])
    set_l = set(df_labels["Patient_ID"])
    set_s = set(df_split["Patient_ID"])

    if set_c != set_l or set_c != set_s:
        raise ValueError("Patient_ID sets do not match exactly across dataset files!")

    # Merge on Patient_ID
    df_merged = df_clinical.merge(df_labels, on="Patient_ID").merge(df_split, on="Patient_ID")

    # 4. Check for introduced nulls
    if df_merged[FEATURE_COLS + LABEL_COLS + ["Split"]].isnull().sum().sum() > 0:
        raise ValueError("Unexpected NaN/Null values detected in merged dataset!")

    split_counts = df_merged["Split"].value_counts().to_dict()
    logging.info(f"Data successfully loaded & validated. Splits: {split_counts}")
    return df_merged

def split_data(df):
    train_mask = df["Split"] == "Train"
    val_mask = df["Split"] == "Val"
    test_mask = df["Split"] == "Test"

    X_train = df.loc[train_mask, FEATURE_COLS].copy()
    X_val = df.loc[val_mask, FEATURE_COLS].copy()
    X_test = df.loc[test_mask, FEATURE_COLS].copy()

    y_train_dict = {col: df.loc[train_mask, col].values for col in LABEL_COLS}
    y_val_dict = {col: df.loc[val_mask, col].values for col in LABEL_COLS}
    y_test_dict = {col: df.loc[test_mask, col].values for col in LABEL_COLS}

    logging.info(
        f"Data partitioned: Train={len(X_train)}, Val={len(X_val)}, Test={len(X_test)}"
    )
    return X_train, y_train_dict, X_val, y_val_dict, X_test, y_test_dict

def compute_scale_pos_weight(y_train_label):
    n_pos = np.sum(y_train_label == 1)
    n_neg = np.sum(y_train_label == 0)
    if n_pos == 0:
        raise ValueError("No positive cases found in train set!")
    spw = float(n_neg) / float(n_pos)
    return spw

def run_manual_grid_search(label, X_train, y_train, X_val, y_val, scale_pos_weight):
    logging.info(f"Starting manual grid search for label '{label}' (36 combinations)...")
    best_aucpr = -1.0
    best_config = None
    best_model = None

    combinations = []
    for md in GRID_SEARCH_SPACE["max_depth"]:
        for lr in GRID_SEARCH_SPACE["learning_rate"]:
            for sub in GRID_SEARCH_SPACE["subsample"]:
                for col in GRID_SEARCH_SPACE["colsample_bytree"]:
                    combinations.append({
                        "max_depth": md,
                        "learning_rate": lr,
                        "subsample": sub,
                        "colsample_bytree": col
                    })

    for idx, cfg in enumerate(combinations, 1):
        model = xgb.XGBClassifier(
            n_estimators=1000,
            max_depth=cfg["max_depth"],
            learning_rate=cfg["learning_rate"],
            subsample=cfg["subsample"],
            colsample_bytree=cfg["colsample_bytree"],
            scale_pos_weight=scale_pos_weight,
            objective="binary:logistic",
            eval_metric="aucpr",
            early_stopping_rounds=20,
            random_state=SEED,
            n_jobs=-1
        )
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False
        )

        val_probs = model.predict_proba(X_val)[:, 1]
        val_aucpr = average_precision_score(y_val, val_probs)

        if val_aucpr > best_aucpr:
            best_aucpr = val_aucpr
            best_config = cfg.copy()
            best_config["n_estimators_used"] = int(model.best_iteration + 1)
            best_model = model

    logging.info(
        f"Label '{label}' Best Val PR-AUC: {best_aucpr:.4f} | Config: {best_config}"
    )
    return best_model, best_config, best_aucpr

def train_baseline_logreg(label, X_train, y_train):
    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(class_weight="balanced", random_state=SEED, solver="lbfgs"))
    ])
    pipe.fit(X_train, y_train)
    return pipe

def evaluate_predictions(y_true, y_prob, threshold=0.5):
    y_pred = (y_prob >= threshold).astype(int)
    roc = roc_auc_score(y_true, y_prob)
    pr = average_precision_score(y_true, y_prob)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    brier = brier_score_loss(y_true, y_prob)
    cm = confusion_matrix(y_true, y_pred)
    cm_norm = confusion_matrix(y_true, y_pred, normalize="true")
    report = classification_report(y_true, y_pred, digits=4, zero_division=0)

    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=10, strategy="uniform")

    return {
        "roc_auc": float(roc),
        "pr_auc": float(pr),
        "f1": float(f1),
        "precision": float(prec),
        "recall": float(rec),
        "brier": float(brier),
        "confusion_matrix": cm.tolist(),
        "confusion_matrix_norm": cm_norm.tolist(),
        "classification_report": report,
        "calibration_curve": {
            "prob_true": prob_true.tolist(),
            "prob_pred": prob_pred.tolist()
        }
    }

def run_shap_analysis(label, model, X_test):
    logging.info(f"Running SHAP TreeExplainer for '{label}'...")
    # Sample deterministic 500 patients for SHAP
    sample_indices = X_test.sample(n=min(500, len(X_test)), random_state=SEED).index
    X_sample = X_test.loc[sample_indices]

    explainer = shap.TreeExplainer(model)
    shap_values = explainer(X_sample)

    # Compute mean absolute SHAP per feature
    if len(shap_values.values.shape) == 3: # multi-class fallback though binary
        vals = np.abs(shap_values.values[:, :, 1]).mean(axis=0)
    else:
        vals = np.abs(shap_values.values).mean(axis=0)

    df_imp = pd.DataFrame({
        "Feature": FEATURE_COLS,
        "Mean_Abs_SHAP": vals
    }).sort_values(by="Mean_Abs_SHAP", ascending=False)

    imp_csv_path = os.path.join(REPORTS_DIR, f"importance_{label}.csv")
    df_imp.to_csv(imp_csv_path, index=False)

    # Generate SHAP summary plot
    plt.figure(figsize=(10, 6))
    shap.summary_plot(shap_values, X_sample, show=False)
    plt.title(f"SHAP Summary Plot - {label}", fontsize=14, pad=15)
    plt.tight_layout()
    plot_png_path = os.path.join(REPORTS_DIR, f"shap_summary_{label}.png")
    plt.savefig(plot_png_path, dpi=300, bbox_inches="tight")
    plt.close()

    logging.info(f"SHAP saved: {imp_csv_path} and {plot_png_path}")
    return df_imp

def main():
    start_time = time.time()
    logging.info("========== Starting Clinical Model Training Pipeline (v4) ==========")

    df = load_and_validate_data()
    X_train, y_train_dict, X_val, y_val_dict, X_test, y_test_dict = split_data(df)

    xgb_models = {}
    xgb_configs = {}
    xgb_val_aucprs = {}
    logreg_models = {}
    scale_pos_weights = {}
    runtimes = {}

    test_xgb_raw_probs = {}
    test_logreg_raw_probs = {}

    # Phase 2: Per-Label Training
    for label in LABEL_COLS:
        lbl_start = time.time()
        logging.info(f"\n================ Label: {label} ================")

        spw = compute_scale_pos_weight(y_train_dict[label])
        scale_pos_weights[label] = spw
        logging.info(f"Computed scale_pos_weight for {label}: {spw:.4f}")

        # XGBoost manual grid search & fit
        model, best_cfg, best_val_aucpr = run_manual_grid_search(
            label, X_train, y_train_dict[label], X_val, y_val_dict[label], spw
        )
        xgb_models[label] = model
        xgb_configs[label] = best_cfg
        xgb_val_aucprs[label] = best_val_aucpr

        # LogReg baseline fit
        logreg_pipe = train_baseline_logreg(label, X_train, y_train_dict[label])
        logreg_models[label] = logreg_pipe

        # Get Test set raw probabilities (Test touched ONLY ONCE at the end)
        test_xgb_raw_probs[label] = model.predict_proba(X_test)[:, 1]
        test_logreg_raw_probs[label] = logreg_pipe.predict_proba(X_test)[:, 1]

        # SHAP TreeExplainer Analysis
        run_shap_analysis(label, model, X_test)

        lbl_end = time.time()
        runtimes[label] = lbl_end - lbl_start
        logging.info(f"Label '{label}' training & SHAP completed in {runtimes[label]:.2f}s")

    # Phase 3: Evaluate Raw Metrics & Suppression Rule
    logging.info("\n--- Phase 3: Evaluating Test Performance & Suppression Rule ---")

    raw_xgb_metrics = {}
    raw_logreg_metrics = {}

    for label in LABEL_COLS:
        raw_xgb_metrics[label] = evaluate_predictions(y_test_dict[label], test_xgb_raw_probs[label])
        raw_logreg_metrics[label] = evaluate_predictions(y_test_dict[label], test_logreg_raw_probs[label])

    # Apply Suppression Rule to final thresholded predictions:
    # If Type2_Diabetes == 1 (predicted threshold 0.5), force Prediabetes prediction to 0.
    test_xgb_suppressed_preds = {
        label: (test_xgb_raw_probs[label] >= 0.5).astype(int).copy()
        for label in LABEL_COLS
    }

    t2d_pos_mask = (test_xgb_suppressed_preds["Type2_Diabetes"] == 1)
    suppressed_count = int(np.sum((test_xgb_suppressed_preds["Prediabetes"] == 1) & t2d_pos_mask))
    test_xgb_suppressed_preds["Prediabetes"][t2d_pos_mask] = 0

    logging.info(f"Suppression Rule Applied on Test Set: Suppressed {suppressed_count} Prediabetes cases where Type2_Diabetes=1.")

    suppressed_xgb_metrics = {}
    for label in LABEL_COLS:
        y_true = y_test_dict[label]
        y_pred = test_xgb_suppressed_preds[label]
        y_prob = test_xgb_raw_probs[label] # raw probability untouched
        roc = roc_auc_score(y_true, y_prob)
        pr = average_precision_score(y_true, y_prob)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        cm = confusion_matrix(y_true, y_pred)
        cm_norm = confusion_matrix(y_true, y_pred, normalize="true")
        report = classification_report(y_true, y_pred, digits=4, zero_division=0)

        suppressed_xgb_metrics[label] = {
            "roc_auc": float(roc),
            "pr_auc": float(pr),
            "f1": float(f1),
            "precision": float(prec),
            "recall": float(rec),
            "confusion_matrix": cm.tolist(),
            "confusion_matrix_norm": cm_norm.tolist(),
            "classification_report": report
        }

    # Phase 4: Save Models & Metadata Companion JSONs
    logging.info("\n--- Phase 4: Saving Models and Metadata JSONs ---")
    pkg_versions = {
        "xgboost": xgb.__version__,
        "scikit-learn": sklearn.__version__,
        "shap": shap.__version__
    }
    train_timestamp = pd.Timestamp.now(tz="UTC").isoformat()

    for label in LABEL_COLS:
        # Save XGBoost native model
        model_path = os.path.join(MODELS_DIR, f"xgboost_{label}.json")
        xgb_models[label].save_model(model_path)

        # Save LogReg pipeline
        logreg_path = os.path.join(MODELS_DIR, f"baseline_logreg_{label}.joblib")
        joblib.dump(logreg_models[label], logreg_path)

        # Metadata companion for XGBoost
        xgb_meta = {
            "model_type": "xgboost",
            "label": label,
            "features": FEATURE_COLS,
            "threshold": 0.5,
            "scale_pos_weight": float(scale_pos_weights[label]),
            "hyperparameters": xgb_configs[label],
            "eval_metric": "aucpr",
            "training_rows": len(X_train),
            "validation_rows": len(X_val),
            "test_rows": len(X_test),
            "train_date": train_timestamp,
            "python_version": sys.version,
            "package_versions": pkg_versions
        }
        with open(os.path.join(MODELS_DIR, f"xgboost_{label}_metadata.json"), "w") as f:
            json.dump(xgb_meta, f, indent=2)

        # Metadata companion for LogReg
        logreg_meta = {
            "model_type": "logistic_regression",
            "label": label,
            "features": FEATURE_COLS,
            "threshold": 0.5,
            "class_weight": "balanced",
            "solver": "lbfgs",
            "training_rows": len(X_train),
            "validation_rows": len(X_val),
            "test_rows": len(X_test),
            "train_date": train_timestamp,
            "python_version": sys.version,
            "package_versions": pkg_versions
        }
        with open(os.path.join(MODELS_DIR, f"baseline_logreg_{label}_metadata.json"), "w") as f:
            json.dump(logreg_meta, f, indent=2)

    # Phase 5: Generate Evaluation Markdown Report
    logging.info("\n--- Phase 5: Generating Evaluation Report ---")
    report_md_path = os.path.join(REPORTS_DIR, "clinical_evaluation.md")

    md_lines = []
    md_lines.append("# Clinical Metabolic Disease Prediction Model (v4) — Evaluation Report\n")
    md_lines.append(f"**Generated On**: {train_timestamp}\n")
    md_lines.append("## Executive Summary (XGBoost Test Performance - Suppressed Predictions)\n")
    md_lines.append("| Label | ROC-AUC | PR-AUC | F1 | Precision | Recall |")
    md_lines.append("|---|---|---|---|---|---|")
    for label in LABEL_COLS:
        m = suppressed_xgb_metrics[label]
        md_lines.append(
            f"| **{label}** | {m['roc_auc']:.4f} | {m['pr_auc']:.4f} | {m['f1']:.4f} | {m['precision']:.4f} | {m['recall']:.4f} |"
        )
    md_lines.append("\n---\n")

    md_lines.append("## Class Imbalance & Scale Pos Weight\n")
    md_lines.append("Computed strictly from Training split (14,000 rows):\n")
    for label in LABEL_COLS:
        md_lines.append(f"- **{label}**: `scale_pos_weight = {scale_pos_weights[label]:.4f}`")
    md_lines.append("\n---\n")

    md_lines.append("## Baseline (Logistic Regression) vs XGBoost Comparison\n")
    md_lines.append("| Label | Model | ROC-AUC | PR-AUC | F1 | Precision | Recall | Brier Score |")
    md_lines.append("|---|---|---|---|---|---|---|---|")
    for label in LABEL_COLS:
        bx = suppressed_xgb_metrics[label]
        bl = raw_logreg_metrics[label]
        brier_x = raw_xgb_metrics[label]["brier"]
        brier_l = bl["brier"]
        md_lines.append(f"| **{label}** | Baseline (LogReg) | {bl['roc_auc']:.4f} | {bl['pr_auc']:.4f} | {bl['f1']:.4f} | {bl['precision']:.4f} | {bl['recall']:.4f} | {brier_l:.4f} |")
        md_lines.append(f"| **{label}** | **XGBoost (v4)** | **{bx['roc_auc']:.4f}** | **{bx['pr_auc']:.4f}** | **{bx['f1']:.4f}** | **{bx['precision']:.4f}** | **{bx['recall']:.4f}** | **{brier_x:.4f}** |")
    md_lines.append("\n---\n")

    md_lines.append("## Mutual Exclusivity Suppression Rule Impact\n")
    md_lines.append("Suppression Rule: If `Type2_Diabetes` prediction = 1, `Prediabetes` prediction is forced to 0 (raw probability untouched).\n")
    md_lines.append("| Metric | Prediabetes (Raw) | Prediabetes (Suppressed) | Change |")
    md_lines.append("|---|---|---|---|")
    pre_raw = raw_xgb_metrics["Prediabetes"]
    pre_sup = suppressed_xgb_metrics["Prediabetes"]
    md_lines.append(f"| Precision | {pre_raw['precision']:.4f} | {pre_sup['precision']:.4f} | {pre_sup['precision']-pre_raw['precision']:+.4f} |")
    md_lines.append(f"| Recall | {pre_raw['recall']:.4f} | {pre_sup['recall']:.4f} | {pre_sup['recall']-pre_raw['recall']:+.4f} |")
    md_lines.append(f"| F1 Score | {pre_raw['f1']:.4f} | {pre_sup['f1']:.4f} | {pre_sup['f1']-pre_raw['f1']:+.4f} |")
    md_lines.append(f"| Total Suppressed Patients | - | {suppressed_count} | - |")
    md_lines.append("\n---\n")

    md_lines.append("## Detailed Per-Label Classification Reports & Confusion Matrices\n")
    for label in LABEL_COLS:
        m = raw_xgb_metrics[label]
        sm = suppressed_xgb_metrics[label]
        cfg = xgb_configs[label]

        md_lines.append(f"### Label: {label}\n")
        md_lines.append(f"- **Best Hyperparameters**: `max_depth={cfg['max_depth']}, learning_rate={cfg['learning_rate']}, subsample={cfg['subsample']}, colsample_bytree={cfg['colsample_bytree']}, n_estimators_used={cfg['n_estimators_used']}`")
        md_lines.append(f"- **Validation PR-AUC**: `{xgb_val_aucprs[label]:.4f}`")
        md_lines.append(f"- **Brier Score**: `{m['brier']:.4f}`")
        md_lines.append("\n#### Classification Report (Suppressed Predictions)\n```")
        md_lines.append(sm['classification_report'])
        md_lines.append("```\n")

        md_lines.append("#### Confusion Matrix (Raw Counts)\n```")
        cm_arr = np.array(sm['confusion_matrix'])
        md_lines.append(f"TN: {cm_arr[0,0]:<5} FP: {cm_arr[0,1]:<5}")
        md_lines.append(f"FN: {cm_arr[1,0]:<5} TP: {cm_arr[1,1]:<5}")
        md_lines.append("```\n")

        md_lines.append("#### Confusion Matrix (Row-Normalized)\n```")
        cm_n = np.array(sm['confusion_matrix_norm'])
        md_lines.append(f"TN: {cm_n[0,0]:.4f} FP: {cm_n[0,1]:.4f}")
        md_lines.append(f"FN: {cm_n[1,0]:.4f} TP: {cm_n[1,1]:.4f}")
        md_lines.append("```\n")

    with open(report_md_path, "w") as f:
        f.write("\n".join(md_lines))

    logging.info(f"Evaluation report written to {report_md_path}")

    # Phase 6: Requirements freeze
    req_path = os.path.join(BASE_DIR, "requirements.txt")
    import subprocess
    freeze_output = subprocess.check_output([sys.executable, "-m", "pip", "freeze"]).decode("utf-8")
    with open(req_path, "w") as f:
        f.write(f"# Python {sys.version.split()[0]}\n")
        f.write(freeze_output)
    logging.info(f"requirements.txt frozen at {req_path}")

    total_time = time.time() - start_time
    logging.info(f"========== Pipeline completed successfully in {total_time:.2f} seconds ==========")

if __name__ == "__main__":
    main()
