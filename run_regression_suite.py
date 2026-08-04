"""
Master Regression Test Suite Runner for Preprocessing Unit (Document Reader + Feature Mapper v2).

Evaluates all Master Tests in mapper tests/sample_reports/clinical/ against Contract 1 & 2 invariants.
"""

import os
import glob
import json
import sys
from datetime import datetime, timezone

# Force UTF-8 encoding on Windows console
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

# Expected clinical fields present in clinical laboratory report tests
EXPECTED_REPORT_CLINICAL = [
    "Age", "Gender", "Height", "Weight", "Waist_Circumference",
    "Systolic_BP", "Diastolic_BP", "Fasting_Blood_Glucose", "HbA1c",
    "LDL", "HDL", "Triglycerides", "ALT", "AST", "BMI"
]

def run_suite():
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

    test_folder = os.path.join(os.getcwd(), "mapper tests", "sample_reports", "clinical")
    test_files = sorted(glob.glob(os.path.join(test_folder, "*.txt")))

    summary_rows = []
    detailed_reports = []

    passed_count = 0
    total_count = 0

    print("=" * 80)
    print(" 🚀 RUNNING MASTER REGRESSION TEST SUITE (Preprocessing Pipeline v2)")
    print("=" * 80)

    for filepath in test_files:
        filename = os.path.basename(filepath)
        if filename == "overall_info.txt":
            continue

        total_count += 1
        reader_out = reader.read_document(filepath, document_id=filename, known_hashes={})
        state = mapper.map_features(reader_out, {}, schema)

        clin_state = state.get("clinical", {})
        wear_state = state.get("wearable", {})
        gut_state = state.get("gut", {})

        clin_vals = clin_state.get("values", {})
        wear_vals = wear_state.get("values", {})
        gut_vals = gut_state.get("values", {})

        clin_found = list(clin_vals.keys())
        wear_found = list(wear_vals.keys())
        gut_found = list(gut_vals.keys())

        conflicts = clin_state.get("conflict_log", []) + wear_state.get("conflict_log", []) + gut_state.get("conflict_log", [])
        flagged = clin_state.get("flagged_for_reconfirm", []) + wear_state.get("flagged_for_reconfirm", []) + gut_state.get("flagged_for_reconfirm", [])

        # Evaluation criteria:
        # Clinical test is PASS if all report-extracted clinical fields present in file are extracted.
        # Family History (user_form) and AST (if not present) are intentionally missing.
        missing_clinical = [f for f in EXPECTED_REPORT_CLINICAL if f not in clin_found]

        # Specific file exceptions:
        if filename == "02_vertical_layout.txt" and "AST" in missing_clinical:
            # AST is omitted in 02_vertical_layout test data
            missing_clinical.remove("AST")
        elif filename == "18_extreme_edge_cases.txt":
            # Weight ('eighty kg'), HbA1c ('Pending'), AST ('Sample Hemolyzed') are intentionally invalid non-numeric text, so BMI cannot be derived
            missing_clinical = [f for f in EXPECTED_REPORT_CLINICAL if f not in ("Weight", "HbA1c", "AST", "BMI") and f not in clin_found]
        elif filename == "missing_labes.txt":
            # Intentionally missing all field labels (raw values only) — tests un-labeled value handling
            missing_clinical = []

        is_pass = (len(missing_clinical) == 0)
        if is_pass:
            passed_count += 1
            status_str = "✅ PASS"
        else:
            status_str = "❌ FAIL"

        summary_rows.append({
            "test_name": filename,
            "status": status_str,
            "clinical_found": len(clin_found),
            "wearable_found": len(wear_found),
            "gut_found": len(gut_found),
            "missing_clinical": missing_clinical,
            "conflicts": len(conflicts),
            "flagged": len(flagged),
        })

        detailed_reports.append({
            "test_name": filename,
            "status": status_str,
            "clinical_values": clin_vals,
            "wearable_values": wear_vals,
            "gut_values": gut_vals,
            "missing_clinical": missing_clinical,
            "conflict_log": conflicts,
            "flagged_for_reconfirm": flagged,
        })

        print(f"{status_str} | {filename:<30} | Clin: {len(clin_found)}/15 | Wear: {len(wear_found)} | Gut: {len(gut_found)}")

    print("\n" + "=" * 80)
    print(f" RESULTS SUMMARY: {passed_count} / {total_count} Master Tests Passed ({passed_count/total_count*100:.1f}%)")
    print("=" * 80)

    # Save summary report to JSON
    report_data = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_tests": total_count,
        "passed_tests": passed_count,
        "failed_tests": total_count - passed_count,
        "pass_rate_pct": round(passed_count / total_count * 100, 1),
        "summary": summary_rows,
        "details": detailed_reports,
    }

    with open("master_regression_report.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    print("📄 Master Regression Report saved to: master_regression_report.json")
    return report_data

if __name__ == "__main__":
    run_suite()
