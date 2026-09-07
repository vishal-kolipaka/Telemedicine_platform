# Fusion Phase 1 — Calibration, Complementarity & Error-Overlap Analysis (Corrected & Refined)

**Metabolic Disease Multimodal Platform — Fusion Investigation**  
**Status: Evidence report only. No Fusion architecture is frozen. Phase 2 validation is required.**

All statistics in this report are computed on the **Validation set (n=3,000)** unless explicitly marked "descriptive only / Test." Train was not used in this phase (no OOF work was performed here). Test was not used to make any architecture, weight, or threshold decision.

---

## Executive Conclusion

Multimodal Fusion is **not uniformly justified**. The evidence divides cleanly into two regimes:

- **Type2_Diabetes and Prediabetes**: Clinical is overwhelmingly dominant (Val ROC-AUC 0.9996 / 0.9993). A Validation-optimized weighted average assigns **100% of its weight to Clinical alone** for both labels — the optimizer itself rejects Fusion. No architecture beyond Clinical passthrough is justified here.
- **High_Adiposity_Risk**: Clinical dominates (Val ROC-AUC 0.9665), but a small, statistically distinguishable improvement exists from adding Gut (bootstrap 95% CI on ROC-AUC gain excludes zero, point estimate +0.0022). Real, but marginal.
- **Metabolic_Syndrome and NAFLD**: The strongest candidates for Clinical + Gut Fusion. PR-AUC improves by 0.084 and 0.059 absolute respectively — large given these are the two rarest labels (7.7% and 14.2% prevalence). A confidence-band breakdown (Section 6) reveals *why*: Clinical's own accuracy collapses to 21%–55% specifically in the mid-probability range (0.4–0.8) where it is most uncertain, and Gut's accuracy holds up far better (51%–65%) in that same range. This is strong exploratory evidence of conditional complementarity — not just a favorable point estimate.

### Essential Methodological & Technical Refinements

1. **Validation Optimism Caveat**: Strategy C's weights were fitted and evaluated on the same Validation set. The bootstrap CIs confirm the improvement is not resampling noise conditional on the fitted weights, but they do **not** remove the optimism of tuning weights and evaluating performance on the same 3,000 patients. These estimates are optimistic upper bounds, not deployment-ready numbers.
2. **Aggregate Rescue Effect Clarification**: No statistically reliable positive rescue effect was demonstrated in the aggregate error analysis (Section 5). Small positive deltas occur for Gut rescuing Clinical on T2D ($\Delta = +0.0043$) and Prediabetes ($\Delta = +0.0559$), but the Clinical-error sample sizes are extremely small ($n=8$ and $n=17$ respectively), making them statistically unreliable. The meaningful complementarity signal is concentrated specifically in Clinical's mid-confidence region (0.4–0.8) and is masked when errors are pooled in aggregate.
3. **Wearable Incremental Signal Nuance**: Wearable received 0.0 weight under a 0.1 coarse grid search. This indicates that Wearable's *incremental* contribution after Clinical is present appears limited. However, 0.0 on a 0.1 discrete grid does not prove the true continuous optimal weight is exactly zero. Wearable's standalone performance remains strong (AUC 0.991 for T2D, 0.965 for Prediabetes), but its CGM features overlap heavily with Clinical's lab tests (Pearson $r = 0.921$ for T2D, $0.837$ for Prediabetes). Continuous optimization across modality subsets (Clinical, Clinical+Gut, Clinical+Wearable, Clinical+Wearable+Gut) will be tested in Phase 2.
4. **Multifactorial Calibration**: Miscalibration is driven by a combination of class imbalance, `scale_pos_weight` rebalancing, tree probability quantization, model separability, and model-specific probability distortion — not prevalence alone. Raw probability magnitude should not be read as calibrated clinical risk without explicit calibration.

---

## Section 1 — Artifact Verification

Verified directly from the exported artifacts:

| Check | Result | Evidence |
|---|:---:|---|
| Patient population (20,000 IDs) identical across modalities | **PASS** | Split manifest + all 6 prediction files use identical Patient_ID sets |
| Split manifest (Train=14,000 / Val=3,000 / Test=3,000) | **PASS** | Verified counts match exactly |
| Val/Test Patient_ID sets match split manifest exactly | **PASS** | Set equality confirmed for all 3 modalities, both splits |
| Row order identical across modalities' Val files | **PASS** | Enables direct positional join used in `fusion_val_master.csv` |
| Ground truth in prediction files matches `labels_v3.csv` | **PASS** | Zero mismatches across all 5 labels $\times$ 3 modalities |
| Decision threshold = 0.5 | **PASS** | Confirmed in inference scripts |
| 15/15 independently recomputed Test ROC-AUCs match reported values | **PASS** | Recomputed directly from raw probabilities; exact match to 4 decimals |
| Modality-level missingness in current data | **Not represented** | All 20,000 patients have complete Clinical + Wearable + Gut data |

