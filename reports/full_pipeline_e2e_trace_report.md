# Comprehensive End-to-End Pipeline Trace Report

**Execution Timestamp (UTC):** 2026-09-07 14:02:24
**Pipeline Architecture:**
```
Raw Input Files → DocumentReader → FeatureMapper
  → [TEST-ONLY simulate_family_history_answers() (if applicable)]
  → ModelRouter → Level-0 Models (Clinical / Wearable / Gut) → Fusion V2
```

---

## Case 1: Clinical + Gut + Wearable

### STAGE 0 — INPUT FILES
- **Files Supplied:** `clinical_report.txt`, `gut_microbiome_report.txt`, `fitbit_wearable_report.txt`
- **File Types:** Plain Text Lab Report, Plain Text Microbiome Lab Report, Plain Text Wearable/CGM Export
- **Modalities Present:** `clinical`, `gut`, `wearable`
- **Modalities Intentionally Absent:** None

### STAGE 1 — DOCUMENTREADER / CONTRACT 1
- **Total Pages Extracted:** 3 (elapsed: 0.0028s)
  - **File `clinical_report.txt` (Page 0):** status=`unknown`, method=`plain_text`, length=1103 chars, OCR confidence=N/A
    *Text Preview:* "APOLLO DIAGNOSTICS           Comprehensive Metabolic Health Profile ------------------------------------------------------------  Patient Name      : Arjun Mehta Patient ID        ..."
  - **File `gut_microbiome_report.txt` (Page 0):** status=`unknown`, method=`plain_text`, length=1137 chars, OCR confidence=N/A
    *Text Preview:* "============================================================ GUT MICROBIOME ANALYSIS REPORT ============================================================  Patient : Arjun Mehta Lab ..."
  - **File `fitbit_wearable_report.txt` (Page 0):** status=`unknown`, method=`plain_text`, length=1007 chars, OCR confidence=N/A
    *Text Preview:* "============================================================ FITBIT HEALTH SUMMARY ============================================================  Patient          : Arjun Mehta Repo..."

### STAGE 2 — FEATUREMAPPER / CONTRACT 2 (BEFORE HARNESS)
- **Patient Info Captured:** ID=`None`, Name=`Arjun Mehta`, Age=`47`, Gender=`Male`
- **`clinical` Domain:** status=`incomplete`, resolved=15 fields, missing=['Family_History_Diabetes', 'Family_History_Hypertension', 'Family_History_CVD']
  *Values Sample:* Age=47, Gender=Male, Height=174.0, Weight=88.0, Waist_Circumference=99.0, Systolic_BP=134.0, ... (+9 more)
- **`wearable` Domain:** status=`complete`, resolved=15 fields, missing=[]
  *Values Sample:* Average_Daily_Steps=6200.0, Active_Minutes=38.0, Sedentary_Time_Minutes=680.0, Resting_Heart_Rate=74.0, Heart_Rate_Variability_RMSSD=28.0, Sleep_Duration_Hours=6.4, ... (+9 more)
- **`gut` Domain:** status=`complete`, resolved=21 fields, missing=[]
  *Values Sample:* Akkermansia=2.1, Faecalibacterium=7.3, Roseburia=3.8, Bifidobacterium=4.2, Bacteroides=18.6, Prevotella=9.4, ... (+15 more)

### STAGE 3 — TEST-ONLY USER FORM SIMULATION
- **Harness Action:** Applied `simulate_family_history_answers()` for 3 required anamnesis fields.
- **Before:** clinical.status = `incomplete`, missing_fields = `['Family_History_Diabetes', 'Family_History_Hypertension', 'Family_History_CVD']`
- **After:** clinical.status = **`complete`**, missing_fields = `[]`
- **Total Clinical Features Present:** 18 / 18
  *Injected Values:*
    - `Family_History_CVD`: canonical_value=`False`, source=`user_form`, validation=`USER_ENTERED`
    - `Family_History_Hypertension`: canonical_value=`True`, source=`user_form`, validation=`USER_ENTERED`
    - `Family_History_Diabetes`: canonical_value=`True`, source=`user_form`, validation=`USER_ENTERED`

### STAGE 4 — MODELROUTER + LEVEL-0 MODELS
- **`clinical` Dispatch:** status = **`success`**
  *Level-0 Inference Results:*
    - `Type2_Diabetes`: raw_prob = 0.8266 (82.66%), decision = `1`
    - `Prediabetes`: raw_prob = 0.3111 (31.11%), decision = `0`
    - `High_Adiposity_Risk`: raw_prob = 0.8239 (82.39%), decision = `1`
    - `Metabolic_Syndrome`: raw_prob = 0.7665 (76.65%), decision = `1`
    - `NAFLD`: raw_prob = 0.6253 (62.53%), decision = `1`
- **`wearable` Dispatch:** status = **`success`**
  *Level-0 Inference Results:*
    - `Type2_Diabetes`: raw_prob = 0.0183 (1.83%), decision = `0`
    - `Prediabetes`: raw_prob = 0.9442 (94.42%), decision = `1`
    - `High_Adiposity_Risk`: raw_prob = 0.8072 (80.72%), decision = `1`
    - `Metabolic_Syndrome`: raw_prob = 0.4551 (45.51%), decision = `0`
    - `NAFLD`: raw_prob = 0.5460 (54.60%), decision = `1`
- **`gut` Dispatch:** status = **`success`**
  *Level-0 Inference Results:*
    - `Type2_Diabetes`: raw_prob = 0.6913 (69.13%), decision = `1`
    - `Prediabetes`: raw_prob = 0.5384 (53.84%), decision = `0`
    - `High_Adiposity_Risk`: raw_prob = 0.6813 (68.13%), decision = `1`
    - `Metabolic_Syndrome`: raw_prob = 0.6473 (64.73%), decision = `1`
    - `NAFLD`: raw_prob = 0.5795 (57.95%), decision = `1`

