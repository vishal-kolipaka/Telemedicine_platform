# Clinical Metabolic Disease Prediction Model (v4) — Evaluation Report

**Generated On**: 2026-08-04T08:39:32.835322+00:00

## Executive Summary (XGBoost Test Performance - Suppressed Predictions)

| Label | ROC-AUC | PR-AUC | F1 | Precision | Recall |
|---|---|---|---|---|---|
| **Type2_Diabetes** | 0.9997 | 0.9994 | 0.9941 | 0.9955 | 0.9927 |
| **Prediabetes** | 0.9992 | 0.9981 | 0.9861 | 0.9893 | 0.9830 |
| **High_Adiposity_Risk** | 0.9674 | 0.9340 | 0.8489 | 0.7932 | 0.9130 |
| **Metabolic_Syndrome** | 0.8873 | 0.4383 | 0.3831 | 0.2517 | 0.8017 |
| **NAFLD** | 0.9005 | 0.6129 | 0.5382 | 0.3946 | 0.8462 |

---

## Class Imbalance & Scale Pos Weight

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
| **Type2_Diabetes** | Baseline (LogReg) | 0.9988 | 0.9982 | 0.9736 | 0.9611 | 0.9864 | 0.0141 |
| **Type2_Diabetes** | **XGBoost (v4)** | **0.9997** | **0.9994** | **0.9941** | **0.9955** | **0.9927** | **0.0083** |
| **Prediabetes** | Baseline (LogReg) | 0.5207 | 0.2951 | 0.3968 | 0.3263 | 0.5064 | 0.2498 |
| **Prediabetes** | **XGBoost (v4)** | **0.9992** | **0.9981** | **0.9861** | **0.9893** | **0.9830** | **0.0079** |
| **High_Adiposity_Risk** | Baseline (LogReg) | 0.9680 | 0.9353 | 0.8530 | 0.8004 | 0.9130 | 0.0721 |
| **High_Adiposity_Risk** | **XGBoost (v4)** | **0.9674** | **0.9340** | **0.8489** | **0.7932** | **0.9130** | **0.0730** |
| **Metabolic_Syndrome** | Baseline (LogReg) | 0.8889 | 0.4550 | 0.3790 | 0.2490 | 0.7931 | 0.1393 |
| **Metabolic_Syndrome** | **XGBoost (v4)** | **0.8873** | **0.4383** | **0.3831** | **0.2517** | **0.8017** | **0.1295** |
| **NAFLD** | Baseline (LogReg) | 0.8996 | 0.5978 | 0.5418 | 0.3995 | 0.8413 | 0.1370 |
| **NAFLD** | **XGBoost (v4)** | **0.9005** | **0.6129** | **0.5382** | **0.3946** | **0.8462** | **0.1325** |

---

## Mutual Exclusivity Suppression Rule Impact

Suppression Rule: If `Type2_Diabetes` prediction = 1, `Prediabetes` prediction is forced to 0 (raw probability untouched).

| Metric | Prediabetes (Raw) | Prediabetes (Suppressed) | Change |
|---|---|---|---|
| Precision | 0.9882 | 0.9893 | +0.0011 |
| Recall | 0.9830 | 0.9830 | +0.0000 |
| F1 Score | 0.9856 | 0.9861 | +0.0005 |
| Total Suppressed Patients | - | 1 | - |

---

## Detailed Per-Label Classification Reports & Confusion Matrices

### Label: Type2_Diabetes

- **Best Hyperparameters**: `max_depth=7, learning_rate=0.1, subsample=0.8, colsample_bytree=1.0, n_estimators_used=20`
- **Validation PR-AUC**: `0.9994`
- **Brier Score**: `0.0083`

#### Classification Report (Suppressed Predictions)
```
              precision    recall  f1-score   support

           0     0.9958    0.9974    0.9966      1898
           1     0.9955    0.9927    0.9941      1102

    accuracy                         0.9957      3000
   macro avg     0.9956    0.9951    0.9953      3000
weighted avg     0.9957    0.9957    0.9957      3000

```

