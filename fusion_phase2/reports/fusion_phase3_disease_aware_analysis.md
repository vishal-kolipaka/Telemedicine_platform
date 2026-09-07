# Fusion Phase 3 — Disease-Aware Fusion, Dominant Modality, Maximum Safeguard & Incremental Signal Analysis

**Date**: 2026-08-09T05:32:04.294049+00:00
**Status**: Research & Experimental Evidence Report. Architecture NOT frozen.

---

## Section 1 — Standalone Modality Performance by Disease (Validation Set, n=3,000)

| Disease | Modality | Rank | ROC-AUC | PR-AUC | F1 | Precision | Recall | Brier | Calib Slope | Calib Intercept |
|:---|:---|:---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Type2_Diabetes | Clinical | #1 | 0.9996 | 0.9994 | 0.9963 | 1.0000 | 0.9927 | 0.0075 | 2.9456 | 1.5692 |
| Type2_Diabetes | Wearable | #2 | 0.9909 | 0.9848 | 0.9242 | 0.8919 | 0.9588 | 0.0400 | 1.1447 | -0.7291 |
| Type2_Diabetes | Gut | #3 | 0.8236 | 0.7277 | 0.6718 | 0.6339 | 0.7145 | 0.1717 | 1.1516 | -0.5207 |
| Prediabetes | Clinical | #1 | 0.9993 | 0.9985 | 0.9913 | 0.9867 | 0.9959 | 0.0057 | 1.1700 | -0.8611 |
| Prediabetes | Wearable | #2 | 0.9648 | 0.9295 | 0.8509 | 0.8083 | 0.8981 | 0.0726 | 1.0471 | -0.5390 |
| Prediabetes | Gut | #3 | 0.6170 | 0.4202 | 0.4987 | 0.3820 | 0.7181 | 0.2377 | 1.3036 | -0.6921 |
| High_Adiposity_Risk | Clinical | #1 | 0.9665 | 0.9327 | 0.8424 | 0.7823 | 0.9125 | 0.0749 | 1.0700 | -0.7858 |
| High_Adiposity_Risk | Gut | #2 | 0.8061 | 0.6738 | 0.6183 | 0.5258 | 0.7503 | 0.1758 | 0.9954 | -0.7004 |
| High_Adiposity_Risk | Wearable | #3 | 0.7959 | 0.6178 | 0.6151 | 0.5319 | 0.7292 | 0.1844 | 0.9460 | -0.7309 |
| Metabolic_Syndrome | Clinical | #1 | 0.9089 | 0.4665 | 0.4140 | 0.2716 | 0.8701 | 0.1257 | 1.4259 | -2.4440 |
| Metabolic_Syndrome | Gut | #2 | 0.8359 | 0.3690 | 0.2866 | 0.1763 | 0.7662 | 0.1568 | 1.2336 | -2.3661 |
| Metabolic_Syndrome | Wearable | #3 | 0.7387 | 0.1658 | 0.2325 | 0.1404 | 0.6753 | 0.2276 | 4.1264 | -2.4463 |
| NAFLD | Clinical | #1 | 0.9109 | 0.6534 | 0.5590 | 0.4217 | 0.8286 | 0.1226 | 1.0029 | -1.6681 |
| NAFLD | Gut | #2 | 0.8150 | 0.4859 | 0.4200 | 0.2905 | 0.7582 | 0.1699 | 1.1547 | -1.7263 |
| NAFLD | Wearable | #3 | 0.5914 | 0.1912 | 0.2725 | 0.1788 | 0.5728 | 0.2411 | 1.2956 | -1.7765 |

---

## Section 2 — Incremental Modality Performance & Dominant Signal

Incremental ROC-AUC gain when adding a secondary or tertiary modality on top of existing modalities:

| Disease | Clinical AUC | Clin -> Clin+Gut (W) | Clin -> Clin+Gut (LR) | Clin -> Clin+Wear (W) | Gut -> Gut+Clin (W) | Clin+Gut -> Full (W) | Clin+Gut -> Full (LR) |
|:---|---:|---:|---:|---:|---:|---:|---:|
| Type2_Diabetes | 0.9996 | -0.0007 | -0.0004 | -0.0005 | +0.1753 | -0.0001 | -0.0001 |
| Prediabetes | 0.9993 | -0.0009 | -0.0001 | -0.0016 | +0.3814 | -0.0007 | -0.0008 |
| High_Adiposity_Risk | 0.9665 | -0.0047 | +0.0016 | -0.0212 | +0.1557 | -0.0110 | -0.0005 |
| Metabolic_Syndrome | 0.9089 | +0.0075 | +0.0108 | -0.0028 | +0.0805 | -0.0025 | +0.0004 |
| NAFLD | 0.9109 | +0.0151 | +0.0168 | -0.0118 | +0.1111 | -0.0108 | +0.0111 |

