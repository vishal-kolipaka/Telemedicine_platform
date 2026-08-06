# Clinical Metabolic Disease Prediction Model (v4) — Operational Guide

This repository contains the standalone, end-to-end Clinical Model component for the metabolic disease prediction platform.

---

## 1. Quick Start & Execution

### Prerequisites & Installation
Ensure Python 3.13+ is installed. Install exact frozen dependencies:
```bash
pip install -r requirements.txt
```

### Training Pipeline
To run the full end-to-end training, grid search, evaluation, SHAP explainability, and artifact generation:
```bash
python src/train_clinical.py
```

### Inference API
To make predictions programmatically for a single patient:
```python
from src.predict_clinical import predict_clinical

patient_data = {
    "Age": 45, "Gender": 1, "Height": 175.0, "Weight": 70.0, "BMI": 22.86,
    "Waist_Circumference": 80.0, "Systolic_BP": 120.0, "Diastolic_BP": 80.0,
    "Fasting_Blood_Glucose": 90.0, "HbA1c": 5.2, "Triglycerides": 120.0,
    "HDL": 55.0, "LDL": 100.0, "ALT": 20.0, "AST": 22.0,
    "Family_History_Diabetes": 0, "Family_History_Hypertension": 0, "Family_History_CVD": 0
}

result = predict_clinical(patient_data)
print("Raw Probabilities:", result["probabilities"])
print("Final Predictions (Suppressed):", result["predictions"])
```

### Running Unit Tests
To run the unit test suite covering schema, datatype, physiological range validation, and suppression logic:
```bash
python -m unittest tests/test_predict_clinical.py
```

---

## 2. Final Test Set Performance Summary (XGBoost v4)

Evaluated on the fixed 3,000 Test set split (`scale_pos_weight` computed from Train split, threshold fixed at 0.5):

| Label | ROC-AUC | PR-AUC | F1 Score | Precision | Recall | Brier Score |
|---|---|---|---|---|---|---|
| **Type2_Diabetes** | 0.9997 | 0.9994 | 0.9941 | 0.9955 | 0.9927 | 0.0083 |
| **Prediabetes** | 0.9992 | 0.9981 | 0.9861 | 0.9893 | 0.9830 | 0.0079 |
| **High_Adiposity_Risk** | 0.9674 | 0.9340 | 0.8489 | 0.7932 | 0.9130 | 0.0730 |
| **Metabolic_Syndrome** | 0.8873 | 0.4383 | 0.3831 | 0.2517 | 0.8017 | 0.1295 |
| **NAFLD** | 0.9005 | 0.6129 | 0.5382 | 0.3946 | 0.8462 | 0.1325 |

---

## 3. Operations & System Resource Specifications

- **Expected Training Runtime**: ~55-60 seconds (CPU multi-threading, 36 combinations x 5 models).
- **Hardware Used**: Standard Multi-core CPU (Intel/AMD 6+ cores).
- **Disk Space Requirement**:
  - Raw Datasets (`./data/`): ~9.0 MB
  - Models & Metadata (`./models/clinical/`): ~1.5 MB (5 native XGBoost `.json` + 5 LogReg `.joblib`)
  - Evaluation Reports & SHAP Artifacts (`./reports/`): ~2.0 MB
  - **Total Space**: ~12.5 MB

---

## 4. Directory Artifacts Overview

```
clinical_model/
├── data/                       # Source CSV datasets (6 files)
├── models/
│   └── clinical/               # 5 XGBoost JSON models + 5 LogReg Joblib pipelines + 10 metadata JSONs
├── reports/
│   ├── clinical_evaluation.md  # Detailed markdown evaluation report
│   ├── shap_summary_<label>.png # 5 SHAP summary plots
│   └── importance_<label>.csv  # 5 SHAP feature importance tables
├── src/
│   ├── train_clinical.py       # End-to-end training pipeline script
│   └── predict_clinical.py     # Input-validated inference interface
├── tests/
│   └── test_predict_clinical.py# Unit test suite
├── requirements.txt            # Pinned package versions
├── training.log                # Execution and log trace
└── README.md                   # Operational guide
```