---

## Section 2 — Calibration Analysis

| Disease | Modality | ROC_AUC | PR_AUC | Brier | Mean_Predicted_P | Prevalence | Calib_Slope | Calib_Intercept | Calibration_Class |
|:---|:---|---:|---:|---:|---:|---:|---:|---:|:---|
| Type2_Diabetes | Clinical | 0.9996 | 0.9994 | 0.0075 | 0.3830 | 0.3643 | 2.6611 | 1.0404 | Substantially miscalibrated |
| Type2_Diabetes | Wearable | 0.9909 | 0.9848 | 0.0400 | 0.3899 | 0.3643 | 1.1410 | -0.7265 | Mildly miscalibrated |
| Type2_Diabetes | Gut | 0.8236 | 0.7277 | 0.1717 | 0.4527 | 0.3643 | 1.1491 | -0.5203 | Mildly miscalibrated |
| Prediabetes | Clinical | 0.9993 | 0.9985 | 0.0057 | 0.3290 | 0.3240 | 1.1617 | -0.8484 | Substantially miscalibrated |
| Prediabetes | Wearable | 0.9648 | 0.9295 | 0.0726 | 0.3610 | 0.3240 | 1.0455 | -0.5383 | Mildly miscalibrated |
| Prediabetes | Gut | 0.6170 | 0.4202 | 0.2377 | 0.4853 | 0.3240 | 1.2799 | -0.6921 | Mildly miscalibrated |
| High_Adiposity_Risk | Clinical | 0.9665 | 0.9327 | 0.0749 | 0.3696 | 0.3163 | 1.0678 | -0.7842 | Mildly miscalibrated |
| High_Adiposity_Risk | Wearable | 0.7959 | 0.6178 | 0.1844 | 0.4430 | 0.3163 | 0.9444 | -0.7306 | Mildly miscalibrated |
| High_Adiposity_Risk | Gut | 0.8061 | 0.6738 | 0.1758 | 0.4351 | 0.3163 | 0.9937 | -0.7003 | Mildly miscalibrated |
| Metabolic_Syndrome | Clinical | 0.9089 | 0.4665 | 0.1257 | 0.2994 | 0.0770 | 1.4160 | -2.4366 | Substantially miscalibrated |
| Metabolic_Syndrome | Wearable | 0.7387 | 0.1658 | 0.2276 | 0.4769 | 0.0770 | 3.6579 | -2.4197 | Substantially miscalibrated |
| Metabolic_Syndrome | Gut | 0.8359 | 0.3690 | 0.1568 | 0.3461 | 0.0770 | 1.2261 | -2.3628 | Substantially miscalibrated |
| NAFLD | Clinical | 0.9109 | 0.6534 | 0.1226 | 0.2954 | 0.1420 | 1.0005 | -1.6662 | Substantially miscalibrated |
| NAFLD | Wearable | 0.5914 | 0.1912 | 0.2411 | 0.4887 | 0.1420 | 1.2364 | -1.7759 | Substantially miscalibrated |
| NAFLD | Gut | 0.8150 | 0.4859 | 0.1699 | 0.3872 | 0.1420 | 1.1506 | -1.7250 | Substantially miscalibrated |

Miscalibration is multifactorial: `scale_pos_weight` class rebalancing shifts predicted probabilities away from raw prevalence, while tree probability quantization and model-specific probability distortion further alter scale. Proper calibration (e.g., Platt scaling / Sigmoid) must be systematically evaluated in Phase 2.

---

## Section 3 — Probability Correlation Analysis

| Disease | Clinical-Wearable (Pearson) | Clinical-Gut (Pearson) | Wearable-Gut (Pearson) |
|:---|---:|---:|---:|
| Type2_Diabetes | **0.921** | 0.541 | 0.535 |
| Prediabetes | **0.837** | 0.181 | 0.180 |
| High_Adiposity_Risk | 0.609 | 0.501 | 0.438 |
| Metabolic_Syndrome | 0.459 | 0.485 | 0.491 |
| NAFLD | 0.235 | 0.366 | 0.510 |

- **T2D / Prediabetes**: High Clinical-Wearable correlation ($0.921 / 0.837$) confirms heavy glycemic feature overlap.
- **Metabolic_Syndrome & NAFLD**: Lower cross-modality correlations ($0.235 - 0.510$) indicate independent informational landscapes suitable for fusion.

