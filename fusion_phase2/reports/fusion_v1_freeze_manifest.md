# Fusion V1 Immutable Freeze Manifest

**Manifest Version**: 1.0.0
**Freeze Timestamp (UTC)**: 2026-08-09T06:39:43.914769+00:00
**Architecture Name**: Fusion V1 Frozen Architecture
**Status**: FROZEN_LOCKED
**Random Seed**: 42

---

## 1. Executive Summary & Verification Confirmation

Fusion V1 is officially **FROZEN AND LOCKED**. All 18 deployment-contract checks have passed. Test set data has **NOT** been loaded, evaluated, or accessed during this freeze operation.

## 2. Level-0 Modality Model Specifications

| Modality | Version | Feature Count | Preprocessing & CLR Rules | Level-1 Fusion Status |
|:---|:---:|:---:|:---|:---|
| **Clinical** | v4 | 18 | Numerical float scaling, zero missing values, `Patient_ID` excluded. | Primary signal for T2D, Prediabetes, High Adiposity, MetSyn, NAFLD. |
| **Wearable** | v3 | 15 | Numerical float scaling, `Patient_ID` excluded. | **Independent Level-0 Modality Only (Excluded from Level-1 Fusion)**. |
| **Gut** | v3 | 21 | Train-only median imputation, row-wise CLR ($\delta=1	ext{e-}5$), `Patient_ID` excluded. | Co-dominant signal for Metabolic Syndrome & NAFLD. |

## 3. Approved Fusion Architecture & Parameter Specifications

### Type2_Diabetes
- **Architecture**: Clinical Passthrough
- **Decision Threshold**: `0.50`
- **Suppression**: None

### Prediabetes
- **Architecture**: Clinical Passthrough
- **Decision Threshold**: `0.50`
- **Post-Decision Suppression**: `IF Pred_T2D == 1 THEN Pred_Prediabetes = 0` (Raw $P(	ext{Prediabetes})$ remains 100% un-mutated)

### High_Adiposity_Risk
- **Architecture**: Clinical Passthrough
- **Decision Threshold**: `0.50`
- **Suppression**: None

### Metabolic_Syndrome
- **Architecture**: Clinical + Gut L2 Logistic Regression Stacker
- **Exact Stacker Equation**: $\text{Logit}_{\text{raw}} = -4.3697 + 2.5799 \cdot P_{\text{Clinical}} + 1.9639 \cdot P_{\text{Gut}}$
- **Platt Recalibration Equation**: $\text{Logit}_{\text{Platt}} = +1.5006 + 1.8243 \cdot \text{Logit}_{\text{raw}}$
- **Calibrated Probability**: $P_{\text{calibrated}} = \text{sigmoid}(\text{Logit}_{\text{Platt}})$
- **Decision Threshold**: `0.20` (**Applies strictly to $P_{\text{calibrated}}$ post-Platt**)
- **Threshold Provenance**: Selected on OOF Train predictions only; evaluated on Validation without Test set tuning.

### NAFLD
- **Architecture**: Clinical + Gut L2 Logistic Regression Stacker
- **Exact Stacker Equation**: $\text{Logit} = -4.7674 + 3.7924 \cdot P_{\text{Clinical}} + 2.8340 \cdot P_{\text{Gut}}$
- **Fused Probability**: $P_{\text{Fused}} = \text{sigmoid}(\text{Logit})$
- **Decision Threshold**: `0.50`

---

## 4. Availability Fallback Policy (Cases 1-7)

| Availability Case | Available Modalities | Pipeline Fallback Behavior |
|:---:|:---|:---|
| **Case 1** | Clinical Only | Clinical Passthrough for all available heads. |
| **Case 2** | Gut Only | Gut Passthrough for available heads. |
| **Case 3** | Wearable Only | Wearable standalone Level-0 prediction emitted independently. |
| **Case 4** | Clinical + Gut | Clinical Passthrough for T2D/Pred/HAR; `Clinical + Gut` LR Stacker for MetSyn/NAFLD. |
| **Case 5** | Clinical + Wearable | Clinical Passthrough (Wearable excluded). |
| **Case 6** | Gut + Wearable | Gut Passthrough (Wearable excluded). |
| **Case 7** | All 3 Available | Clinical Passthrough for T2D/Pred/HAR; `Clinical + Gut` LR Stacker for MetSyn/NAFLD (Wearable excluded). |

---

## 5. Wearable Participation Policy

> *Under Fusion V1, Wearable is excluded from Level-1 disease probability fusion because no disease demonstrated robust positive incremental signal from Wearable beyond the selected Clinical / Clinical+Gut baseline. Wearable remains fully active as an independent Level-0 modality for continuous remote monitoring, CGMs, dashboards, clinician explanations, and future Fusion V2 research.*

