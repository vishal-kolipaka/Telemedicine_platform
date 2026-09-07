# FUSION V1 — REAL OUTPUT DEMONSTRATION REPORT

**Date**: 2026-08-09T07:47:54.156784+00:00
**Data Source**: Actual Non-Test Level-0 Predictions (`fusion_val_master.csv`, $n=3,000$ patients)
> **Test Protection & Integrity Statement**:

> *"Use ONLY existing, properly aligned NON-TEST Level-0 prediction outputs. Zero synthetic probabilities created. Held-out Test set (`fusion_test_master.csv`) was NOT loaded, evaluated, or accessed."*

---

## 1. Selected Non-Test Patient Cases

| Patient ID | Selected Case Category | Raw T2D | Raw Pred | Raw HAR | Raw MetSyn | Raw NAFLD | # Pos | Suppressed |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `P14006` | **0 Positive Diseases** | NEG | NEG | NEG | NEG | NEG | **0** | NO |
| `P14001` | **1 Positive Disease** | POS | NEG | NEG | NEG | NEG | **1** | NO |
| `P14010` | **2 Positive Diseases** | NEG | POS | POS | NEG | NEG | **2** | NO |
| `P14004` | **3+ Positive Diseases** | POS | NEG | POS | POS | NEG | **3** | NO |
| `P14996` | **T2D Positive + Multiple** | POS | NEG | NEG | NEG | NEG | **1** | YES |
| `P14007` | **Prediabetes Suppressed** | NEG | POS | POS | NEG | POS | **3** | NO |
| `P14014` | **Metabolic Syndrome Positive** | NEG | POS | POS | NEG | NEG | **2** | NO |
| `P14021` | **NAFLD Positive** | POS | NEG | POS | POS | POS | **4** | NO |
| `P14002` | **High Prob Below Threshold** | POS | NEG | NEG | NEG | NEG | **1** | NO |
| `P14003` | **4 Positive Diseases** | POS | NEG | NEG | NEG | NEG | **1** | NO |

---

## 2. Detailed 10-Patient Real Output Transformations

### Patient 1: `P14006`

#### Section 3 — Raw Level-0 Input Predictions (3 Modalities × 5 Diseases = 15 Predictions):
```
Patient_ID: P14006

                    Clinical     Gut       Wearable
------------------------------------------------------
T2D                   0.0660      0.2094       0.0062
Prediabetes           0.0017      0.5399       0.0122
High Adiposity        0.0264      0.2024       0.1350
Metabolic Syndrome    0.2487      0.0610       0.4196
NAFLD                 0.0237      0.1759       0.3751
```

#### Section 4 — Fusion Input Routing & Modality Rules:
- **T2D**: Clinical Passthrough -> P_Fused = 0.0660 (Gut = NOT USED, Wearable = NOT USED)
- **Prediabetes**: Clinical Passthrough -> P_Fused = 0.0017 (Gut = NOT USED, Wearable = NOT USED)
- **High Adiposity**: Clinical Passthrough -> P_Fused = 0.0264 (Gut = NOT USED, Wearable = NOT USED)
- **Metabolic Syndrome**: Clinical (0.2487) + Gut (0.0610) -> LR Stacker -> Platt Recalibrated -> P_Fused = 0.0062 (Wearable = NOT USED)
- **NAFLD**: Clinical (0.0237) + Gut (0.1759) -> LR Stacker -> P_Fused = 0.0151 (Wearable = NOT USED)

#### Section 5 — Actual Numerical Calculation (Full-Precision Recomputation):
**Metabolic Syndrome Step-by-Step**:
1. Logit_raw = -4.3697124012 + 2.5798532189 × (0.2487) + 1.9638807682 × (0.0610) = -3.608207
2. P_raw = sigmoid(-3.608207) = 0.026385
3. Logit_platt = 1.5006 + 1.8243 × (-3.608207) = -5.081852
4. P_calibrated = sigmoid(-5.081852) = **0.0062**
5. Prediction: P_calibrated (0.0062) >= 0.20 -> **NEGATIVE**

**NAFLD Step-by-Step**:
1. Logit = -4.7670735247 + 3.7924128668 × (0.0237) + 2.8339984355 × (0.1759) = -4.178519
2. P_Fused = sigmoid(-4.178519) = **0.0151**
3. Prediction: P_Fused (0.0151) >= 0.50 -> **NEGATIVE**

#### Section 6 — Final Disease Risk Scores & Independent Decisions:
| Disease | Risk Score | Threshold | Prediction |
|:---|---:|---:|:---:|
| Type2 Diabetes | 0.0660 | 0.50 | **NEGATIVE** |
| Prediabetes | 0.0017 | 0.50 | **NEGATIVE** |
| High Adiposity Risk | 0.0264 | 0.50 | **NEGATIVE** |
| Metabolic Syndrome | 0.0062 | **0.20 (Applied AFTER Platt)** | **NEGATIVE** |
| NAFLD | 0.0151 | 0.50 | **NEGATIVE** |