### STAGE 5 — FUSION V2 EXECUTION
- **Pathway Applied:** `C_W_G` (Clinical + Wearable + Gut Stacker), Case: `C+G+W`, Active Modalities: `['clinical', 'wearable', 'gut']`

#### Final Disease Decisions Table:

| Disease | Risk Score | Risk % | Decision | Threshold | Confidence Label | Strategy | Modalities Used |
|:---|---:|---:|:---:|:---:|:---:|:---:|:---:|
| **Type2 Diabetes** | 0.9793 | 97.93% | **Positive** | 0.21 | `FINAL_PREDICTION` | `pathway_c_w_g_stacker` | `clinical+wearable+gut` |
| **Prediabetes** | 0.1564 | 15.64% | **N/A (Suppressed)** | 0.73 | `SUPPRESSED_BY_T2D` | `pathway_c_w_g_stacker` | `clinical+wearable+gut` |
| **High Adiposity Risk** | 0.8612 | 86.12% | **Positive** | 0.46 | `FINAL_PREDICTION` | `pathway_c_w_g_stacker` | `clinical+wearable+gut` |
| **Metabolic Syndrome** | 0.3996 | 39.96% | **Positive** | 0.28 | `FINAL_PREDICTION` | `pathway_c_w_g_stacker` | `clinical+wearable+gut` |
| **NAFLD** | 0.2643 | 26.43% | **Negative** | 0.39 | `FINAL_PREDICTION` | `pathway_c_w_g_stacker` | `clinical+wearable+gut` |

---

## Case 2: Clinical + Gut

### STAGE 0 — INPUT FILES
- **Files Supplied:** `clinical_report.txt`, `gut_microbiome_report.txt`
- **File Types:** Plain Text Lab Report, Plain Text Microbiome Lab Report
- **Modalities Present:** `clinical`, `gut`
- **Modalities Intentionally Absent:** `wearable`

### STAGE 1 — DOCUMENTREADER / CONTRACT 1
- **Total Pages Extracted:** 2 (elapsed: 0.0030s)
  - **File `clinical_report.txt` (Page 0):** status=`unknown`, method=`plain_text`, length=1103 chars, OCR confidence=N/A
    *Text Preview:* "APOLLO DIAGNOSTICS           Comprehensive Metabolic Health Profile ------------------------------------------------------------  Patient Name      : Arjun Mehta Patient ID        ..."
  - **File `gut_microbiome_report.txt` (Page 0):** status=`unknown`, method=`plain_text`, length=1137 chars, OCR confidence=N/A
    *Text Preview:* "============================================================ GUT MICROBIOME ANALYSIS REPORT ============================================================  Patient : Arjun Mehta Lab ..."

### STAGE 2 — FEATUREMAPPER / CONTRACT 2 (BEFORE HARNESS)
- **Patient Info Captured:** ID=`None`, Name=`Arjun Mehta`, Age=`47`, Gender=`Male`
- **`clinical` Domain:** status=`incomplete`, resolved=15 fields, missing=['Family_History_Diabetes', 'Family_History_Hypertension', 'Family_History_CVD']
  *Values Sample:* Age=47, Gender=Male, Height=174.0, Weight=88.0, Waist_Circumference=99.0, Systolic_BP=134.0, ... (+9 more)
- **`wearable` Domain:** status=`not_available`, resolved=0 fields, missing=['Average_Daily_Steps', 'Active_Minutes', 'Sedentary_Time_Minutes', 'Resting_Heart_Rate', 'Heart_Rate_Variability_RMSSD', 'Sleep_Duration_Hours', 'Sleep_Efficiency_Score', 'Autonomic_Stress_Score', 'Activity_Energy_Expenditure', 'Exercise_Frequency_Days', 'CGM_Average_Glucose', 'CGM_Glucose_CV', 'CGM_Time_In_Range', 'CGM_Time_Above_Range', 'CGM_Time_Below_Range']
- **`gut` Domain:** status=`complete`, resolved=21 fields, missing=[]
  *Values Sample:* Akkermansia=2.1, Faecalibacterium=7.3, Roseburia=3.8, Bifidobacterium=4.2, Bacteroides=18.6, Prevotella=9.4, ... (+15 more)

### STAGE 3 — TEST-ONLY USER FORM SIMULATION
- **Harness Action:** Applied `simulate_family_history_answers()` for 3 required anamnesis fields.
- **Before:** clinical.status = `incomplete`, missing_fields = `['Family_History_Diabetes', 'Family_History_Hypertension', 'Family_History_CVD']`
- **After:** clinical.status = **`complete`**, missing_fields = `[]`
- **Total Clinical Features Present:** 18 / 18
  *Injected Values:*
    - `Family_History_CVD`: canonical_value=`False`, source=`user_form`, validation=`USER_ENTERED`
    - `Family_History_Hypertension`: canonical_value=`True`, source=`user_form`, validation=`USER_ENTERED`
    - `Family_History_Diabetes`: canonical_value=`True`, source=`user_form`, validation=`USER_ENTERED`

### STAGE 4 — MODELROUTER + LEVEL-0 MODELS
- **`clinical` Dispatch:** status = **`success`**
  *Level-0 Inference Results:*
    - `Type2_Diabetes`: raw_prob = 0.8266 (82.66%), decision = `1`
    - `Prediabetes`: raw_prob = 0.3111 (31.11%), decision = `0`
    - `High_Adiposity_Risk`: raw_prob = 0.8239 (82.39%), decision = `1`
    - `Metabolic_Syndrome`: raw_prob = 0.7665 (76.65%), decision = `1`
    - `NAFLD`: raw_prob = 0.6253 (62.53%), decision = `1`
