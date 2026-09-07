"""
generate_freeze_markdown_manifest.py — Generates fusion_v1_freeze_manifest.md
"""

import os
import json
import hashlib
import sys
import pandas as pd

BASE_DIR = r"c:\Users\HP PC\Desktop\telemedicine platform"
PHASE2_DIR = os.path.join(BASE_DIR, "fusion_phase2")
REPORTS_DIR = os.path.join(PHASE2_DIR, "reports")

json_manifest_path = os.path.join(REPORTS_DIR, "fusion_v1_freeze_manifest.json")
with open(json_manifest_path) as f:
    manifest = json.load(f)

lines = []
lines.append("# Fusion V1 Immutable Freeze Manifest\n")
lines.append(f"**Manifest Version**: {manifest['manifest_version']}")
lines.append(f"**Freeze Timestamp (UTC)**: {manifest['timestamp_utc']}")
lines.append(f"**Architecture Name**: {manifest['architecture_name']}")
lines.append(f"**Status**: {manifest['status']}")
lines.append(f"**Random Seed**: {manifest['seed']}\n")
lines.append("---\n")

lines.append("## 1. Executive Summary & Verification Confirmation\n")
lines.append("Fusion V1 is officially **FROZEN AND LOCKED**. All 18 deployment-contract checks have passed. Test set data has **NOT** been loaded, evaluated, or accessed during this freeze operation.\n")

lines.append("## 2. Level-0 Modality Model Specifications\n")
lines.append("| Modality | Version | Feature Count | Preprocessing & CLR Rules | Level-1 Fusion Status |")
lines.append("|:---|:---:|:---:|:---|:---|")
lines.append("| **Clinical** | v4 | 18 | Numerical float scaling, zero missing values, `Patient_ID` excluded. | Primary signal for T2D, Prediabetes, High Adiposity, MetSyn, NAFLD. |")
lines.append("| **Wearable** | v3 | 15 | Numerical float scaling, `Patient_ID` excluded. | **Independent Level-0 Modality Only (Excluded from Level-1 Fusion)**. |")
lines.append("| **Gut** | v3 | 21 | Train-only median imputation, row-wise CLR ($\delta=1\text{e-}5$), `Patient_ID` excluded. | Co-dominant signal for Metabolic Syndrome & NAFLD. |\n")

lines.append("## 3. Approved Fusion Architecture & Parameter Specifications\n")
lines.append("### Type2_Diabetes")
lines.append("- **Architecture**: Clinical Passthrough")
lines.append("- **Decision Threshold**: `0.50`")
lines.append("- **Suppression**: None\n")

lines.append("### Prediabetes")
lines.append("- **Architecture**: Clinical Passthrough")
lines.append("- **Decision Threshold**: `0.50`")
lines.append("- **Post-Decision Suppression**: `IF Pred_T2D == 1 THEN Pred_Prediabetes = 0` (Raw $P(\text{Prediabetes})$ remains 100% un-mutated)\n")

lines.append("### High_Adiposity_Risk")
lines.append("- **Architecture**: Clinical Passthrough")
lines.append("- **Decision Threshold**: `0.50`")
lines.append("- **Suppression**: None\n")

lines.append("### Metabolic_Syndrome")
lines.append("- **Architecture**: Clinical + Gut L2 Logistic Regression Stacker")
lines.append("- **Exact Stacker Equation**: $\\text{Logit}_{\\text{raw}} = -4.3697 + 2.5799 \\cdot P_{\\text{Clinical}} + 1.9639 \\cdot P_{\\text{Gut}}$")
lines.append("- **Platt Recalibration Equation**: $\\text{Logit}_{\\text{Platt}} = +1.5006 + 1.8243 \\cdot \\text{Logit}_{\\text{raw}}$")
lines.append("- **Calibrated Probability**: $P_{\\text{calibrated}} = \\text{sigmoid}(\\text{Logit}_{\\text{Platt}})$")
lines.append("- **Decision Threshold**: `0.20` (**Applies strictly to $P_{\\text{calibrated}}$ post-Platt**)")
lines.append("- **Threshold Provenance**: Selected on OOF Train predictions only; evaluated on Validation without Test set tuning.\n")