#### Section 7 — Prediabetes Post-Decision Suppression Audit:
- Raw P(Prediabetes): `0.0017` (Un-mutated)
- Raw Pred_Prediabetes: `NEGATIVE`
- Final Pred_Prediabetes: `NEGATIVE`
- Suppressed: **NO**

#### Section 9 — Risk Presentation Ranking (Presentation Only — Positivity Determined by Threshold):
1. **Type2 Diabetes** — 0.0660 — **NEGATIVE**
2. **High Adiposity Risk** — 0.0264 — **NEGATIVE**
3. **NAFLD** — 0.0151 — **NEGATIVE**
4. **Metabolic Syndrome** — 0.0062 — **NEGATIVE**
5. **Prediabetes** — 0.0017 — **NEGATIVE**

---

### Patient 2: `P14001`

#### Section 3 — Raw Level-0 Input Predictions (3 Modalities × 5 Diseases = 15 Predictions):
```
Patient_ID: P14001

                    Clinical     Gut       Wearable
------------------------------------------------------
T2D                   0.9343      0.3923       0.9950
Prediabetes           0.0012      0.5383       0.0114
High Adiposity        0.0504      0.3060       0.7703
Metabolic Syndrome    0.1113      0.4006       0.5415
NAFLD                 0.7654      0.3257       0.5471
```

#### Section 4 — Fusion Input Routing & Modality Rules:
- **T2D**: Clinical Passthrough -> P_Fused = 0.9343 (Gut = NOT USED, Wearable = NOT USED)
- **Prediabetes**: Clinical Passthrough -> P_Fused = 0.0012 (Gut = NOT USED, Wearable = NOT USED)
- **High Adiposity**: Clinical Passthrough -> P_Fused = 0.0504 (Gut = NOT USED, Wearable = NOT USED)
- **Metabolic Syndrome**: Clinical (0.1113) + Gut (0.4006) -> LR Stacker -> Platt Recalibrated -> P_Fused = 0.0109 (Wearable = NOT USED)
- **NAFLD**: Clinical (0.7654) + Gut (0.3257) -> LR Stacker -> P_Fused = 0.2807 (Wearable = NOT USED)

#### Section 5 — Actual Numerical Calculation (Full-Precision Recomputation):
**Metabolic Syndrome Step-by-Step**:
1. Logit_raw = -4.3697124012 + 2.5798532189 × (0.1113) + 1.9638807682 × (0.4006) = -3.295840
2. P_raw = sigmoid(-3.295840) = 0.035714
3. Logit_platt = 1.5006 + 1.8243 × (-3.295840) = -4.512001
4. P_calibrated = sigmoid(-4.512001) = **0.0109**
5. Prediction: P_calibrated (0.0109) >= 0.20 -> **NEGATIVE**

**NAFLD Step-by-Step**:
1. Logit = -4.7670735247 + 3.7924128668 × (0.7654) + 2.8339984355 × (0.3257) = -0.941160
2. P_Fused = sigmoid(-0.941160) = **0.2807**
3. Prediction: P_Fused (0.2807) >= 0.50 -> **NEGATIVE**

#### Section 6 — Final Disease Risk Scores & Independent Decisions:
| Disease | Risk Score | Threshold | Prediction |
|:---|---:|---:|:---:|
| Type2 Diabetes | 0.9343 | 0.50 | **POSITIVE** |
| Prediabetes | 0.0012 | 0.50 | **NEGATIVE** |
| High Adiposity Risk | 0.0504 | 0.50 | **NEGATIVE** |
| Metabolic Syndrome | 0.0109 | **0.20 (Applied AFTER Platt)** | **NEGATIVE** |
| NAFLD | 0.2807 | 0.50 | **NEGATIVE** |

#### Section 7 — Prediabetes Post-Decision Suppression Audit:
- Raw P(Prediabetes): `0.0012` (Un-mutated)
- Raw Pred_Prediabetes: `NEGATIVE`
- Final Pred_Prediabetes: `NEGATIVE`
- Suppressed: **NO**

#### Section 9 — Risk Presentation Ranking (Presentation Only — Positivity Determined by Threshold):
1. **Type2 Diabetes** — 0.9343 — **POSITIVE**
2. **NAFLD** — 0.2807 — **NEGATIVE**
3. **High Adiposity Risk** — 0.0504 — **NEGATIVE**
4. **Metabolic Syndrome** — 0.0109 — **NEGATIVE**
5. **Prediabetes** — 0.0012 — **NEGATIVE**

---

### Patient 3: `P14010`

#### Section 3 — Raw Level-0 Input Predictions (3 Modalities × 5 Diseases = 15 Predictions):
```
Patient_ID: P14010

                    Clinical     Gut       Wearable
------------------------------------------------------
T2D                   0.0660      0.0515       0.0089
Prediabetes           0.9980      0.5343       0.9800
High Adiposity        0.8501      0.0565       0.7143
Metabolic Syndrome    0.3632      0.0445       0.4293
NAFLD                 0.2177      0.0711       0.5452
```