- **`wearable` Dispatch:** status = **`not_run`**
  *Reason:* `Mapper status was 'not_available' (expected 'complete')` (Model was NOT executed)
- **`gut` Dispatch:** status = **`success`**
  *Level-0 Inference Results:*
    - `Type2_Diabetes`: raw_prob = 0.6913 (69.13%), decision = `1`
    - `Prediabetes`: raw_prob = 0.5384 (53.84%), decision = `0`
    - `High_Adiposity_Risk`: raw_prob = 0.6813 (68.13%), decision = `1`
    - `Metabolic_Syndrome`: raw_prob = 0.6473 (64.73%), decision = `1`
    - `NAFLD`: raw_prob = 0.5795 (57.95%), decision = `1`

### STAGE 5 — FUSION V2 EXECUTION
- **Pathway Applied:** `C_G` (Clinical + Gut Stacker), Case: `C+G`, Active Modalities: `['clinical', 'gut']`

#### Final Disease Decisions Table:

| Disease | Risk Score | Risk % | Decision | Threshold | Confidence Label | Strategy | Modalities Used |
|:---|---:|---:|:---:|:---:|:---:|:---:|:---:|
| **Type2 Diabetes** | 1.0000 | 100.00% | **Positive** | 0.49 | `FINAL_PREDICTION` | `pathway_c_g_stacker` | `clinical+gut` |
| **Prediabetes** | 0.0455 | 4.55% | **N/A (Suppressed)** | 0.37 | `SUPPRESSED_BY_T2D` | `pathway_c_g_stacker` | `clinical+gut` |
| **High Adiposity Risk** | 0.8616 | 86.16% | **Positive** | 0.46 | `FINAL_PREDICTION` | `pathway_c_g_stacker` | `clinical+gut` |
| **Metabolic Syndrome** | 0.3834 | 38.34% | **Positive** | 0.29 | `FINAL_PREDICTION` | `pathway_c_g_stacker` | `clinical+gut` |
| **NAFLD** | 0.3175 | 31.75% | **Negative** | 0.36 | `FINAL_PREDICTION` | `pathway_c_g_stacker` | `clinical+gut` |

---

## Case 3: Clinical + Wearable

### STAGE 0 — INPUT FILES
- **Files Supplied:** `clinical_report.txt`, `fitbit_wearable_report.txt`
- **File Types:** Plain Text Lab Report, Plain Text Wearable/CGM Export
- **Modalities Present:** `clinical`, `wearable`
- **Modalities Intentionally Absent:** `gut`

### STAGE 1 — DOCUMENTREADER / CONTRACT 1
- **Total Pages Extracted:** 2 (elapsed: 0.0026s)
  - **File `clinical_report.txt` (Page 0):** status=`unknown`, method=`plain_text`, length=1103 chars, OCR confidence=N/A
    *Text Preview:* "APOLLO DIAGNOSTICS           Comprehensive Metabolic Health Profile ------------------------------------------------------------  Patient Name      : Arjun Mehta Patient ID        ..."
  - **File `fitbit_wearable_report.txt` (Page 0):** status=`unknown`, method=`plain_text`, length=1007 chars, OCR confidence=N/A
    *Text Preview:* "============================================================ FITBIT HEALTH SUMMARY ============================================================  Patient          : Arjun Mehta Repo..."

### STAGE 2 — FEATUREMAPPER / CONTRACT 2 (BEFORE HARNESS)
- **Patient Info Captured:** ID=`None`, Name=`Arjun Mehta`, Age=`47`, Gender=`Male`
- **`clinical` Domain:** status=`incomplete`, resolved=15 fields, missing=['Family_History_Diabetes', 'Family_History_Hypertension', 'Family_History_CVD']
  *Values Sample:* Age=47, Gender=Male, Height=174.0, Weight=88.0, Waist_Circumference=99.0, Systolic_BP=134.0, ... (+9 more)
- **`wearable` Domain:** status=`complete`, resolved=15 fields, missing=[]
  *Values Sample:* Average_Daily_Steps=6200.0, Active_Minutes=38.0, Sedentary_Time_Minutes=680.0, Resting_Heart_Rate=74.0, Heart_Rate_Variability_RMSSD=28.0, Sleep_Duration_Hours=6.4, ... (+9 more)
- **`gut` Domain:** status=`not_available`, resolved=0 fields, missing=['Akkermansia', 'Faecalibacterium', 'Roseburia', 'Bifidobacterium', 'Bacteroides', 'Prevotella', 'Ruminococcus', 'Blautia', 'Collinsella', 'Escherichia_Shigella', 'Coprococcus', 'Alistipes', 'Subdoligranulum', 'Enterococcus', 'Eubacterium', 'Parabacteroides', 'Lactobacillus', 'Klebsiella', 'Streptococcus', 'Eggerthella', 'Other_Taxa']

### STAGE 3 — TEST-ONLY USER FORM SIMULATION
- **Harness Action:** Applied `simulate_family_history_answers()` for 3 required anamnesis fields.
- **Before:** clinical.status = `incomplete`, missing_fields = `['Family_History_Diabetes', 'Family_History_Hypertension', 'Family_History_CVD']`
- **After:** clinical.status = **`complete`**, missing_fields = `[]`
- **Total Clinical Features Present:** 18 / 18
  *Injected Values:*
    - `Family_History_CVD`: canonical_value=`False`, source=`user_form`, validation=`USER_ENTERED`
    - `Family_History_Hypertension`: canonical_value=`True`, source=`user_form`, validation=`USER_ENTERED`
    - `Family_History_Diabetes`: canonical_value=`True`, source=`user_form`, validation=`USER_ENTERED`