---

## Section 3 — Testing the 'Don't Reduce a Strong Output' Hypothesis

Distribution of probability difference `Fusion_P - Strongest_Modality_P` across Validation patients ($n=3,000$):

| Disease | Fusion Strategy | Mean Diff | Median Diff | Std Diff | % Decreased | % Increased | % |Diff| > 0.05 | % |Diff| > 0.10 |
|:---|:---|---:|---:|---:|---:|---:|---:|---:|
| Type2_Diabetes | Clinical+Gut LR | -0.2286 | -0.1244 | 0.2655 | 70.1% | 29.9% | 72.9% | 53.0% |
| Type2_Diabetes | Full Fusion LR | -0.2288 | -0.1262 | 0.2658 | 63.9% | 36.1% | 72.6% | 53.1% |
| Prediabetes | Clinical+Gut LR | -0.3369 | -0.3481 | 0.1089 | 99.4% | 0.6% | 98.6% | 96.6% |
| Prediabetes | Full Fusion LR | -0.3346 | -0.4460 | 0.2482 | 95.7% | 4.3% | 68.2% | 67.5% |
| High_Adiposity_Risk | Clinical+Gut LR | -0.2915 | -0.2661 | 0.1561 | 99.0% | 1.0% | 95.9% | 90.7% |
| High_Adiposity_Risk | Full Fusion LR | -0.2930 | -0.2537 | 0.2233 | 95.8% | 4.2% | 84.0% | 73.4% |
| Metabolic_Syndrome | Clinical+Gut LR | -0.4732 | -0.4631 | 0.0782 | 100.0% | 0.0% | 100.0% | 100.0% |
| Metabolic_Syndrome | Full Fusion LR | -0.4725 | -0.4686 | 0.0850 | 100.0% | 0.0% | 100.0% | 100.0% |
| NAFLD | Clinical+Gut LR | -0.4381 | -0.4413 | 0.1058 | 100.0% | 0.0% | 100.0% | 100.0% |
| NAFLD | Full Fusion LR | -0.4395 | -0.4577 | 0.1452 | 99.4% | 0.6% | 97.7% | 95.4% |

---

## Section 4 — Evaluation of the MAX Probability Strategy (`P_max = max(P_c, P_w, P_g)`)

