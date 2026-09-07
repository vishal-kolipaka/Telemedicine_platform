# Fusion Phase 1: Artifact Inventory & Prediction Export Report

**Date**: 2026-08-09  
**Scope**: Artifact Inventory, Cross-Modality Consistency Verification, Prediction Export (Val & Test), Recomputed Sanity-Check Metrics, Train-Set Status Check, and Modality-Level Missingness Check.  
**Execution Mode**: Strictly frozen-model inference and artifact verification. No model training, tuning, calibration, or OOF generation performed.

---

## PART 1 — Artifact Inventory

| Modality | Artifact Type | Path | Found? | Notes / Details |
|---|---|---|:---:|---|
| **clinical_model** | XGBoost Models (5 labels) | `clinical_model/models/clinical/xgboost_<label>.json` | **Y** | Native XGBoost JSON format (3.3.0) |
| **clinical_model** | LogReg Baselines (5 labels) | `clinical_model/models/clinical/baseline_logreg_<label>.joblib` | **Y** | Joblib serialized sklearn Pipeline |
| **clinical_model** | Inference Script | `clinical_model/src/predict_clinical.py` | **Y** | Module `predict_clinical.py` |
| **clinical_model** | Metadata JSONs (5 labels) | `clinical_model/models/clinical/xgboost_<label>_metadata.json` | **Y** | Configuration & hyperparameters metadata |
| **clinical_model** | Saved Prediction Files | None | **N** | Pre-computed prediction files were not stored on disk |
| **clinical_model** | Training Log | `clinical_model/training.log` | **Y** | Execution log (pipeline completed in 55.77s) |
| **clinical_model** | Evaluation Report | `clinical_model/reports/clinical_evaluation.md` | **Y** | Markdown evaluation report |
| **clinical_model** | SHAP Importance Files | `clinical_model/reports/importance_<label>.csv` | **Y** | Mean absolute SHAP values (500 samples) |
| **clinical_model** | Requirements File | `clinical_model/requirements.txt` | **Y** | Frozen environment dependencies |
| **wearable_model** | XGBoost Models (5 labels) | `wearable_model/models/wearable/xgboost_<label>.json` | **Y** | Native XGBoost JSON format (3.3.0) |
| **wearable_model** | LogReg Baselines (5 labels) | `wearable_model/models/wearable/baseline_logreg_<label>.joblib` | **Y** | Joblib serialized sklearn Pipeline |
| **wearable_model** | Inference Script | `wearable_model/src/predict_wearable.py` | **Y** | Module `predict_wearable.py` |
| **wearable_model** | Metadata JSONs (5 labels) | `wearable_model/models/wearable/xgboost_<label>_metadata.json` | **Y** | Configuration & hyperparameters metadata |
| **wearable_model** | Saved Prediction Files | None | **N** | Pre-computed prediction files were not stored on disk |
| **wearable_model** | Training Log | `wearable_model/training.log` | **Y** | Execution log (pipeline completed in 47.85s) |
| **wearable_model** | Evaluation Report | `wearable_model/reports/wearable_evaluation.md` | **Y** | Markdown evaluation report |
| **wearable_model** | SHAP Importance Files | `wearable_model/reports/importance_<label>.csv` | **Y** | Mean absolute SHAP values (500 samples) |
| **wearable_model** | Requirements File | `wearable_model/requirements.txt` | **Y** | Frozen environment dependencies |
| **gut_model** | XGBoost Models (5 labels) | `gut_model/models/gut/xgboost_<label>.json` | **Y** | Native XGBoost JSON format (3.3.0) |
| **gut_model** | LogReg Baselines (5 labels) | `gut_model/models/gut/baseline_logreg_<label>.joblib` | **Y** | Joblib serialized sklearn Pipeline |
| **gut_model** | Inference Script | `gut_model/src/predict_gut.py` | **Y** | Module `predict_gut.py` |
| **gut_model** | Metadata JSONs (5 labels) | `gut_model/models/gut/xgboost_<label>_metadata.json` | **Y** | Includes `imputation_medians` & `clr_delta` |
| **gut_model** | Saved Prediction Files | None | **N** | Pre-computed prediction files were not stored on disk |
| **gut_model** | Training Log | `gut_model/training.log` | **Y** | Execution log (pipeline completed in 109.9s) |
| **gut_model** | Evaluation Report | `gut_model/reports/gut_evaluation.md` | **Y** | Markdown evaluation report |
| **gut_model** | SHAP Importance Files | `gut_model/reports/importance_<label>.csv` | **Y** | Mean absolute SHAP values (500 samples) |
| **gut_model** | Requirements File | `gut_model/requirements.txt` | **Y** | Frozen environment dependencies |

