# FUSION V1 — OUTPUT DEMONSTRATION REPORT

**Date**: 2026-08-09T07:34:23.586434+00:00
**Dataset Source**: Non-Test Validation Set (`fusion_val_master.csv`, $n=3,000$ patients)
> **Test Protection Notice**: *Held-out Test set (`fusion_test_master.csv`) was NOT loaded, accessed, or evaluated in this demonstration.*

---

## Compact 10-Patient Summary Table

| Patient ID | T2D | Prediabetes | HAR | MetSyn | NAFLD | # Positive | Prediabetes Suppressed |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `P14006` | **NEG** | **NEG** | **NEG** | **NEG** | **NEG** | **0** | NO |
| `P14001` | **POS** | **NEG** | **NEG** | **NEG** | **NEG** | **1** | NO |
| `P14010` | **NEG** | **POS** | **POS** | **NEG** | **NEG** | **2** | NO |
| `P14004` | **POS** | **NEG** | **POS** | **POS** | **NEG** | **3** | NO |
| `P14007` | **NEG** | **POS** | **POS** | **NEG** | **POS** | **3** | NO |
| `P14996` | **POS** | **NEG** | **NEG** | **NEG** | **NEG** | **1** | YES |
| `P14014` | **NEG** | **POS** | **POS** | **NEG** | **NEG** | **2** | NO |
| `P14021` | **POS** | **NEG** | **POS** | **POS** | **POS** | **4** | NO |
| `P14002` | **POS** | **NEG** | **NEG** | **NEG** | **NEG** | **1** | NO |
| `P14003` | **POS** | **NEG** | **NEG** | **NEG** | **NEG** | **1** | NO |

---

## Detailed 10-Patient Transformation Logs

### Patient 1: `P14006`

#### Step 1 — Level-0 Raw Inputs (3 Modalities × 5 Diseases = 15 Probabilities):
| Modality | Type2 Diabetes | Prediabetes | High Adiposity | Metabolic Syndrome | NAFLD |
|:---|---:|---:|---:|---:|---:|
| **Clinical** | 0.0660 | 0.0017 | 0.0264 | 0.2487 | 0.0237 |
| **Gut** | 0.2094 | 0.5399 | 0.2024 | 0.0610 | 0.1759 |
| **Wearable** | 0.0062 | 0.0122 | 0.1350 | 0.4196 | 0.3751 |

#### Step 2 — Level-1 Modality Routing & Calculation:
- **T2D**: Clinical Passthrough ($P_{\text{Fused}} = P_{\text{Clin}} = 0.0660$)
- **Prediabetes**: Clinical Passthrough ($P_{\text{Fused}} = P_{\text{Clin}} = 0.0017$)
- **High Adiposity Risk**: Clinical Passthrough ($P_{\text{Fused}} = P_{\text{Clin}} = 0.0264$)
- **Metabolic Syndrome**: Clinical (0.2487) + Gut (0.0610) $\rightarrow$ Raw LR (0.0264) $\rightarrow$ Platt Recalibrated (0.0062)
- **NAFLD**: Clinical (0.0237) + Gut (0.1759) $\rightarrow$ Fused LR (0.0151)
- **Wearable**: *100% Excluded from Level-1 Fusion equations (preserved for Level-0 monitoring only).*

#### Step 3 — Final Disease Output & Decisions:
| Disease | Fused Risk Score | Decision Threshold | Binary Decision |
|:---|---:|---:|:---:|
| **Type2 Diabetes** | 0.0660 | 0.50 | **NEGATIVE** |
| **Prediabetes** | 0.0017 | 0.50 | **NEGATIVE** |
| **High Adiposity Risk** | 0.0264 | 0.50 | **NEGATIVE** |
| **Metabolic Syndrome** | 0.0062 | **0.20 (Post-Platt)** | **NEGATIVE** |
| **NAFLD** | 0.0151 | 0.50 | **NEGATIVE** |

#### Step 4 — Prediabetes Post-Decision Suppression Audit:
- Raw Probability: `0.0017` (Un-mutated)
- Raw Binary Decision: `NEGATIVE`
- Final Binary Decision: `NEGATIVE`
- Suppressed Due to Active T2D (`Pred_T2D == 1`): **NO**

