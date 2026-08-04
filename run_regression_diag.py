"""
Diagnostic runner for all 12 Master Regression Tests in mapper tests/sample_reports/clinical/
"""

import os
import glob
import json
import sys

# Ensure UTF-8 stdout
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.preprocessing.reader import DocumentReader, ReaderConfig
from src.preprocessing.reader.extractors.pdf_text_extractor import PdfTextExtractor
from src.preprocessing.reader.extractors.tesseract_ocr_extractor import TesseractOCRExtractor
from src.preprocessing.reader.extractors.pandas_structured_parser import PandasStructuredParser
from src.preprocessing.mapper import (
    FeatureMapper,
    MapperConfig,
    DefaultCandidateExtractor,
    RegexMatchingEngine,
    LLMFallbackMatchingEngine,
    RangeValidator,
    UnitValidator,
    TypeValidator,
    BMICalculator,
)

def main():
    schema_path = os.path.join("src", "preprocessing", "feature_schema.json")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    reader = DocumentReader(
        pdf_extractor=PdfTextExtractor(),
        ocr_extractor=TesseractOCRExtractor(),
        structured_parser=PandasStructuredParser(),
        config=ReaderConfig(),
    )
    config = MapperConfig()
    mapper = FeatureMapper(
        candidate_extractor=DefaultCandidateExtractor(),
        regex_engine=RegexMatchingEngine(config),
        llm_engine=LLMFallbackMatchingEngine(config),
        validators=[RangeValidator(), UnitValidator(), TypeValidator()],
        derived_calculators={"BMI": BMICalculator()},
        config=config,
    )

    test_folder = os.path.join("mapper tests", "sample_reports", "clinical")
    test_files = sorted(glob.glob(os.path.join(test_folder, "*.txt")))

    results = {}

    for filepath in test_files:
        filename = os.path.basename(filepath)
        if filename == "overall_info.txt":
            continue

        print(f"\n{'='*70}\nRunning: {filename}\n{'='*70}")
        reader_out = reader.read_document(filepath, document_id=filename, known_hashes={})
        state = mapper.map_features(reader_out, {}, schema)

        clin_vals = list(state.get("clinical", {}).get("values", {}).keys())
        wear_vals = list(state.get("wearable", {}).get("values", {}).keys())
        gut_vals = list(state.get("gut", {}).get("values", {}).keys())

        print(f"Clinical Fields Found ({len(clin_vals)}): {clin_vals}")
        print(f"Wearable Fields Found ({len(wear_vals)}): {wear_vals}")
        print(f"Gut Fields Found ({len(gut_vals)}): {gut_vals}")

        results[filename] = {
            "clinical": clin_vals,
            "wearable": wear_vals,
            "gut": gut_vals,
            "conflict_log": state.get("clinical", {}).get("conflict_log", []),
            "flagged": state.get("clinical", {}).get("flagged_for_reconfirm", []),
        }

    with open("regression_diag_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