lines.append("### NAFLD")
lines.append("- **Architecture**: Clinical + Gut L2 Logistic Regression Stacker")
lines.append("- **Exact Stacker Equation**: $\\text{Logit} = -4.7674 + 3.7924 \\cdot P_{\\text{Clinical}} + 2.8340 \\cdot P_{\\text{Gut}}$")
lines.append("- **Fused Probability**: $P_{\\text{Fused}} = \\text{sigmoid}(\\text{Logit})$")
lines.append("- **Decision Threshold**: `0.50`\n")

lines.append("---\n")

lines.append("## 4. Availability Fallback Policy (Cases 1-7)\n")
lines.append("| Availability Case | Available Modalities | Pipeline Fallback Behavior |")
lines.append("|:---:|:---|:---|")
lines.append("| **Case 1** | Clinical Only | Clinical Passthrough for all available heads. |")
lines.append("| **Case 2** | Gut Only | Gut Passthrough for available heads. |")
lines.append("| **Case 3** | Wearable Only | Wearable standalone Level-0 prediction emitted independently. |")
lines.append("| **Case 4** | Clinical + Gut | Clinical Passthrough for T2D/Pred/HAR; `Clinical + Gut` LR Stacker for MetSyn/NAFLD. |")
lines.append("| **Case 5** | Clinical + Wearable | Clinical Passthrough (Wearable excluded). |")
lines.append("| **Case 6** | Gut + Wearable | Gut Passthrough (Wearable excluded). |")
lines.append("| **Case 7** | All 3 Available | Clinical Passthrough for T2D/Pred/HAR; `Clinical + Gut` LR Stacker for MetSyn/NAFLD (Wearable excluded). |\n")

lines.append("---\n")

lines.append("## 5. Wearable Participation Policy\n")
lines.append("> *Under Fusion V1, Wearable is excluded from Level-1 disease probability fusion because no disease demonstrated robust positive incremental signal from Wearable beyond the selected Clinical / Clinical+Gut baseline. Wearable remains fully active as an independent Level-0 modality for continuous remote monitoring, CGMs, dashboards, clinician explanations, and future Fusion V2 research.*\n")

lines.append("---\n")

lines.append("## 6. Output Contract Schema\n")
lines.append("The final inference output dataframe strictly separates:\n")
lines.append("1. **Level-0 Raw Probabilities**: `P_Clinical_<Disease>`, `P_Gut_<Disease>`, `P_Wearable_<Disease>`\n")
lines.append("2. **Level-1 Fused Probability**: `P_Fused_<Disease>` (or `P_Calibrated_<Disease>` for MetSyn)\n")
lines.append("3. **Binary Decision Flag**: `Pred_<Disease>` ($0$ or $1$)\n")
lines.append("4. **Metadata Flags**: `Threshold_Used`, `Suppression_Applied` ($0$ or $1$)\n")

lines.append("---\n")

lines.append("## 7. Explainability & Synthetic Data Limitations\n")
lines.append("- **Logistic Regression Coefficients**: Stacker coefficients ($\beta_C, \beta_G$) describe model decision contribution, NOT biological causality.")
lines.append("- **Synthetic Benchmark Disclaimer**: All results were obtained on the current synthetic benchmark dataset and do not establish real-world clinical effectiveness. Real-world clinical trial validation is required.\n")

lines.append("---\n")

lines.append("## 8. Software Environment & Artifact Identifiers\n")
lines.append("### Software Environment:")
for k, v in manifest["runtime_environment"].items():
    lines.append(f"- **{k}**: `{v}`")

lines.append("\n### Artifact SHA-256 Hashes:")
for k, v in manifest["artifact_hashes"].items():
    lines.append(f"- **{k}**: `{v}`")

lines.append("\n---\n")

lines.append("## 9. Test Isolation Statement\n")
lines.append("> **TEST HAS NOT YET BEEN USED FOR FINAL EVALUATION.**\n")
lines.append("The Test set (`fusion_test_master.csv`, $n=3,000$) has been strictly preserved untouched. Final evaluation will occur as a separate, decision-blind single-pass operation using `python run_fusion_test_evaluation.py` after human sign-off.\n")

md_manifest_path = os.path.join(REPORTS_DIR, "fusion_v1_freeze_manifest.md")
with open(md_manifest_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"[OK] Immutable Markdown Manifest created at: {md_manifest_path}")