### STAGE 4 — MODELROUTER + LEVEL-0 MODELS
- **`clinical` Dispatch:** status = **`success`**
  *Level-0 Inference Results:*
    - `Type2_Diabetes`: raw_prob = 0.8266 (82.66%), decision = `1`
    - `Prediabetes`: raw_prob = 0.3111 (31.11%), decision = `0`
    - `High_Adiposity_Risk`: raw_prob = 0.8239 (82.39%), decision = `1`
    - `Metabolic_Syndrome`: raw_prob = 0.7665 (76.65%), decision = `1`
    - `NAFLD`: raw_prob = 0.6253 (62.53%), decision = `1`
- **`wearable` Dispatch:** status = **`success`**
  *Level-0 Inference Results:*
    - `Type2_Diabetes`: raw_prob = 0.0183 (1.83%), decision = `0`
    - `Prediabetes`: raw_prob = 0.9442 (94.42%), decision = `1`
    - `High_Adiposity_Risk`: raw_prob = 0.8072 (80.72%), decision = `1`
    - `Metabolic_Syndrome`: raw_prob = 0.4551 (45.51%), decision = `0`
    - `NAFLD`: raw_prob = 0.5460 (54.60%), decision = `1`
- **`gut` Dispatch:** status = **`not_run`**
  *Reason:* `Mapper status was 'not_available' (expected 'complete')` (Model was NOT executed)

### STAGE 5 — FUSION V2 EXECUTION
- **Pathway Applied:** `C_W` (Clinical + Wearable Stacker), Case: `C+W`, Active Modalities: `['clinical', 'wearable']`

#### Final Disease Decisions Table:

| Disease | Risk Score | Risk % | Decision | Threshold | Confidence Label | Strategy | Modalities Used |
|:---|---:|---:|:---:|:---:|:---:|:---:|:---:|
| **Type2 Diabetes** | 0.9593 | 95.93% | **Positive** | 0.48 | `FINAL_PREDICTION` | `pathway_c_w_stacker` | `clinical+wearable` |
| **Prediabetes** | 0.1431 | 14.31% | **N/A (Suppressed)** | 0.61 | `SUPPRESSED_BY_T2D` | `pathway_c_w_stacker` | `clinical+wearable` |
| **High Adiposity Risk** | 0.8127 | 81.27% | **Positive** | 0.44 | `FINAL_PREDICTION` | `pathway_c_w_stacker` | `clinical+wearable` |
| **Metabolic Syndrome** | 0.3031 | 30.31% | **Negative** | 0.34 | `FINAL_PREDICTION` | `pathway_c_w_stacker` | `clinical+wearable` |
| **NAFLD** | 0.2497 | 24.97% | **Negative** | 0.43 | `FINAL_PREDICTION` | `pathway_c_w_stacker` | `clinical+wearable` |

---

## Case 4: Gut + Wearable

### STAGE 0 — INPUT FILES
- **Files Supplied:** `gut_microbiome_report.txt`, `fitbit_wearable_report.txt`
- **File Types:** Plain Text Microbiome Lab Report, Plain Text Wearable/CGM Export
- **Modalities Present:** `gut`, `wearable`
- **Modalities Intentionally Absent:** `clinical`

### STAGE 1 — DOCUMENTREADER / CONTRACT 1
- **Total Pages Extracted:** 2 (elapsed: 0.0028s)
  - **File `gut_microbiome_report.txt` (Page 0):** status=`unknown`, method=`plain_text`, length=1137 chars, OCR confidence=N/A
    *Text Preview:* "============================================================ GUT MICROBIOME ANALYSIS REPORT ============================================================  Patient : Arjun Mehta Lab ..."
  - **File `fitbit_wearable_report.txt` (Page 0):** status=`unknown`, method=`plain_text`, length=1007 chars, OCR confidence=N/A
    *Text Preview:* "============================================================ FITBIT HEALTH SUMMARY ============================================================  Patient          : Arjun Mehta Repo..."

### STAGE 2 — FEATUREMAPPER / CONTRACT 2 (BEFORE HARNESS)
- **Patient Info Captured:** ID=`None`, Name=`Arjun Mehta`, Age=`None`, Gender=`None`
- **`clinical` Domain:** status=`not_available`, resolved=0 fields, missing=['Age', 'Gender', 'Height', 'Weight', 'BMI', 'Waist_Circumference', 'Systolic_BP', 'Diastolic_BP', 'Fasting_Blood_Glucose', 'HbA1c', 'Triglycerides', 'HDL', 'LDL', 'ALT', 'AST', 'Family_History_Diabetes', 'Family_History_Hypertension', 'Family_History_CVD']
- **`wearable` Domain:** status=`complete`, resolved=15 fields, missing=[]
  *Values Sample:* Average_Daily_Steps=6200.0, Active_Minutes=38.0, Sedentary_Time_Minutes=680.0, Resting_Heart_Rate=74.0, Heart_Rate_Variability_RMSSD=28.0, Sleep_Duration_Hours=6.4, ... (+9 more)
- **`gut` Domain:** status=`complete`, resolved=21 fields, missing=[]
  *Values Sample:* Akkermansia=2.1, Faecalibacterium=7.3, Roseburia=3.8, Bifidobacterium=4.2, Bacteroides=18.6, Prevotella=9.4, ... (+15 more)

### STAGE 3 — TEST-ONLY USER FORM SIMULATION
- **Harness Status:** Not applicable (Clinical domain was not incomplete solely due to family history).

### STAGE 4 — MODELROUTER + LEVEL-0 MODELS
- **`clinical` Dispatch:** status = **`not_run`**
  *Reason:* `Mapper status was 'not_available' (expected 'complete')` (Model was NOT executed)