---

## 6. Output Contract Schema

The final inference output dataframe strictly separates:

1. **Level-0 Raw Probabilities**: `P_Clinical_<Disease>`, `P_Gut_<Disease>`, `P_Wearable_<Disease>`

2. **Level-1 Fused Probability**: `P_Fused_<Disease>` (or `P_Calibrated_<Disease>` for MetSyn)

3. **Binary Decision Flag**: `Pred_<Disease>` ($0$ or $1$)

4. **Metadata Flags**: `Threshold_Used`, `Suppression_Applied` ($0$ or $1$)

---

## 7. Explainability & Synthetic Data Limitations

- **Logistic Regression Coefficients**: Stacker coefficients ($eta_C, eta_G$) describe model decision contribution, NOT biological causality.
- **Synthetic Benchmark Disclaimer**: All results were obtained on the current synthetic benchmark dataset and do not establish real-world clinical effectiveness. Real-world clinical trial validation is required.

---

## 8. Software Environment & Artifact Identifiers

### Software Environment:
- **python_version**: `3.13.5`
- **scikit_learn_version**: `1.8.0`
- **xgboost_version**: `3.3.0`
- **joblib_version**: `1.5.3`
- **pandas_version**: `3.0.0`
- **numpy_version**: `2.4.1`

### Artifact SHA-256 Hashes:
- **clinical_xgboost_Type2_Diabetes**: `9255a2892216582bab5be6d0735e68dda13d0812f1a79bb9a83d4d8a9189036d`
- **clinical_xgboost_Prediabetes**: `553f44af3c1c62a3a54d5412464c67b97c1af78980043255c8d9dcf6fbd57b2b`
- **clinical_xgboost_High_Adiposity_Risk**: `649331a7943fb8ab23ee90e527ad6b31de585134ee4d1e7157417f47f50b3a18`
- **clinical_xgboost_Metabolic_Syndrome**: `548fac4d3bf689dca8cd903a979491496db9b1107837b370f0473c9aa932e38d`
- **clinical_xgboost_NAFLD**: `97ea9a1ace420244c39026a1812835f47416640912026e3cabcf4f0024b5b56f`
- **wearable_xgboost_Type2_Diabetes**: `cd83c41b69231f5f58a4ba99218f9e4eb9fdabd12276e2ea13eba7eb61b1c4d2`
- **wearable_xgboost_Prediabetes**: `ece447786a4a469f0f43be73e42ac533025afd9b20f07c362cda0847fee2fb1a`
- **wearable_xgboost_High_Adiposity_Risk**: `be387424351c7c9ce8f60d5d5cbce175e8b86e5f1ca0ca7442b28568c4375607`
- **wearable_xgboost_Metabolic_Syndrome**: `eb1012933c6c1161db3700ca78cf7bc51b7a96959a780b05936c6a9bd6bd5030`
- **wearable_xgboost_NAFLD**: `552233be5b2bc4ea800c41e8fb9bf6f494720a33c81a5514a9f9eda06082fc54`
- **gut_xgboost_Type2_Diabetes**: `147e5e1ccbcdcecc6fef537302cb87f01433c690ba9c4ea19df293b7cb3edf8d`
- **gut_xgboost_Prediabetes**: `3a22f71bd4c1db7bf0a52430efd43c611dc9b489400d1ebed212e57c494d8464`
- **gut_xgboost_High_Adiposity_Risk**: `0f907ea4db581d0c6c68479253b99e1b198793167078f3050b18454f4b585d49`
- **gut_xgboost_Metabolic_Syndrome**: `6ac1a661b70a8c256939cc7a5e4ff7ef7a03a140aceb38896a23513f4e17089a`
- **gut_xgboost_NAFLD**: `840c0060e3c68510522d6e6a04e38aad6ae33bad18167109b6b4bd4949f5dda0`
- **metsyn_stacker_joblib**: `7467b27b54fb2fb8df20310e6700c393b2159386528daf4ce5acff34053635fb`
- **nafld_stacker_joblib**: `c11e0e9869125482175e3561df94d035a4bd5ea551c33f53b1736a2d9a93f303`

---

## 9. Test Isolation Statement

> **TEST HAS NOT YET BEEN USED FOR FINAL EVALUATION.**

The Test set (`fusion_test_master.csv`, $n=3,000$) has been strictly preserved untouched. Final evaluation will occur as a separate, decision-blind single-pass operation using `python run_fusion_test_evaluation.py` after human sign-off.
