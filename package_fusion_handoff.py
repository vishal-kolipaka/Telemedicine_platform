"""
package_fusion_handoff.py
Packages all Fusion Phase 1 artifacts into fusion_phase1_handoff/ and zips it to fusion_phase1_handoff.zip.
Reports existence, paths, file sizes, and CSV row counts.
"""

import os
import shutil
import zipfile
import pandas as pd

BASE_DIR = r"c:\Users\HP PC\Desktop\telemedicine platform"
HANDOFF_DIR = os.path.join(BASE_DIR, "fusion_phase1_handoff")
ZIP_PATH = os.path.join(BASE_DIR, "fusion_phase1_handoff.zip")

os.makedirs(HANDOFF_DIR, exist_ok=True)

target_files = [
    "artifact_inventory_report.md",
    "clinical_val_predictions.csv",
    "clinical_test_predictions.csv",
    "wearable_val_predictions.csv",
    "wearable_test_predictions.csv",
    "gut_val_predictions.csv",
    "gut_test_predictions.csv",
    "fusion_val_master.csv",
    "fusion_test_master.csv",
    "fusion_val_master_gaps.csv",
    "fusion_test_master_gaps.csv",
    "labels_v3.csv",
    "split_manifest_v3.csv"
]

print("=== STEP 1: CONFIRM FILE EXISTENCE & EXACT PATHS ===")

file_status = []

for filename in target_files:
    # Look in root first, then fusion_exports/ or data dirs
    possible_paths = [
        os.path.join(BASE_DIR, filename),
        os.path.join(BASE_DIR, "fusion_exports", filename),
        os.path.join(BASE_DIR, "clinical_model", "data", filename)
    ]
    
    found_path = None
    for p in possible_paths:
        if os.path.exists(p):
            found_path = p
            break
            
    if found_path:
        file_status.append({"Filename": filename, "Status": "FOUND", "Exact Path": found_path})
        # Copy file without modification
        shutil.copy2(found_path, os.path.join(HANDOFF_DIR, filename))
    else:
        file_status.append({"Filename": filename, "Status": "NOT FOUND (Optional/Gap)", "Exact Path": "N/A"})

df_status = pd.DataFrame(file_status)
print(df_status.to_string())


print("\n=== STEP 2: CREATE ZIP ARCHIVE ===")

with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(HANDOFF_DIR):
        for file in files:
            file_p = os.path.join(root, file)
            arcname = os.path.relpath(file_p, HANDOFF_DIR)
            zipf.write(file_p, arcname)

zip_size_bytes = os.path.getsize(ZIP_PATH)
zip_size_mb = zip_size_bytes / (1024 * 1024)

print(f"\nZip Archive Path: {ZIP_PATH}")
print(f"Zip Archive Size: {zip_size_bytes:,} bytes ({zip_size_mb:.2f} MB)")


print("\n=== STEP 3: SANITY-CHECK FILE LISTING & ROW COUNTS ===")

listing_rows = []

for item in os.listdir(HANDOFF_DIR):
    item_p = os.path.join(HANDOFF_DIR, item)
    size = os.path.getsize(item_p)
    
    if item.endswith(".csv"):
        df = pd.read_csv(item_p)
        row_count = len(df)
        col_count = len(df.columns)
        details = f"{row_count} rows, {col_count} cols"
    else:
        details = "Markdown Report"
        
    listing_rows.append({
        "Filename": item,
        "Size (bytes)": f"{size:,}",
        "Details / Row Count": details
    })

df_listing = pd.DataFrame(listing_rows)
print(df_listing.to_string())