#### Section 4 — Fusion Input Routing & Modality Rules:
- **T2D**: Clinical Passthrough -> P_Fused = 0.0660 (Gut = NOT USED, Wearable = NOT USED)
- **Prediabetes**: Clinical Passthrough -> P_Fused = 0.9980 (Gut = NOT USED, Wearable = NOT USED)
- **High Adiposity**: Clinical Passthrough -> P_Fused = 0.8501 (Gut = NOT USED, Wearable = NOT USED)
- **Metabolic Syndrome**: Clinical (0.3632) + Gut (0.0445) -> LR Stacker -> Platt Recalibrated -> P_Fused = 0.0099 (Wearable = NOT USED)
- **NAFLD**: Clinical (0.2177) + Gut (0.0711) -> LR Stacker -> P_Fused = 0.0232 (Wearable = NOT USED)

#### Section 5 — Actual Numerical Calculation (Full-Precision Recomputation):
**Metabolic Syndrome Step-by-Step**:
1. Logit_raw = -4.3697124012 + 2.5798532189 × (0.3632) + 1.9638807682 × (0.0445) = -3.345323
2. P_raw = sigmoid(-3.345323) = 0.034049
3. Logit_platt = 1.5006 + 1.8243 × (-3.345323) = -4.602272
4. P_calibrated = sigmoid(-4.602272) = **0.0099**
5. Prediction: P_calibrated (0.0099) >= 0.20 -> **NEGATIVE**

**NAFLD Step-by-Step**:
1. Logit = -4.7670735247 + 3.7924128668 × (0.2177) + 2.8339984355 × (0.0711) = -3.739812
2. P_Fused = sigmoid(-3.739812) = **0.0232**
3. Prediction: P_Fused (0.0232) >= 0.50 -> **NEGATIVE**

#### Section 6 — Final Disease Risk Scores & Independent Decisions:
| Disease | Risk Score | Threshold | Prediction |
|:---|---:|---:|:---:|
| Type2 Diabetes | 0.0660 | 0.50 | **NEGATIVE** |
| Prediabetes | 0.9980 | 0.50 | **POSITIVE** |
| High Adiposity Risk | 0.8501 | 0.50 | **POSITIVE** |
| Metabolic Syndrome | 0.0099 | **0.20 (Applied AFTER Platt)** | **NEGATIVE** |
| NAFLD | 0.0232 | 0.50 | **NEGATIVE** |

#### Section 7 — Prediabetes Post-Decision Suppression Audit:
- Raw P(Prediabetes): `0.9980` (Un-mutated)
- Raw Pred_Prediabetes: `POSITIVE`
- Final Pred_Prediabetes: `POSITIVE`
- Suppressed: **NO**

#### Section 9 — Risk Presentation Ranking (Presentation Only — Positivity Determined by Threshold):
1. **Prediabetes** — 0.9980 — **POSITIVE**
2. **High Adiposity Risk** — 0.8501 — **POSITIVE**
3. **Type2 Diabetes** — 0.0660 — **NEGATIVE**
4. **NAFLD** — 0.0232 — **NEGATIVE**
5. **Metabolic Syndrome** — 0.0099 — **NEGATIVE**

---

### Patient 4: `P14004`

#### Section 3 — Raw Level-0 Input Predictions (3 Modalities × 5 Diseases = 15 Predictions):
```
Patient_ID: P14004

                    Clinical     Gut       Wearable
------------------------------------------------------
T2D                   0.9343      0.9028       0.9950
Prediabetes           0.0012      0.1803       0.0114
High Adiposity        0.9966      0.9364       0.7703
Metabolic Syndrome    0.7423      0.7897       0.5327
NAFLD                 0.2208      0.8876       0.5659
```

#### Section 4 — Fusion Input Routing & Modality Rules:
- **T2D**: Clinical Passthrough -> P_Fused = 0.9343 (Gut = NOT USED, Wearable = NOT USED)
- **Prediabetes**: Clinical Passthrough -> P_Fused = 0.0012 (Gut = NOT USED, Wearable = NOT USED)
- **High Adiposity**: Clinical Passthrough -> P_Fused = 0.9966 (Gut = NOT USED, Wearable = NOT USED)
- **Metabolic Syndrome**: Clinical (0.7423) + Gut (0.7897) -> LR Stacker -> Platt Recalibrated -> P_Fused = 0.4629 (Wearable = NOT USED)
- **NAFLD**: Clinical (0.2208) + Gut (0.8876) -> LR Stacker -> P_Fused = 0.1956 (Wearable = NOT USED)

