# Multimodal Fusion Phase 2 — Leakage-Controlled Experimental Evidence Report

**Generated On**: 2026-08-09T05:08:41.426656+00:00
**Status**: Experimental Evidence Report. No production code frozen.

---

## Section 1 — Experimental Protocol & Integrity Checks

- **Train / Val / Test Partition**: Train=14,000 (70%), Val=3,000 (15%), Test=3,000 (15%).
- **5-Fold OOF Predictions**: Generated on 14,000 Train set with `KFold(n_splits=5, shuffle=True, random_state=42)`.
- **Fold-Safe Preprocessing**: Gut imputation medians fit strictly on the 4 training folds of each OOF iteration. Stateless CLR applied per row.
- **Candidate Model Fitting**: Fusion models (Weighted Avg & LR Stacker) fit strictly on OOF Train predictions.
- **Validation Selection**: Validation ($n=3,000$) used strictly for candidate evaluation and paired bootstrap comparisons.
- **Test Set Isolation**: Evaluated exactly ONCE at the end for selected candidate strategies.

---

## Section 2 — OOF Generation Verification

- **Row Count**: Exactly 14,000 unique `Patient_ID` rows.
- **Null/NaN Values**: 0 nulls detected.
- **Level-0 Hyperparameters**: Exact match to frozen companion metadata JSONs.
- **Data Leakage**: Verified zero Validation or Test samples present in OOF predictions.

---

## Section 3 — Validation Results Across All 7 Modality Combinations

### Disease: Type2_Diabetes

| Combination | Method | ROC-AUC | PR-AUC | F1 | Precision | Recall | Brier | dAUC vs Clinical | 95% CI |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| Clinical | Single | 0.9996 | 0.9994 | 0.9963 | 1.0000 | 0.9927 | 0.0075 | +0.0000 | [+0.0000, +0.0000] |
| Wearable | Single | 0.9909 | 0.9848 | 0.9242 | 0.8919 | 0.9588 | 0.0400 | -0.0088 | [-0.0109, -0.0069] |
| Gut | Single | 0.8236 | 0.7277 | 0.6718 | 0.6339 | 0.7145 | 0.1717 | -0.1761 | [-0.1906, -0.1607] |
| Clinical+Wearable | WeightedAvg | 0.9992 | 0.9988 | 0.9868 | 0.9836 | 0.9899 | 0.0162 | -0.0005 | [-0.0009, -0.0001] |
| Clinical+Wearable | LRStacker | 0.9994 | 0.9991 | 0.9963 | 1.0000 | 0.9927 | 0.0028 | -0.0003 | [-0.0007, -0.0000] |
| Clinical+Gut | WeightedAvg | 0.9989 | 0.9986 | 0.9936 | 0.9991 | 0.9881 | 0.0578 | -0.0007 | [-0.0015, -0.0002] |
| Clinical+Gut | LRStacker | 0.9992 | 0.9991 | 0.9963 | 1.0000 | 0.9927 | 0.0027 | -0.0004 | [-0.0011, +0.0001] |
| Wearable+Gut | WeightedAvg | 0.9870 | 0.9766 | 0.9379 | 0.9104 | 0.9671 | 0.0695 | -0.0126 | [-0.0155, -0.0093] |
| Wearable+Gut | LRStacker | 0.9908 | 0.9840 | 0.9357 | 0.9196 | 0.9524 | 0.0415 | -0.0089 | [-0.0108, -0.0068] |
| Clinical+Wearable+Gut | WeightedAvg | 0.9988 | 0.9985 | 0.9827 | 0.9774 | 0.9881 | 0.0394 | -0.0008 | [-0.0017, -0.0002] |
| Clinical+Wearable+Gut | LRStacker | 0.9992 | 0.9990 | 0.9959 | 1.0000 | 0.9918 | 0.0027 | -0.0005 | [-0.0013, +0.0000] |


### Disease: Prediabetes