### Feature Lists & Decision Threshold Summary

- **Clinical Feature List (18 features)**: `Age`, `Gender`, `Height`, `Weight`, `BMI`, `Waist_Circumference`, `Systolic_BP`, `Diastolic_BP`, `Fasting_Blood_Glucose`, `HbA1c`, `Triglycerides`, `HDL`, `LDL`, `ALT`, `AST`, `Family_History_Diabetes`, `Family_History_Hypertension`, `Family_History_CVD`.
- **Wearable Feature List (15 features)**: `Average_Daily_Steps`, `Active_Minutes`, `Sedentary_Time_Minutes`, `Resting_Heart_Rate`, `Heart_Rate_Variability_RMSSD`, `Sleep_Duration_Hours`, `Sleep_Efficiency_Score`, `Autonomic_Stress_Score`, `Activity_Energy_Expenditure`, `Exercise_Frequency_Days`, `CGM_Average_Glucose`, `CGM_Glucose_CV`, `CGM_Time_In_Range`, `CGM_Time_Above_Range`, `CGM_Time_Below_Range`.
- **Gut Feature List (21 CLR-transformed features)**: `Akkermansia_CLR`, `Faecalibacterium_CLR`, `Roseburia_CLR`, `Bifidobacterium_CLR`, `Bacteroides_CLR`, `Prevotella_CLR`, `Ruminococcus_CLR`, `Blautia_CLR`, `Collinsella_CLR`, `Escherichia_Shigella_CLR`, `Coprococcus_CLR`, `Alistipes_CLR`, `Subdoligranulum_CLR`, `Enterococcus_CLR`, `Eubacterium_CLR`, `Parabacteroides_CLR`, `Lactobacillus_CLR`, `Klebsiella_CLR`, `Streptococcus_CLR`, `Eggerthella_CLR`, `Other_Taxa_CLR`.
- **Decision Thresholds**: Confirmed strictly `0.5` across all 3 modalities for binary decision classification.

---

## PART 2 — Cross-Modality Consistency Verification

| Check | Result | Evidence Found | Notes |
|---|:---:|---|---|
| **1. Patient Population Universe** | **PASS** | 20,000 unique `Patient_ID` strings across all 6 CSV files (`labels_v3.csv`, `split_manifest_v3.csv`, `clinical_v3.csv`, `wearable_standard_v3.csv`, `wearable_cgm_v3.csv`, `gut_v3.csv`). | `Patient_ID` values are 100% identical and in the exact same index order across all datasets. No missing IDs. |
| **2. Split Manifest Counts & Assignment** | **PASS** | Verified single `split_manifest_v3.csv` shared across all modalities. Row counts: Train=14,000 (70%), Val=3,000 (15%), Test=3,000 (15%). | Zero split mismatch or index misalignment across modalities. |
| **3. Labels Ground Truth Verification** | **PASS** | `labels_v3.csv` contains columns: `Patient_ID`, `Type2_Diabetes`, `Prediabetes`, `High_Adiposity_Risk`, `Metabolic_Syndrome`, `NAFLD`. Data types are strictly integer `0` or `1`. | Identical ground truth labels referenced across all 3 model pipelines. |
| **4. Label Ordering Consistency** | **PASS** | All metadata JSONs and prediction pipelines process `LABEL_COLS` in exact identical order: `["Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk", "Metabolic_Syndrome", "NAFLD"]`. | Constant ordering enforced. |
| **5. Decision Threshold Consistency** | **PASS** | All 15 metadata companion JSONs specify `threshold: 0.5`. All `predict_*.py` modules hardcode `0.5`. | Confirmed `0.5` for all binary decisions. No custom/tuned thresholds used. |
| **6. Patient_ID Exclusion Verification** | **PASS** | Feature lists: Clinical (18), Wearable (15), Gut (21 CLR). `Patient_ID` is absent from all model input feature schemas. | `Patient_ID` is strictly used as an identifier key for joining. |

---

## PART 3 — Prediction Export Summary

All prediction files have been generated via inference on the frozen models for Validation ($n=3,000$) and Test ($n=3,000$) splits.

### Per-Modality Prediction Export Files
1. `clinical_val_predictions.csv` (3,000 rows)
2. `clinical_test_predictions.csv` (3,000 rows)
3. `wearable_val_predictions.csv` (3,000 rows)
4. `wearable_test_predictions.csv` (3,000 rows)
5. `gut_val_predictions.csv` (3,000 rows)
6. `gut_test_predictions.csv` (3,000 rows)

### Combined Alignment Master Files
1. `fusion_val_master.csv` (3,000 rows, 21 columns)
2. `fusion_test_master.csv` (3,000 rows, 21 columns)