#### Step 5 — Risk Score Presentation Ranking (Presentation Only):
1. **Type2 Diabetes**: `0.0660` (Threshold: 0.50 $\rightarrow$ Decision: **NEGATIVE**)
2. **High Adiposity Risk**: `0.0264` (Threshold: 0.50 $\rightarrow$ Decision: **NEGATIVE**)
3. **NAFLD**: `0.0151` (Threshold: 0.50 $\rightarrow$ Decision: **NEGATIVE**)
4. **Metabolic Syndrome**: `0.0062` (Threshold: 0.20 (Post-Platt) $\rightarrow$ Decision: **NEGATIVE**)
5. **Prediabetes**: `0.0017` (Threshold: 0.50 $\rightarrow$ Decision: **NEGATIVE**)

---

### Patient 2: `P14001`

#### Step 1 — Level-0 Raw Inputs (3 Modalities × 5 Diseases = 15 Probabilities):
| Modality | Type2 Diabetes | Prediabetes | High Adiposity | Metabolic Syndrome | NAFLD |
|:---|---:|---:|---:|---:|---:|
| **Clinical** | 0.9343 | 0.0012 | 0.0504 | 0.1113 | 0.7654 |
| **Gut** | 0.3923 | 0.5383 | 0.3060 | 0.4006 | 0.3257 |
| **Wearable** | 0.9950 | 0.0114 | 0.7703 | 0.5415 | 0.5471 |

#### Step 2 — Level-1 Modality Routing & Calculation:
- **T2D**: Clinical Passthrough ($P_{\text{Fused}} = P_{\text{Clin}} = 0.9343$)
- **Prediabetes**: Clinical Passthrough ($P_{\text{Fused}} = P_{\text{Clin}} = 0.0012$)
- **High Adiposity Risk**: Clinical Passthrough ($P_{\text{Fused}} = P_{\text{Clin}} = 0.0504$)
- **Metabolic Syndrome**: Clinical (0.1113) + Gut (0.4006) $\rightarrow$ Raw LR (0.0357) $\rightarrow$ Platt Recalibrated (0.0109)
- **NAFLD**: Clinical (0.7654) + Gut (0.3257) $\rightarrow$ Fused LR (0.2807)
- **Wearable**: *100% Excluded from Level-1 Fusion equations (preserved for Level-0 monitoring only).*

#### Step 3 — Final Disease Output & Decisions:
| Disease | Fused Risk Score | Decision Threshold | Binary Decision |
|:---|---:|---:|:---:|
| **Type2 Diabetes** | 0.9343 | 0.50 | **POSITIVE** |
| **Prediabetes** | 0.0012 | 0.50 | **NEGATIVE** |
| **High Adiposity Risk** | 0.0504 | 0.50 | **NEGATIVE** |
| **Metabolic Syndrome** | 0.0109 | **0.20 (Post-Platt)** | **NEGATIVE** |
| **NAFLD** | 0.2807 | 0.50 | **NEGATIVE** |

#### Step 4 — Prediabetes Post-Decision Suppression Audit:
- Raw Probability: `0.0012` (Un-mutated)
- Raw Binary Decision: `NEGATIVE`
- Final Binary Decision: `NEGATIVE`
- Suppressed Due to Active T2D (`Pred_T2D == 1`): **NO**

#### Step 5 — Risk Score Presentation Ranking (Presentation Only):
1. **Type2 Diabetes**: `0.9343` (Threshold: 0.50 $\rightarrow$ Decision: **POSITIVE**)
2. **NAFLD**: `0.2807` (Threshold: 0.50 $\rightarrow$ Decision: **NEGATIVE**)
3. **High Adiposity Risk**: `0.0504` (Threshold: 0.50 $\rightarrow$ Decision: **NEGATIVE**)
4. **Metabolic Syndrome**: `0.0109` (Threshold: 0.20 (Post-Platt) $\rightarrow$ Decision: **NEGATIVE**)
5. **Prediabetes**: `0.0012` (Threshold: 0.50 $\rightarrow$ Decision: **NEGATIVE**)

---

### Patient 3: `P14010`

#### Step 1 — Level-0 Raw Inputs (3 Modalities × 5 Diseases = 15 Probabilities):
| Modality | Type2 Diabetes | Prediabetes | High Adiposity | Metabolic Syndrome | NAFLD |
|:---|---:|---:|---:|---:|---:|
| **Clinical** | 0.0660 | 0.9980 | 0.8501 | 0.3632 | 0.2177 |
| **Gut** | 0.0515 | 0.5343 | 0.0565 | 0.0445 | 0.0711 |
| **Wearable** | 0.0089 | 0.9800 | 0.7143 | 0.4293 | 0.5452 |