#### Confusion Matrix (Raw Counts)
```
TN: 1893  FP: 5    
FN: 8     TP: 1094 
```

#### Confusion Matrix (Row-Normalized)
```
TN: 0.9974 FP: 0.0026
FN: 0.0073 TP: 0.9927
```

### Label: Prediabetes

- **Best Hyperparameters**: `max_depth=5, learning_rate=0.1, subsample=0.8, colsample_bytree=1.0, n_estimators_used=62`
- **Validation PR-AUC**: `0.9985`
- **Brier Score**: `0.0079`

#### Classification Report (Suppressed Predictions)
```
              precision    recall  f1-score   support

           0     0.9923    0.9951    0.9937      2060
           1     0.9893    0.9830    0.9861       940

    accuracy                         0.9913      3000
   macro avg     0.9908    0.9891    0.9899      3000
weighted avg     0.9913    0.9913    0.9913      3000

```

#### Confusion Matrix (Raw Counts)
```
TN: 2050  FP: 10   
FN: 16    TP: 924  
```

#### Confusion Matrix (Row-Normalized)
```
TN: 0.9951 FP: 0.0049
FN: 0.0170 TP: 0.9830
```

### Label: High_Adiposity_Risk

- **Best Hyperparameters**: `max_depth=3, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, n_estimators_used=165`
- **Validation PR-AUC**: `0.9327`
- **Brier Score**: `0.0730`

#### Classification Report (Suppressed Predictions)
```
              precision    recall  f1-score   support

           0     0.9555    0.8869    0.9199      2034
           1     0.7932    0.9130    0.8489       966

    accuracy                         0.8953      3000
   macro avg     0.8743    0.9000    0.8844      3000
weighted avg     0.9032    0.8953    0.8971      3000

```

#### Confusion Matrix (Raw Counts)
```
TN: 1804  FP: 230  
FN: 84    TP: 882  
```

#### Confusion Matrix (Row-Normalized)
```
TN: 0.8869 FP: 0.1131
FN: 0.0870 TP: 0.9130
```

### Label: Metabolic_Syndrome

- **Best Hyperparameters**: `max_depth=5, learning_rate=0.05, subsample=0.8, colsample_bytree=1.0, n_estimators_used=41`
- **Validation PR-AUC**: `0.4665`
- **Brier Score**: `0.1295`

#### Classification Report (Suppressed Predictions)
```
              precision    recall  f1-score   support

           0     0.9797    0.8002    0.8809      2768
           1     0.2517    0.8017    0.3831       232

    accuracy                         0.8003      3000
   macro avg     0.6157    0.8010    0.6320      3000
weighted avg     0.9234    0.8003    0.8424      3000

```

#### Confusion Matrix (Raw Counts)
```
TN: 2215  FP: 553  
FN: 46    TP: 186  
```

#### Confusion Matrix (Row-Normalized)
```
TN: 0.8002 FP: 0.1998
FN: 0.1983 TP: 0.8017
```

### Label: NAFLD

- **Best Hyperparameters**: `max_depth=5, learning_rate=0.1, subsample=0.8, colsample_bytree=1.0, n_estimators_used=53`
- **Validation PR-AUC**: `0.6534`
- **Brier Score**: `0.1325`

#### Classification Report (Suppressed Predictions)
```
              precision    recall  f1-score   support

           0     0.9696    0.7910    0.8713      2584
           1     0.3946    0.8462    0.5382       416

    accuracy                         0.7987      3000
   macro avg     0.6821    0.8186    0.7047      3000
weighted avg     0.8899    0.7987    0.8251      3000

```

#### Confusion Matrix (Raw Counts)
```
TN: 2044  FP: 540  
FN: 64    TP: 352  
```

#### Confusion Matrix (Row-Normalized)
```
TN: 0.7910 FP: 0.2090
FN: 0.1538 TP: 0.8462
```
