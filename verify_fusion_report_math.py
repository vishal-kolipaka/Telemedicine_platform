"""
verify_fusion_report_math.py
Verifies key numerical claims from fusion_investigation_report.md against extracted CSVs.
"""

import os
import pandas as pd
import numpy as np

EXTRACTED_DIR = r"c:\Users\HP PC\Desktop\telemedicine platform\fusion_analysis\extracted"

# 1. Base classification metrics & correlation
df_strat = pd.read_csv(os.path.join(EXTRACTED_DIR, "strategy_comparison.csv"))
print("=== Strategy Comparison (Strategy A vs C) ===")
print(df_strat[["Disease", "Best_Modality", "ROC_AUC_A", "ROC_AUC_C", "ROC_AUC_diff", "PR_AUC_A", "PR_AUC_C", "PR_AUC_diff", "CI_excludes_zero"]].to_string())

# 2. Confidence band analysis
df_conf = pd.read_csv(os.path.join(EXTRACTED_DIR, "confidence_band_analysis.csv"))
print("\n=== Key Confidence Band Slices (MetSyn & NAFLD 0.6-0.8 band) ===")
metsyn_mid = df_conf[(df_conf["Disease"] == "Metabolic_Syndrome") & (df_conf["Clinical_P_Band"] == "0.6-0.8")]
nafld_mid = df_conf[(df_conf["Disease"] == "NAFLD") & (df_conf["Clinical_P_Band"] == "0.6-0.8")]
print(metsyn_mid[["Disease", "Clinical_P_Band", "N", "Clinical_Acc_InBand", "Wearable_Acc_InBand", "Gut_Acc_InBand"]].to_string())
print(nafld_mid[["Disease", "Clinical_P_Band", "N", "Clinical_Acc_InBand", "Wearable_Acc_InBand", "Gut_Acc_InBand"]].to_string())

# 3. Pearson correlations
df_pearson = pd.read_csv(os.path.join(EXTRACTED_DIR, "correlation_pearson.csv"))
print("\n=== Pearson Correlations ===")
print(df_pearson.to_string())