#### Step 2 — Level-1 Modality Routing & Calculation:
- **T2D**: Clinical Passthrough ($P_{\text{Fused}} = P_{\text{Clin}} = 0.0660$)
- **Prediabetes**: Clinical Passthrough ($P_{\text{Fused}} = P_{\text{Clin}} = 0.9980$)
- **High Adiposity Risk**: Clinical Passthrough ($P_{\text{Fused}} = P_{\text{Clin}} = 0.8501$)
- **Metabolic Syndrome**: Clinical (0.3632) + Gut (0.0445) $\rightarrow$ Raw LR (0.0340) $\rightarrow$ Platt Recalibrated (0.0099)
- **NAFLD**: Clinical (0.2177) + Gut (0.0711) $\rightarrow$ Fused LR (0.0232)
- **Wearable**: *100% Excluded from Level-1 Fusion equations (preserved for Level-0 monitoring only).*

#### Step 3 — Final Disease Output & Decisions:
| Disease | Fused Risk Score | Decision Threshold | Binary Decision |
|:---|---:|---:|:---:|
| **Type2 Diabetes** | 0.0660 | 0.50 | **NEGATIVE** |
| **Prediabetes** | 0.9980 | 0.50 | **POSITIVE** |
| **High Adiposity Risk** | 0.8501 | 0.50 | **POSITIVE** |
| **Metabolic Syndrome** | 0.0099 | **0.20 (Post-Platt)** | **NEGATIVE** |
| **NAFLD** | 0.0232 | 0.50 | **NEGATIVE** |

#### Step 4 — Prediabetes Post-Decision Suppression Audit:
- Raw Probability: `0.9980` (Un-mutated)
- Raw Binary Decision: `POSITIVE`
- Final Binary Decision: `POSITIVE`
- Suppressed Due to Active T2D (`Pred_T2D == 1`): **NO**

#### Step 5 — Risk Score Presentation Ranking (Presentation Only):
1. **Prediabetes**: `0.9980` (Threshold: 0.50 $\rightarrow$ Decision: **POSITIVE**)
2. **High Adiposity Risk**: `0.8501` (Threshold: 0.50 $\rightarrow$ Decision: **POSITIVE**)
3. **Type2 Diabetes**: `0.0660` (Threshold: 0.50 $\rightarrow$ Decision: **NEGATIVE**)
4. **NAFLD**: `0.0232` (Threshold: 0.50 $\rightarrow$ Decision: **NEGATIVE**)
5. **Metabolic Syndrome**: `0.0099` (Threshold: 0.20 (Post-Platt) $\rightarrow$ Decision: **NEGATIVE**)

---

### Patient 4: `P14004`

#### Step 1 — Level-0 Raw Inputs (3 Modalities × 5 Diseases = 15 Probabilities):
| Modality | Type2 Diabetes | Prediabetes | High Adiposity | Metabolic Syndrome | NAFLD |
|:---|---:|---:|---:|---:|---:|
| **Clinical** | 0.9343 | 0.0012 | 0.9966 | 0.7423 | 0.2208 |
| **Gut** | 0.9028 | 0.1803 | 0.9364 | 0.7897 | 0.8876 |
| **Wearable** | 0.9950 | 0.0114 | 0.7703 | 0.5327 | 0.5659 |

#### Step 2 — Level-1 Modality Routing & Calculation:
- **T2D**: Clinical Passthrough ($P_{\text{Fused}} = P_{\text{Clin}} = 0.9343$)
- **Prediabetes**: Clinical Passthrough ($P_{\text{Fused}} = P_{\text{Clin}} = 0.0012$)
- **High Adiposity Risk**: Clinical Passthrough ($P_{\text{Fused}} = P_{\text{Clin}} = 0.9966$)
- **Metabolic Syndrome**: Clinical (0.7423) + Gut (0.7897) $\rightarrow$ Raw LR (0.2882) $\rightarrow$ Platt Recalibrated (0.4629)
- **NAFLD**: Clinical (0.2208) + Gut (0.8876) $\rightarrow$ Fused LR (0.1956)
- **Wearable**: *100% Excluded from Level-1 Fusion equations (preserved for Level-0 monitoring only).*