#### Section 6 — Final Disease Risk Scores & Independent Decisions:
| Disease | Risk Score | Threshold | Prediction |
|:---|---:|---:|:---:|
| Type2 Diabetes | 0.9343 | 0.50 | **POSITIVE** |
| Prediabetes | 0.0012 | 0.50 | **NEGATIVE** |
| High Adiposity Risk | 0.9966 | 0.50 | **POSITIVE** |
| Metabolic Syndrome | 0.4629 | **0.20 (Applied AFTER Platt)** | **POSITIVE** |
| NAFLD | 0.1956 | 0.50 | **NEGATIVE** |

#### Section 7 — Prediabetes Post-Decision Suppression Audit:
- Raw P(Prediabetes): `0.0012` (Un-mutated)
- Raw Pred_Prediabetes: `NEGATIVE`
- Final Pred_Prediabetes: `NEGATIVE`
- Suppressed: **NO**

#### Section 9 — Risk Presentation Ranking (Presentation Only — Positivity Determined by Threshold):
1. **High Adiposity Risk** — 0.9966 — **POSITIVE**
2. **Type2 Diabetes** — 0.9343 — **POSITIVE**
3. **Metabolic Syndrome** — 0.4629 — **POSITIVE**
4. **NAFLD** — 0.1956 — **NEGATIVE**
5. **Prediabetes** — 0.0012 — **NEGATIVE**

---

### Patient 5: `P14996`

#### Section 3 — Raw Level-0 Input Predictions (3 Modalities × 5 Diseases = 15 Predictions):
```
Patient_ID: P14996

                    Clinical     Gut       Wearable
------------------------------------------------------
T2D                   0.7532      0.4106       0.0331
Prediabetes           0.7728      0.5259       0.9790
High Adiposity        0.0363      0.6436       0.4533
Metabolic Syndrome    0.1352      0.2995       0.4626
NAFLD                 0.0759      0.3018       0.5011
```

#### Section 4 — Fusion Input Routing & Modality Rules:
- **T2D**: Clinical Passthrough -> P_Fused = 0.7532 (Gut = NOT USED, Wearable = NOT USED)
- **Prediabetes**: Clinical Passthrough -> P_Fused = 0.7728 (Gut = NOT USED, Wearable = NOT USED)
- **High Adiposity**: Clinical Passthrough -> P_Fused = 0.0363 (Gut = NOT USED, Wearable = NOT USED)
- **Metabolic Syndrome**: Clinical (0.1352) + Gut (0.2995) -> LR Stacker -> Platt Recalibrated -> P_Fused = 0.0085 (Wearable = NOT USED)
- **NAFLD**: Clinical (0.0759) + Gut (0.3018) -> LR Stacker -> P_Fused = 0.0260 (Wearable = NOT USED)

#### Section 6 — Final Disease Risk Scores & Independent Decisions:
| Disease | Risk Score | Threshold | Prediction |
|:---|---:|---:|:---:|
| Type2 Diabetes | 0.7532 | 0.50 | **POSITIVE** |
| Prediabetes | 0.7728 | 0.50 | **NEGATIVE** |
| High Adiposity Risk | 0.0363 | 0.50 | **NEGATIVE** |
| Metabolic Syndrome | 0.0085 | **0.20 (Applied AFTER Platt)** | **NEGATIVE** |
| NAFLD | 0.0260 | 0.50 | **NEGATIVE** |

#### Section 7 — Prediabetes Post-Decision Suppression Audit:
- Raw P(Prediabetes): `0.7728` (Un-mutated)
- Raw Pred_Prediabetes: `POSITIVE`
- Final Pred_Prediabetes: `NEGATIVE`
- Suppressed: **YES**

#### Section 9 — Risk Presentation Ranking (Presentation Only — Positivity Determined by Threshold):
1. **Prediabetes** — 0.7728 — **NEGATIVE**
2. **Type2 Diabetes** — 0.7532 — **POSITIVE**
3. **High Adiposity Risk** — 0.0363 — **NEGATIVE**
4. **NAFLD** — 0.0260 — **NEGATIVE**
5. **Metabolic Syndrome** — 0.0085 — **NEGATIVE**

---

### Patient 6: `P14007`

#### Section 3 — Raw Level-0 Input Predictions (3 Modalities × 5 Diseases = 15 Predictions):
```
Patient_ID: P14007

                    Clinical     Gut       Wearable
------------------------------------------------------
T2D                   0.0660      0.7113       0.0057
Prediabetes           0.9976      0.4905       0.9656
High Adiposity        0.7830      0.6599       0.2855
Metabolic Syndrome    0.7078      0.4791       0.4626
NAFLD                 0.8711      0.5336       0.4543
```

#### Section 4 — Fusion Input Routing & Modality Rules:
- **T2D**: Clinical Passthrough -> P_Fused = 0.0660 (Gut = NOT USED, Wearable = NOT USED)
- **Prediabetes**: Clinical Passthrough -> P_Fused = 0.9976 (Gut = NOT USED, Wearable = NOT USED)
- **High Adiposity**: Clinical Passthrough -> P_Fused = 0.7830 (Gut = NOT USED, Wearable = NOT USED)
- **Metabolic Syndrome**: Clinical (0.7078) + Gut (0.4791) -> LR Stacker -> Platt Recalibrated -> P_Fused = 0.1941 (Wearable = NOT USED)
- **NAFLD**: Clinical (0.8711) + Gut (0.5336) -> LR Stacker -> P_Fused = 0.5121 (Wearable = NOT USED)

