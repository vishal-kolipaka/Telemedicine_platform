import sys
import os

log_file = os.path.join(os.getcwd(), "tesseract_diag.txt")
with open(log_file, "w") as f:
    f.write("Starting Tesseract Diagnostic...\n")
    try:
        import pytesseract
        f.write("pytesseract imported successfully\n")
    except Exception as e:
        f.write(f"Failed to import pytesseract: {e}\n")
        sys.exit(0)

    try:
        ver = pytesseract.get_tesseract_version()
        f.write(f"Tesseract binary found! Version: {ver}\n")
    except Exception as e:
        f.write(f"Tesseract binary NOT FOUND on PATH or pytesseract default location: {e}\n")
        
        # Check standard Windows paths
        paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
            os.path.expanduser(r"~\AppData\Local\Tesseract-OCR\tesseract.exe"),
        ]
        found = False
        for p in paths:
            exists = os.path.exists(p)
            f.write(f"  Checking {p} -> {exists}\n")
            if exists:
                pytesseract.pytesseract.tesseract_cmd = p
                try:
                    ver2 = pytesseract.get_tesseract_version()
                    f.write(f"  -> SUCCESS! Found working Tesseract at '{p}', version: {ver2}\n")
                    found = True
                    break
                except Exception as e2:
                    f.write(f"  -> Error executing {p}: {e2}\n")
        
        if not found:
            f.write("RESULT: Tesseract OCR binary is NOT INSTALLED on this Windows system!\n")