#### Step 3 — Final Disease Output & Decisions:
| Disease | Fused Risk Score | Decision Threshold | Binary Decision |
|:---|---:|---:|:---:|
| **Type2 Diabetes** | 0.9343 | 0.50 | **POSITIVE** |
| **Prediabetes** | 0.0012 | 0.50 | **NEGATIVE** |
| **High Adiposity Risk** | 0.9966 | 0.50 | **POSITIVE** |
| **Metabolic Syndrome** | 0.4629 | **0.20 (Post-Platt)** | **POSITIVE** |
| **NAFLD** | 0.1956 | 0.50 | **NEGATIVE** |

#### Step 4 — Prediabetes Post-Decision Suppression Audit:
- Raw Probability: `0.0012` (Un-mutated)
- Raw Binary Decision: `NEGATIVE`
- Final Binary Decision: `NEGATIVE`
- Suppressed Due to Active T2D (`Pred_T2D == 1`): **NO**

#### Step 5 — Risk Score Presentation Ranking (Presentation Only):
1. **High Adiposity Risk**: `0.9966` (Threshold: 0.50 $\rightarrow$ Decision: **POSITIVE**)
2. **Type2 Diabetes**: `0.9343` (Threshold: 0.50 $\rightarrow$ Decision: **POSITIVE**)
3. **Metabolic Syndrome**: `0.4629` (Threshold: 0.20 (Post-Platt) $\rightarrow$ Decision: **POSITIVE**)
4. **NAFLD**: `0.1956` (Threshold: 0.50 $\rightarrow$ Decision: **NEGATIVE**)
5. **Prediabetes**: `0.0012` (Threshold: 0.50 $\rightarrow$ Decision: **NEGATIVE**)

---

### Patient 5: `P14007`

#### Step 1 — Level-0 Raw Inputs (3 Modalities × 5 Diseases = 15 Probabilities):
| Modality | Type2 Diabetes | Prediabetes | High Adiposity | Metabolic Syndrome | NAFLD |
|:---|---:|---:|---:|---:|---:|
| **Clinical** | 0.0660 | 0.9976 | 0.7830 | 0.7078 | 0.8711 |
| **Gut** | 0.7113 | 0.4905 | 0.6599 | 0.4791 | 0.5336 |
| **Wearable** | 0.0057 | 0.9656 | 0.2855 | 0.4626 | 0.4543 |

#### Step 2 — Level-1 Modality Routing & Calculation:
- **T2D**: Clinical Passthrough ($P_{\text{Fused}} = P_{\text{Clin}} = 0.0660$)
- **Prediabetes**: Clinical Passthrough ($P_{\text{Fused}} = P_{\text{Clin}} = 0.9976$)
- **High Adiposity Risk**: Clinical Passthrough ($P_{\text{Fused}} = P_{\text{Clin}} = 0.7830$)
- **Metabolic Syndrome**: Clinical (0.7078) + Gut (0.4791) $\rightarrow$ Raw LR (0.1676) $\rightarrow$ Platt Recalibrated (0.1941)
- **NAFLD**: Clinical (0.8711) + Gut (0.5336) $\rightarrow$ Fused LR (0.5121)
- **Wearable**: *100% Excluded from Level-1 Fusion equations (preserved for Level-0 monitoring only).*

#### Step 3 — Final Disease Output & Decisions:
| Disease | Fused Risk Score | Decision Threshold | Binary Decision |
|:---|---:|---:|:---:|
| **Type2 Diabetes** | 0.0660 | 0.50 | **NEGATIVE** |
| **Prediabetes** | 0.9976 | 0.50 | **POSITIVE** |
| **High Adiposity Risk** | 0.7830 | 0.50 | **POSITIVE** |
| **Metabolic Syndrome** | 0.1941 | **0.20 (Post-Platt)** | **NEGATIVE** |
| **NAFLD** | 0.5121 | 0.50 | **POSITIVE** |

#### Step 4 — Prediabetes Post-Decision Suppression Audit:
- Raw Probability: `0.9976` (Un-mutated)
- Raw Binary Decision: `POSITIVE`
- Final Binary Decision: `POSITIVE`
- Suppressed Due to Active T2D (`Pred_T2D == 1`): **NO**