#### Section 6 — Final Disease Risk Scores & Independent Decisions:
| Disease | Risk Score | Threshold | Prediction |
|:---|---:|---:|:---:|
| Type2 Diabetes | 0.0660 | 0.50 | **NEGATIVE** |
| Prediabetes | 0.9976 | 0.50 | **POSITIVE** |
| High Adiposity Risk | 0.7830 | 0.50 | **POSITIVE** |
| Metabolic Syndrome | 0.1941 | **0.20 (Applied AFTER Platt)** | **NEGATIVE** |
| NAFLD | 0.5121 | 0.50 | **POSITIVE** |

#### Section 7 — Prediabetes Post-Decision Suppression Audit:
- Raw P(Prediabetes): `0.9976` (Un-mutated)
- Raw Pred_Prediabetes: `POSITIVE`
- Final Pred_Prediabetes: `POSITIVE`
- Suppressed: **NO**

#### Section 9 — Risk Presentation Ranking (Presentation Only — Positivity Determined by Threshold):
1. **Prediabetes** — 0.9976 — **POSITIVE**
2. **High Adiposity Risk** — 0.7830 — **POSITIVE**
3. **NAFLD** — 0.5121 — **POSITIVE**
4. **Metabolic Syndrome** — 0.1941 — **NEGATIVE**
5. **Type2 Diabetes** — 0.0660 — **NEGATIVE**

---

### Patient 7: `P14014`

#### Section 3 — Raw Level-0 Input Predictions (3 Modalities × 5 Diseases = 15 Predictions):
```
Patient_ID: P14014

                    Clinical     Gut       Wearable
------------------------------------------------------
T2D                   0.1825      0.4549       0.4283
Prediabetes           0.9536      0.4773       0.8029
High Adiposity        0.8298      0.4922       0.4000
Metabolic Syndrome    0.5732      0.5724       0.5182
NAFLD                 0.9392      0.3243       0.5043
```

#### Section 4 — Fusion Input Routing & Modality Rules:
- **T2D**: Clinical Passthrough -> P_Fused = 0.1825 (Gut = NOT USED, Wearable = NOT USED)
- **Prediabetes**: Clinical Passthrough -> P_Fused = 0.9536 (Gut = NOT USED, Wearable = NOT USED)
- **High Adiposity**: Clinical Passthrough -> P_Fused = 0.8298 (Gut = NOT USED, Wearable = NOT USED)
- **Metabolic Syndrome**: Clinical (0.5732) + Gut (0.5724) -> LR Stacker -> Platt Recalibrated -> P_Fused = 0.1515 (Wearable = NOT USED)
- **NAFLD**: Clinical (0.9392) + Gut (0.3243) -> LR Stacker -> P_Fused = 0.4290 (Wearable = NOT USED)

#### Section 6 — Final Disease Risk Scores & Independent Decisions:
| Disease | Risk Score | Threshold | Prediction |
|:---|---:|---:|:---:|
| Type2 Diabetes | 0.1825 | 0.50 | **NEGATIVE** |
| Prediabetes | 0.9536 | 0.50 | **POSITIVE** |
| High Adiposity Risk | 0.8298 | 0.50 | **POSITIVE** |
| Metabolic Syndrome | 0.1515 | **0.20 (Applied AFTER Platt)** | **NEGATIVE** |
| NAFLD | 0.4290 | 0.50 | **NEGATIVE** |

#### Section 7 — Prediabetes Post-Decision Suppression Audit:
- Raw P(Prediabetes): `0.9536` (Un-mutated)
- Raw Pred_Prediabetes: `POSITIVE`
- Final Pred_Prediabetes: `POSITIVE`
- Suppressed: **NO**

#### Section 9 — Risk Presentation Ranking (Presentation Only — Positivity Determined by Threshold):
1. **Prediabetes** — 0.9536 — **POSITIVE**
2. **High Adiposity Risk** — 0.8298 — **POSITIVE**
3. **NAFLD** — 0.4290 — **NEGATIVE**
4. **Type2 Diabetes** — 0.1825 — **NEGATIVE**
5. **Metabolic Syndrome** — 0.1515 — **NEGATIVE**

---

### Patient 8: `P14021`

#### Section 3 — Raw Level-0 Input Predictions (3 Modalities × 5 Diseases = 15 Predictions):
```
Patient_ID: P14021

                    Clinical     Gut       Wearable
------------------------------------------------------
T2D                   0.9343      0.8922       0.9938
Prediabetes           0.0022      0.2933       0.0114
High Adiposity        0.9861      0.8826       0.6540
Metabolic Syndrome    0.7968      0.6939       0.5313
NAFLD                 0.9053      0.7464       0.5478
```