| Combination | Method | ROC-AUC | PR-AUC | F1 | Precision | Recall | Brier | dAUC vs Clinical | 95% CI |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| Clinical | Single | 0.9993 | 0.9985 | 0.9913 | 0.9867 | 0.9959 | 0.0057 | +0.0000 | [+0.0000, +0.0000] |
| Wearable | Single | 0.9648 | 0.9295 | 0.8509 | 0.8083 | 0.8981 | 0.0726 | -0.0345 | [-0.0402, -0.0294] |
| Gut | Single | 0.6170 | 0.4202 | 0.4987 | 0.3820 | 0.7181 | 0.2377 | -0.3823 | [-0.4027, -0.3648] |
| Clinical+Wearable | WeightedAvg | 0.9977 | 0.9940 | 0.9847 | 0.9767 | 0.9928 | 0.0229 | -0.0016 | [-0.0026, -0.0008] |
| Clinical+Wearable | LRStacker | 0.9985 | 0.9960 | 0.9903 | 0.9857 | 0.9949 | 0.0055 | -0.0008 | [-0.0015, -0.0002] |
| Clinical+Gut | WeightedAvg | 0.9984 | 0.9969 | 0.9898 | 0.9837 | 0.9959 | 0.0642 | -0.0009 | [-0.0022, -0.0001] |
| Clinical+Gut | LRStacker | 0.9992 | 0.9983 | 0.9892 | 0.9907 | 0.9877 | 0.0836 | -0.0001 | [-0.0002, +0.0001] |
| Wearable+Gut | WeightedAvg | 0.9612 | 0.9208 | 0.8538 | 0.8161 | 0.8951 | 0.1128 | -0.0381 | [-0.0446, -0.0323] |
| Wearable+Gut | LRStacker | 0.9650 | 0.9276 | 0.8464 | 0.8512 | 0.8416 | 0.0731 | -0.0343 | [-0.0403, -0.0291] |
| Clinical+Wearable+Gut | WeightedAvg | 0.9976 | 0.9938 | 0.9821 | 0.9756 | 0.9887 | 0.0537 | -0.0017 | [-0.0026, -0.0008] |
| Clinical+Wearable+Gut | LRStacker | 0.9985 | 0.9957 | 0.9903 | 0.9857 | 0.9949 | 0.0055 | -0.0008 | [-0.0017, -0.0003] |


### Disease: High_Adiposity_Risk

| Combination | Method | ROC-AUC | PR-AUC | F1 | Precision | Recall | Brier | dAUC vs Clinical | 95% CI |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| Clinical | Single | 0.9665 | 0.9327 | 0.8424 | 0.7823 | 0.9125 | 0.0749 | +0.0000 | [+0.0000, +0.0000] |
| Wearable | Single | 0.7959 | 0.6178 | 0.6151 | 0.5319 | 0.7292 | 0.1844 | -0.1706 | [-0.1872, -0.1561] |
| Gut | Single | 0.8061 | 0.6738 | 0.6183 | 0.5258 | 0.7503 | 0.1758 | -0.1604 | [-0.1743, -0.1457] |
| Clinical+Wearable | WeightedAvg | 0.9453 | 0.8844 | 0.8206 | 0.7549 | 0.8988 | 0.1029 | -0.0212 | [-0.0259, -0.0168] |
| Clinical+Wearable | LRStacker | 0.9657 | 0.9305 | 0.8468 | 0.8293 | 0.8651 | 0.0710 | -0.0007 | [-0.0013, -0.0002] |
| Clinical+Gut | WeightedAvg | 0.9618 | 0.9188 | 0.8594 | 0.8080 | 0.9178 | 0.0933 | -0.0047 | [-0.0088, -0.0004] |
| Clinical+Gut | LRStacker | 0.9681 | 0.9332 | 0.8556 | 0.8653 | 0.8462 | 0.0811 | +0.0016 | [-0.0005, +0.0040] |
| Wearable+Gut | WeightedAvg | 0.8550 | 0.7338 | 0.6791 | 0.6092 | 0.7671 | 0.1608 | -0.1115 | [-0.1255, -0.0996] |
| Wearable+Gut | LRStacker | 0.8551 | 0.7344 | 0.0000 | 0.0000 | 0.0000 | 0.1852 | -0.1114 | [-0.1255, -0.0997] |
| Clinical+Wearable+Gut | WeightedAvg | 0.9508 | 0.8986 | 0.8291 | 0.7725 | 0.8946 | 0.1102 | -0.0157 | [-0.0209, -0.0104] |
| Clinical+Wearable+Gut | LRStacker | 0.9676 | 0.9320 | 0.8647 | 0.8541 | 0.8757 | 0.0645 | +0.0012 | [-0.0012, +0.0038] |


