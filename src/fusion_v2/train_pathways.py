"""
train_pathways.py — Systematic Training and Serialization of the 35 Pathway Meta-Models

Trains and serializes the 7-Pathway Stacking Architecture:
  Pathways (7): C, W, G, C_W, C_G, W_G, C_W_G
  Diseases (5): Type2_Diabetes, Prediabetes, High_Adiposity_Risk, Metabolic_Syndrome, NAFLD
  Total models: 35 specialized meta-stackers

Training Pipeline:
  1. Train Split (N=14,000 OOF): Fit L2-regularized Logistic Regression per pathway and per disease.
  2. Validation Split (N=3,000): Fit Platt calibration parameters (A, B) and optimize decision thresholds (maximizing F1).
  3. Test Split (N=3,000): Single-pass holdout evaluation for reporting and audit verification.
  4. Serialization: Outputs 'src/fusion_v2/models/pathway_manifest.json'.
"""

from __future__ import annotations

import os
import json
import warnings
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    roc_auc_score, average_precision_score, brier_score_loss,
    f1_score, precision_score, recall_score
)

warnings.filterwarnings("ignore")
np.random.seed(42)

DISEASES = [
    "Type2_Diabetes",
    "Prediabetes",
    "High_Adiposity_Risk",
    "Metabolic_Syndrome",
    "NAFLD",
]

PATHWAYS = {
    "C": ["Clinical"],
    "W": ["Wearable"],
    "G": ["Gut"],
    "C_W": ["Clinical", "Wearable"],
    "C_G": ["Clinical", "Gut"],
    "W_G": ["Wearable", "Gut"],
    "C_W_G": ["Clinical", "Wearable", "Gut"],
}


def calc_ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """Calculates Expected Calibration Error (ECE)."""
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
    return float(ece)


def fit_platt_scaling(y_true: np.ndarray, raw_logits: np.ndarray) -> tuple[float, float]:
    """Fits Platt scaling (1D Logistic Regression on raw logits).
    P_cal = sigmoid(A * raw_logit + B).
    """
    lr_cal = LogisticRegression(penalty=None, solver="lbfgs", random_state=42)
    X = raw_logits.reshape(-1, 1)
    lr_cal.fit(X, y_true)
    A = float(lr_cal.coef_[0][0])
    B = float(lr_cal.intercept_[0])
    return A, B


def apply_platt_scaling(raw_logits: np.ndarray, A: float, B: float) -> np.ndarray:
    """Applies fitted Platt calibration."""
    cal_logits = A * raw_logits + B
    cal_logits = np.clip(cal_logits, -50.0, 50.0)
    return 1.0 / (1.0 + np.exp(-cal_logits))


def optimize_threshold(y_true: np.ndarray, y_prob: np.ndarray) -> tuple[float, float]:
    """Finds threshold in [0.05, 0.95] that maximizes F1 score."""
    best_t = 0.50
    best_f1 = -1.0
    for t in np.linspace(0.05, 0.95, 91):
        yp = (y_prob >= t).astype(int)
        f = f1_score(y_true, yp, zero_division=0)
        if f > best_f1:
            best_f1 = f
            best_t = float(t)
    return round(best_t, 2), float(best_f1)