- **`wearable` Dispatch:** status = **`success`**
  *Level-0 Inference Results:*
    - `Type2_Diabetes`: raw_prob = 0.0183 (1.83%), decision = `0`
    - `Prediabetes`: raw_prob = 0.9442 (94.42%), decision = `1`
    - `High_Adiposity_Risk`: raw_prob = 0.8072 (80.72%), decision = `1`
    - `Metabolic_Syndrome`: raw_prob = 0.4551 (45.51%), decision = `0`
    - `NAFLD`: raw_prob = 0.5460 (54.60%), decision = `1`
- **`gut` Dispatch:** status = **`success`**
  *Level-0 Inference Results:*
    - `Type2_Diabetes`: raw_prob = 0.6913 (69.13%), decision = `1`
    - `Prediabetes`: raw_prob = 0.5384 (53.84%), decision = `0`
    - `High_Adiposity_Risk`: raw_prob = 0.6813 (68.13%), decision = `1`
    - `Metabolic_Syndrome`: raw_prob = 0.6473 (64.73%), decision = `1`
    - `NAFLD`: raw_prob = 0.5795 (57.95%), decision = `1`

### STAGE 5 — FUSION V2 EXECUTION
- **Pathway Applied:** `W_G` (Wearable + Gut Stacker), Case: `W+G`, Active Modalities: `['wearable', 'gut']`

#### Final Disease Decisions Table:

| Disease | Risk Score | Risk % | Decision | Threshold | Confidence Label | Strategy | Modalities Used |
|:---|---:|---:|:---:|:---:|:---:|:---:|:---:|
| **Type2 Diabetes** | 0.0136 | 1.36% | **Negative** | 0.53 | `FINAL_PREDICTION` | `pathway_w_g_stacker` | `wearable+gut` |
| **Prediabetes** | 0.9218 | 92.18% | **Positive** | 0.50 | `FINAL_PREDICTION` | `pathway_w_g_stacker` | `wearable+gut` |
| **High Adiposity Risk** | 0.7560 | 75.60% | **Positive** | 0.33 | `FINAL_PREDICTION` | `pathway_w_g_stacker` | `wearable+gut` |
| **Metabolic Syndrome** | 0.1525 | 15.25% | **Negative** | 0.26 | `FINAL_PREDICTION` | `pathway_w_g_stacker` | `wearable+gut` |
| **NAFLD** | 0.1827 | 18.27% | **Negative** | 0.28 | `FINAL_PREDICTION` | `pathway_w_g_stacker` | `wearable+gut` |

---

## Case 5: Clinical only

### STAGE 0 — INPUT FILES
- **Files Supplied:** `clinical_report.txt`
- **File Types:** Plain Text Lab Report
- **Modalities Present:** `clinical`
- **Modalities Intentionally Absent:** `gut`, `wearable`

### STAGE 1 — DOCUMENTREADER / CONTRACT 1
- **Total Pages Extracted:** 1 (elapsed: 0.0013s)
  - **File `clinical_report.txt` (Page 0):** status=`unknown`, method=`plain_text`, length=1103 chars, OCR confidence=N/A
    *Text Preview:* "APOLLO DIAGNOSTICS           Comprehensive Metabolic Health Profile ------------------------------------------------------------  Patient Name      : Arjun Mehta Patient ID        ..."

### STAGE 2 — FEATUREMAPPER / CONTRACT 2 (BEFORE HARNESS)
- **Patient Info Captured:** ID=`None`, Name=`None`, Age=`47`, Gender=`Male`
- **`clinical` Domain:** status=`incomplete`, resolved=15 fields, missing=['Family_History_Diabetes', 'Family_History_Hypertension', 'Family_History_CVD']
  *Values Sample:* Age=47, Gender=Male, Height=174.0, Weight=88.0, Waist_Circumference=99.0, Systolic_BP=134.0, ... (+9 more)
- **`wearable` Domain:** status=`not_available`, resolved=0 fields, missing=['Average_Daily_Steps', 'Active_Minutes', 'Sedentary_Time_Minutes', 'Resting_Heart_Rate', 'Heart_Rate_Variability_RMSSD', 'Sleep_Duration_Hours', 'Sleep_Efficiency_Score', 'Autonomic_Stress_Score', 'Activity_Energy_Expenditure', 'Exercise_Frequency_Days', 'CGM_Average_Glucose', 'CGM_Glucose_CV', 'CGM_Time_In_Range', 'CGM_Time_Above_Range', 'CGM_Time_Below_Range']
- **`gut` Domain:** status=`not_available`, resolved=0 fields, missing=['Akkermansia', 'Faecalibacterium', 'Roseburia', 'Bifidobacterium', 'Bacteroides', 'Prevotella', 'Ruminococcus', 'Blautia', 'Collinsella', 'Escherichia_Shigella', 'Coprococcus', 'Alistipes', 'Subdoligranulum', 'Enterococcus', 'Eubacterium', 'Parabacteroides', 'Lactobacillus', 'Klebsiella', 'Streptococcus', 'Eggerthella', 'Other_Taxa']

### STAGE 3 — TEST-ONLY USER FORM SIMULATION
- **Harness Action:** Applied `simulate_family_history_answers()` for 3 required anamnesis fields.
- **Before:** clinical.status = `incomplete`, missing_fields = `['Family_History_Diabetes', 'Family_History_Hypertension', 'Family_History_CVD']`
- **After:** clinical.status = **`complete`**, missing_fields = `[]`
- **Total Clinical Features Present:** 18 / 18
  *Injected Values:*
    - `Family_History_CVD`: canonical_value=`False`, source=`user_form`, validation=`USER_ENTERED`
    - `Family_History_Hypertension`: canonical_value=`True`, source=`user_form`, validation=`USER_ENTERED`
    - `Family_History_Diabetes`: canonical_value=`True`, source=`user_form`, validation=`USER_ENTERED`