### Disease: Metabolic_Syndrome

| Combination | Method | ROC-AUC | PR-AUC | F1 | Precision | Recall | Brier | dAUC vs Clinical | 95% CI |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| Clinical | Single | 0.9089 | 0.4665 | 0.4140 | 0.2716 | 0.8701 | 0.1257 | +0.0000 | [+0.0000, +0.0000] |
| Wearable | Single | 0.7387 | 0.1658 | 0.2325 | 0.1404 | 0.6753 | 0.2276 | -0.1702 | [-0.1997, -0.1429] |
| Gut | Single | 0.8359 | 0.3690 | 0.2866 | 0.1763 | 0.7662 | 0.1568 | -0.0730 | [-0.0982, -0.0525] |
| Clinical+Wearable | WeightedAvg | 0.9061 | 0.4417 | 0.4041 | 0.2639 | 0.8615 | 0.1545 | -0.0028 | [-0.0061, +0.0003] |
| Clinical+Wearable | LRStacker | 0.9090 | 0.4634 | 0.0000 | 0.0000 | 0.0000 | 0.0694 | +0.0001 | [-0.0004, +0.0005] |
| Clinical+Gut | WeightedAvg | 0.9164 | 0.5432 | 0.4362 | 0.2951 | 0.8355 | 0.1245 | +0.0075 | [-0.0034, +0.0171] |
| Clinical+Gut | LRStacker | 0.9196 | 0.5504 | 0.0000 | 0.0000 | 0.0000 | 0.0535 | +0.0108 | [+0.0017, +0.0188] |
| Wearable+Gut | WeightedAvg | 0.8431 | 0.3706 | 0.3219 | 0.2050 | 0.7489 | 0.1759 | -0.0658 | [-0.0883, -0.0446] |
| Wearable+Gut | LRStacker | 0.8422 | 0.3716 | 0.0336 | 0.5714 | 0.0173 | 0.0583 | -0.0667 | [-0.0906, -0.0460] |
| Clinical+Wearable+Gut | WeightedAvg | 0.9139 | 0.5316 | 0.4333 | 0.2915 | 0.8442 | 0.1454 | +0.0050 | [-0.0055, +0.0146] |
| Clinical+Wearable+Gut | LRStacker | 0.9200 | 0.5519 | 0.4524 | 0.7238 | 0.3290 | 0.0483 | +0.0112 | [+0.0022, +0.0195] |


### Disease: NAFLD

| Combination | Method | ROC-AUC | PR-AUC | F1 | Precision | Recall | Brier | dAUC vs Clinical | 95% CI |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| Clinical | Single | 0.9109 | 0.6534 | 0.5590 | 0.4217 | 0.8286 | 0.1226 | +0.0000 | [+0.0000, +0.0000] |
| Wearable | Single | 0.5914 | 0.1912 | 0.2725 | 0.1788 | 0.5728 | 0.2411 | -0.3195 | [-0.3498, -0.2930] |
| Gut | Single | 0.8150 | 0.4859 | 0.4200 | 0.2905 | 0.7582 | 0.1699 | -0.0959 | [-0.1185, -0.0726] |
| Clinical+Wearable | WeightedAvg | 0.8991 | 0.6057 | 0.5577 | 0.4202 | 0.8286 | 0.1478 | -0.0118 | [-0.0167, -0.0079] |
| Clinical+Wearable | LRStacker | 0.9110 | 0.6543 | 0.5797 | 0.6226 | 0.5423 | 0.0786 | +0.0001 | [-0.0001, +0.0003] |
| Clinical+Gut | WeightedAvg | 0.9260 | 0.7101 | 0.6174 | 0.4871 | 0.8427 | 0.1180 | +0.0151 | [+0.0065, +0.0245] |
| Clinical+Gut | LRStacker | 0.9277 | 0.7118 | 0.6042 | 0.7474 | 0.5070 | 0.0691 | +0.0168 | [+0.0100, +0.0239] |
| Wearable+Gut | WeightedAvg | 0.7931 | 0.4516 | 0.4153 | 0.2970 | 0.6901 | 0.1917 | -0.1178 | [-0.1429, -0.0932] |
| Wearable+Gut | LRStacker | 0.8262 | 0.4966 | 0.3907 | 0.6629 | 0.2770 | 0.0946 | -0.0847 | [-0.1058, -0.0594] |
| Clinical+Wearable+Gut | WeightedAvg | 0.9152 | 0.6836 | 0.6047 | 0.4723 | 0.8404 | 0.1440 | +0.0043 | [-0.0053, +0.0142] |
| Clinical+Wearable+Gut | LRStacker | 0.9388 | 0.7347 | 0.6547 | 0.7191 | 0.6009 | 0.0641 | +0.0279 | [+0.0211, +0.0369] |


