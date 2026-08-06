# Wearable Metabolic Disease Prediction Model (v3) — Operational Guide

This repository contains the standalone, end-to-end Wearable Model component for the metabolic disease prediction platform.

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
python src/train_wearable.py
```

### Inference API
To make predictions programmatically for a single patient using 15 wearable features:
```python
from src.predict_wearable import predict_wearable

patient_data = {
    "Average_Daily_Steps": 10000.0, "Active_Minutes": 45.0, "Sedentary_Time_Minutes": 480.0,
    "Resting_Heart_Rate": 65.0, "Heart_Rate_Variability_RMSSD": 55.0, "Sleep_Duration_Hours": 7.5,
    "Sleep_Efficiency_Score": 88.0, "Autonomic_Stress_Score": 25.0, "Activity_Energy_Expenditure": 450.0,
    "Exercise_Frequency_Days": 4.0, "CGM_Average_Glucose": 95.0, "CGM_Glucose_CV": 18.0,
    "CGM_Time_In_Range": 95.0, "CGM_Time_Above_Range": 3.0, "CGM_Time_Below_Range": 2.0
}

result = predict_wearable(patient_data)
print("Raw Probabilities:", result["probabilities"])
print("Final Predictions (Suppressed):", result["predictions"])
```

### Running Unit Tests
To run the unit test suite covering schema, datatype, physiological range validation, min/max plausible values, and suppression logic:
```bash
python -m unittest tests/test_predict_wearable.py
```

---

## 2. Final Test Set Performance Summary (XGBoost v3)

Evaluated on the fixed 3,000 Test set split (`scale_pos_weight` computed from Train split, threshold fixed at 0.5):

| Label | ROC-AUC | PR-AUC | F1 Score | Precision | Recall | Brier Score |
|---|---|---|---|---|---|---|
| **Type2_Diabetes** | 0.9915 | 0.9859 | 0.9280 | 0.8940 | 0.9646 | 0.0385 |
| **Prediabetes** | 0.9623 | 0.9229 | 0.8195 | 0.8252 | 0.8138 | 0.0781 |
| **High_Adiposity_Risk** | 0.8106 | 0.6432 | 0.6458 | 0.5566 | 0.7692 | 0.1797 |
| **Metabolic_Syndrome** | 0.7274 | 0.1724 | 0.2433 | 0.1477 | 0.6897 | 0.2275 |
| **NAFLD** | 0.6009 | 0.1796 | 0.2703 | 0.1758 | 0.5841 | 0.2416 |

---

## 3. Operations & System Resource Specifications

- **Expected Training Runtime**: ~45-50 seconds (CPU multi-threading, 36 combinations x 5 models).
- **Hardware Used**: Standard Multi-core CPU (Intel/AMD 6+ cores).
- **Disk Space Requirement**:
  - Raw Datasets (`./data/`): ~9.0 MB
  - Models & Metadata (`./models/wearable/`): ~1.5 MB (5 native XGBoost `.json` + 5 LogReg `.joblib`)
  - Evaluation Reports & SHAP Artifacts (`./reports/`): ~2.5 MB
  - **Total Space**: ~13.0 MB

---

## 4. Directory Artifacts Overview

```
wearable_model/
├── data/                       # Source CSV datasets (6 files)
├── models/
│   └── wearable/               # 5 XGBoost JSON models + 5 LogReg Joblib pipelines + 10 metadata JSONs
├── reports/
│   ├── wearable_evaluation.md  # Detailed markdown evaluation report
│   ├── shap_summary_<label>.png # 5 SHAP summary plots
│   └── importance_<label>.csv  # 5 SHAP feature importance tables
├── src/
│   ├── train_wearable.py       # End-to-end training pipeline script
│   └── predict_wearable.py     # Input-validated inference interface
├── tests/
│   └── test_predict_wearable.py# Unit test suite
├── requirements.txt            # Pinned package versions
├── training.log                # Execution and log trace
└── README.md                   # Operational guide
```