#### Step 5 — Risk Score Presentation Ranking (Presentation Only):
1. **Prediabetes**: `0.9976` (Threshold: 0.50 $\rightarrow$ Decision: **POSITIVE**)
2. **High Adiposity Risk**: `0.7830` (Threshold: 0.50 $\rightarrow$ Decision: **POSITIVE**)
3. **NAFLD**: `0.5121` (Threshold: 0.50 $\rightarrow$ Decision: **POSITIVE**)
4. **Metabolic Syndrome**: `0.1941` (Threshold: 0.20 (Post-Platt) $\rightarrow$ Decision: **NEGATIVE**)
5. **Type2 Diabetes**: `0.0660` (Threshold: 0.50 $\rightarrow$ Decision: **NEGATIVE**)

---

### Patient 6: `P14996`

#### Step 1 — Level-0 Raw Inputs (3 Modalities × 5 Diseases = 15 Probabilities):
| Modality | Type2 Diabetes | Prediabetes | High Adiposity | Metabolic Syndrome | NAFLD |
|:---|---:|---:|---:|---:|---:|
| **Clinical** | 0.7532 | 0.7728 | 0.0363 | 0.1352 | 0.0759 |
| **Gut** | 0.4106 | 0.5259 | 0.6436 | 0.2995 | 0.3018 |
| **Wearable** | 0.0331 | 0.9790 | 0.4533 | 0.4626 | 0.5011 |

#### Step 2 — Level-1 Modality Routing & Calculation:
- **T2D**: Clinical Passthrough ($P_{\text{Fused}} = P_{\text{Clin}} = 0.7532$)
- **Prediabetes**: Clinical Passthrough ($P_{\text{Fused}} = P_{\text{Clin}} = 0.7728$)
- **High Adiposity Risk**: Clinical Passthrough ($P_{\text{Fused}} = P_{\text{Clin}} = 0.0363$)
- **Metabolic Syndrome**: Clinical (0.1352) + Gut (0.2995) $\rightarrow$ Raw LR (0.0313) $\rightarrow$ Platt Recalibrated (0.0085)
- **NAFLD**: Clinical (0.0759) + Gut (0.3018) $\rightarrow$ Fused LR (0.0260)
- **Wearable**: *100% Excluded from Level-1 Fusion equations (preserved for Level-0 monitoring only).*

#### Step 3 — Final Disease Output & Decisions:
| Disease | Fused Risk Score | Decision Threshold | Binary Decision |
|:---|---:|---:|:---:|
| **Type2 Diabetes** | 0.7532 | 0.50 | **POSITIVE** |
| **Prediabetes** | 0.7728 | 0.50 | **NEGATIVE** |
| **High Adiposity Risk** | 0.0363 | 0.50 | **NEGATIVE** |
| **Metabolic Syndrome** | 0.0085 | **0.20 (Post-Platt)** | **NEGATIVE** |
| **NAFLD** | 0.0260 | 0.50 | **NEGATIVE** |

#### Step 4 — Prediabetes Post-Decision Suppression Audit:
- Raw Probability: `0.7728` (Un-mutated)
- Raw Binary Decision: `POSITIVE`
- Final Binary Decision: `NEGATIVE`
- Suppressed Due to Active T2D (`Pred_T2D == 1`): **YES**

#### Step 5 — Risk Score Presentation Ranking (Presentation Only):
1. **Prediabetes**: `0.7728` (Threshold: 0.50 $\rightarrow$ Decision: **NEGATIVE**)
2. **Type2 Diabetes**: `0.7532` (Threshold: 0.50 $\rightarrow$ Decision: **POSITIVE**)
3. **High Adiposity Risk**: `0.0363` (Threshold: 0.50 $\rightarrow$ Decision: **NEGATIVE**)
4. **NAFLD**: `0.0260` (Threshold: 0.50 $\rightarrow$ Decision: **NEGATIVE**)
5. **Metabolic Syndrome**: `0.0085` (Threshold: 0.20 (Post-Platt) $\rightarrow$ Decision: **NEGATIVE**)

---

### Patient 7: `P14014`

#### Step 1 — Level-0 Raw Inputs (3 Modalities × 5 Diseases = 15 Probabilities):
| Modality | Type2 Diabetes | Prediabetes | High Adiposity | Metabolic Syndrome | NAFLD |
|:---|---:|---:|---:|---:|---:|
| **Clinical** | 0.1825 | 0.9536 | 0.8298 | 0.5732 | 0.9392 |
| **Gut** | 0.4549 | 0.4773 | 0.4922 | 0.5724 | 0.3243 |
| **Wearable** | 0.4283 | 0.8029 | 0.4000 | 0.5182 | 0.5043 |

