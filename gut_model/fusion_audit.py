"""
fusion_audit.py - Cross-modality probability correlation and complementarity analysis.
Generates raw probabilities from all 3 frozen modalities on the Test+Val splits,
then computes correlations, disagreement patterns, and complementarity metrics.

CRITICAL: This script loads the frozen models and runs inference. It does NOT retrain anything.
"""
import os
import sys
import json
import numpy as np
import pandas as pd
import xgboost as xgb
from scipy import stats

BASE = r"c:\Users\HP PC\Desktop\telemedicine platform"

# ---- Load shared data ----
labels = pd.read_csv(os.path.join(BASE, "clinical_model", "data", "labels_v3.csv"))
splits = pd.read_csv(os.path.join(BASE, "clinical_model", "data", "split_manifest_v3.csv"))
clinical = pd.read_csv(os.path.join(BASE, "clinical_model", "data", "clinical_v3.csv"))
wearable_std = pd.read_csv(os.path.join(BASE, "wearable_model", "data", "wearable_standard_v3.csv"))
wearable_cgm = pd.read_csv(os.path.join(BASE, "wearable_model", "data", "wearable_cgm_v3.csv"))
gut_raw = pd.read_csv(os.path.join(BASE, "gut_model", "data", "gut_v3.csv"))

LABEL_COLS = ["Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk", "Metabolic_Syndrome", "NAFLD"]

# ---- Verify Patient_ID alignment ----
assert list(labels["Patient_ID"]) == list(splits["Patient_ID"]), "labels/splits Patient_ID mismatch"
assert list(labels["Patient_ID"]) == list(clinical["Patient_ID"]), "labels/clinical Patient_ID mismatch"
assert list(labels["Patient_ID"]) == list(wearable_std["Patient_ID"]), "labels/wearable_std Patient_ID mismatch"
assert list(labels["Patient_ID"]) == list(wearable_cgm["Patient_ID"]), "labels/wearable_cgm Patient_ID mismatch"
assert list(labels["Patient_ID"]) == list(gut_raw["Patient_ID"]), "labels/gut Patient_ID mismatch"
print("[OK] Patient_ID alignment verified across ALL datasets")

# ---- Split masks ----
train_mask = splits["Split"] == "Train"
val_mask = splits["Split"] == "Val"
test_mask = splits["Split"] == "Test"
print(f"Train={train_mask.sum()}, Val={val_mask.sum()}, Test={test_mask.sum()}")

# ---- Load Clinical features ----
CLINICAL_FEATURES = [
    "Age", "Gender", "Height", "Weight", "BMI", "Waist_Circumference",
    "Systolic_BP", "Diastolic_BP", "Fasting_Blood_Glucose", "HbA1c",
    "Triglycerides", "HDL", "LDL", "ALT", "AST",
    "Family_History_Diabetes", "Family_History_Hypertension", "Family_History_CVD"
]
X_clinical = clinical[CLINICAL_FEATURES]

# ---- Load Wearable features ----
WEARABLE_FEATURES = [
    "Average_Daily_Steps", "Active_Minutes", "Sedentary_Time_Minutes",
    "Resting_Heart_Rate", "Heart_Rate_Variability_RMSSD",
    "Sleep_Duration_Hours", "Sleep_Efficiency_Score", "Autonomic_Stress_Score",
    "Activity_Energy_Expenditure", "Exercise_Frequency_Days",
    "CGM_Average_Glucose", "CGM_Glucose_CV",
    "CGM_Time_In_Range", "CGM_Time_Above_Range", "CGM_Time_Below_Range"
]
wearable_merged = wearable_std.merge(wearable_cgm, on="Patient_ID")
X_wearable = wearable_merged[WEARABLE_FEATURES]

# ---- Load Gut features + CLR transform ----
GUT_RAW_TAXA = [
    "Akkermansia", "Faecalibacterium", "Roseburia", "Bifidobacterium",
    "Bacteroides", "Prevotella", "Ruminococcus", "Blautia", "Collinsella",
    "Escherichia_Shigella", "Coprococcus", "Alistipes", "Subdoligranulum",
    "Enterococcus", "Eubacterium", "Parabacteroides", "Lactobacillus",
    "Klebsiella", "Streptococcus", "Eggerthella", "Other_Taxa"
]
GUT_CLR_FEATURES = [t + "_CLR" for t in GUT_RAW_TAXA]
CLR_DELTA = 1e-5

# Load gut metadata for imputation medians
with open(os.path.join(BASE, "gut_model", "models", "gut", "xgboost_Type2_Diabetes_metadata.json")) as f:
    gut_meta = json.load(f)
imputation_medians = gut_meta["preprocessing"]["imputation_medians"]

# Apply imputation using TRAIN-only medians (same as training pipeline)
gut_taxa = gut_raw[GUT_RAW_TAXA].copy()
null_mask = gut_taxa.isnull().all(axis=1)
print(f"Gut null rows (MCAR): {null_mask.sum()}")
for col in GUT_RAW_TAXA:
    gut_taxa.loc[gut_taxa[col].isnull(), col] = imputation_medians[col]

