"""
redteam_audit_checks.py — Script inspecting files and artifacts for Audits 1-16
"""

import os
import json
import hashlib
import pandas as pd
import numpy as np

BASE_DIR = r"c:\Users\HP PC\Desktop\telemedicine platform"

def check_file(rel_path):
    p = os.path.join(BASE_DIR, rel_path)
    exists = os.path.exists(p)
    return p, exists

# Check level-0 metadata
clin_meta_path, clin_meta_exists = check_file(os.path.join("clinical_model", "models", "clinical_xgboost_v4_metadata.json"))
wear_meta_path, wear_meta_exists = check_file(os.path.join("wearable_model", "models", "wearable_xgboost_v3_metadata.json"))
gut_meta_path, gut_meta_exists = check_file(os.path.join("gut_model", "models", "gut_xgboost_v3_metadata.json"))

print("=== LEVEL-0 METADATA CHECK ===")
print(f"Clinical Meta Exists: {clin_meta_exists}")
print(f"Wearable Meta Exists: {wear_meta_exists}")
print(f"Gut Meta Exists: {gut_meta_exists}")

if clin_meta_exists:
    with open(clin_meta_path) as f:
        c_m = json.load(f)
    print("Clinical Metadata Keys:", list(c_m.keys())[:10])

if wear_meta_exists:
    with open(wear_meta_path) as f:
        w_m = json.load(f)
    print("Wearable Metadata Keys:", list(w_m.keys())[:10])

if gut_meta_exists:
    with open(gut_meta_path) as f:
        g_m = json.load(f)
    print("Gut Metadata Keys:", list(g_m.keys())[:10])

# Check Patient_ID merging in exported CSVs
val_master_path, val_master_exists = check_file("fusion_val_master.csv")
print(f"fusion_val_master.csv Exists: {val_master_exists}")
if val_master_exists:
    df_vm = pd.read_csv(val_master_path)
    print("fusion_val_master Columns:", list(df_vm.columns)[:8])
    print("Patient_ID present and unique:", "Patient_ID" in df_vm.columns and df_vm["Patient_ID"].nunique() == len(df_vm))