### STAGE 4 — MODELROUTER + LEVEL-0 MODELS
- **`clinical` Dispatch:** status = **`success`**
  *Level-0 Inference Results:*
    - `Type2_Diabetes`: raw_prob = 0.8266 (82.66%), decision = `1`
    - `Prediabetes`: raw_prob = 0.3111 (31.11%), decision = `0`
    - `High_Adiposity_Risk`: raw_prob = 0.8239 (82.39%), decision = `1`
    - `Metabolic_Syndrome`: raw_prob = 0.7665 (76.65%), decision = `1`
    - `NAFLD`: raw_prob = 0.6253 (62.53%), decision = `1`
- **`wearable` Dispatch:** status = **`not_run`**
  *Reason:* `Mapper status was 'not_available' (expected 'complete')` (Model was NOT executed)
- **`gut` Dispatch:** status = **`not_run`**
  *Reason:* `Mapper status was 'not_available' (expected 'complete')` (Model was NOT executed)

### STAGE 5 — FUSION V2 EXECUTION
- **Pathway Applied:** `C` (Clinical Only Stacker), Case: `C`, Active Modalities: `['clinical']`

#### Final Disease Decisions Table:

| Disease | Risk Score | Risk % | Decision | Threshold | Confidence Label | Strategy | Modalities Used |
|:---|---:|---:|:---:|:---:|:---:|:---:|:---:|
| **Type2 Diabetes** | 0.9979 | 99.79% | **Positive** | 0.43 | `FINAL_PREDICTION` | `pathway_c_stacker` | `clinical` |
| **Prediabetes** | 0.1429 | 14.29% | **N/A (Suppressed)** | 0.34 | `SUPPRESSED_BY_T2D` | `pathway_c_stacker` | `clinical` |
| **High Adiposity Risk** | 0.7038 | 70.38% | **Positive** | 0.40 | `FINAL_PREDICTION` | `pathway_c_stacker` | `clinical` |
| **Metabolic Syndrome** | 0.3210 | 32.10% | **Positive** | 0.32 | `FINAL_PREDICTION` | `pathway_c_stacker` | `clinical` |
| **NAFLD** | 0.2397 | 23.97% | **Negative** | 0.36 | `FINAL_PREDICTION` | `pathway_c_stacker` | `clinical` |

---

## Case 6: Gut only

### STAGE 0 — INPUT FILES
- **Files Supplied:** `gut_microbiome_report.txt`
- **File Types:** Plain Text Microbiome Lab Report
- **Modalities Present:** `gut`
- **Modalities Intentionally Absent:** `clinical`, `wearable`

### STAGE 1 — DOCUMENTREADER / CONTRACT 1
- **Total Pages Extracted:** 1 (elapsed: 0.0014s)
  - **File `gut_microbiome_report.txt` (Page 0):** status=`unknown`, method=`plain_text`, length=1137 chars, OCR confidence=N/A
    *Text Preview:* "============================================================ GUT MICROBIOME ANALYSIS REPORT ============================================================  Patient : Arjun Mehta Lab ..."

### STAGE 2 — FEATUREMAPPER / CONTRACT 2 (BEFORE HARNESS)
- **Patient Info Captured:** ID=`None`, Name=`Arjun Mehta`, Age=`None`, Gender=`None`
- **`clinical` Domain:** status=`not_available`, resolved=0 fields, missing=['Age', 'Gender', 'Height', 'Weight', 'BMI', 'Waist_Circumference', 'Systolic_BP', 'Diastolic_BP', 'Fasting_Blood_Glucose', 'HbA1c', 'Triglycerides', 'HDL', 'LDL', 'ALT', 'AST', 'Family_History_Diabetes', 'Family_History_Hypertension', 'Family_History_CVD']
- **`wearable` Domain:** status=`not_available`, resolved=0 fields, missing=['Average_Daily_Steps', 'Active_Minutes', 'Sedentary_Time_Minutes', 'Resting_Heart_Rate', 'Heart_Rate_Variability_RMSSD', 'Sleep_Duration_Hours', 'Sleep_Efficiency_Score', 'Autonomic_Stress_Score', 'Activity_Energy_Expenditure', 'Exercise_Frequency_Days', 'CGM_Average_Glucose', 'CGM_Glucose_CV', 'CGM_Time_In_Range', 'CGM_Time_Above_Range', 'CGM_Time_Below_Range']
- **`gut` Domain:** status=`complete`, resolved=21 fields, missing=[]
  *Values Sample:* Akkermansia=2.1, Faecalibacterium=7.3, Roseburia=3.8, Bifidobacterium=4.2, Bacteroides=18.6, Prevotella=9.4, ... (+15 more)

### STAGE 3 — TEST-ONLY USER FORM SIMULATION
- **Harness Status:** Not applicable (Clinical domain was not incomplete solely due to family history).

### STAGE 4 — MODELROUTER + LEVEL-0 MODELS
- **`clinical` Dispatch:** status = **`not_run`**
  *Reason:* `Mapper status was 'not_available' (expected 'complete')` (Model was NOT executed)
- **`wearable` Dispatch:** status = **`not_run`**
  *Reason:* `Mapper status was 'not_available' (expected 'complete')` (Model was NOT executed)
- **`gut` Dispatch:** status = **`success`**
  *Level-0 Inference Results:*
    - `Type2_Diabetes`: raw_prob = 0.6913 (69.13%), decision = `1`
    - `Prediabetes`: raw_prob = 0.5384 (53.84%), decision = `0`
    - `High_Adiposity_Risk`: raw_prob = 0.6813 (68.13%), decision = `1`
    - `Metabolic_Syndrome`: raw_prob = 0.6473 (64.73%), decision = `1`
    - `NAFLD`: raw_prob = 0.5795 (57.95%), decision = `1`