#### Step 2 — Level-1 Modality Routing & Calculation:
- **T2D**: Clinical Passthrough ($P_{\text{Fused}} = P_{\text{Clin}} = 0.1825$)
- **Prediabetes**: Clinical Passthrough ($P_{\text{Fused}} = P_{\text{Clin}} = 0.9536$)
- **High Adiposity Risk**: Clinical Passthrough ($P_{\text{Fused}} = P_{\text{Clin}} = 0.8298$)
- **Metabolic Syndrome**: Clinical (0.5732) + Gut (0.5724) $\rightarrow$ Raw LR (0.1459) $\rightarrow$ Platt Recalibrated (0.1515)
- **NAFLD**: Clinical (0.9392) + Gut (0.3243) $\rightarrow$ Fused LR (0.4290)
- **Wearable**: *100% Excluded from Level-1 Fusion equations (preserved for Level-0 monitoring only).*

#### Step 3 — Final Disease Output & Decisions:
| Disease | Fused Risk Score | Decision Threshold | Binary Decision |
|:---|---:|---:|:---:|
| **Type2 Diabetes** | 0.1825 | 0.50 | **NEGATIVE** |
| **Prediabetes** | 0.9536 | 0.50 | **POSITIVE** |
| **High Adiposity Risk** | 0.8298 | 0.50 | **POSITIVE** |
| **Metabolic Syndrome** | 0.1515 | **0.20 (Post-Platt)** | **NEGATIVE** |
| **NAFLD** | 0.4290 | 0.50 | **NEGATIVE** |

#### Step 4 — Prediabetes Post-Decision Suppression Audit:
- Raw Probability: `0.9536` (Un-mutated)
- Raw Binary Decision: `POSITIVE`
- Final Binary Decision: `POSITIVE`
- Suppressed Due to Active T2D (`Pred_T2D == 1`): **NO**

#### Step 5 — Risk Score Presentation Ranking (Presentation Only):
1. **Prediabetes**: `0.9536` (Threshold: 0.50 $\rightarrow$ Decision: **POSITIVE**)
2. **High Adiposity Risk**: `0.8298` (Threshold: 0.50 $\rightarrow$ Decision: **POSITIVE**)
3. **NAFLD**: `0.4290` (Threshold: 0.50 $\rightarrow$ Decision: **NEGATIVE**)
4. **Type2 Diabetes**: `0.1825` (Threshold: 0.50 $\rightarrow$ Decision: **NEGATIVE**)
5. **Metabolic Syndrome**: `0.1515` (Threshold: 0.20 (Post-Platt) $\rightarrow$ Decision: **NEGATIVE**)

---

### Patient 8: `P14021`

#### Step 1 — Level-0 Raw Inputs (3 Modalities × 5 Diseases = 15 Probabilities):
| Modality | Type2 Diabetes | Prediabetes | High Adiposity | Metabolic Syndrome | NAFLD |
|:---|---:|---:|---:|---:|---:|
| **Clinical** | 0.9343 | 0.0022 | 0.9861 | 0.7968 | 0.9053 |
| **Gut** | 0.8922 | 0.2933 | 0.8826 | 0.6939 | 0.7464 |
| **Wearable** | 0.9938 | 0.0114 | 0.6540 | 0.5313 | 0.5478 |

#### Step 2 — Level-1 Modality Routing & Calculation:
- **T2D**: Clinical Passthrough ($P_{\text{Fused}} = P_{\text{Clin}} = 0.9343$)
- **Prediabetes**: Clinical Passthrough ($P_{\text{Fused}} = P_{\text{Clin}} = 0.0022$)
- **High Adiposity Risk**: Clinical Passthrough ($P_{\text{Fused}} = P_{\text{Clin}} = 0.9861$)
- **Metabolic Syndrome**: Clinical (0.7968) + Gut (0.6939) $\rightarrow$ Raw LR (0.2786) $\rightarrow$ Platt Recalibrated (0.4415)
- **NAFLD**: Clinical (0.9053) + Gut (0.7464) $\rightarrow$ Fused LR (0.6860)
- **Wearable**: *100% Excluded from Level-1 Fusion equations (preserved for Level-0 monitoring only).*

