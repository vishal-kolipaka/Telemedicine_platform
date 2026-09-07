"""
inspect_fusion_analysis.py
Extracts and inspects the contents of fusion_analysis/files (1).zip
"""

import os
import zipfile

BASE_DIR = r"c:\Users\HP PC\Desktop\telemedicine platform\fusion_analysis"
ZIP_PATH = os.path.join(BASE_DIR, "files (1).zip")
EXTRACT_DIR = os.path.join(BASE_DIR, "extracted")

os.makedirs(EXTRACT_DIR, exist_ok=True)

with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
    zip_ref.extractall(EXTRACT_DIR)
    file_list = zip_ref.namelist()

print("Extracted files:")
for f in file_list:
    p = os.path.join(EXTRACT_DIR, f)
    if os.path.isfile(p):
        print(f"  {f} ({os.path.getsize(p)} bytes)")
    else:
        print(f"  [DIR] {f}")