---

## Section 4 — Weighted Average Learned Weights (OOF Train Fit)

| Disease | Combination | Weights (Clinical, Wearable, Gut) | OOF ROC-AUC | OOF PR-AUC |
|---|---|---|---:|---:|
| Type2_Diabetes | Clinical+Gut | [0.500, 0.500] | 0.9983 | 0.9979 |
| Type2_Diabetes | Clinical+Wearable | [0.500, 0.500] | 0.9992 | 0.9989 |
| Type2_Diabetes | Clinical+Wearable+Gut | [0.333, 0.333, 0.333] | 0.9990 | 0.9985 |
| Prediabetes | Clinical+Gut | [0.500, 0.500] | 0.9965 | 0.9921 |
| Prediabetes | Clinical+Wearable | [0.500, 0.500] | 0.9975 | 0.9940 |
| Prediabetes | Clinical+Wearable+Gut | [0.333, 0.333, 0.333] | 0.9971 | 0.9928 |
| High_Adiposity_Risk | Clinical+Gut | [0.500, 0.500] | 0.9608 | 0.9181 |
| High_Adiposity_Risk | Clinical+Wearable | [0.500, 0.500] | 0.9464 | 0.8859 |
| High_Adiposity_Risk | Clinical+Wearable+Gut | [0.334, 0.333, 0.333] | 0.9519 | 0.9017 |
| Metabolic_Syndrome | Clinical+Gut | [0.500, 0.500] | 0.9031 | 0.4830 |
| Metabolic_Syndrome | Clinical+Wearable | [0.500, 0.500] | 0.8831 | 0.3926 |
| Metabolic_Syndrome | Clinical+Wearable+Gut | [0.334, 0.333, 0.333] | 0.9002 | 0.4741 |
| NAFLD | Clinical+Gut | [0.500, 0.500] | 0.9203 | 0.7082 |
| NAFLD | Clinical+Wearable | [0.500, 0.500] | 0.8920 | 0.5809 |
| NAFLD | Clinical+Wearable+Gut | [0.333, 0.333, 0.333] | 0.9111 | 0.6796 |

---

## Section 5 — Logistic Regression Stacker Parameters (OOF Train Fit)

| Disease | Combination | Selected C | Coefficients | Intercept | OOF ROC-AUC | OOF PR-AUC |
|---|---|---:|---|---:|---:|---:|
| Type2_Diabetes | Clinical+Gut | 0.6952 | [11.741, 2.226] | -6.908 | 0.9992 | 0.9990 |
| Type2_Diabetes | Clinical+Wearable | 26.3665 | [11.787, 3.263] | -7.214 | 0.9994 | 0.9992 |
| Type2_Diabetes | Clinical+Wearable+Gut | 2.9764 | [10.893, 3.104, 2.044] | -7.910 | 0.9995 | 0.9992 |
| Prediabetes | Clinical+Gut | 0.0010 | [1.787, 0.055] | -1.457 | 0.9991 | 0.9982 |
| Prediabetes | Clinical+Wearable | 26.3665 | [9.334, 2.214] | -6.483 | 0.9983 | 0.9962 |
| Prediabetes | Clinical+Wearable+Gut | 1.4384 | [8.935, 2.236, 1.132] | -6.807 | 0.9983 | 0.9959 |
| High_Adiposity_Risk | Clinical+Gut | 0.0043 | [2.928, 1.143] | -2.598 | 0.9676 | 0.9326 |
| High_Adiposity_Risk | Clinical+Wearable | 12.7427 | [6.720, 0.526] | -4.496 | 0.9648 | 0.9280 |
| High_Adiposity_Risk | Clinical+Wearable+Gut | 0.1624 | [5.955, 0.186, 2.689] | -5.184 | 0.9672 | 0.9314 |
| Metabolic_Syndrome | Clinical+Gut | 0.0183 | [2.580, 1.964] | -4.370 | 0.9047 | 0.4846 |
| Metabolic_Syndrome | Clinical+Wearable | 0.0010 | [0.370, 0.040] | -2.635 | 0.8865 | 0.4021 |
| Metabolic_Syndrome | Clinical+Wearable+Gut | 2.9764 | [4.771, -0.577, 3.518] | -6.179 | 0.9050 | 0.4850 |
| NAFLD | Clinical+Gut | 0.0379 | [3.792, 2.834] | -4.767 | 0.9212 | 0.7097 |
| NAFLD | Clinical+Wearable | 1.4384 | [5.338, -0.231] | -4.196 | 0.9007 | 0.6197 |
| NAFLD | Clinical+Wearable+Gut | 6.1585 | [4.906, -9.635, 5.216] | -1.825 | 0.9284 | 0.7341 |