# Apply CLR transform
taxa_arr = gut_taxa.values + CLR_DELTA
log_arr = np.log(taxa_arr)
log_mean = log_arr.mean(axis=1, keepdims=True)
clr_arr = log_arr - log_mean
X_gut = pd.DataFrame(clr_arr, columns=GUT_CLR_FEATURES, index=gut_taxa.index)
assert np.all(np.isfinite(X_gut.values)), "Non-finite CLR values!"
print(f"[OK] Gut CLR transform applied: {X_gut.shape}")

# ---- Load frozen models ----
def load_xgb_models(modality_dir, subdir):
    models = {}
    for label in LABEL_COLS:
        model = xgb.XGBClassifier()
        model.load_model(os.path.join(BASE, modality_dir, "models", subdir, f"xgboost_{label}.json"))
        models[label] = model
    return models

clinical_models = load_xgb_models("clinical_model", "clinical")
wearable_models = load_xgb_models("wearable_model", "wearable")
gut_models = load_xgb_models("gut_model", "gut")
print("[OK] All 15 frozen models loaded")

# ---- Generate raw probabilities for ALL 20k patients ----
def get_probs(models, X_features):
    probs = {}
    for label in LABEL_COLS:
        probs[label] = models[label].predict_proba(X_features)[:, 1]
    return probs

clinical_probs = get_probs(clinical_models, X_clinical)
wearable_probs = get_probs(wearable_models, X_wearable)
gut_probs = get_probs(gut_models, X_gut)
print("[OK] Raw probabilities generated for all 20k patients across 3 modalities")

# ---- Build probability DataFrame ----
prob_df = pd.DataFrame({"Patient_ID": labels["Patient_ID"], "Split": splits["Split"]})
for label in LABEL_COLS:
    prob_df[f"clinical_{label}"] = clinical_probs[label]
    prob_df[f"wearable_{label}"] = wearable_probs[label]
    prob_df[f"gut_{label}"] = gut_probs[label]
    prob_df[f"label_{label}"] = labels[label].values

# ---- Correlation Analysis (Test set only) ----
print("\n" + "="*80)
print("PROBABILITY CORRELATIONS (Test Set, n=3000)")
print("="*80)

test_df = prob_df[prob_df["Split"] == "Test"].copy()
val_df = prob_df[prob_df["Split"] == "Val"].copy()
train_df = prob_df[prob_df["Split"] == "Train"].copy()

for label in LABEL_COLS:
    c = test_df[f"clinical_{label}"]
    w = test_df[f"wearable_{label}"]
    g = test_df[f"gut_{label}"]
    
    corr_cw = np.corrcoef(c, w)[0, 1]
    corr_cg = np.corrcoef(c, g)[0, 1]
    corr_wg = np.corrcoef(w, g)[0, 1]
    
    print(f"\n  {label}:")
    print(f"    corr(Clinical, Wearable) = {corr_cw:.4f}")
    print(f"    corr(Clinical, Gut)      = {corr_cg:.4f}")
    print(f"    corr(Wearable, Gut)      = {corr_wg:.4f}")

# ---- Disagreement Analysis (Test set) ----
print("\n" + "="*80)
print("PREDICTION DISAGREEMENT ANALYSIS (Test Set, threshold=0.5)")
print("="*80)

for label in LABEL_COLS:
    c_pred = (test_df[f"clinical_{label}"] >= 0.5).astype(int)
    w_pred = (test_df[f"wearable_{label}"] >= 0.5).astype(int)
    g_pred = (test_df[f"gut_{label}"] >= 0.5).astype(int)
    y_true = test_df[f"label_{label}"]
    
    all_agree = ((c_pred == w_pred) & (w_pred == g_pred)).sum()
    c_w_disagree = (c_pred != w_pred).sum()
    c_g_disagree = (c_pred != g_pred).sum()
    w_g_disagree = (w_pred != g_pred).sum()
    
    # Cases where weaker modalities are right and clinical is wrong
    clinical_wrong = (c_pred != y_true)
    wearable_right_clinical_wrong = (clinical_wrong & (w_pred == y_true)).sum()
    gut_right_clinical_wrong = (clinical_wrong & (g_pred == y_true)).sum()
    either_right_clinical_wrong = (clinical_wrong & ((w_pred == y_true) | (g_pred == y_true))).sum()
    clinical_wrong_count = clinical_wrong.sum()
    
    print(f"\n  {label}:")
    print(f"    All 3 agree:                  {all_agree}/{len(test_df)} ({100*all_agree/len(test_df):.1f}%)")
    print(f"    Clinical vs Wearable disagree: {c_w_disagree}")
    print(f"    Clinical vs Gut disagree:      {c_g_disagree}")
    print(f"    Wearable vs Gut disagree:      {w_g_disagree}")
    print(f"    Clinical wrong (total):        {clinical_wrong_count}")
    print(f"    Wearable right when Clin wrong: {wearable_right_clinical_wrong}")
    print(f"    Gut right when Clin wrong:      {gut_right_clinical_wrong}")
    print(f"    Either right when Clin wrong:   {either_right_clinical_wrong}")