def evaluate_metrics(y_true: np.ndarray, y_prob: np.ndarray, threshold: float) -> dict[str, float]:
    """Computes full classification, discrimination, and calibration metrics."""
    y_prob_c = np.clip(y_prob, 1e-7, 1.0 - 1e-7)
    roc = float(roc_auc_score(y_true, y_prob_c))
    pr = float(average_precision_score(y_true, y_prob_c))
    brier = float(brier_score_loss(y_true, y_prob_c))
    ece = calc_ece(y_true, y_prob_c)
    
    yp = (y_prob >= threshold).astype(int)
    f1 = float(f1_score(y_true, yp, zero_division=0))
    prec = float(precision_score(y_true, yp, zero_division=0))
    rec = float(recall_score(y_true, yp, zero_division=0))
    tn = int(np.sum((y_true == 0) & (yp == 0)))
    fp = int(np.sum((y_true == 0) & (yp == 1)))
    spec = float(tn / max(1, tn + fp))
    
    return {
        "roc_auc": round(roc, 4),
        "pr_auc": round(pr, 4),
        "f1": round(f1, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "specificity": round(spec, 4),
        "brier_score": round(brier, 4),
        "ece": round(ece, 4),
        "threshold": threshold,
    }


def main():
    print("========================================================================")
    print("  ADAPTIVE 7-PATHWAY LATE-FUSION TRAINING & SERIALIZATION PIPELINE")
    print("========================================================================")

    # 1. Load Data
    oof_df = pd.read_csv("fusion_phase2/oof/oof_train_predictions.csv")
    labels_df = pd.read_csv("datasets/labels_v3.csv")
    split_df = pd.read_csv("datasets/split_manifest_v3.csv")
    
    train_pids = split_df[split_df["Split"] == "Train"]["Patient_ID"]
    train_labels_df = labels_df[labels_df["Patient_ID"].isin(train_pids)].set_index("Patient_ID").loc[oof_df["Patient_ID"]].reset_index()
    
    val_df = pd.read_csv("fusion_val_master.csv")
    test_df = pd.read_csv("fusion_test_master.csv")
    
    print(f"Loaded Splits: Train OOF={len(oof_df)}, Val={len(val_df)}, Test={len(test_df)}")

    manifest = {
        "version": "2.1.0",
        "description": "Adaptive 7-Pathway Late-Fusion Stacking Meta-Models Manifest",
        "diseases": DISEASES,
        "pathways": list(PATHWAYS.keys()),
        "models": {},
    }

    # 2. Iterate Over All 7 Pathways
    for path_key, modalities in PATHWAYS.items():
        manifest["models"][path_key] = {
            "modalities": modalities,
            "dimension": len(modalities),
            "diseases": {},
        }
        print(f"\n--- Fitting Pathway [{path_key}] (Modalities: {', '.join(modalities)}) ---")

        for dis in DISEASES:
            y_train = train_labels_df[dis].values
            y_val = val_df[f"{dis}_true"].values
            y_test = test_df[f"{dis}_true"].values

            # Assemble feature matrices: [Mod1_dis_prob, Mod2_dis_prob, ...]
            X_train = np.column_stack([oof_df[f"{m}_{dis}_prob"].values for m in modalities])
            X_val = np.column_stack([val_df[f"{m}_{dis}_prob"].values for m in modalities])
            X_test = np.column_stack([test_df[f"{m}_{dis}_prob"].values for m in modalities])

            if len(modalities) == 1:
                # Single-modality pass-through / identity with calibrated thresholding
                intercept = 0.0
                coefs = [1.0]
                val_raw_logits = np.log(np.clip(X_val[:, 0], 1e-6, 1.0 - 1e-6) / np.clip(1.0 - X_val[:, 0], 1e-6, 1.0 - 1e-6))
                
                # Fit Platt scaling
                platt_A, platt_B = fit_platt_scaling(y_val, val_raw_logits)
                val_cal_probs = apply_platt_scaling(val_raw_logits, platt_A, platt_B)
                
                test_raw_logits = np.log(np.clip(X_test[:, 0], 1e-6, 1.0 - 1e-6) / np.clip(1.0 - X_test[:, 0], 1e-6, 1.0 - 1e-6))
                test_cal_probs = apply_platt_scaling(test_raw_logits, platt_A, platt_B)

            else:
                # Multi-modality L2 Stacker
                lr = LogisticRegression(penalty="l2", C=1.0, solver="lbfgs", random_state=42)
                lr.fit(X_train, y_train)
                
                intercept = float(lr.intercept_[0])
                coefs = [float(c) for c in lr.coef_[0]]
                
                val_raw_logits = intercept + np.dot(X_val, coefs)
                
                # Fit Platt scaling on Validation
                platt_A, platt_B = fit_platt_scaling(y_val, val_raw_logits)
                val_cal_probs = apply_platt_scaling(val_raw_logits, platt_A, platt_B)
                
                test_raw_logits = intercept + np.dot(X_test, coefs)
                test_cal_probs = apply_platt_scaling(test_raw_logits, platt_A, platt_B)

            # Optimize threshold on Validation
            opt_thresh, val_f1 = optimize_threshold(y_val, val_cal_probs)

            # Evaluate Validation and Test metrics
            val_metrics = evaluate_metrics(y_val, val_cal_probs, opt_thresh)
            test_metrics = evaluate_metrics(y_test, test_cal_probs, opt_thresh)

            # Format human-readable formula
            formula_terms = [f"{coefs[i]:.4f} * {modalities[i]}" for i in range(len(modalities))]
            formula_str = f"sigmoid({intercept:.4f} + {' + '.join(formula_terms)})"

            model_entry = {
                "disease": dis,
                "pathway": path_key,
                "modalities": modalities,
                "intercept": round(intercept, 6),
                "coefficients": {modalities[i].lower(): round(coefs[i], 6) for i in range(len(modalities))},
                "platt_scaling": {
                    "A": round(platt_A, 6),
                    "B": round(platt_B, 6),
                },
                "threshold": opt_thresh,
                "formula": formula_str,
                "validation_metrics": val_metrics,
                "test_metrics": test_metrics,
            }

            manifest["models"][path_key]["diseases"][dis] = model_entry
            print(f"  • {dis:22s} | Val ROC={val_metrics['roc_auc']:.4f}, PR={val_metrics['pr_auc']:.4f}, F1={val_metrics['f1']:.4f} | Thresh={opt_thresh:.2f} | Formula={formula_str}")

    # 3. Save Manifest
    out_dir = "src/fusion_v2/models"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "pathway_manifest.json")
    
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    print(f"\n[SUCCESS] Serialized 35 pathway meta-models to '{out_path}'.")


if __name__ == "__main__":
    main()