### STAGE 5 — FUSION V2 EXECUTION
- **Pathway Applied:** `G` (Gut Only Stacker), Case: `G`, Active Modalities: `['gut']`

#### Final Disease Decisions Table:

| Disease | Risk Score | Risk % | Decision | Threshold | Confidence Label | Strategy | Modalities Used |
|:---|---:|---:|:---:|:---:|:---:|:---:|:---:|
| **Type2 Diabetes** | 0.6006 | 60.06% | **Positive** | 0.36 | `REDUCED_MODALITY` | `pathway_g_stacker` | `gut` |
| **Prediabetes** | 0.3795 | 37.95% | **N/A (Suppressed)** | 0.24 | `SUPPRESSED_BY_T2D` | `pathway_g_stacker` | `gut` |
| **High Adiposity Risk** | 0.5140 | 51.40% | **Positive** | 0.34 | `REDUCED_MODALITY` | `pathway_g_stacker` | `gut` |
| **Metabolic Syndrome** | 0.1656 | 16.56% | **Negative** | 0.18 | `REDUCED_MODALITY` | `pathway_g_stacker` | `gut` |
| **NAFLD** | 0.2049 | 20.49% | **Negative** | 0.25 | `REDUCED_MODALITY` | `pathway_g_stacker` | `gut` |

---

## Case 7: Wearable only

### STAGE 0 — INPUT FILES
- **Files Supplied:** `fitbit_wearable_report.txt`
- **File Types:** Plain Text Wearable/CGM Export
- **Modalities Present:** `wearable`
- **Modalities Intentionally Absent:** `clinical`, `gut`

### STAGE 1 — DOCUMENTREADER / CONTRACT 1
- **Total Pages Extracted:** 1 (elapsed: 0.0018s)
  - **File `fitbit_wearable_report.txt` (Page 0):** status=`unknown`, method=`plain_text`, length=1007 chars, OCR confidence=N/A
    *Text Preview:* "============================================================ FITBIT HEALTH SUMMARY ============================================================  Patient          : Arjun Mehta Repo..."

### STAGE 2 — FEATUREMAPPER / CONTRACT 2 (BEFORE HARNESS)
- **Patient Info Captured:** ID=`None`, Name=`Arjun Mehta`, Age=`None`, Gender=`None`
- **`clinical` Domain:** status=`not_available`, resolved=0 fields, missing=['Age', 'Gender', 'Height', 'Weight', 'BMI', 'Waist_Circumference', 'Systolic_BP', 'Diastolic_BP', 'Fasting_Blood_Glucose', 'HbA1c', 'Triglycerides', 'HDL', 'LDL', 'ALT', 'AST', 'Family_History_Diabetes', 'Family_History_Hypertension', 'Family_History_CVD']
- **`wearable` Domain:** status=`complete`, resolved=15 fields, missing=[]
  *Values Sample:* Average_Daily_Steps=6200.0, Active_Minutes=38.0, Sedentary_Time_Minutes=680.0, Resting_Heart_Rate=74.0, Heart_Rate_Variability_RMSSD=28.0, Sleep_Duration_Hours=6.4, ... (+9 more)
- **`gut` Domain:** status=`not_available`, resolved=0 fields, missing=['Akkermansia', 'Faecalibacterium', 'Roseburia', 'Bifidobacterium', 'Bacteroides', 'Prevotella', 'Ruminococcus', 'Blautia', 'Collinsella', 'Escherichia_Shigella', 'Coprococcus', 'Alistipes', 'Subdoligranulum', 'Enterococcus', 'Eubacterium', 'Parabacteroides', 'Lactobacillus', 'Klebsiella', 'Streptococcus', 'Eggerthella', 'Other_Taxa']

### STAGE 3 — TEST-ONLY USER FORM SIMULATION
- **Harness Status:** Not applicable (Clinical domain was not incomplete solely due to family history).

### STAGE 4 — MODELROUTER + LEVEL-0 MODELS
- **`clinical` Dispatch:** status = **`not_run`**
  *Reason:* `Mapper status was 'not_available' (expected 'complete')` (Model was NOT executed)
- **`wearable` Dispatch:** status = **`success`**
  *Level-0 Inference Results:*
    - `Type2_Diabetes`: raw_prob = 0.0183 (1.83%), decision = `0`
    - `Prediabetes`: raw_prob = 0.9442 (94.42%), decision = `1`
    - `High_Adiposity_Risk`: raw_prob = 0.8072 (80.72%), decision = `1`
    - `Metabolic_Syndrome`: raw_prob = 0.4551 (45.51%), decision = `0`
    - `NAFLD`: raw_prob = 0.5460 (54.60%), decision = `1`
- **`gut` Dispatch:** status = **`not_run`**
  *Reason:* `Mapper status was 'not_available' (expected 'complete')` (Model was NOT executed)

### STAGE 5 — FUSION V2 EXECUTION
- **Pathway Applied:** `W` (Wearable Only Stacker), Case: `W`, Active Modalities: `['wearable']`

#### Final Disease Decisions Table:

| Disease | Risk Score | Risk % | Decision | Threshold | Confidence Label | Strategy | Modalities Used |
|:---|---:|---:|:---:|:---:|:---:|:---:|:---:|
| **Type2 Diabetes** | 0.0050 | 0.50% | **Negative** | 0.44 | `REDUCED_MODALITY` | `pathway_w_stacker` | `wearable` |
| **Prediabetes** | 0.9185 | 91.85% | **Positive** | 0.36 | `REDUCED_MODALITY` | `pathway_w_stacker` | `wearable` |
| **High Adiposity Risk** | 0.6510 | 65.10% | **Positive** | 0.28 | `REDUCED_MODALITY` | `pathway_w_stacker` | `wearable` |
| **Metabolic Syndrome** | 0.0396 | 3.96% | **Negative** | 0.12 | `REDUCED_MODALITY` | `pathway_w_stacker` | `wearable` |
| **NAFLD** | 0.1769 | 17.69% | **Positive** | 0.12 | `REDUCED_MODALITY` | `pathway_w_stacker` | `wearable` |