#### Section 4 — Fusion Input Routing & Modality Rules:
- **T2D**: Clinical Passthrough -> P_Fused = 0.9343 (Gut = NOT USED, Wearable = NOT USED)
- **Prediabetes**: Clinical Passthrough -> P_Fused = 0.0022 (Gut = NOT USED, Wearable = NOT USED)
- **High Adiposity**: Clinical Passthrough -> P_Fused = 0.9861 (Gut = NOT USED, Wearable = NOT USED)
- **Metabolic Syndrome**: Clinical (0.7968) + Gut (0.6939) -> LR Stacker -> Platt Recalibrated -> P_Fused = 0.4415 (Wearable = NOT USED)
- **NAFLD**: Clinical (0.9053) + Gut (0.7464) -> LR Stacker -> P_Fused = 0.6860 (Wearable = NOT USED)

#### Section 6 — Final Disease Risk Scores & Independent Decisions:
| Disease | Risk Score | Threshold | Prediction |
|:---|---:|---:|:---:|
| Type2 Diabetes | 0.9343 | 0.50 | **POSITIVE** |
| Prediabetes | 0.0022 | 0.50 | **NEGATIVE** |
| High Adiposity Risk | 0.9861 | 0.50 | **POSITIVE** |
| Metabolic Syndrome | 0.4415 | **0.20 (Applied AFTER Platt)** | **POSITIVE** |
| NAFLD | 0.6860 | 0.50 | **POSITIVE** |

#### Section 7 — Prediabetes Post-Decision Suppression Audit:
- Raw P(Prediabetes): `0.0022` (Un-mutated)
- Raw Pred_Prediabetes: `NEGATIVE`
- Final Pred_Prediabetes: `NEGATIVE`
- Suppressed: **NO**

#### Section 9 — Risk Presentation Ranking (Presentation Only — Positivity Determined by Threshold):
1. **High Adiposity Risk** — 0.9861 — **POSITIVE**
2. **Type2 Diabetes** — 0.9343 — **POSITIVE**
3. **NAFLD** — 0.6860 — **POSITIVE**
4. **Metabolic Syndrome** — 0.4415 — **POSITIVE**
5. **Prediabetes** — 0.0022 — **NEGATIVE**

---

### Patient 9: `P14002`

#### Section 3 — Raw Level-0 Input Predictions (3 Modalities × 5 Diseases = 15 Predictions):
```
Patient_ID: P14002

                    Clinical     Gut       Wearable
------------------------------------------------------
T2D                   0.9343      0.3558       0.9737
Prediabetes           0.0012      0.5428       0.0614
High Adiposity        0.0028      0.4028       0.4555
Metabolic Syndrome    0.0751      0.1915       0.5249
NAFLD                 0.0036      0.4119       0.5262
```

#### Section 4 — Fusion Input Routing & Modality Rules:
- **T2D**: Clinical Passthrough -> P_Fused = 0.9343 (Gut = NOT USED, Wearable = NOT USED)
- **Prediabetes**: Clinical Passthrough -> P_Fused = 0.0012 (Gut = NOT USED, Wearable = NOT USED)
- **High Adiposity**: Clinical Passthrough -> P_Fused = 0.0028 (Gut = NOT USED, Wearable = NOT USED)
- **Metabolic Syndrome**: Clinical (0.0751) + Gut (0.1915) -> LR Stacker -> Platt Recalibrated -> P_Fused = 0.0044 (Wearable = NOT USED)
- **NAFLD**: Clinical (0.0036) + Gut (0.4119) -> LR Stacker -> P_Fused = 0.0270 (Wearable = NOT USED)

#### Section 6 — Final Disease Risk Scores & Independent Decisions:
| Disease | Risk Score | Threshold | Prediction |
|:---|---:|---:|:---:|
| Type2 Diabetes | 0.9343 | 0.50 | **POSITIVE** |
| Prediabetes | 0.0012 | 0.50 | **NEGATIVE** |
| High Adiposity Risk | 0.0028 | 0.50 | **NEGATIVE** |
| Metabolic Syndrome | 0.0044 | **0.20 (Applied AFTER Platt)** | **NEGATIVE** |
| NAFLD | 0.0270 | 0.50 | **NEGATIVE** |

#### Section 7 — Prediabetes Post-Decision Suppression Audit:
- Raw P(Prediabetes): `0.0012` (Un-mutated)
- Raw Pred_Prediabetes: `NEGATIVE`
- Final Pred_Prediabetes: `NEGATIVE`
- Suppressed: **NO**

#### Section 9 — Risk Presentation Ranking (Presentation Only — Positivity Determined by Threshold):
1. **Type2 Diabetes** — 0.9343 — **POSITIVE**
2. **NAFLD** — 0.0270 — **NEGATIVE**
3. **Metabolic Syndrome** — 0.0044 — **NEGATIVE**
4. **High Adiposity Risk** — 0.0028 — **NEGATIVE**
5. **Prediabetes** — 0.0012 — **NEGATIVE**