> **Gap Check**: `val_gaps = 0`, `test_gaps = 0`. No missing predictions or unaligned rows exist; therefore, `fusion_val_master_gaps.csv` and `fusion_test_master_gaps.csv` were not required.

---

## PART 4 — Recomputed Sanity-Check Metrics (Test Set)

Using the exported Test prediction files (`fusion_test_master.csv`), ROC-AUC, PR-AUC, and Brier scores were recomputed for each modality $\times$ disease combination and compared against the previously reported evaluation reports:

| Modality | Disease | Recomputed Test ROC-AUC | Previously Reported Test ROC-AUC | Match? | Recomputed PR-AUC | Recomputed Brier |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **Clinical** | Type2_Diabetes | 0.9997 | 0.9997 | **Y** | 0.9994 | 0.0083 |
| **Wearable** | Type2_Diabetes | 0.9915 | 0.9915 | **Y** | 0.9859 | 0.0385 |
| **Gut** | Type2_Diabetes | 0.8286 | 0.8286 | **Y** | 0.7214 | 0.1688 |
| **Clinical** | Prediabetes | 0.9992 | 0.9992 | **Y** | 0.9981 | 0.0079 |
| **Wearable** | Prediabetes | 0.9623 | 0.9623 | **Y** | 0.9229 | 0.0781 |
| **Gut** | Prediabetes | 0.6146 | 0.6146 | **Y** | 0.4058 | 0.2384 |
| **Clinical** | High_Adiposity_Risk | 0.9674 | 0.9674 | **Y** | 0.9340 | 0.0730 |
| **Wearable** | High_Adiposity_Risk | 0.8106 | 0.8106 | **Y** | 0.6432 | 0.1797 |
| **Gut** | High_Adiposity_Risk | 0.8049 | 0.8049 | **Y** | 0.6842 | 0.1747 |
| **Clinical** | Metabolic_Syndrome | 0.8873 | 0.8873 | **Y** | 0.4383 | 0.1295 |
| **Wearable** | Metabolic_Syndrome | 0.7274 | 0.7274 | **Y** | 0.1724 | 0.2275 |
| **Gut** | Metabolic_Syndrome | 0.8086 | 0.8086 | **Y** | 0.2908 | 0.1610 |
| **Clinical** | NAFLD | 0.9005 | 0.9005 | **Y** | 0.6129 | 0.1325 |
| **Wearable** | NAFLD | 0.6009 | 0.6009 | **Y** | 0.1796 | 0.2416 |
| **Gut** | NAFLD | 0.8089 | 0.8089 | **Y** | 0.4554 | 0.1720 |

> **Verdict**: 100% Match across all 15 models ($15 / 15$ **Y**). All exported probabilities match the exact frozen model evaluations.

---

## PART 5 — Train-Set Status Check

1. **Pre-existing Train Prediction Files**:
   - No saved Train-set prediction files currently exist in any modality directory.
2. **Artifact Completeness for OOF Regeneration**:
   - **Clinical**: 5 native XGBoost JSON models + metadata JSONs + exact hyperparameter configs + fixed random seed (`42`). Complete for exact OOF regeneration.
   - **Wearable**: 5 native XGBoost JSON models + metadata JSONs + exact hyperparameter configs + fixed random seed (`42`). Complete for exact OOF regeneration.
   - **Gut**: 5 native XGBoost JSON models + metadata JSONs + exact hyperparameter configs + stored `imputation_medians` + `clr_delta` ($1\text{e-}5$) + fixed random seed (`42`). Complete for exact OOF regeneration.

---

## PART 6 — Modality-Level Missingness Check

1. **Modality-Level Missingness**:
   - Every `Patient_ID` ($n=20,000$) has complete underlying feature datasets across all three modalities (Clinical features, Wearable standard + CGM features, Gut raw taxa).
   - **Statement**: **modality-level missingness is NOT represented in the current dataset.**
2. **Gut Feature-Level Missingness**:
   - 1,922 rows in `gut_v3.csv` contained all-NaN taxa values (MCAR).
   - These 1,922 rows were imputed during training using strictly Train-set column medians (stored in metadata as `imputation_medians`).

---

## Deliverables Verification Checklist

- [x] `artifact_inventory_report.md` (this report)
- [x] `clinical_val_predictions.csv` & `clinical_test_predictions.csv`
- [x] `wearable_val_predictions.csv` & `wearable_test_predictions.csv`
- [x] `gut_val_predictions.csv` & `gut_test_predictions.csv`
- [x] `fusion_val_master.csv` & `fusion_test_master.csv`
- [x] Part 4 Sanity Check Table (15/15 Match = Y)
