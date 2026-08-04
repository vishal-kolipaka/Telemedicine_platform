"""
Document Reader CLI Test Script
===============================
Run this script to test the Document Reader module on any file (PDF, Image, CSV, XLSX).

Usage:
    python run_reader.py <path_to_file>

Example:
    python run_reader.py Clinical_Dataset.csv
    python run_reader.py my_report.pdf
"""

import sys
import json
import os

from src.preprocessing.reader import DocumentReader, ReaderConfig
from src.preprocessing.reader.extractors.pdf_text_extractor import PdfTextExtractor
from src.preprocessing.reader.extractors.tesseract_ocr_extractor import TesseractOCRExtractor
from src.preprocessing.reader.extractors.pandas_structured_parser import PandasStructuredParser


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_reader.py <path_to_file>")
        print("\nExamples:")
        print("  python run_reader.py Clinical_Dataset.csv")
        print("  python run_reader.py Wearable_Dataset.csv")
        print("  python run_reader.py Gut_Microbiome_Dataset.csv")
        sys.exit(1)

    file_path = sys.argv[1]

    # Search in root, datasets/, testing datas/, or search recursively
    if not os.path.exists(file_path):
        candidate_paths = [
            os.path.join("datasets", file_path),
            os.path.join("testing datas", file_path),
        ]
        found_path = None
        for path in candidate_paths:
            if os.path.exists(path):
                found_path = path
                break

        if found_path:
            file_path = found_path
        else:
            # Fallback: search recursively in the workspace for the filename
            filename_only = os.path.basename(file_path)
            for root, dirs, files in os.walk("."):
                if filename_only in files:
                    file_path = os.path.join(root, filename_only)
                    break

        if not os.path.exists(file_path):
            print(f"Error: File '{sys.argv[1]}' not found.")
            sys.exit(1)

    print(f"\n{'='*70}")
    print(f"  PROCESSING DOCUMENT: {os.path.basename(file_path)}")
    print(f"{'='*70}\n")

    # 1. Initialize config & extractors (Dependency Injection)
    config = ReaderConfig()
    pdf_extractor = PdfTextExtractor(enable_table_extraction=config.enable_table_extraction)
    ocr_extractor = TesseractOCRExtractor()
    structured_parser = PandasStructuredParser()

    # 2. Instantiate orchestrator
    reader = DocumentReader(
        pdf_extractor=pdf_extractor,
        ocr_extractor=ocr_extractor,
        structured_parser=structured_parser,
        config=config,
    )

    # 3. Process document
    try:
        output = reader.read_document(
            file_path=file_path,
            document_id=f"doc_{os.path.basename(file_path)}",
            known_hashes={},  # No previous hashes for standalone test
        )
    except Exception as e:
        print(f"🔴 Document Reader Error: {e}")
        sys.exit(1)

    # 4. Display Summary Results
    print("📊 EXTRACTION SUMMARY")
    print(f"  • File Type:             {output.get('file_type')}")
    print(f"  • MIME Type:             {output.get('mime_type')}")
    print(f"  • File Size:             {output.get('file_size_bytes')} bytes")
    print(f"  • Page Count:            {output.get('page_count')}")
    print(f"  • Report Date:           {output.get('report_date')} (Confidence: {output.get('report_date_confidence')})")
    print(f"  • Quality Check:         {'PASSED ✅' if output['quality_check']['passed'] else 'FAILED ❌'}")
    if not output['quality_check']['passed']:
        print(f"    Reason:                {output['quality_check']['reason']}")
    print(f"  • Extraction Confidence: {output.get('extraction_confidence').upper()}")
    print(f"  • File Hash (SHA256):    {output.get('file_hash')[:16]}...")

    print("\n📝 RAW TEXT PREVIEW (First 300 chars)")
    print("-" * 50)
    pages = output.get("pages", [])
    if pages:
        first_page_text = pages[0].get("raw_text", "")
        preview = first_page_text[:300] + ("..." if len(first_page_text) > 300 else "")
        print(preview)
    else:
        print("(No text extracted)")
    print("-" * 50)

    # 5. Save complete output to JSON file
    out_json_path = "reader_output.json"
    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"\n💾 Full extracted JSON saved to: '{out_json_path}'")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