---

### Patient 10: `P14003`

#### Section 3 — Raw Level-0 Input Predictions (3 Modalities × 5 Diseases = 15 Predictions):
```
Patient_ID: P14003

                    Clinical     Gut       Wearable
------------------------------------------------------
T2D                   0.9343      0.6555       0.9554
Prediabetes           0.0011      0.5321       0.0721
High Adiposity        0.0023      0.6163       0.1284
Metabolic Syndrome    0.0816      0.6195       0.5025
NAFLD                 0.3016      0.6053       0.5461
```

#### Section 4 — Fusion Input Routing & Modality Rules:
- **T2D**: Clinical Passthrough -> P_Fused = 0.9343 (Gut = NOT USED, Wearable = NOT USED)
- **Prediabetes**: Clinical Passthrough -> P_Fused = 0.0011 (Gut = NOT USED, Wearable = NOT USED)
- **High Adiposity**: Clinical Passthrough -> P_Fused = 0.0023 (Gut = NOT USED, Wearable = NOT USED)
- **Metabolic Syndrome**: Clinical (0.0816) + Gut (0.6195) -> LR Stacker -> Platt Recalibrated -> P_Fused = 0.0205 (Wearable = NOT USED)
- **NAFLD**: Clinical (0.3016) + Gut (0.6053) -> LR Stacker -> P_Fused = 0.1292 (Wearable = NOT USED)

#### Section 6 — Final Disease Risk Scores & Independent Decisions:
| Disease | Risk Score | Threshold | Prediction |
|:---|---:|---:|:---:|
| Type2 Diabetes | 0.9343 | 0.50 | **POSITIVE** |
| Prediabetes | 0.0011 | 0.50 | **NEGATIVE** |
| High Adiposity Risk | 0.0023 | 0.50 | **NEGATIVE** |
| Metabolic Syndrome | 0.0205 | **0.20 (Applied AFTER Platt)** | **NEGATIVE** |
| NAFLD | 0.1292 | 0.50 | **NEGATIVE** |

#### Section 7 — Prediabetes Post-Decision Suppression Audit:
- Raw P(Prediabetes): `0.0011` (Un-mutated)
- Raw Pred_Prediabetes: `NEGATIVE`
- Final Pred_Prediabetes: `NEGATIVE`
- Suppressed: **NO**

#### Section 9 — Risk Presentation Ranking (Presentation Only — Positivity Determined by Threshold):
1. **Type2 Diabetes** — 0.9343 — **POSITIVE**
2. **NAFLD** — 0.1292 — **NEGATIVE**
3. **Metabolic Syndrome** — 0.0205 — **NEGATIVE**
4. **High Adiposity Risk** — 0.0023 — **NEGATIVE**
5. **Prediabetes** — 0.0011 — **NEGATIVE**

---

## Section 10 — Final Compact Summary Table

| Patient_ID | T2D | Prediabetes | HAR | MetSyn | NAFLD | # Positive |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `P14006` | **NEG** | **NEG** | **NEG** | **NEG** | **NEG** | **0** |
| `P14001` | **POS** | **NEG** | **NEG** | **NEG** | **NEG** | **1** |
| `P14010` | **NEG** | **POS** | **POS** | **NEG** | **NEG** | **2** |
| `P14004` | **POS** | **NEG** | **POS** | **POS** | **NEG** | **3** |
| `P14996` | **POS** | **NEG** | **NEG** | **NEG** | **NEG** | **1** |
| `P14007` | **NEG** | **POS** | **POS** | **NEG** | **POS** | **3** |
| `P14014` | **NEG** | **POS** | **POS** | **NEG** | **NEG** | **2** |
| `P14021` | **POS** | **NEG** | **POS** | **POS** | **POS** | **4** |
| `P14002` | **POS** | **NEG** | **NEG** | **NEG** | **NEG** | **1** |
| `P14003` | **POS** | **NEG** | **NEG** | **NEG** | **NEG** | **1** |

### Per-Patient Presentation Risk Rankings:

**Patient `P14006` Risk Ranking**:
  1. Type2 Diabetes — 0.0660 — **NEGATIVE**
  2. High Adiposity Risk — 0.0264 — **NEGATIVE**
  3. NAFLD — 0.0151 — **NEGATIVE**
  4. Metabolic Syndrome — 0.0062 — **NEGATIVE**
  5. Prediabetes — 0.0017 — **NEGATIVE**

**Patient `P14001` Risk Ranking**:
  1. Type2 Diabetes — 0.9343 — **POSITIVE**
  2. NAFLD — 0.2807 — **NEGATIVE**
  3. High Adiposity Risk — 0.0504 — **NEGATIVE**
  4. Metabolic Syndrome — 0.0109 — **NEGATIVE**
  5. Prediabetes — 0.0012 — **NEGATIVE**