| Disease | Strategy | ROC-AUC | PR-AUC | F1 | Precision | Recall | Brier | Calib Slope | Calib Intercept |
|:---|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| Type2_Diabetes | Clinical Single | 0.9996 | 0.9994 | 0.9963 | 1.0000 | 0.9927 | 0.0075 | 2.9456 | 1.5692 |
| Type2_Diabetes | P_max (max of 3) | 0.9964 | 0.9945 | 0.8022 | 0.6706 | 0.9982 | 0.1261 | 3.3314 | -6.7563 |
| Type2_Diabetes | Clin+Gut Weighted | 0.9989 | 0.9986 | 0.9936 | 0.9991 | 0.9881 | 0.0578 | 9.2090 | 0.1770 |
| Type2_Diabetes | Clin+Gut LRStacker | 0.9992 | 0.9991 | 0.9963 | 1.0000 | 0.9927 | 0.0027 | 1.6961 | 2.7821 |
| Type2_Diabetes | Full LRStacker | 0.9992 | 0.9990 | 0.9959 | 1.0000 | 0.9918 | 0.0027 | 1.2609 | 1.0344 |
| Prediabetes | Clinical Single | 0.9993 | 0.9985 | 0.9913 | 0.9867 | 0.9959 | 0.0057 | 1.1700 | -0.8611 |
| Prediabetes | P_max (max of 3) | 0.9978 | 0.9962 | 0.6183 | 0.4475 | 1.0000 | 0.1809 | 2.1682 | -5.8034 |
| Prediabetes | Clin+Gut Weighted | 0.9984 | 0.9969 | 0.9898 | 0.9837 | 0.9959 | 0.0642 | 5.3337 | -0.6899 |
| Prediabetes | Clin+Gut LRStacker | 0.9992 | 0.9983 | 0.9892 | 0.9907 | 0.9877 | 0.0836 | 6.3691 | 2.4548 |
| Prediabetes | Full LRStacker | 0.9985 | 0.9957 | 0.9903 | 0.9857 | 0.9949 | 0.0055 | 1.1283 | -0.2764 |
| High_Adiposity_Risk | Clinical Single | 0.9665 | 0.9327 | 0.8424 | 0.7823 | 0.9125 | 0.0749 | 1.0700 | -0.7858 |
| High_Adiposity_Risk | P_max (max of 3) | 0.9400 | 0.9030 | 0.6358 | 0.4713 | 0.9768 | 0.2035 | 1.6301 | -2.8584 |
| High_Adiposity_Risk | Clin+Gut Weighted | 0.9618 | 0.9188 | 0.8594 | 0.8080 | 0.9178 | 0.0933 | 2.3675 | -0.7244 |
| High_Adiposity_Risk | Clin+Gut LRStacker | 0.9681 | 0.9332 | 0.8556 | 0.8653 | 0.8462 | 0.0811 | 2.2824 | 0.4088 |
| High_Adiposity_Risk | Full LRStacker | 0.9676 | 0.9320 | 0.8647 | 0.8541 | 0.8757 | 0.0645 | 1.0962 | -0.0235 |
| Metabolic_Syndrome | Clinical Single | 0.9089 | 0.4665 | 0.4140 | 0.2716 | 0.8701 | 0.1257 | 1.4259 | -2.4440 |
| Metabolic_Syndrome | P_max (max of 3) | 0.8914 | 0.4605 | 0.2359 | 0.1343 | 0.9697 | 0.2816 | 2.2592 | -4.0389 |
| Metabolic_Syndrome | Clin+Gut Weighted | 0.9164 | 0.5432 | 0.4362 | 0.2951 | 0.8355 | 0.1245 | 2.0177 | -2.4093 |
| Metabolic_Syndrome | Clin+Gut LRStacker | 0.9196 | 0.5504 | 0.0000 | 0.0000 | 0.0000 | 0.0535 | 2.0306 | 1.7964 |
| Metabolic_Syndrome | Full LRStacker | 0.9200 | 0.5519 | 0.4524 | 0.7238 | 0.3290 | 0.0483 | 1.1225 | 0.1420 |
| NAFLD | Clinical Single | 0.9109 | 0.6534 | 0.5590 | 0.4217 | 0.8286 | 0.1226 | 1.0029 | -1.6681 |
| NAFLD | P_max (max of 3) | 0.8765 | 0.6494 | 0.3366 | 0.2053 | 0.9343 | 0.2848 | 1.8028 | -3.3699 |
| NAFLD | Clin+Gut Weighted | 0.9260 | 0.7101 | 0.6174 | 0.4871 | 0.8427 | 0.1180 | 2.0073 | -1.6777 |
| NAFLD | Clin+Gut LRStacker | 0.9277 | 0.7118 | 0.6042 | 0.7474 | 0.5070 | 0.0691 | 1.3564 | 0.2392 |
| NAFLD | Full LRStacker | 0.9388 | 0.7347 | 0.6547 | 0.7191 | 0.6009 | 0.0641 | 1.0923 | -0.0176 |

> **Diagnostic Finding on P_max**: Taking `P_max` consistently **worsens calibration** (Brier scores increase, calibration intercept shifts positive) and increases false positives compared to weighted averaging or Clinical passthrough. MAX is **not recommended** as a general fusion replacement.

---

## Section 5 — 'Best Available Modality' (Empirical Passthrough) Strategy

| Disease | Dominant Modality | Dominant Passthrough ROC-AUC | Dominant Passthrough PR-AUC | Clin+Gut LR ROC-AUC | Clin+Gut LR PR-AUC | Recommendation |
|:---|:---|---:|---:|---:|---:|:---|
| Type2_Diabetes | Clinical | 0.9996 | 0.9994 | 0.9992 | 0.9991 | Use Dominant Passthrough |
| Prediabetes | Clinical | 0.9993 | 0.9985 | 0.9992 | 0.9983 | Use Dominant Passthrough |
| High_Adiposity_Risk | Clinical | 0.9665 | 0.9327 | 0.9681 | 0.9332 | Use Dominant Passthrough |
| Metabolic_Syndrome | Clinical | 0.9089 | 0.4665 | 0.9196 | 0.5504 | Use Clin+Gut Fusion |
| NAFLD | Clinical | 0.9109 | 0.6534 | 0.9277 | 0.7118 | Use Clin+Gut Fusion |