#### Step 3 — Final Disease Output & Decisions:
| Disease | Fused Risk Score | Decision Threshold | Binary Decision |
|:---|---:|---:|:---:|
| **Type2 Diabetes** | 0.9343 | 0.50 | **POSITIVE** |
| **Prediabetes** | 0.0022 | 0.50 | **NEGATIVE** |
| **High Adiposity Risk** | 0.9861 | 0.50 | **POSITIVE** |
| **Metabolic Syndrome** | 0.4415 | **0.20 (Post-Platt)** | **POSITIVE** |
| **NAFLD** | 0.6860 | 0.50 | **POSITIVE** |

#### Step 4 — Prediabetes Post-Decision Suppression Audit:
- Raw Probability: `0.0022` (Un-mutated)
- Raw Binary Decision: `NEGATIVE`
- Final Binary Decision: `NEGATIVE`
- Suppressed Due to Active T2D (`Pred_T2D == 1`): **NO**

#### Step 5 — Risk Score Presentation Ranking (Presentation Only):
1. **High Adiposity Risk**: `0.9861` (Threshold: 0.50 $\rightarrow$ Decision: **POSITIVE**)
2. **Type2 Diabetes**: `0.9343` (Threshold: 0.50 $\rightarrow$ Decision: **POSITIVE**)
3. **NAFLD**: `0.6860` (Threshold: 0.50 $\rightarrow$ Decision: **POSITIVE**)
4. **Metabolic Syndrome**: `0.4415` (Threshold: 0.20 (Post-Platt) $\rightarrow$ Decision: **POSITIVE**)
5. **Prediabetes**: `0.0022` (Threshold: 0.50 $\rightarrow$ Decision: **NEGATIVE**)

---

### Patient 9: `P14002`

#### Step 1 — Level-0 Raw Inputs (3 Modalities × 5 Diseases = 15 Probabilities):
| Modality | Type2 Diabetes | Prediabetes | High Adiposity | Metabolic Syndrome | NAFLD |
|:---|---:|---:|---:|---:|---:|
| **Clinical** | 0.9343 | 0.0012 | 0.0028 | 0.0751 | 0.0036 |
| **Gut** | 0.3558 | 0.5428 | 0.4028 | 0.1915 | 0.4119 |
| **Wearable** | 0.9737 | 0.0614 | 0.4555 | 0.5249 | 0.5262 |

#### Step 2 — Level-1 Modality Routing & Calculation:
- **T2D**: Clinical Passthrough ($P_{\text{Fused}} = P_{\text{Clin}} = 0.9343$)
- **Prediabetes**: Clinical Passthrough ($P_{\text{Fused}} = P_{\text{Clin}} = 0.0012$)
- **High Adiposity Risk**: Clinical Passthrough ($P_{\text{Fused}} = P_{\text{Clin}} = 0.0028$)
- **Metabolic Syndrome**: Clinical (0.0751) + Gut (0.1915) $\rightarrow$ Raw LR (0.0219) $\rightarrow$ Platt Recalibrated (0.0044)
- **NAFLD**: Clinical (0.0036) + Gut (0.4119) $\rightarrow$ Fused LR (0.0270)
- **Wearable**: *100% Excluded from Level-1 Fusion equations (preserved for Level-0 monitoring only).*

#### Step 3 — Final Disease Output & Decisions:
| Disease | Fused Risk Score | Decision Threshold | Binary Decision |
|:---|---:|---:|:---:|
| **Type2 Diabetes** | 0.9343 | 0.50 | **POSITIVE** |
| **Prediabetes** | 0.0012 | 0.50 | **NEGATIVE** |
| **High Adiposity Risk** | 0.0028 | 0.50 | **NEGATIVE** |
| **Metabolic Syndrome** | 0.0044 | **0.20 (Post-Platt)** | **NEGATIVE** |
| **NAFLD** | 0.0270 | 0.50 | **NEGATIVE** |

#### Step 4 — Prediabetes Post-Decision Suppression Audit:
- Raw Probability: `0.0012` (Un-mutated)
- Raw Binary Decision: `NEGATIVE`
- Final Binary Decision: `NEGATIVE`
- Suppressed Due to Active T2D (`Pred_T2D == 1`): **NO**

#### Step 5 — Risk Score Presentation Ranking (Presentation Only):
1. **Type2 Diabetes**: `0.9343` (Threshold: 0.50 $\rightarrow$ Decision: **POSITIVE**)
2. **NAFLD**: `0.0270` (Threshold: 0.50 $\rightarrow$ Decision: **NEGATIVE**)
3. **Metabolic Syndrome**: `0.0044` (Threshold: 0.20 (Post-Platt) $\rightarrow$ Decision: **NEGATIVE**)
4. **High Adiposity Risk**: `0.0028` (Threshold: 0.50 $\rightarrow$ Decision: **NEGATIVE**)
5. **Prediabetes**: `0.0012` (Threshold: 0.50 $\rightarrow$ Decision: **NEGATIVE**)

