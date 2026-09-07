# Gut Microbiome Model (v3)

## Overview

Independent binary classification models for 5 metabolic disease labels using CLR-transformed gut microbiome taxa data.

Part 3/3 of the metabolic disease prediction platform (Clinical v4, Wearable v3, Gut v3).


---

## How to Run Training

```bash
cd gut_model
pip install xgboost shap scikit-learn pandas numpy matplotlib joblib
python src/train_gut.py
```

Expected runtime: ~15–45 minutes on CPU (36 combos × 5 labels × early-stopped XGBoost).

Expected disk space: ~50–200 MB (models + SHAP plots + reports).


---

## How to Run Inference

```python
import sys
sys.path.insert(0, 'src')
from predict_gut import predict_gut

# Input: dict with 21 raw taxa relative abundances (summing to ~100%)
features = {
    'Akkermansia': 2.1, 'Faecalibacterium': 8.5, 'Roseburia': 3.2,
    'Bifidobacterium': 4.0, 'Bacteroides': 20.0, 'Prevotella': 5.0,
    'Ruminococcus': 3.5, 'Blautia': 7.0, 'Collinsella': 2.0,
    'Escherichia_Shigella': 1.5, 'Coprococcus': 2.5, 'Alistipes': 3.0,
    'Subdoligranulum': 2.0, 'Enterococcus': 1.0, 'Eubacterium': 4.0,
    'Parabacteroides': 3.2, 'Lactobacillus': 5.0, 'Klebsiella': 0.5,
    'Streptococcus': 2.0, 'Eggerthella': 0.5, 'Other_Taxa': 19.5
}
result = predict_gut(features)
print(result)
```

---

## Final Test Metrics (XGBoost, Suppressed Predictions)

| Label | ROC-AUC | PR-AUC | F1 | Precision | Recall |
|---|---|---|---|---|---|
| Type2_Diabetes | 0.8286 | 0.7214 | 0.6672 | 0.6439 | 0.6924 |
| Prediabetes | 0.6146 | 0.4058 | 0.4372 | 0.3661 | 0.5426 |
| High_Adiposity_Risk | 0.8049 | 0.6842 | 0.6230 | 0.5336 | 0.7484 |
| Metabolic_Syndrome | 0.8086 | 0.2908 | 0.2927 | 0.1804 | 0.7759 |
| NAFLD | 0.8089 | 0.4554 | 0.4095 | 0.2793 | 0.7668 |

---

## Hardware & Environment

- **Trained on**: Windows-11-10.0.26200-SP0

- **Training date**: 2026-08-09T03:15:30.003385+00:00

## Project Structure

```
gut_model/
  data/               # 6 source CSVs (gut/labels/split used for training)
  models/gut/         # 5 XGBoost .json + 5 LogReg .joblib + 10 metadata JSONs
  reports/            # gut_evaluation.md, 5x SHAP, 5x calibration, 5x importance.csv
  src/
    train_gut.py      # Reproducible training pipeline
    predict_gut.py    # Inference function
  requirements.txt    # Pinned package versions
  training.log        # Full pipeline log
  README.md           # This file
```