# NEW SYNTHETIC FUSION V1 FUNCTIONAL / STRESS VALIDATION REPORT

**Date**: 2026-08-09T07:17:58.551167+00:00
**Dataset Type**: NEW SYNTHETIC FUNCTIONAL / STRESS VALIDATION ($n=500$ new synthetic patients)
> **Disclaimer**: *This validation was performed on a newly generated synthetic stress dataset specifically for software/functional pipeline testing. It does NOT represent real-world clinical validation.*

---

## 1. Executive Summary & Verification Log

- **New Patients Tested**: 500 unique synthetic stress patients (`STRESS_001` to `STRESS_500`).
- **Split Protection**: Confirmed 0 patients belonged to Train, OOF, Validation, or Test splits.
- **Level-0 Probability Integrity**: 15/15 raw probabilities verified finite, bounded in $[0.0, 1.0]$, 0 NaNs.
- **Wearable Exclusion**: Verified 100% (mutating Wearable produced exact 0.0 change in fused heads).
- **Architecture Invariance**: **Fusion V1 architecture was NOT changed during this validation.**
- **Test Isolation**: **Held-out Test set (`fusion_test_master.csv`) was NOT accessed.**

## 2. Multi-Disease Positive Counts Distribution ($n=500$ Stress Patients)

| Positive Disease Count per Patient | Patient Count | Percentage |
|:---:|---:|---:|
| **0 Positive Diseases** | 37 | 7.4% |
| **1 Positive Diseases** | 189 | 37.8% |
| **2 Positive Diseases** | 194 | 38.8% |
| **3 Positive Diseases** | 73 | 14.6% |
| **4 Positive Diseases** | 7 | 1.4% |
| **5 Positive Diseases** | 0 | 0.0% |

---

## 3. Observed Multi-Disease Patient Examples

### Example with 0 Positive Diseases (Patient `STRESS_002`):
- **Active Positive Diseases**: `None (Zero Positive)`
- **Fused Probabilities**: `{'Type2_Diabetes': np.float64(0.21), 'Prediabetes': np.float64(0.19), 'High_Adiposity_Risk': np.float64(0.01), 'Metabolic_Syndrome': np.float64(0.0032), 'NAFLD': np.float64(0.0339)}`

### Example with 1 Positive Diseases (Patient `STRESS_006`):
- **Active Positive Diseases**: `['High_Adiposity_Risk']`
- **Fused Probabilities**: `{'Type2_Diabetes': np.float64(0.19), 'Prediabetes': np.float64(0.2), 'High_Adiposity_Risk': np.float64(0.5), 'Metabolic_Syndrome': np.float64(0.0033), 'NAFLD': np.float64(0.0352)}`

### Example with 2 Positive Diseases (Patient `STRESS_004`):
- **Active Positive Diseases**: `['High_Adiposity_Risk', 'Metabolic_Syndrome']`
- **Fused Probabilities**: `{'Type2_Diabetes': np.float64(0.2), 'Prediabetes': np.float64(0.0), 'High_Adiposity_Risk': np.float64(1.0), 'Metabolic_Syndrome': np.float64(0.5039), 'NAFLD': np.float64(0.0339)}`

### Example with 3 Positive Diseases (Patient `STRESS_001`):
- **Active Positive Diseases**: `['Type2_Diabetes', 'High_Adiposity_Risk', 'NAFLD']`
- **Fused Probabilities**: `{'Type2_Diabetes': np.float64(0.51), 'Prediabetes': np.float64(0.99), 'High_Adiposity_Risk': np.float64(1.0), 'Metabolic_Syndrome': np.float64(0.1462), 'NAFLD': np.float64(0.6155)}`

### Example with 4 Positive Diseases (Patient `STRESS_126`):
- **Active Positive Diseases**: `['Type2_Diabetes', 'High_Adiposity_Risk', 'Metabolic_Syndrome', 'NAFLD']`
- **Fused Probabilities**: `{'Type2_Diabetes': np.float64(0.8507), 'Prediabetes': np.float64(0.9783), 'High_Adiposity_Risk': np.float64(0.877), 'Metabolic_Syndrome': np.float64(0.374), 'NAFLD': np.float64(0.6125)}`

---

## 4. Conflicting Modality Signal Results (Patients 50–55)

| Patient ID | Clinical MetSyn | Gut MetSyn | Wearable MetSyn | Raw LR Logit | Calibrated MetSyn Prob | Pred MetSyn (t=0.20) |
|:---:|---:|---:|---:|---:|---:|:---:|
| `STRESS_051` | 0.85 | 0.10 | 0.90 | 0.1213 | 0.1079 | **0** |
| `STRESS_052` | 0.85 | 0.10 | 0.90 | 0.1213 | 0.1079 | **0** |
| `STRESS_053` | 0.85 | 0.10 | 0.90 | 0.1213 | 0.1079 | **0** |
| `STRESS_054` | 0.10 | 0.85 | 0.10 | 0.0800 | 0.0495 | **0** |
| `STRESS_055` | 0.10 | 0.85 | 0.10 | 0.0800 | 0.0495 | **0** |
| `STRESS_056` | 0.10 | 0.85 | 0.10 | 0.0800 | 0.0495 | **0** |

---

## 5. Prediabetes Post-Decision Suppression Audit

- **Total Prediabetes Raw Positives ($t=0.50$)**: 260 patients
- **T2D Active Positive Predictions ($t=0.50$)**: 256 patients
- **Suppressed Prediabetes Cases**: **133** cases masked from 1 to 0
- **Raw P(Prediabetes) Integrity**: Preserved 100% un-mutated in output schema.

---

## 6. Presentation-Only Risk Score Ranking Example

Patient `STRESS_051` Fused Probabilities & Presentation Rank:
1. **Prediabetes**: 0.8505 (Threshold = 0.50 $\rightarrow$ Positivity: `True`)
2. **NAFLD**: 0.3963 (Threshold = 0.50 $\rightarrow$ Positivity: `False`)
3. **Type2_Diabetes**: 0.1700 (Threshold = 0.50 $\rightarrow$ Positivity: `False`)
4. **High_Adiposity_Risk**: 0.1231 (Threshold = 0.50 $\rightarrow$ Positivity: `False`)
5. **Metabolic_Syndrome**: 0.1079 (Threshold = 0.20 $\rightarrow$ Positivity: `False`)

---

## 7. Validation Conclusion

NEW SYNTHETIC FUSION V1 FUNCTIONAL / STRESS VALIDATION = **PASS**.