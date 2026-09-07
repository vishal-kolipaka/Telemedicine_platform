import json
import pandas as pd
import numpy as np

# 1. Load manifest
with open('src/fusion_v2/models/pathway_manifest.json') as f:
    manifest = json.load(f)

print("="*80)
print("AUDIT TASK 1 & 2: 35 PATHWAY-DISEASE META-MODELS TABLE")
print("="*80)

rows = []
for p, pdata in manifest['models'].items():
    mods = pdata['modalities']
    for d, ddata in pdata['diseases'].items():
        coefs = ddata['coefficients']
        intercept = ddata['intercept']
        platt = ddata.get('platt_scaling', {})
        thresh = ddata['threshold']
        val_m = ddata.get('validation_metrics', {})
        test_m = ddata.get('test_metrics', {})
        formula = ddata.get('formula', '')
        
        rows.append({
            'Pathway': p,
            'Disease': d,
            'Input_Dim': len(mods),
            'Num_Coefs': len(coefs),
            'Intercept': intercept,
            'Coefficients': str(coefs),
            'Platt_A': platt.get('A'),
            'Platt_B': platt.get('B'),
            'Threshold': thresh,
            'Val_ROC': val_m.get('roc_auc'),
            'Val_PR': val_m.get('pr_auc'),
            'Val_F1': val_m.get('f1'),
            'Test_ROC': test_m.get('roc_auc'),
            'Test_PR': test_m.get('pr_auc'),
            'Test_F1': test_m.get('f1'),
            'Formula': formula
        })

df = pd.DataFrame(rows)
print(f"Total Models Found: {len(df)}")
for i, r in df.iterrows():
    print(f"[{r['Pathway']:5s}] {r['Disease']:22s} | Dim={r['Input_Dim']} | Intercept={r['Intercept']:+9.4f} | Platt(A={r['Platt_A']:+.4f}, B={r['Platt_B']:+.4f}) | Thresh={r['Threshold']:.2f} | Val ROC={r['Val_ROC']:.4f} PR={r['Val_PR']:.4f} | Test ROC={r['Test_ROC']:.4f} PR={r['Test_PR']:.4f} | Formula: {r['Formula']}")

print("\n" + "="*80)
print("SPECIFIC AUDIT TASK 1 INSPECTION SAMPLES")
print("="*80)

sample_keys = [
    ("C", "Type2_Diabetes"),
    ("C_W", "Type2_Diabetes"),
    ("C_W_G", "Type2_Diabetes"),
    ("C_G", "Metabolic_Syndrome"),
    ("W_G", "NAFLD")
]

for p, d in sample_keys:
    entry = manifest['models'][p]['diseases'][d]
    print(f"\n--- Model: Pathway='{p}', Disease='{d}' ---")
    print(json.dumps(entry, indent=2))
