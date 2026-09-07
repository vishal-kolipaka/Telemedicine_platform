import json

with open('investigation_results.json') as f:
    data = json.load(f)

for dis in ['Type2_Diabetes', 'Prediabetes', 'High_Adiposity_Risk']:
    dinfo = data[dis]
    print(f"\n{'='*35} {dis} {'='*35}")
    print("--- 1. INDIVIDUAL MODALITIES (Validation) ---")
    for m in ['C', 'G', 'W']:
        vm = dinfo['val_metrics'][m]
        tm = dinfo['test_metrics'][m]
        print(f"  {m:3s} | VAL : ROC={vm['ROC-AUC']:.4f} | PR={vm['PR-AUC']:.4f} | F1={vm['F1']:.4f} | Brier={vm['Brier']:.4f} | ECE={vm['ECE']:.4f} | Thresh={dinfo['thresholds'][m]:.2f}")
        print(f"      | TEST: ROC={tm['ROC-AUC']:.4f} | PR={tm['PR-AUC']:.4f} | F1={tm['F1']:.4f} | Brier={tm['Brier']:.4f} | ECE={tm['ECE']:.4f}")
    
    print("\n--- 2. ALL COMBINATIONS (Validation - All Strategies) ---")
    for c in ['C', 'G', 'W', 
              'C+G_SimpleAvg', 'C+G_WeightedAvg', 'C+G_Logistic', 'C+G_Interaction',
              'C+W_SimpleAvg', 'C+W_WeightedAvg', 'C+W_Logistic', 'C+W_Interaction',
              'G+W_SimpleAvg', 'G+W_WeightedAvg', 'G+W_Logistic', 'G+W_Interaction',
              'C+G+W_SimpleAvg', 'C+G+W_WeightedAvg', 'C+G+W_Logistic', 'C+G+W_LogisticNonNeg', 'C+G+W_Interaction']:
        if c in dinfo['val_metrics']:
            vm = dinfo['val_metrics'][c]
            tm = dinfo['test_metrics'][c]
            print(f"  {c:22s} | VAL ROC={vm['ROC-AUC']:.4f}, PR={vm['PR-AUC']:.4f}, F1={vm['F1']:.4f}, Brier={vm['Brier']:.4f}, ECE={vm['ECE']:.4f} | TEST ROC={tm['ROC-AUC']:.4f}, PR={tm['PR-AUC']:.4f}, F1={tm['F1']:.4f}")
            
    print("\n--- 3. FORMULAS & COEFFICIENTS ---")
    for c in ['C+G_Logistic', 'C+W_Logistic', 'G+W_Logistic', 'C+G+W_Logistic', 'C+G+W_LogisticNonNeg', 'C+G+W_Interaction']:
        if c in dinfo['formulas']:
            print(f"  {c:22s}: {dinfo['formulas'][c]}")

    print("\n--- 4. BOOTSTRAP 95% CIs (5,000 Replicates on Validation) ---")
    for comp, bres in dinfo['bootstrap'].items():
        sig_str = "SIGNIFICANT" if bres['roc_sig'] else "NOT_SIG"
        print(f"  {comp:25s} | dROC={bres['delta_roc']:+.4f} CI=[{bres['roc_ci'][0]:+.4f}, {bres['roc_ci'][1]:+.4f}] ({sig_str:11s}) | dPR={bres['delta_pr']:+.4f} CI=[{bres['pr_ci'][0]:+.4f}, {bres['pr_ci'][1]:+.4f}]")
