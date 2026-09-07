"""
find_level0_paths.py — Locate actual Level-0 model artifact files
"""

import os

BASE_DIR = r"c:\Users\HP PC\Desktop\telemedicine platform"

for dir_name in ["clinical_model", "wearable_model", "gut_model"]:
    p = os.path.join(BASE_DIR, dir_name)
    print(f"\n--- Files in {dir_name} ---")
    if os.path.exists(p):
        for root, dirs, files in os.walk(p):
            for f in files:
                if f.endswith(".joblib") or f.endswith(".json") or f.endswith(".pkl") or f.endswith(".csv"):
                    print("  ", os.path.relpath(os.path.join(root, f), BASE_DIR))

