# Fusion V1 — Decision-Blind Final Test Evaluation Report

**Date**: 2026-08-09T06:45:03.539984+00:00
**Evaluation Status**: Decision-Blind Final Pass on Untouched Test Set ($n=3,000$)

> **Mandatory Mandatory Isolation Statement**:

> *"Fusion V1 architecture was frozen before Test evaluation. Test data were not used for architecture selection, tuning, calibration, threshold selection, or model fitting. This is the decision-blind final Test evaluation."*

---

## 1. Executive Summary & Verification Log

- **Processed Patients**: Exactly 3,000 unique `Patient_ID` rows.
- **Patient ID Alignment**: 100% verified using explicit key join `on='Patient_ID'`.
- **Probability Integrity**: 0 NaNs, 0 Infs; all continuous probabilities bounded in $[0, 1]$.
- **Artifact Hashes Verified**:
  - `metsyn_stacker_joblib`: `7467b27b54fb2fb8df20310e6700c393b2159386528daf4ce5acff34053635fb`
  - `nafld_stacker_joblib`: `c11e0e9869125482175e3561df94d035a4bd5ea551c33f53b1736a2d9a93f303`

---

## 2. Validation (Selection Evidence) vs. Test (Final Evaluation) Metrics

| Disease | Architecture | Threshold | Val ROC | Test ROC | Val PR | Test PR | Val Brier | Test Brier | Val F1 | Test F1 | Test Prec | Test Rec | Test Pos Pred | Test Pos Act |
|:---|:---|:---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Type2_Diabetes | Clinical Passthrough | 0.50 | 0.9996 | 0.9997 | 0.9994 | 0.9994 | 0.0075 | 0.0083 | 0.9963 | 0.9941 | 0.9955 | 0.9927 | 1099 | 1102 |
| Prediabetes (Suppressed) | Clinical Passthrough + Masking | 0.50 | 0.9993 | 0.9992 | 0.9985 | 0.9981 | 0.0057 | 0.0079 | 0.9913 | 0.9861 | 0.9893 | 0.9830 | 934 | 940 |
| High_Adiposity_Risk | Clinical Passthrough | 0.50 | 0.9665 | 0.9674 | 0.9327 | 0.9340 | 0.0749 | 0.0730 | 0.8424 | 0.8489 | 0.7932 | 0.9130 | 1112 | 966 |
| Metabolic_Syndrome | Clinical+Gut LR + Platt | 0.20 | 0.9196 | 0.8969 | 0.5504 | 0.4557 | 0.0483 | 0.0530 | 0.5213 | 0.4976 | 0.3964 | 0.6681 | 391 | 232 |
| NAFLD | Clinical+Gut LR | 0.50 | 0.9277 | 0.9247 | 0.7118 | 0.7001 | 0.0691 | 0.0696 | 0.6042 | 0.6156 | 0.7509 | 0.5216 | 289 | 416 |

---

## 3. Prediabetes Post-Decision Suppression Audit

- **Raw P(Prediabetes)**: Preserved 100% un-mutated in output schema (`P_Clinical_Prediabetes`).
- **Raw Prediabetes Positives (t=0.50)**: 935 positive predictions.
- **Suppression Rule Applied**: `IF Pred_T2D == 1 THEN Pred_Prediabetes = 0`.
- **Cases Suppressed**: **1** patient predictions masked from positive to negative due to active T2D diagnosis.
- **Final Suppressed Prediabetes Positives**: 934 positive predictions.

---

## 4. Metabolic Syndrome Calibration & Threshold Audit

- **Raw Stacker Logit**: Logit_raw = -4.3697124012 + 2.5798532189 * P_Clin + 1.9638807682 * P_Gut
- **Platt Recalibration**: Logit_Platt = 1.5006 + 1.8243 * Logit_raw
- **Calibrated Probabilities**: Range $[0.0153, 0.4184]$ across Validation; Range $[0.0142, 0.4170]$ across Test.
- **Decision Threshold (t = 0.20)**: Evaluated strictly post-Platt (P_calibrated >= 0.20).
- **Test Positives Crossing Threshold (t=0.20)**: **391** patients predicted positive (Actual positive cases: **232**).
- **Test Metrics**: ROC-AUC = **0.8969**, PR-AUC = **0.4557**, Brier = **0.0530**, F1 = **0.4976** (Precision = **0.3964**, Recall = **0.6681**).

---

## 5. Wearable Participation Verification

- **Level-0 Preservation**: Wearable v3 raw probabilities (`P_Wearable_<Disease>`) generated and saved for all 3,000 Test patients.
- **Level-1 Exclusion**: Verified 100% that Wearable probabilities did **NOT** participate in any Level-1 disease probability equation for Fusion V1.

---

## 6. Confusion Matrices (Test Set, $n=3,000$)

### Type2_Diabetes:
- **True Negatives (TN)**: 0 | **False Positives (FP)**: 107.19999999999993
- **TN**: 1893 | **FP**: 5 | **FN**: 8 | **TP**: 1094

### Prediabetes (Suppressed):
- **True Negatives (TN)**: 0 | **False Positives (FP)**: 88.0
- **TN**: 2050 | **FP**: 10 | **FN**: 16 | **TP**: 924

### High_Adiposity_Risk:
- **True Negatives (TN)**: 0 | **False Positives (FP)**: 242.60000000000002
- **TN**: 1804 | **FP**: 230 | **FN**: 84 | **TP**: 882

### Metabolic_Syndrome:
- **True Negatives (TN)**: 0 | **False Positives (FP)**: 182.2
- **TN**: 2532 | **FP**: 236 | **FN**: 77 | **TP**: 155

### NAFLD:
- **True Negatives (TN)**: 0 | **False Positives (FP)**: -85.40000000000003
- **TN**: 2512 | **FP**: 72 | **FN**: 199 | **TP**: 217

---

## 7. Fusion V1 Final Status

Fusion V1 decision-blind Test evaluation is **COMPLETE**.
No further model adjustments, threshold tuning, or architecture changes will be made for V1.