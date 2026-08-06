# Wearable Metabolic Disease Prediction Model (v3) — Evaluation Report

**Generated On**: 2026-08-04T09:48:52.543699+00:00 | **Algorithm**: XGBOOST

## Executive Summary (XGBoost Test Performance - Suppressed Predictions)

| Label | ROC-AUC | PR-AUC | F1 | Precision | Recall |
|---|---|---|---|---|---|
| **Type2_Diabetes** | 0.9915 | 0.9859 | 0.9280 | 0.8940 | 0.9646 |
| **Prediabetes** | 0.9623 | 0.9229 | 0.8195 | 0.8252 | 0.8138 |
| **High_Adiposity_Risk** | 0.8106 | 0.6432 | 0.6458 | 0.5566 | 0.7692 |
| **Metabolic_Syndrome** | 0.7274 | 0.1724 | 0.2433 | 0.1477 | 0.6897 |
| **NAFLD** | 0.6009 | 0.1796 | 0.2703 | 0.1758 | 0.5841 |

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
| **Type2_Diabetes** | Baseline (LogReg) | 0.9916 | 0.9860 | 0.9283 | 0.8961 | 0.9628 | 0.0383 |
| **Type2_Diabetes** | **XGBoost (v3)** | **0.9915** | **0.9859** | **0.9280** | **0.8940** | **0.9646** | **0.0385** |
| **Prediabetes** | Baseline (LogReg) | 0.5899 | 0.3591 | 0.4572 | 0.3697 | 0.5989 | 0.2428 |
| **Prediabetes** | **XGBoost (v3)** | **0.9623** | **0.9229** | **0.8195** | **0.8252** | **0.8138** | **0.0781** |
| **High_Adiposity_Risk** | Baseline (LogReg) | 0.8156 | 0.6443 | 0.6424 | 0.5570 | 0.7588 | 0.1789 |
| **High_Adiposity_Risk** | **XGBoost (v3)** | **0.8106** | **0.6432** | **0.6458** | **0.5566** | **0.7692** | **0.1797** |
| **Metabolic_Syndrome** | Baseline (LogReg) | 0.7394 | 0.1749 | 0.2410 | 0.1458 | 0.6940 | 0.2100 |
| **Metabolic_Syndrome** | **XGBoost (v3)** | **0.7274** | **0.1724** | **0.2433** | **0.1477** | **0.6897** | **0.2275** |
| **NAFLD** | Baseline (LogReg) | 0.5908 | 0.1719 | 0.2637 | 0.1709 | 0.5769 | 0.2437 |
| **NAFLD** | **XGBoost (v3)** | **0.6009** | **0.1796** | **0.2703** | **0.1758** | **0.5841** | **0.2416** |

---

## Mutual Exclusivity Suppression Rule Impact

Suppression Rule: If `Type2_Diabetes` prediction = 1, `Prediabetes` prediction is forced to 0 (raw probability untouched).

| Metric | Prediabetes (Raw) | Prediabetes (Suppressed) | Change |
|---|---|---|---|
| Precision | 0.7801 | 0.8252 | +0.0451 |
| Recall | 0.8947 | 0.8138 | -0.0809 |
| F1 Score | 0.8335 | 0.8195 | -0.0140 |
| Total Suppressed Patients | - | 151 | - |

---

## Detailed Per-Label Classification Reports & Confusion Matrices

### Label: Type2_Diabetes

- **Best Hyperparameters**: `max_depth=3, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, n_estimators_used=94`
- **Validation PR-AUC**: `0.9848`
- **Brier Score**: `0.0385`
- **Calibration Curve Plot**: `reports/calibration_Type2_Diabetes.png`

#### Classification Report (Suppressed Predictions)
```
              precision    recall  f1-score   support

           0     0.9785    0.9336    0.9555      1898
           1     0.8940    0.9646    0.9280      1102

    accuracy                         0.9450      3000
   macro avg     0.9362    0.9491    0.9417      3000
weighted avg     0.9474    0.9450    0.9454      3000

```

#### Confusion Matrix (Raw Counts)
```
TN: 1772  FP: 126  
FN: 39    TP: 1063 
```