---

## Section 6 — Dominant Modality + Small Wearable Contribution Strategies

| Disease | Strategy | ROC-AUC | PR-AUC | F1 | Brier |
|:---|:---|---:|---:|---:|---:|
| Metabolic_Syndrome | Strat A (0.50 C + 0.50 G) | 0.9164 | 0.5432 | 0.4362 | 0.1245 |
| Metabolic_Syndrome | Strat B (0.60 C + 0.40 G) | 0.9202 | 0.5507 | 0.4385 | 0.1220 |
| Metabolic_Syndrome | Strat C (0.70 C + 0.30 G) | 0.9205 | 0.5506 | 0.4307 | 0.1210 |
| Metabolic_Syndrome | Strat D (0.55 C + 0.35 G + 0.10 W) | 0.9200 | 0.5480 | 0.4380 | 0.1267 |
| Metabolic_Syndrome | Strat E (0.60 C + 0.30 G + 0.10 W) | 0.9204 | 0.5475 | 0.4391 | 0.1259 |
| Metabolic_Syndrome | Strat F (0.65 C + 0.25 G + 0.10 W) | 0.9199 | 0.5467 | 0.4243 | 0.1254 |
| Metabolic_Syndrome | Strat G (0.65 C + 0.30 G + 0.05 W) | 0.9206 | 0.5509 | 0.4326 | 0.1232 |
| Metabolic_Syndrome | Optimized Clin+Gut LR | 0.9196 | 0.5504 | 0.0000 | 0.0535 |
| NAFLD | Strat A (0.50 C + 0.50 G) | 0.9260 | 0.7100 | 0.6174 | 0.1180 |
| NAFLD | Strat B (0.60 C + 0.40 G) | 0.9278 | 0.7121 | 0.6088 | 0.1144 |
| NAFLD | Strat C (0.70 C + 0.30 G) | 0.9261 | 0.7082 | 0.5942 | 0.1130 |
| NAFLD | Strat D (0.55 C + 0.35 G + 0.10 W) | 0.9259 | 0.7064 | 0.6061 | 0.1198 |
| NAFLD | Strat E (0.60 C + 0.30 G + 0.10 W) | 0.9253 | 0.7052 | 0.5954 | 0.1185 |
| NAFLD | Strat F (0.65 C + 0.25 G + 0.10 W) | 0.9240 | 0.7023 | 0.5865 | 0.1177 |
| NAFLD | Strat G (0.65 C + 0.30 G + 0.05 W) | 0.9258 | 0.7068 | 0.5933 | 0.1154 |
| NAFLD | Optimized Clin+Gut LR | 0.9277 | 0.7118 | 0.6042 | 0.0691 |

---

## Section 7 — Confidence-Aware Dominant Modality Strategy

Rule: If `max_probability - second_highest_probability >= delta`, preserve max_probability; else use Clin+Gut LR Stacker.

| Disease | Delta Threshold | ROC-AUC | PR-AUC | F1 | Brier | % Preserved Dominant |
|:---|:---:|---:|---:|---:|---:|---:|
| Metabolic_Syndrome | delta = 0.05 | 0.7045 | 0.3419 | 0.2121 | 0.2528 | 83.7% |
| Metabolic_Syndrome | delta = 0.10 | 0.6390 | 0.2604 | 0.2052 | 0.2207 | 69.6% |
| Metabolic_Syndrome | delta = 0.15 | 0.5974 | 0.1850 | 0.1824 | 0.1918 | 56.8% |
| Metabolic_Syndrome | delta = 0.20 | 0.6154 | 0.1650 | 0.1684 | 0.1640 | 46.1% |
| NAFLD | delta = 0.05 | 0.8541 | 0.5984 | 0.3710 | 0.2549 | 83.7% |
| NAFLD | delta = 0.10 | 0.8369 | 0.5571 | 0.4090 | 0.2249 | 69.0% |
| NAFLD | delta = 0.15 | 0.8248 | 0.5178 | 0.4477 | 0.1954 | 55.8% |
| NAFLD | delta = 0.20 | 0.8223 | 0.4884 | 0.4770 | 0.1702 | 44.9% |

---

## Section 8 — Availability Scenario Analysis (Cases 1 through 7)