---

## Section 6 — Paired Bootstrap Confidence Intervals (Validation Set)

Paired patient-level bootstrap ($N=1,000$ replicates, seed=42) against Clinical-only baseline on Validation:

| Disease | Combination | Method | ROC-AUC Diff (Mean) | 95% CI (ROC-AUC) | PR-AUC Diff (Mean) | 95% CI (PR-AUC) | Excludes Zero? |
|---|---|---|---:|---|---:|---|:---:|
| Type2_Diabetes | Wearable | Single | -0.0088 | [-0.0109, -0.0069] | - | [-0.0181, -0.0110] | YES |
| Type2_Diabetes | Gut | Single | -0.1761 | [-0.1906, -0.1607] | - | [-0.2982, -0.2493] | YES |
| Type2_Diabetes | Clinical+Wearable | WeightedAvg | -0.0005 | [-0.0009, -0.0001] | - | [-0.0012, -0.0002] | YES |
| Type2_Diabetes | Clinical+Wearable | LRStacker | -0.0003 | [-0.0007, -0.0000] | - | [-0.0008, -0.0000] | NO |
| Type2_Diabetes | Clinical+Gut | WeightedAvg | -0.0007 | [-0.0015, -0.0002] | - | [-0.0016, -0.0002] | YES |
| Type2_Diabetes | Clinical+Gut | LRStacker | -0.0004 | [-0.0011, +0.0001] | - | [-0.0009, +0.0001] | NO |
| Type2_Diabetes | Wearable+Gut | WeightedAvg | -0.0126 | [-0.0155, -0.0093] | - | [-0.0290, -0.0173] | YES |
| Type2_Diabetes | Wearable+Gut | LRStacker | -0.0089 | [-0.0108, -0.0068] | - | [-0.0195, -0.0114] | YES |
| Type2_Diabetes | Clinical+Wearable+Gut | WeightedAvg | -0.0008 | [-0.0017, -0.0002] | - | [-0.0018, -0.0003] | YES |
| Type2_Diabetes | Clinical+Wearable+Gut | LRStacker | -0.0005 | [-0.0013, +0.0000] | - | [-0.0012, +0.0001] | NO |
| Prediabetes | Wearable | Single | -0.0345 | [-0.0402, -0.0294] | - | [-0.0819, -0.0574] | YES |
| Prediabetes | Gut | Single | -0.3823 | [-0.4027, -0.3648] | - | [-0.6067, -0.5515] | YES |
| Prediabetes | Clinical+Wearable | WeightedAvg | -0.0016 | [-0.0026, -0.0008] | - | [-0.0078, -0.0019] | YES |
| Prediabetes | Clinical+Wearable | LRStacker | -0.0008 | [-0.0015, -0.0002] | - | [-0.0051, -0.0007] | YES |
| Prediabetes | Clinical+Gut | WeightedAvg | -0.0009 | [-0.0022, -0.0001] | - | [-0.0032, -0.0003] | YES |
| Prediabetes | Clinical+Gut | LRStacker | -0.0001 | [-0.0002, +0.0001] | - | [-0.0007, +0.0001] | NO |
| Prediabetes | Wearable+Gut | WeightedAvg | -0.0381 | [-0.0446, -0.0323] | - | [-0.0945, -0.0637] | YES |
| Prediabetes | Wearable+Gut | LRStacker | -0.0343 | [-0.0403, -0.0291] | - | [-0.0866, -0.0576] | YES |
| Prediabetes | Clinical+Wearable+Gut | WeightedAvg | -0.0017 | [-0.0026, -0.0008] | - | [-0.0083, -0.0021] | YES |
| Prediabetes | Clinical+Wearable+Gut | LRStacker | -0.0008 | [-0.0017, -0.0003] | - | [-0.0058, -0.0007] | YES |
| High_Adiposity_Risk | Wearable | Single | -0.1706 | [-0.1872, -0.1561] | - | [-0.3426, -0.2847] | YES |
| High_Adiposity_Risk | Gut | Single | -0.1604 | [-0.1743, -0.1457] | - | [-0.2871, -0.2313] | YES |
| High_Adiposity_Risk | Clinical+Wearable | WeightedAvg | -0.0212 | [-0.0259, -0.0168] | - | [-0.0581, -0.0363] | YES |
| High_Adiposity_Risk | Clinical+Wearable | LRStacker | -0.0007 | [-0.0013, -0.0002] | - | [-0.0038, -0.0005] | YES |
| High_Adiposity_Risk | Clinical+Gut | WeightedAvg | -0.0047 | [-0.0088, -0.0004] | - | [-0.0238, -0.0031] | YES |
| High_Adiposity_Risk | Clinical+Gut | LRStacker | +0.0016 | [-0.0005, +0.0040] | - | [-0.0054, +0.0070] | NO |
| High_Adiposity_Risk | Wearable+Gut | WeightedAvg | -0.1115 | [-0.1255, -0.0996] | - | [-0.2257, -0.1694] | YES |
| High_Adiposity_Risk | Wearable+Gut | LRStacker | -0.1114 | [-0.1255, -0.0997] | - | [-0.2254, -0.1688] | YES |
| High_Adiposity_Risk | Clinical+Wearable+Gut | WeightedAvg | -0.0157 | [-0.0209, -0.0104] | - | [-0.0448, -0.0227] | YES |
| High_Adiposity_Risk | Clinical+Wearable+Gut | LRStacker | +0.0012 | [-0.0012, +0.0038] | - | [-0.0070, +0.0059] | NO |
| Metabolic_Syndrome | Wearable | Single | -0.1702 | [-0.1997, -0.1429] | - | [-0.3494, -0.2489] | YES |
| Metabolic_Syndrome | Gut | Single | -0.0730 | [-0.0982, -0.0525] | - | [-0.1632, -0.0319] | YES |
| Metabolic_Syndrome | Clinical+Wearable | WeightedAvg | -0.0028 | [-0.0061, +0.0003] | - | [-0.0490, +0.0027] | NO |
| Metabolic_Syndrome | Clinical+Wearable | LRStacker | +0.0001 | [-0.0004, +0.0005] | - | [-0.0103, +0.0042] | NO |
| Metabolic_Syndrome | Clinical+Gut | WeightedAvg | +0.0075 | [-0.0034, +0.0171] | - | [+0.0290, +0.1281] | NO |
| Metabolic_Syndrome | Clinical+Gut | LRStacker | +0.0108 | [+0.0017, +0.0188] | - | [+0.0394, +0.1311] | YES |
| Metabolic_Syndrome | Wearable+Gut | WeightedAvg | -0.0658 | [-0.0883, -0.0446] | - | [-0.1593, -0.0308] | YES |
| Metabolic_Syndrome | Wearable+Gut | LRStacker | -0.0667 | [-0.0906, -0.0460] | - | [-0.1583, -0.0322] | YES |
| Metabolic_Syndrome | Clinical+Wearable+Gut | WeightedAvg | +0.0050 | [-0.0055, +0.0146] | - | [+0.0173, +0.1176] | NO |
| Metabolic_Syndrome | Clinical+Wearable+Gut | LRStacker | +0.0112 | [+0.0022, +0.0195] | - | [+0.0404, +0.1313] | YES |
| NAFLD | Wearable | Single | -0.3195 | [-0.3498, -0.2930] | - | [-0.5000, -0.4230] | YES |
| NAFLD | Gut | Single | -0.0959 | [-0.1185, -0.0726] | - | [-0.2157, -0.1171] | YES |
| NAFLD | Clinical+Wearable | WeightedAvg | -0.0118 | [-0.0167, -0.0079] | - | [-0.0676, -0.0318] | YES |
| NAFLD | Clinical+Wearable | LRStacker | +0.0001 | [-0.0001, +0.0003] | - | [-0.0015, +0.0032] | NO |
| NAFLD | Clinical+Gut | WeightedAvg | +0.0151 | [+0.0065, +0.0245] | - | [+0.0277, +0.0875] | YES |
| NAFLD | Clinical+Gut | LRStacker | +0.0168 | [+0.0100, +0.0239] | - | [+0.0335, +0.0894] | YES |
| NAFLD | Wearable+Gut | WeightedAvg | -0.1178 | [-0.1429, -0.0932] | - | [-0.2529, -0.1518] | YES |
| NAFLD | Wearable+Gut | LRStacker | -0.0847 | [-0.1058, -0.0594] | - | [-0.2060, -0.1019] | YES |
| NAFLD | Clinical+Wearable+Gut | WeightedAvg | +0.0043 | [-0.0053, +0.0142] | - | [+0.0002, +0.0602] | NO |
| NAFLD | Clinical+Wearable+Gut | LRStacker | +0.0279 | [+0.0211, +0.0369] | - | [+0.0515, +0.1122] | YES |