# ---- Per-disease AUC comparison (Test set) ----
print("\n" + "="*80)
print("PER-DISEASE ROC-AUC COMPARISON (Test Set)")
print("="*80)

from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss

print(f"\n{'Label':<25} {'Clinical':>10} {'Wearable':>10} {'Gut':>10} {'SimpleAvg':>10}")
print("-" * 70)

for label in LABEL_COLS:
    y = test_df[f"label_{label}"]
    c = test_df[f"clinical_{label}"]
    w = test_df[f"wearable_{label}"]
    g = test_df[f"gut_{label}"]
    avg = (c + w + g) / 3.0
    
    auc_c = roc_auc_score(y, c)
    auc_w = roc_auc_score(y, w)
    auc_g = roc_auc_score(y, g)
    auc_avg = roc_auc_score(y, avg)
    
    print(f"  {label:<23} {auc_c:>10.4f} {auc_w:>10.4f} {auc_g:>10.4f} {auc_avg:>10.4f}")

print(f"\n{'Label':<25} {'Clinical':>10} {'Wearable':>10} {'Gut':>10} {'SimpleAvg':>10}")
print("-" * 70)
print("PR-AUC:")
for label in LABEL_COLS:
    y = test_df[f"label_{label}"]
    c = test_df[f"clinical_{label}"]
    w = test_df[f"wearable_{label}"]
    g = test_df[f"gut_{label}"]
    avg = (c + w + g) / 3.0
    
    pr_c = average_precision_score(y, c)
    pr_w = average_precision_score(y, w)
    pr_g = average_precision_score(y, g)
    pr_avg = average_precision_score(y, avg)
    
    print(f"  {label:<23} {pr_c:>10.4f} {pr_w:>10.4f} {pr_g:>10.4f} {pr_avg:>10.4f}")

print("\nBrier Scores:")
for label in LABEL_COLS:
    y = test_df[f"label_{label}"]
    c = test_df[f"clinical_{label}"]
    w = test_df[f"wearable_{label}"]
    g = test_df[f"gut_{label}"]
    avg = (c + w + g) / 3.0
    
    br_c = brier_score_loss(y, c)
    br_w = brier_score_loss(y, w)
    br_g = brier_score_loss(y, g)
    br_avg = brier_score_loss(y, avg)
    
    print(f"  {label:<23} {br_c:>10.4f} {br_w:>10.4f} {br_g:>10.4f} {br_avg:>10.4f}")

# ---- Calibration analysis: probability distribution statistics ----
print("\n" + "="*80)
print("PROBABILITY DISTRIBUTION STATS (Test Set)")
print("="*80)

for label in LABEL_COLS:
    print(f"\n  {label}:")
    for mod in ["clinical", "wearable", "gut"]:
        p = test_df[f"{mod}_{label}"]
        print(f"    {mod:>10}: mean={p.mean():.4f}, std={p.std():.4f}, min={p.min():.4f}, max={p.max():.4f}, median={p.median():.4f}")

# ---- Train-set leakage analysis: check if Train probs are overfit ----
print("\n" + "="*80)
print("TRAIN vs TEST AUC COMPARISON (leakage indicator)")
print("="*80)

print(f"\n{'Label':<25} {'Clin_Train':>11} {'Clin_Test':>11} {'Wear_Train':>11} {'Wear_Test':>11} {'Gut_Train':>11} {'Gut_Test':>11}")
print("-" * 90)

for label in LABEL_COLS:
    y_tr = train_df[f"label_{label}"]
    y_te = test_df[f"label_{label}"]
    
    auc_c_tr = roc_auc_score(y_tr, train_df[f"clinical_{label}"])
    auc_c_te = roc_auc_score(y_te, test_df[f"clinical_{label}"])
    auc_w_tr = roc_auc_score(y_tr, train_df[f"wearable_{label}"])
    auc_w_te = roc_auc_score(y_te, test_df[f"wearable_{label}"])
    auc_g_tr = roc_auc_score(y_tr, train_df[f"gut_{label}"])
    auc_g_te = roc_auc_score(y_te, test_df[f"gut_{label}"])
    
    print(f"  {label:<23} {auc_c_tr:>11.4f} {auc_c_te:>11.4f} {auc_w_tr:>11.4f} {auc_w_te:>11.4f} {auc_g_tr:>11.4f} {auc_g_te:>11.4f}")

# ---- Save probability matrix for fusion use ----
prob_df.to_csv(os.path.join(BASE, "gut_model", "data", "fusion_probabilities_audit.csv"), index=False)
print(f"\n[OK] Full probability matrix saved to fusion_probabilities_audit.csv")
print("\n[DONE] Fusion audit analysis complete.")