| Scenario | Disease | Candidate Strategy | ROC-AUC | PR-AUC | Brier | Evaluated Policy |
|:---|:---|:---|---:|---:|---:|:---|
| Case 1: Clin Only | Metabolic_Syndrome | Clinical Passthrough | 0.9089 | 0.4665 | 0.1257 | Pure Single Modality |
| Case 2: Gut Only | Metabolic_Syndrome | Gut Passthrough | 0.8359 | 0.3690 | 0.1568 | Pure Single Modality |
| Case 3: Wear Only | Metabolic_Syndrome | Wearable Passthrough | 0.7387 | 0.1658 | 0.2276 | Pure Single Modality |
| Case 4: Clin+Gut | Metabolic_Syndrome | Clin+Gut LRStacker | 0.9196 | 0.5504 | 0.0535 | Recommended 2-Modality Fusion |
| Case 4: Clin+Gut | Metabolic_Syndrome | MAX(Clin, Gut) | 0.9000 | 0.4628 | 0.2009 | Experimental Safeguard |
| Case 5: Clin+Wear | Metabolic_Syndrome | Clinical Single | 0.9089 | 0.4665 | 0.1257 | Fallback to Clinical (Wearable ignored) |
| Case 5: Clin+Wear | Metabolic_Syndrome | Clin+Wear LRStacker | 0.9090 | 0.4634 | 0.0694 | 2-Modality Fusion |
| Case 6: Gut+Wear | Metabolic_Syndrome | Gut Single | 0.8359 | 0.3690 | 0.1568 | Fallback to Gut |
| Case 6: Gut+Wear | Metabolic_Syndrome | Gut+Wear LRStacker | 0.8416 | 0.3726 | 0.0584 | 2-Modality Fusion |
| Case 7: All 3 | Metabolic_Syndrome | Clin+Gut LRStacker | 0.9196 | 0.5504 | 0.0535 | Primary 2-Modality Fusion (Wearable ignored) |
| Case 7: All 3 | Metabolic_Syndrome | Full LRStacker | 0.9200 | 0.5519 | 0.0483 | 3-Modality Fusion |
| Case 1: Clin Only | NAFLD | Clinical Passthrough | 0.9109 | 0.6534 | 0.1226 | Pure Single Modality |
| Case 2: Gut Only | NAFLD | Gut Passthrough | 0.8150 | 0.4859 | 0.1699 | Pure Single Modality |
| Case 3: Wear Only | NAFLD | Wearable Passthrough | 0.5914 | 0.1912 | 0.2411 | Pure Single Modality |
| Case 4: Clin+Gut | NAFLD | Clin+Gut LRStacker | 0.9277 | 0.7118 | 0.0691 | Recommended 2-Modality Fusion |
| Case 4: Clin+Gut | NAFLD | MAX(Clin, Gut) | 0.8975 | 0.6552 | 0.2127 | Experimental Safeguard |
| Case 5: Clin+Wear | NAFLD | Clinical Single | 0.9109 | 0.6534 | 0.1226 | Fallback to Clinical (Wearable ignored) |
| Case 5: Clin+Wear | NAFLD | Clin+Wear LRStacker | 0.9110 | 0.6543 | 0.0786 | 2-Modality Fusion |
| Case 6: Gut+Wear | NAFLD | Gut Single | 0.8150 | 0.4859 | 0.1699 | Fallback to Gut |
| Case 6: Gut+Wear | NAFLD | Gut+Wear LRStacker | 0.8252 | 0.4967 | 0.0948 | 2-Modality Fusion |
| Case 7: All 3 | NAFLD | Clin+Gut LRStacker | 0.9277 | 0.7118 | 0.0691 | Primary 2-Modality Fusion (Wearable ignored) |
| Case 7: All 3 | NAFLD | Full LRStacker | 0.9388 | 0.7347 | 0.0641 | 3-Modality Fusion |

---

## Section 9 — Calibration Comparison

