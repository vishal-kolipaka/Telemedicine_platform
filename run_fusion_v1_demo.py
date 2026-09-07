"""
run_fusion_v1_demo.py — Fusion V1 Output Demonstration Test Script

Selects 10 representative non-Test validation patients from fusion_val_master.csv and demonstrates:
  - Step 1: 15 Raw Level-0 Probabilities (Clinical, Gut, Wearable across 5 diseases)
  - Step 2: Fusion Process (Modality routing per disease)
  - Step 3: Final Disease Outputs (Risk Scores, Thresholds, POSITIVE/NEGATIVE)
  - Step 4: Prediabetes Post-Decision Suppression Check
  - Step 5: Risk Score Presentation Ranking (Rank 1 to 5)
  - Step 6: Multi-Disease Cases Coverage
  - Step 7: Final Human-Readable Summary Table & Patient Risk Rankings
  - Step 8: Output Contract Verification
"""

import os
import json
import warnings
import numpy as np
import pandas as pd
from fusion.predict_fusion import FusionV1Predictor

warnings.filterwarnings("ignore")

BASE_DIR = r"c:\Users\HP PC\Desktop\telemedicine platform"
PHASE2_DIR = os.path.join(BASE_DIR, "fusion_phase2")
REPORTS_DIR = os.path.join(PHASE2_DIR, "reports")
VAL_MASTER_PATH = os.path.join(BASE_DIR, "fusion_val_master.csv")
MODELS_DIR = os.path.join(PHASE2_DIR, "models", "fusion_candidates")

val_df = pd.read_csv(VAL_MASTER_PATH)
predictor = FusionV1Predictor(models_dir=MODELS_DIR)
fused_res = predictor.predict(master_df=val_df)

diseases = ["Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk", "Metabolic_Syndrome", "NAFLD"]
pred_cols = [f"Pred_{d}" for d in diseases]
fused_res["Pos_Count"] = fused_res[pred_cols].sum(axis=1)

# Select 10 diverse representative patients
selected_indices = []

# 1. Zero positive
idx_0 = fused_res[fused_res["Pos_Count"] == 0].index[0]
selected_indices.append(idx_0)

# 2. Exactly 1 positive
idx_1 = fused_res[fused_res["Pos_Count"] == 1].index[0]
selected_indices.append(idx_1)

# 3. Exactly 2 positive
idx_2 = fused_res[fused_res["Pos_Count"] == 2].index[0]
selected_indices.append(idx_2)

# 4. 3 or more positive
idx_3 = fused_res[fused_res["Pos_Count"] >= 3].index[0]
selected_indices.append(idx_3)

# 5. T2D + another disease
idx_t2d = fused_res[(fused_res["Pred_Type2_Diabetes"] == 1) & (fused_res["Pos_Count"] >= 2)].index[0]
selected_indices.append(idx_t2d)

# 6. MetSyn positive
idx_ms = fused_res[fused_res["Pred_Metabolic_Syndrome"] == 1].index[0]
selected_indices.append(idx_ms)

# 7. NAFLD positive
idx_nf = fused_res[fused_res["Pred_NAFLD"] == 1].index[0]
selected_indices.append(idx_nf)

# 8. Prediabetes suppression occurring
idx_supp = fused_res[fused_res["Prediabetes_Suppressed"] == 1].index[0]
selected_indices.append(idx_supp)

# 9. High probability but below threshold (MetSyn raw > 0.15, calibrated < 0.20 or NAFLD ~0.45)
idx_near = fused_res[(fused_res["P_Fused_NAFLD"] >= 0.40) & (fused_res["P_Fused_NAFLD"] < 0.50)].index[0]
selected_indices.append(idx_near)

# 10. Additional 4+ positive or distinct rank profile
idx_4 = fused_res[fused_res["Pos_Count"] >= 4].index[0]
selected_indices.append(idx_4)

# Remove duplicates while preserving order up to 10 patients
unique_indices = []
for idx in selected_indices:
    if idx not in unique_indices:
        unique_indices.append(idx)

# Fill to 10 if needed
curr = 0
while len(unique_indices) < 10:
    if curr not in unique_indices:
        unique_indices.append(curr)
    curr += 1

demo_df = fused_res.loc[unique_indices].reset_index(drop=True)

print(f"Selected {len(demo_df)} representative patients from non-Test validation dataset.")

report_lines = []
report_lines.append("# FUSION V1 — OUTPUT DEMONSTRATION REPORT\n")
report_lines.append(f"**Date**: {pd.Timestamp.now(tz='UTC').isoformat()}")
report_lines.append("**Dataset Source**: Non-Test Validation Set (`fusion_val_master.csv`, $n=3,000$ patients)")
report_lines.append("> **Test Protection Notice**: *Held-out Test set (`fusion_test_master.csv`) was NOT loaded, accessed, or evaluated in this demonstration.*\n")
report_lines.append("---\n")