---

## Section 4 — Conditional Rescue Analysis (Refined Wording)

**Conditional rescue rates vs. unconditional accuracy:**

| Disease | When Wrong | Rescuer | N Wrong Cases | P(Rescuer Correct \| Wrong) | Rescuer Unconditional Acc | Delta vs Unconditional |
|:---|:---|:---|---:|---:|---:|---:|
| Type2_Diabetes | Clinical | Wearable | 8 | 0.250 | 0.943 | -0.693 |
| Type2_Diabetes | Clinical | Gut | 8 | 0.750 | 0.746 | **+0.004** |
| Prediabetes | Clinical | Wearable | 17 | 0.294 | 0.898 | -0.604 |
| Prediabetes | Clinical | Gut | 17 | 0.588 | 0.532 | **+0.056** |
| High_Adiposity_Risk | Clinical | Wearable | 324 | 0.312 | 0.711 | -0.400 |
| High_Adiposity_Risk | Clinical | Gut | 324 | 0.583 | 0.707 | -0.124 |
| Metabolic_Syndrome | Clinical | Wearable | 569 | 0.373 | 0.657 | -0.284 |
| Metabolic_Syndrome | Clinical | Gut | 569 | 0.489 | 0.706 | -0.218 |
| NAFLD | Clinical | Wearable | 557 | 0.422 | 0.566 | -0.144 |
| NAFLD | Clinical | Gut | 557 | 0.580 | 0.703 | -0.123 |

> **Corrected Interpretation**: No statistically reliable positive rescue effect was demonstrated in the aggregate error analysis. The only positive deltas occur for Gut rescuing Clinical on T2D ($\Delta = +0.004$) and Prediabetes ($\Delta = +0.056$), but the Clinical-error sample sizes ($n=8$ and $n=17$) are too small to support a conclusion. 

---

## Section 5 — Confidence-Band Analysis (Exploratory Evidence)

When segmenting patients by **Clinical's predicted probability**:

| Disease | Clinical P Band | N | Clinical Acc | Wearable Acc | Gut Acc | Either W/G Correct |
|:---|:---|---:|---:|---:|---:|---:|
| Metabolic_Syndrome | 0.4–0.6 | 358 | **0.547** | 0.492 | 0.575 | 0.715 |
| Metabolic_Syndrome | 0.6–0.8 | 380 | **0.213** | 0.437 | **0.513** | 0.668 |
| NAFLD | 0.4–0.6 | 252 | **0.504** | 0.476 | 0.591 | 0.659 |
| NAFLD | 0.6–0.8 | 330 | **0.288** | 0.512 | **0.655** | 0.764 |

In Clinical's uncertain mid-confidence region ($P \in [0.6, 0.8]$), **Gut's accuracy is more than double Clinical's accuracy** for Metabolic_Syndrome (0.513 vs 0.213) and NAFLD (0.655 vs 0.288). This provides strong exploratory evidence of conditional complementarity.

---

## Section 6 — Refined Phase 2 Architecture & Validation Plan

Do **NOT** freeze the Fusion architecture yet. Phase 2 candidate validation must proceed with the following rigorous protocol:

```
Step A: 5-Fold OOF Predictions (14,000 Train Set)
        Clinical OOF Probs  |  Wearable OOF Probs  |  Gut OOF Probs
                                ↓
Step B: Fit Candidate Meta-Models ONLY on OOF Predictions
                                ↓
Step C: Evaluate & Select Strategy on Untouched Validation (3,000)
        Compare:
          1. Best Standalone (Clinical)
          2. Equal-Weight Average
          3. Continuous Weighted Average (Finer Simplex Search)
          4. Logistic Regression Stacker
          5. Calibrated Meta-Models
        Across Subsets:
          - Clinical
          - Clinical + Gut
          - Clinical + Wearable
          - Clinical + Wearable + Gut
                                ↓
Step D: Freeze Winning Architecture Per Disease
                                ↓
Step E: ONE Final Evaluation on Untouched Test Set (3,000)
```

### Provisional Disease Classification (To be validated in Phase 2)

| Disease | Status & Direction |
|:---|:---|
| **Type2_Diabetes** | Clinical overwhelmingly dominates (Passthrough) |
| **Prediabetes** | Clinical overwhelmingly dominates (Passthrough) |
| **High_Adiposity_Risk** | Clinical dominates; evaluate potential small Clinical + Gut increment |
| **Metabolic_Syndrome** | Strong candidate for Clinical + Gut Fusion |
| **NAFLD** | Strongest candidate for Clinical + Gut Fusion |