---

### Patient 10: `P14003`

#### Step 1 — Level-0 Raw Inputs (3 Modalities × 5 Diseases = 15 Probabilities):
| Modality | Type2 Diabetes | Prediabetes | High Adiposity | Metabolic Syndrome | NAFLD |
|:---|---:|---:|---:|---:|---:|
| **Clinical** | 0.9343 | 0.0011 | 0.0023 | 0.0816 | 0.3016 |
| **Gut** | 0.6555 | 0.5321 | 0.6163 | 0.6195 | 0.6053 |
| **Wearable** | 0.9554 | 0.0721 | 0.1284 | 0.5025 | 0.5461 |

#### Step 2 — Level-1 Modality Routing & Calculation:
- **T2D**: Clinical Passthrough ($P_{\text{Fused}} = P_{\text{Clin}} = 0.9343$)
- **Prediabetes**: Clinical Passthrough ($P_{\text{Fused}} = P_{\text{Clin}} = 0.0011$)
- **High Adiposity Risk**: Clinical Passthrough ($P_{\text{Fused}} = P_{\text{Clin}} = 0.0023$)
- **Metabolic Syndrome**: Clinical (0.0816) + Gut (0.6195) $\rightarrow$ Raw LR (0.0501) $\rightarrow$ Platt Recalibrated (0.0205)
- **NAFLD**: Clinical (0.3016) + Gut (0.6053) $\rightarrow$ Fused LR (0.1292)
- **Wearable**: *100% Excluded from Level-1 Fusion equations (preserved for Level-0 monitoring only).*

#### Step 3 — Final Disease Output & Decisions:
| Disease | Fused Risk Score | Decision Threshold | Binary Decision |
|:---|---:|---:|:---:|
| **Type2 Diabetes** | 0.9343 | 0.50 | **POSITIVE** |
| **Prediabetes** | 0.0011 | 0.50 | **NEGATIVE** |
| **High Adiposity Risk** | 0.0023 | 0.50 | **NEGATIVE** |
| **Metabolic Syndrome** | 0.0205 | **0.20 (Post-Platt)** | **NEGATIVE** |
| **NAFLD** | 0.1292 | 0.50 | **NEGATIVE** |

#### Step 4 — Prediabetes Post-Decision Suppression Audit:
- Raw Probability: `0.0011` (Un-mutated)
- Raw Binary Decision: `NEGATIVE`
- Final Binary Decision: `NEGATIVE`
- Suppressed Due to Active T2D (`Pred_T2D == 1`): **NO**

#### Step 5 — Risk Score Presentation Ranking (Presentation Only):
1. **Type2 Diabetes**: `0.9343` (Threshold: 0.50 $\rightarrow$ Decision: **POSITIVE**)
2. **NAFLD**: `0.1292` (Threshold: 0.50 $\rightarrow$ Decision: **NEGATIVE**)
3. **Metabolic Syndrome**: `0.0205` (Threshold: 0.20 (Post-Platt) $\rightarrow$ Decision: **NEGATIVE**)
4. **High Adiposity Risk**: `0.0023` (Threshold: 0.50 $\rightarrow$ Decision: **NEGATIVE**)
5. **Prediabetes**: `0.0011` (Threshold: 0.50 $\rightarrow$ Decision: **NEGATIVE**)

---

## Step 8 — Output Contract Verification

Verified that the final output schema contains all required elements:

- `Patient_ID` (Key)
- All 15 Level-0 raw probabilities (`P_Clinical_*`, `P_Gut_*`, `P_Wearable_*`)
- All 5 Level-1 fused probabilities (`P_Fused_*`)
- Metabolic Syndrome raw LR probability (`P_Raw_LR_Metabolic_Syndrome`)
- Metabolic Syndrome Platt calibrated probability (`P_Fused_Metabolic_Syndrome`)
- All 5 independent binary predictions (`Pred_*`)
- Prediabetes raw decision (`Pred_Prediabetes_Raw`) and suppression flag (`Prediabetes_Suppressed`)
- Disease-specific decision thresholds (`Threshold_*`)