#### Confusion Matrix (Row-Normalized)
```
TN: 0.9336 FP: 0.0664
FN: 0.0354 TP: 0.9646
```

### Label: Prediabetes

- **Best Hyperparameters**: `max_depth=7, learning_rate=0.05, subsample=1.0, colsample_bytree=1.0, n_estimators_used=76`
- **Validation PR-AUC**: `0.9295`
- **Brier Score**: `0.0781`
- **Calibration Curve Plot**: `reports/calibration_Prediabetes.png`

#### Classification Report (Suppressed Predictions)
```
              precision    recall  f1-score   support

           0     0.9156    0.9214    0.9185      2060
           1     0.8252    0.8138    0.8195       940

    accuracy                         0.8877      3000
   macro avg     0.8704    0.8676    0.8690      3000
weighted avg     0.8873    0.8877    0.8875      3000

```

#### Confusion Matrix (Raw Counts)
```
TN: 1898  FP: 162  
FN: 175   TP: 765  
```

#### Confusion Matrix (Row-Normalized)
```
TN: 0.9214 FP: 0.0786
FN: 0.1862 TP: 0.8138
```

### Label: High_Adiposity_Risk

- **Best Hyperparameters**: `max_depth=3, learning_rate=0.1, subsample=1.0, colsample_bytree=0.8, n_estimators_used=168`
- **Validation PR-AUC**: `0.6178`
- **Brier Score**: `0.1797`
- **Calibration Curve Plot**: `reports/calibration_High_Adiposity_Risk.png`

#### Classification Report (Suppressed Predictions)
```
              precision    recall  f1-score   support

           0     0.8661    0.7089    0.7797      2034
           1     0.5566    0.7692    0.6458       966

    accuracy                         0.7283      3000
   macro avg     0.7113    0.7390    0.7127      3000
weighted avg     0.7664    0.7283    0.7366      3000

```

#### Confusion Matrix (Raw Counts)
```
TN: 1442  FP: 592  
FN: 223   TP: 743  
```

#### Confusion Matrix (Row-Normalized)
```
TN: 0.7089 FP: 0.2911
FN: 0.2308 TP: 0.7692
```

### Label: Metabolic_Syndrome

- **Best Hyperparameters**: `max_depth=5, learning_rate=0.05, subsample=1.0, colsample_bytree=1.0, n_estimators_used=6`
- **Validation PR-AUC**: `0.1658`
- **Brier Score**: `0.2275`
- **Calibration Curve Plot**: `reports/calibration_Metabolic_Syndrome.png`

#### Classification Report (Suppressed Predictions)
```
              precision    recall  f1-score   support

           0     0.9624    0.6665    0.7876      2768
           1     0.1477    0.6897    0.2433       232

    accuracy                         0.6683      3000
   macro avg     0.5551    0.6781    0.5155      3000
weighted avg     0.8994    0.6683    0.7455      3000

```

#### Confusion Matrix (Raw Counts)
```
TN: 1845  FP: 923  
FN: 72    TP: 160  
```

#### Confusion Matrix (Row-Normalized)
```
TN: 0.6665 FP: 0.3335
FN: 0.3103 TP: 0.6897
```

### Label: NAFLD

- **Best Hyperparameters**: `max_depth=3, learning_rate=0.05, subsample=0.8, colsample_bytree=1.0, n_estimators_used=28`
- **Validation PR-AUC**: `0.1912`
- **Brier Score**: `0.2416`
- **Calibration Curve Plot**: `reports/calibration_NAFLD.png`

#### Classification Report (Suppressed Predictions)
```
              precision    recall  f1-score   support

           0     0.8931    0.5592    0.6878      2584
           1     0.1758    0.5841    0.2703       416

    accuracy                         0.5627      3000
   macro avg     0.5345    0.5717    0.4790      3000
weighted avg     0.7936    0.5627    0.6299      3000

```

#### Confusion Matrix (Raw Counts)
```
TN: 1445  FP: 1139 
FN: 173   TP: 243  
```

#### Confusion Matrix (Row-Normalized)
```
TN: 0.5592 FP: 0.4408
FN: 0.4159 TP: 0.5841
```
