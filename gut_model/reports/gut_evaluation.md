# Gut Microbiome Metabolic Disease Prediction Model (v3) — Evaluation Report

**Generated On**: 2026-08-09T03:15:30.003385+00:00

**Model Version**: gut_v3

**Algorithm**: XGBoost (objective=binary:logistic, eval_metric=aucpr)

**Features**: 21 CLR-transformed taxa (delta=1e-5)

**Preprocessing**: Train-only median imputation → row-wise CLR


---

## Executive Summary (XGBoost Test Performance — Suppressed Predictions)

| Label | ROC-AUC | PR-AUC | F1 | Precision | Recall |
|---|---|---|---|---|---|
| **Type2_Diabetes** | 0.8286 | 0.7214 | 0.6672 | 0.6439 | 0.6924 |
| **Prediabetes** | 0.6146 | 0.4058 | 0.4372 | 0.3661 | 0.5426 |
| **High_Adiposity_Risk** | 0.8049 | 0.6842 | 0.6230 | 0.5336 | 0.7484 |
| **Metabolic_Syndrome** | 0.8086 | 0.2908 | 0.2927 | 0.1804 | 0.7759 |
| **NAFLD** | 0.8089 | 0.4554 | 0.4095 | 0.2793 | 0.7668 |

---

## Diagnostic AUC Reference (RandomForest 3-fold CV baseline — informational only)

| Label | Reference AUC | XGBoost Test AUC | Notes |

|---|---|---|---|
| Type2_Diabetes | 0.81 | 0.8286 |  |
| Prediabetes | 0.58 | 0.6146 | Within expected range (0.52–0.70) |
| High_Adiposity_Risk | 0.81 | 0.8049 |  |
| Metabolic_Syndrome | 0.83 | 0.8086 |  |
| NAFLD | 0.81 | 0.8089 |  |

---

## Class Imbalance & Scale Pos Weights

Computed strictly from Training split (14,000 rows):

- **Type2_Diabetes**: `scale_pos_weight = 1.7663`
- **Prediabetes**: `scale_pos_weight = 2.1167`
- **High_Adiposity_Risk**: `scale_pos_weight = 2.1215`
- **Metabolic_Syndrome**: `scale_pos_weight = 12.2325`
- **NAFLD**: `scale_pos_weight = 5.7470`

---

## Baseline (Logistic Regression) vs XGBoost Comparison

| Label | Model | ROC-AUC | PR-AUC | F1 | Precision | Recall | Brier Score |
|---|---|---|---|---|---|---|---|
| **Type2_Diabetes** | Baseline (LogReg) | 0.8298 | 0.7200 | 0.6725 | 0.6481 | 0.6987 | 0.1696 |
| **Type2_Diabetes** | **XGBoost (v3)** | **0.8286** | **0.7214** | **0.6672** | **0.6439** | **0.6924** | **0.1688** |
| **Prediabetes** | Baseline (LogReg) | 0.5493 | 0.3310 | 0.4374 | 0.3424 | 0.6053 | 0.2485 |
| **Prediabetes** | **XGBoost (v3)** | **0.6146** | **0.4058** | **0.4372** | **0.3661** | **0.5426** | **0.2384** |
| **High_Adiposity_Risk** | Baseline (LogReg) | 0.8096 | 0.6959 | 0.6244 | 0.5786 | 0.6781 | 0.1754 |
| **High_Adiposity_Risk** | **XGBoost (v3)** | **0.8049** | **0.6842** | **0.6230** | **0.5336** | **0.7484** | **0.1747** |
| **Metabolic_Syndrome** | Baseline (LogReg) | 0.8054 | 0.2825 | 0.3166 | 0.2051 | 0.6940 | 0.1656 |
| **Metabolic_Syndrome** | **XGBoost (v3)** | **0.8086** | **0.2908** | **0.2927** | **0.1804** | **0.7759** | **0.1610** |
| **NAFLD** | Baseline (LogReg) | 0.8052 | 0.4660 | 0.4285 | 0.3112 | 0.6875 | 0.1771 |
| **NAFLD** | **XGBoost (v3)** | **0.8089** | **0.4554** | **0.4095** | **0.2793** | **0.7668** | **0.1720** |

---

## Mutual Exclusivity Suppression Rule Impact

Rule: If `Type2_Diabetes` prediction = 1, `Prediabetes` prediction forced to 0 (raw probability untouched).

| Metric | Prediabetes (Raw) | Prediabetes (Suppressed) | Change |
|---|---|---|---|
| Precision | 0.3709 | 0.3661 | -0.0048 |
| Recall    | 0.7287 | 0.5426 | -0.1862 |
| F1 Score  | 0.4916 | 0.4372 | -0.0544 |
| Total Suppressed | — | 454 | — |