**Patient `P14010` Risk Ranking**:
  1. Prediabetes — 0.9980 — **POSITIVE**
  2. High Adiposity Risk — 0.8501 — **POSITIVE**
  3. Type2 Diabetes — 0.0660 — **NEGATIVE**
  4. NAFLD — 0.0232 — **NEGATIVE**
  5. Metabolic Syndrome — 0.0099 — **NEGATIVE**

**Patient `P14004` Risk Ranking**:
  1. High Adiposity Risk — 0.9966 — **POSITIVE**
  2. Type2 Diabetes — 0.9343 — **POSITIVE**
  3. Metabolic Syndrome — 0.4629 — **POSITIVE**
  4. NAFLD — 0.1956 — **NEGATIVE**
  5. Prediabetes — 0.0012 — **NEGATIVE**

**Patient `P14996` Risk Ranking**:
  1. Prediabetes — 0.7728 — **NEGATIVE**
  2. Type2 Diabetes — 0.7532 — **POSITIVE**
  3. High Adiposity Risk — 0.0363 — **NEGATIVE**
  4. NAFLD — 0.0260 — **NEGATIVE**
  5. Metabolic Syndrome — 0.0085 — **NEGATIVE**

**Patient `P14007` Risk Ranking**:
  1. Prediabetes — 0.9976 — **POSITIVE**
  2. High Adiposity Risk — 0.7830 — **POSITIVE**
  3. NAFLD — 0.5121 — **POSITIVE**
  4. Metabolic Syndrome — 0.1941 — **NEGATIVE**
  5. Type2 Diabetes — 0.0660 — **NEGATIVE**

**Patient `P14014` Risk Ranking**:
  1. Prediabetes — 0.9536 — **POSITIVE**
  2. High Adiposity Risk — 0.8298 — **POSITIVE**
  3. NAFLD — 0.4290 — **NEGATIVE**
  4. Type2 Diabetes — 0.1825 — **NEGATIVE**
  5. Metabolic Syndrome — 0.1515 — **NEGATIVE**

**Patient `P14021` Risk Ranking**:
  1. High Adiposity Risk — 0.9861 — **POSITIVE**
  2. Type2 Diabetes — 0.9343 — **POSITIVE**
  3. NAFLD — 0.6860 — **POSITIVE**
  4. Metabolic Syndrome — 0.4415 — **POSITIVE**
  5. Prediabetes — 0.0022 — **NEGATIVE**

**Patient `P14002` Risk Ranking**:
  1. Type2 Diabetes — 0.9343 — **POSITIVE**
  2. NAFLD — 0.0270 — **NEGATIVE**
  3. Metabolic Syndrome — 0.0044 — **NEGATIVE**
  4. High Adiposity Risk — 0.0028 — **NEGATIVE**
  5. Prediabetes — 0.0012 — **NEGATIVE**

**Patient `P14003` Risk Ranking**:
  1. Type2 Diabetes — 0.9343 — **POSITIVE**
  2. NAFLD — 0.1292 — **NEGATIVE**
  3. Metabolic Syndrome — 0.0205 — **NEGATIVE**
  4. High Adiposity Risk — 0.0023 — **NEGATIVE**
  5. Prediabetes — 0.0011 — **NEGATIVE**

---

## Section 11 — Output Contract Check

Confirmed 100% presence of all required fields:

- [x] `Patient_ID`
- [x] All 15 Level-0 raw probabilities (`P_Clinical_*`, `P_Gut_*`, `P_Wearable_*`)
- [x] All 5 Level-1 fused probabilities (`P_Fused_*`)
- [x] Metabolic Syndrome raw LR probability (`P_Raw_LR_Metabolic_Syndrome`)
- [x] Metabolic Syndrome Platt calibrated probability (`P_Fused_Metabolic_Syndrome`)
- [x] All 5 binary predictions (`Pred_*`)
- [x] All 5 disease decision thresholds (`Threshold_*`)
- [x] Prediabetes raw decision (`Pred_Prediabetes_Raw`)
- [x] Prediabetes final decision (`Pred_Prediabetes`)
- [x] Prediabetes suppression flag (`Prediabetes_Suppressed`)
- [x] Number of positive diseases (`Pos_Count`)
- [x] Risk score presentation ranking

## Section 12 — Final Safety Confirmations Checklist

- [x] **No architecture changes**
- [x] **No coefficient changes**
- [x] **No threshold changes**
- [x] **No retraining**
- [x] **No fusion optimization**
- [x] **No Test data accessed** (`fusion_test_master.csv` 100% untouched)
- [x] **No synthetic Level-0 probabilities created** (Used 100% actual validation prediction outputs)
- [x] **No predictions manually modified**
- [x] **Wearable excluded from Fusion V1 Level-1 equations**
- [x] **All 5 diseases evaluated independently**
- [x] **Multiple positive diseases allowed** (No single-winner mechanism)
- [x] **Ranking used ONLY for presentation**
- [x] **Prediabetes suppression modifies binary decision only** (Raw probability un-mutated)