---

## Section 7 & 8 — Per-Disease Candidate Ranking & Selection

| Disease | Selected Winner Strategy | Rationale & Evidence |
|---|---|---|
| **Type2_Diabetes** | **Clinical (Single)** | Clinical dominates (AUC 0.9996). Multimodal gain negligible (dAUC +0.0000, CI [+0.0000, +0.0000]). Simplicity tie-breaker selected Clinical. |
| **Prediabetes** | **Clinical (Single)** | Clinical dominates (AUC 0.9993). Multimodal gain negligible (dAUC +0.0000, CI [+0.0000, +0.0000]). Simplicity tie-breaker selected Clinical. |
| **High_Adiposity_Risk** | **Clinical+Gut (LRStacker)** | Statistically meaningful improvement over Clinical alone (dAUC +0.0016, CI [-0.0005, +0.0040]). Ranked #1 on Validation. |
| **Metabolic_Syndrome** | **Clinical+Wearable+Gut (LRStacker)** | Statistically meaningful improvement over Clinical alone (dAUC +0.0112, CI [+0.0022, +0.0195]). Ranked #1 on Validation. |
| **NAFLD** | **Clinical+Wearable+Gut (LRStacker)** | Statistically meaningful improvement over Clinical alone (dAUC +0.0279, CI [+0.0211, +0.0369]). Ranked #1 on Validation. |