---

## Case 8: No usable modality

### STAGE 0 — INPUT FILES
- **Files Supplied:** `non_medical_doc.txt`
- **File Types:** Non-medical Pharmacy Invoice
- **Modalities Present:** None
- **Modalities Intentionally Absent:** `clinical`, `gut`, `wearable`

### STAGE 1 — DOCUMENTREADER / CONTRACT 1
- **Total Pages Extracted:** 1 (elapsed: 0.0012s)
  - **File `non_medical_doc.txt` (Page 0):** status=`unknown`, method=`plain_text`, length=493 chars, OCR confidence=N/A
    *Text Preview:* "============================================================ ACME PHARMACY INVOICE & RECEIPT ============================================================ Order ID: ORD-992144 Date:..."

### STAGE 2 — FEATUREMAPPER / CONTRACT 2 (BEFORE HARNESS)
- **Patient Info Captured:** ID=`None`, Name=`None`, Age=`None`, Gender=`None`
- **`clinical` Domain:** status=`not_available`, resolved=0 fields, missing=['Age', 'Gender', 'Height', 'Weight', 'BMI', 'Waist_Circumference', 'Systolic_BP', 'Diastolic_BP', 'Fasting_Blood_Glucose', 'HbA1c', 'Triglycerides', 'HDL', 'LDL', 'ALT', 'AST', 'Family_History_Diabetes', 'Family_History_Hypertension', 'Family_History_CVD']
- **`wearable` Domain:** status=`not_available`, resolved=0 fields, missing=['Average_Daily_Steps', 'Active_Minutes', 'Sedentary_Time_Minutes', 'Resting_Heart_Rate', 'Heart_Rate_Variability_RMSSD', 'Sleep_Duration_Hours', 'Sleep_Efficiency_Score', 'Autonomic_Stress_Score', 'Activity_Energy_Expenditure', 'Exercise_Frequency_Days', 'CGM_Average_Glucose', 'CGM_Glucose_CV', 'CGM_Time_In_Range', 'CGM_Time_Above_Range', 'CGM_Time_Below_Range']
- **`gut` Domain:** status=`not_available`, resolved=0 fields, missing=['Akkermansia', 'Faecalibacterium', 'Roseburia', 'Bifidobacterium', 'Bacteroides', 'Prevotella', 'Ruminococcus', 'Blautia', 'Collinsella', 'Escherichia_Shigella', 'Coprococcus', 'Alistipes', 'Subdoligranulum', 'Enterococcus', 'Eubacterium', 'Parabacteroides', 'Lactobacillus', 'Klebsiella', 'Streptococcus', 'Eggerthella', 'Other_Taxa']

### STAGE 3 — TEST-ONLY USER FORM SIMULATION
- **Harness Status:** Not applicable (Clinical domain was not incomplete solely due to family history).

### STAGE 4 — MODELROUTER + LEVEL-0 MODELS
- **`clinical` Dispatch:** status = **`not_run`**
  *Reason:* `Mapper status was 'not_available' (expected 'complete')` (Model was NOT executed)
- **`wearable` Dispatch:** status = **`not_run`**
  *Reason:* `Mapper status was 'not_available' (expected 'complete')` (Model was NOT executed)
- **`gut` Dispatch:** status = **`not_run`**
  *Reason:* `Mapper status was 'not_available' (expected 'complete')` (Model was NOT executed)

### STAGE 5 — FUSION V2 EXECUTION
- **Pathway Applied:** `insufficient` (Insufficient Modalities), Case: `none`, Active Modalities: `[]`

#### Final Disease Decisions Table:

| Disease | Risk Score | Risk % | Decision | Threshold | Confidence Label | Strategy | Modalities Used |
|:---|---:|---:|:---:|:---:|:---:|:---:|:---:|
| **Type2 Diabetes** | N/A | N/A | **N/A** | N/A | `INSUFFICIENT_EVIDENCE` | `insufficient` | `None` |
| **Prediabetes** | N/A | N/A | **N/A** | N/A | `INSUFFICIENT_EVIDENCE` | `insufficient` | `None` |
| **High Adiposity Risk** | N/A | N/A | **N/A** | N/A | `INSUFFICIENT_EVIDENCE` | `insufficient` | `None` |
| **Metabolic Syndrome** | N/A | N/A | **N/A** | N/A | `INSUFFICIENT_EVIDENCE` | `insufficient` | `None` |
| **NAFLD** | N/A | N/A | **N/A** | N/A | `INSUFFICIENT_EVIDENCE` | `insufficient` | `None` |

---

## Executive Pipeline Audit & Synthesis

### 1. Availability Combinations Verification
All 8 availability combinations were executed end-to-end starting strictly from real disk files:
- **Case 1 (Clinical + Gut + Wearable):** Successfully executed full 3-modality pathway stacking.
- **Case 2 (Clinical + Gut):** Successfully executed 2-modality C+G pathway stacking.
- **Case 3 (Clinical + Wearable):** Successfully executed 2-modality C+W pathway stacking.
- **Case 4 (Gut + Wearable):** Successfully executed 2-modality G+W pathway stacking.
- **Case 5 (Clinical only):** Successfully executed single-modality Clinical pathway.
- **Case 6 (Gut only):** Successfully executed single-modality Gut pathway.
- **Case 7 (Wearable only):** Successfully executed single-modality Wearable pathway.
- **Case 8 (No usable modality):** Successfully executed Insufficient Evidence fallback.

**Report File Location:** `D:\Desktop\telemedicine platform\reports\full_pipeline_e2e_trace_report.md`