| Disease | Strategy | Brier Score | Calibration Slope | Calibration Intercept | Calibration Diagnostic |
|:---|:---|---:|---:|---:|:---|
| Type2_Diabetes | Clinical Single | 0.0075 | 2.9456 | 1.5692 | Miscalibrated / Shifted Scale |
| Type2_Diabetes | Clin+Gut Weighted | 0.0578 | 9.2090 | 0.1770 | Miscalibrated / Shifted Scale |
| Type2_Diabetes | Clin+Gut LRStacker | 0.0027 | 1.6961 | 2.7821 | Miscalibrated / Shifted Scale |
| Prediabetes | Clinical Single | 0.0057 | 1.1700 | -0.8611 | Miscalibrated / Shifted Scale |
| Prediabetes | Clin+Gut Weighted | 0.0642 | 5.3337 | -0.6899 | Miscalibrated / Shifted Scale |
| Prediabetes | Clin+Gut LRStacker | 0.0836 | 6.3691 | 2.4548 | Miscalibrated / Shifted Scale |
| High_Adiposity_Risk | Clinical Single | 0.0749 | 1.0700 | -0.7858 | Miscalibrated / Shifted Scale |
| High_Adiposity_Risk | Clin+Gut Weighted | 0.0933 | 2.3675 | -0.7244 | Miscalibrated / Shifted Scale |
| High_Adiposity_Risk | Clin+Gut LRStacker | 0.0811 | 2.2824 | 0.4088 | Miscalibrated / Shifted Scale |
| Metabolic_Syndrome | Clinical Single | 0.1257 | 1.4259 | -2.4440 | Miscalibrated / Shifted Scale |
| Metabolic_Syndrome | Clin+Gut Weighted | 0.1245 | 2.0177 | -2.4093 | Miscalibrated / Shifted Scale |
| Metabolic_Syndrome | Clin+Gut LRStacker | 0.0535 | 2.0306 | 1.7964 | Miscalibrated / Shifted Scale |
| NAFLD | Clinical Single | 0.1226 | 1.0029 | -1.6681 | Miscalibrated / Shifted Scale |
| NAFLD | Clin+Gut Weighted | 0.1180 | 2.0073 | -1.6777 | Miscalibrated / Shifted Scale |
| NAFLD | Clin+Gut LRStacker | 0.0691 | 1.3564 | 0.2392 | Miscalibrated / Shifted Scale |

---

## Section 10 — Disease-Specific Evidence Matrix

| Disease | Dominant Modality | Clinical+Gut Needed? | Wearable Incremental Value | Full Fusion Evidence | Simplest Strong Strategy |
|:---|:---:|:---:|:---:|:---:|:---|
| **Type2_Diabetes** | Clinical | NO | None (Redundant, $r=0.92$) | None (0% Weight) | **Clinical Single (Passthrough)** |
| **Prediabetes** | Clinical | NO | None (Redundant, $r=0.84$) | None (0% Weight) | **Clinical Single (Passthrough)** |
| **High Adiposity** | Clinical | NO | None (Degrades AUC) | None ($\Delta	ext{AUC}$ CI includes 0) | **Clinical Single (Passthrough)** |
| **Metabolic Syn** | Clinical + Gut | **YES** ($\Delta	ext{PR} = +0.084$) | None (Full vs C+G $\Delta	ext{AUC} = +0.0004$) | Weak | **Clinical + Gut (LRStacker)** |
| **NAFLD** | Clinical + Gut | **YES** ($\Delta	ext{PR} = +0.058$) | Suppressor term only (Coef $-9.635$) | Artifactual | **Clinical + Gut (LRStacker)** |

---

## Section 11 — Final Research Recommendation

> **Disclaimer**: This section represents the research evidence recommendation based on Validation data ($n=3,000$) and OOF Train predictions ($n=14,000$). It is NOT a production architecture freeze.

### Disease Classification Recommendations:
1. **Category A — Single-Modality Dominant (Type2_Diabetes, Prediabetes, High_Adiposity_Risk)**:
   - **Type2_Diabetes**: Clinical Single (AUC = 0.9996). Passthrough.
   - **Prediabetes**: Clinical Single (AUC = 0.9993). Passthrough.
   - **High_Adiposity_Risk**: Clinical Single (AUC = 0.9665). Multimodal gains are statistically inconclusive (CI includes zero); simplicity tie-breaker selects Clinical.
2. **Category B — Clinical + Gut Co-Dominant (Metabolic_Syndrome, NAFLD)**:
   - **Metabolic_Syndrome**: `Clinical + Gut` LR Stacker (AUC = 0.9196, PR = 0.5504, +0.0839 PR gain over Clinical). Wearable provides zero incremental benefit.
   - **NAFLD**: `Clinical + Gut` LR Stacker (AUC = 0.9277, PR = 0.7118, +0.0584 PR gain over Clinical). Full 3-modality fusion relies on a negative Wearable coefficient (-9.635) acting as a noise-suppressor, which creates clinical feedback hazards. `Clinical + Gut` is the robust, interpretable choice.
3. **Category C — Clinical + Gut + Wearable**: **None** (No disease demonstrated robust positive 3-modality contribution without negative suppressor artifacts).
4. **Category D — Unresolved**: **None**.