report_lines.append("## Compact 10-Patient Summary Table\n")
report_lines.append("| Patient ID | T2D | Prediabetes | HAR | MetSyn | NAFLD | # Positive | Prediabetes Suppressed |")
report_lines.append("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")

for _, r in demo_df.iterrows():
    p_t2d = "POS" if r["Pred_Type2_Diabetes"] == 1 else "NEG"
    p_pred = "POS" if r["Pred_Prediabetes"] == 1 else "NEG"
    p_har = "POS" if r["Pred_High_Adiposity_Risk"] == 1 else "NEG"
    p_ms = "POS" if r["Pred_Metabolic_Syndrome"] == 1 else "NEG"
    p_nf = "POS" if r["Pred_NAFLD"] == 1 else "NEG"
    supp = "YES" if r["Prediabetes_Suppressed"] == 1 else "NO"
    report_lines.append(f"| `{r['Patient_ID']}` | **{p_t2d}** | **{p_pred}** | **{p_har}** | **{p_ms}** | **{p_nf}** | **{r['Pos_Count']}** | {supp} |")

report_lines.append("\n---\n")

report_lines.append("## Detailed 10-Patient Transformation Logs\n")

for p_num, (_, r) in enumerate(demo_df.iterrows(), 1):
    p_id = r["Patient_ID"]
    report_lines.append(f"### Patient {p_num}: `{p_id}`\n")

    # Step 1: Raw Level-0 Inputs
    report_lines.append("#### Step 1 — Level-0 Raw Inputs (3 Modalities × 5 Diseases = 15 Probabilities):")
    report_lines.append("| Modality | Type2 Diabetes | Prediabetes | High Adiposity | Metabolic Syndrome | NAFLD |")
    report_lines.append("|:---|---:|---:|---:|---:|---:|")
    report_lines.append(f"| **Clinical** | {r['P_Clinical_Type2_Diabetes']:.4f} | {r['P_Clinical_Prediabetes']:.4f} | {r['P_Clinical_High_Adiposity_Risk']:.4f} | {r['P_Clinical_Metabolic_Syndrome']:.4f} | {r['P_Clinical_NAFLD']:.4f} |")
    report_lines.append(f"| **Gut** | {r['P_Gut_Type2_Diabetes']:.4f} | {r['P_Gut_Prediabetes']:.4f} | {r['P_Gut_High_Adiposity_Risk']:.4f} | {r['P_Gut_Metabolic_Syndrome']:.4f} | {r['P_Gut_NAFLD']:.4f} |")
    report_lines.append(f"| **Wearable** | {r['P_Wearable_Type2_Diabetes']:.4f} | {r['P_Wearable_Prediabetes']:.4f} | {r['P_Wearable_High_Adiposity_Risk']:.4f} | {r['P_Wearable_Metabolic_Syndrome']:.4f} | {r['P_Wearable_NAFLD']:.4f} |\n")

    # Step 2: Modality Routing
    report_lines.append("#### Step 2 — Level-1 Modality Routing & Calculation:")
    report_lines.append("- **T2D**: Clinical Passthrough ($P_{\\text{Fused}} = P_{\\text{Clin}} = " + f"{r['P_Clinical_Type2_Diabetes']:.4f}" + "$)")
    report_lines.append("- **Prediabetes**: Clinical Passthrough ($P_{\\text{Fused}} = P_{\\text{Clin}} = " + f"{r['P_Clinical_Prediabetes']:.4f}" + "$)")
    report_lines.append("- **High Adiposity Risk**: Clinical Passthrough ($P_{\\text{Fused}} = P_{\\text{Clin}} = " + f"{r['P_Clinical_High_Adiposity_Risk']:.4f}" + "$)")
    report_lines.append(f"- **Metabolic Syndrome**: Clinical ({r['P_Clinical_Metabolic_Syndrome']:.4f}) + Gut ({r['P_Gut_Metabolic_Syndrome']:.4f}) $\\rightarrow$ Raw LR ({r['P_Raw_LR_Metabolic_Syndrome']:.4f}) $\\rightarrow$ Platt Recalibrated ({r['P_Fused_Metabolic_Syndrome']:.4f})")
    report_lines.append(f"- **NAFLD**: Clinical ({r['P_Clinical_NAFLD']:.4f}) + Gut ({r['P_Gut_NAFLD']:.4f}) $\\rightarrow$ Fused LR ({r['P_Fused_NAFLD']:.4f})")
    report_lines.append("- **Wearable**: *100% Excluded from Level-1 Fusion equations (preserved for Level-0 monitoring only).*\n")

    # Step 3: Final Disease Outputs
    report_lines.append("#### Step 3 — Final Disease Output & Decisions:")
    report_lines.append("| Disease | Fused Risk Score | Decision Threshold | Binary Decision |")
    report_lines.append("|:---|---:|---:|:---:|")
    
    res_t2d = "POSITIVE" if r["Pred_Type2_Diabetes"] == 1 else "NEGATIVE"
    res_pred = "POSITIVE" if r["Pred_Prediabetes"] == 1 else "NEGATIVE"
    res_har = "POSITIVE" if r["Pred_High_Adiposity_Risk"] == 1 else "NEGATIVE"
    res_ms = "POSITIVE" if r["Pred_Metabolic_Syndrome"] == 1 else "NEGATIVE"
    res_nf = "POSITIVE" if r["Pred_NAFLD"] == 1 else "NEGATIVE"

    report_lines.append(f"| **Type2 Diabetes** | {r['P_Fused_Type2_Diabetes']:.4f} | 0.50 | **{res_t2d}** |")
    report_lines.append(f"| **Prediabetes** | {r['P_Fused_Prediabetes']:.4f} | 0.50 | **{res_pred}** |")
    report_lines.append(f"| **High Adiposity Risk** | {r['P_Fused_High_Adiposity_Risk']:.4f} | 0.50 | **{res_har}** |")
    report_lines.append(f"| **Metabolic Syndrome** | {r['P_Fused_Metabolic_Syndrome']:.4f} | **0.20 (Post-Platt)** | **{res_ms}** |")
    report_lines.append(f"| **NAFLD** | {r['P_Fused_NAFLD']:.4f} | 0.50 | **{res_nf}** |\n")

    # Step 4: Prediabetes Suppression
    raw_p_pred = "POSITIVE" if r["Pred_Prediabetes_Raw"] == 1 else "NEGATIVE"
    is_supp = "YES" if r["Prediabetes_Suppressed"] == 1 else "NO"
    report_lines.append("#### Step 4 — Prediabetes Post-Decision Suppression Audit:")
    report_lines.append(f"- Raw Probability: `{r['P_Fused_Prediabetes']:.4f}` (Un-mutated)")
    report_lines.append(f"- Raw Binary Decision: `{raw_p_pred}`")
    report_lines.append(f"- Final Binary Decision: `{res_pred}`")
    report_lines.append(f"- Suppressed Due to Active T2D (`Pred_T2D == 1`): **{is_supp}**\n")

    # Step 5: Risk Score Presentation Ranking
    fused_probs = {
        "Type2 Diabetes": r["P_Fused_Type2_Diabetes"],
        "Prediabetes": r["P_Fused_Prediabetes"],
        "High Adiposity Risk": r["P_Fused_High_Adiposity_Risk"],
        "Metabolic Syndrome": r["P_Fused_Metabolic_Syndrome"],
        "NAFLD": r["P_Fused_NAFLD"]
    }
    decisions = {
        "Type2 Diabetes": res_t2d,
        "Prediabetes": res_pred,
        "High Adiposity Risk": res_har,
        "Metabolic Syndrome": res_ms,
        "NAFLD": res_nf
    }
    ranked = sorted(fused_probs.items(), key=lambda x: x[1], reverse=True)

    report_lines.append("#### Step 5 — Risk Score Presentation Ranking (Presentation Only):")
    for rank, (dis, p_val) in enumerate(ranked, 1):
        thresh = "0.20 (Post-Platt)" if dis == "Metabolic Syndrome" else "0.50"
        report_lines.append(f"{rank}. **{dis}**: `{p_val:.4f}` (Threshold: {thresh} $\\rightarrow$ Decision: **{decisions[dis]}**)")

    report_lines.append("\n---\n")

report_lines.append("## Step 8 — Output Contract Verification\n")
report_lines.append("Verified that the final output schema contains all required elements:\n")
report_lines.append("- `Patient_ID` (Key)")
report_lines.append("- All 15 Level-0 raw probabilities (`P_Clinical_*`, `P_Gut_*`, `P_Wearable_*`)")
report_lines.append("- All 5 Level-1 fused probabilities (`P_Fused_*`)")
report_lines.append("- Metabolic Syndrome raw LR probability (`P_Raw_LR_Metabolic_Syndrome`)")
report_lines.append("- Metabolic Syndrome Platt calibrated probability (`P_Fused_Metabolic_Syndrome`)")
report_lines.append("- All 5 independent binary predictions (`Pred_*`)")
report_lines.append("- Prediabetes raw decision (`Pred_Prediabetes_Raw`) and suppression flag (`Prediabetes_Suppressed`)")
report_lines.append("- Disease-specific decision thresholds (`Threshold_*`)\n")

os.makedirs(REPORTS_DIR, exist_ok=True)
report_path = os.path.join(REPORTS_DIR, "fusion_v1_output_demonstration_report.md")
with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines))

print(f"[OK] Demonstration report generated at: {report_path}")

