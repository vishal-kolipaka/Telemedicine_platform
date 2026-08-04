import os
import sys
import shutil

log_path = r"c:\Users\HP PC\Desktop\telemedicine platform\ocr_test_log.txt"

with open(log_path, "w") as f:
    f.write(f"Python: {sys.version}\n")
    which_tes = shutil.which("tesseract")
    f.write(f"shutil.which('tesseract'): {which_tes}\n")
    
    import pytesseract
    try:
        ver = pytesseract.get_tesseract_version()
        f.write(f"Pytesseract version: {ver}\n")
    except Exception as e:
        f.write(f"Pytesseract error: {e}\n")

    # Check common Tesseract install locations on Windows
    common = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
    ]
    for p in common:
        f.write(f"Path '{p}': {os.path.exists(p)}\n")