---

## Detailed Per-Label Classification Reports & Confusion Matrices

### Label: Type2_Diabetes

- **Best Hyperparameters**: `max_depth=5, learning_rate=0.01, subsample=0.8, colsample_bytree=0.8, n_estimators_used=513`
- **Validation PR-AUC (best config)**: `0.7277`
- **Test Brier Score**: `0.1688`

#### Classification Report (Suppressed Predictions)
```
              precision    recall  f1-score   support

           0     0.8132    0.7777    0.7950      1898
           1     0.6439    0.6924    0.6672      1102

    accuracy                         0.7463      3000
   macro avg     0.7286    0.7350    0.7311      3000
weighted avg     0.7510    0.7463    0.7481      3000

```

#### Confusion Matrix (Raw Counts)
```
TN: 1476   FP: 422   
FN: 339    TP: 763   
```

#### Confusion Matrix (Row-Normalized)
```
TN: 0.7777  FP: 0.2223
FN: 0.3076  TP: 0.6924
```

### Label: Prediabetes

- **Best Hyperparameters**: `max_depth=7, learning_rate=0.05, subsample=1.0, colsample_bytree=0.8, n_estimators_used=38`
- **Validation PR-AUC (best config)**: `0.4202`
- **Test Brier Score**: `0.2384`

#### Classification Report (Suppressed Predictions)
```
              precision    recall  f1-score   support

           0     0.7324    0.5714    0.6419      2060
           1     0.3661    0.5426    0.4372       940

    accuracy                         0.5623      3000
   macro avg     0.5493    0.5570    0.5396      3000
weighted avg     0.6176    0.5623    0.5778      3000

```

#### Confusion Matrix (Raw Counts)
```
TN: 1177   FP: 883   
FN: 430    TP: 510   
```

#### Confusion Matrix (Row-Normalized)
```
TN: 0.5714  FP: 0.4286
FN: 0.4574  TP: 0.5426
```

### Label: High_Adiposity_Risk

- **Best Hyperparameters**: `max_depth=5, learning_rate=0.05, subsample=0.8, colsample_bytree=1.0, n_estimators_used=122`
- **Validation PR-AUC (best config)**: `0.6738`
- **Test Brier Score**: `0.1747`

#### Classification Report (Suppressed Predictions)
```
              precision    recall  f1-score   support

           0     0.8523    0.6893    0.7622      2034
           1     0.5336    0.7484    0.6230       966

    accuracy                         0.7083      3000
   macro avg     0.6929    0.7189    0.6926      3000
weighted avg     0.7497    0.7083    0.7174      3000

```

#### Confusion Matrix (Raw Counts)
```
TN: 1402   FP: 632   
FN: 243    TP: 723   
```

#### Confusion Matrix (Row-Normalized)
```
TN: 0.6893  FP: 0.3107
FN: 0.2516  TP: 0.7484
```

### Label: Metabolic_Syndrome

- **Best Hyperparameters**: `max_depth=3, learning_rate=0.1, subsample=0.8, colsample_bytree=0.8, n_estimators_used=40`
- **Validation PR-AUC (best config)**: `0.3690`
- **Test Brier Score**: `0.1610`

#### Classification Report (Suppressed Predictions)
```
              precision    recall  f1-score   support

           0     0.9740    0.7045    0.8176      2768
           1     0.1804    0.7759    0.2927       232

    accuracy                         0.7100      3000
   macro avg     0.5772    0.7402    0.5551      3000
weighted avg     0.9126    0.7100    0.7770      3000

```

#### Confusion Matrix (Raw Counts)
```
TN: 1950   FP: 818   
FN: 52     TP: 180   
```

#### Confusion Matrix (Row-Normalized)
```
TN: 0.7045  FP: 0.2955
FN: 0.2241  TP: 0.7759
```

### Label: NAFLD

- **Best Hyperparameters**: `max_depth=3, learning_rate=0.1, subsample=1.0, colsample_bytree=0.8, n_estimators_used=64`
- **Validation PR-AUC (best config)**: `0.4859`
- **Test Brier Score**: `0.1720`

#### Classification Report (Suppressed Predictions)
```
              precision    recall  f1-score   support

           0     0.9478    0.6815    0.7929      2584
           1     0.2793    0.7668    0.4095       416

    accuracy                         0.6933      3000
   macro avg     0.6136    0.7242    0.6012      3000
weighted avg     0.8551    0.6933    0.7397      3000

```

#### Confusion Matrix (Raw Counts)
```
TN: 1761   FP: 823   
FN: 97     TP: 319   
```

#### Confusion Matrix (Row-Normalized)
```
TN: 0.6815  FP: 0.3185
FN: 0.2332  TP: 0.7668
```