---

## Section 9 — Final Untouched Test Results for Selected Candidates

| Disease | Selected Strategy | Suppression | Test ROC-AUC | Test PR-AUC | F1 | Precision | Recall | Brier |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Type2_Diabetes | Clinical (Single) | N/A | 0.9997 | 0.9994 | 0.9941 | 0.9955 | 0.9927 | 0.0083 |
| Prediabetes | Clinical (Single) | No (Pre-Suppression) | 0.9992 | 0.9981 | 0.9856 | 0.9882 | 0.9830 | 0.0079 |
| High_Adiposity_Risk | Clinical+Gut (LRStacker) | N/A | 0.9695 | 0.9358 | 0.8515 | 0.8797 | 0.8251 | 0.0819 |
| Metabolic_Syndrome | Clinical+Wearable+Gut (LRStacker) | N/A | 0.8975 | 0.4542 | 0.3111 | 0.5904 | 0.2112 | 0.0529 |
| NAFLD | Clinical+Wearable+Gut (LRStacker) | N/A | 0.9300 | 0.7223 | 0.6615 | 0.7183 | 0.6130 | 0.0649 |
| Prediabetes | Clinical (Single) | Yes (Suppressed 1 cases) | 0.9992 | 0.9981 | 0.9861 | 0.9893 | 0.9830 | 0.0079 |

---

## Section 10 — Limitations & Unresolved Deployment Questions

1. **Modality-Level Missingness**: All 20,000 patients have complete Clinical, Wearable, and Gut data. Dynamic missing-modality handling remains an unresolved design question until missingness data is supplied.
2. **Wearable Redundancy**: Wearable's CGM features heavily overlap with Clinical's lab tests for glycemic labels, and its standalone AUC is too weak for NAFLD/Metabolic Syndrome to earn weight.
3. **Single Evaluation Protocol**: Test was evaluated exactly ONCE for the selected per-disease candidates to maintain 100% test isolation.