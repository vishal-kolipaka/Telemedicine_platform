"""
Unseen Real-World Report Generalization Validation Script.

Runs the Document Reader + Feature Mapper v2 pipeline on 7 completely unseen report files
(Quest Diagnostics, Max Healthcare, Metropolis, Apple Health, Whoop/Libre, Viome, Lal Path Labs).

Calculates Precision, Recall, F1 Score, and flags any potential generalization issues.
"""

import os
import glob
import json
import sys
from datetime import datetime, timezone

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

# Ground truth expected fields for each unseen test file
UNSEEN_GROUND_TRUTH = {
    "unseen_clinical_max_health.txt": {
        "clinical": ["Age", "Gender", "Height", "Weight", "Waist_Circumference", "Systolic_BP", "Diastolic_BP", "Fasting_Blood_Glucose", "HbA1c", "LDL", "HDL", "Triglycerides", "ALT", "AST", "BMI"],
        "wearable": [],
        "gut": [],
    },
    "unseen_clinical_quest_diagnostics.txt": {
        "clinical": ["Age", "Gender", "Height", "Weight", "Waist_Circumference", "Systolic_BP", "Diastolic_BP", "Fasting_Blood_Glucose", "HbA1c", "LDL", "HDL", "Triglycerides", "ALT", "AST", "BMI"],
        "wearable": [],
        "gut": [],
    },
    "unseen_clinical_metropolis.txt": {
        "clinical": ["Age", "Gender", "Height", "Weight", "Waist_Circumference", "Systolic_BP", "Diastolic_BP", "Fasting_Blood_Glucose", "HbA1c", "LDL", "HDL", "Triglycerides", "ALT", "AST", "BMI"],
        "wearable": [],
        "gut": [],
    },
    "unseen_wearable_apple_health.txt": {
        "clinical": ["Age", "Gender"],
        "wearable": ["Age", "Gender", "Average_Daily_Steps", "Active_Minutes", "Sedentary_Time_Minutes", "Resting_Heart_Rate", "Sleep_Duration_Hours", "Activity_Energy_Expenditure", "CGM_Average_Glucose", "CGM_Glucose_CV", "CGM_Time_In_Range", "CGM_Time_Above_Range"],
        "gut": [],
    },
    "unseen_wearable_whoop_summary.txt": {
        "clinical": ["Age", "Gender"],
        "wearable": ["Age", "Gender", "Average_Daily_Steps", "Active_Minutes", "Sedentary_Time_Minutes", "Resting_Heart_Rate", "Sleep_Duration_Hours", "Activity_Energy_Expenditure", "CGM_Average_Glucose", "CGM_Glucose_CV", "CGM_Time_In_Range", "CGM_Time_Above_Range"],
        "gut": [],
    },
    "unseen_gut_microbiome_viome.txt": {
        "clinical": ["Age", "Gender"],
        "wearable": [],
        "gut": ["Age", "Gender", "Akkermansia", "Faecalibacterium", "Bifidobacterium", "Roseburia", "Alistipes", "Escherichia_Shigella", "Collinsella", "Prevotella", "Blautia"],
    },
    "unseen_multimodal_comprehensive.txt": {
        "clinical": ["Age", "Gender", "Height", "Weight", "Waist_Circumference", "Systolic_BP", "Diastolic_BP", "Fasting_Blood_Glucose", "HbA1c", "LDL", "HDL", "Triglycerides", "ALT", "AST", "BMI"],
        "wearable": ["Age", "Gender", "Average_Daily_Steps", "Active_Minutes", "Sedentary_Time_Minutes", "Resting_Heart_Rate", "Sleep_Duration_Hours", "Activity_Energy_Expenditure", "CGM_Average_Glucose", "CGM_Glucose_CV", "CGM_Time_In_Range", "CGM_Time_Above_Range"],
        "gut": ["Age", "Gender", "Akkermansia", "Faecalibacterium", "Bifidobacterium", "Roseburia", "Alistipes", "Escherichia_Shigella", "Collinsella", "Prevotella", "Blautia"],
    },
}

def validate_unseen():
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

    unseen_folder = os.path.join("mapper tests", "unseen_reports")
    unseen_files = sorted(glob.glob(os.path.join(unseen_folder, "*.txt")))

    total_tp = 0
    total_fp = 0
    total_fn = 0

    per_file_metrics = []

    print("=" * 85)
    print(" 🧪 UNSEEN REAL-WORLD REPORT GENERALIZATION VALIDATION")
    print("=" * 85)

    for filepath in unseen_files:
        filename = os.path.basename(filepath)
        gt = UNSEEN_GROUND_TRUTH.get(filename, {"clinical": [], "wearable": [], "gut": []})

        reader_out = reader.read_document(filepath, document_id=filename, known_hashes={})
        state = mapper.map_features(reader_out, {}, schema)

        clin_extracted = set(state.get("clinical", {}).get("values", {}).keys())
        wear_extracted = set(state.get("wearable", {}).get("values", {}).keys())
        gut_extracted = set(state.get("gut", {}).get("values", {}).keys())

        # Match against ground truth per model
        all_extracted = clin_extracted | wear_extracted | gut_extracted
        all_expected = set(gt["clinical"]) | set(gt["wearable"]) | set(gt["gut"])

        tp = len(all_extracted & all_expected)
        fp = len(all_extracted - all_expected)
        fn = len(all_expected - all_extracted)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 1.0

        total_tp += tp
        total_fp += fp
        total_fn += fn

        status = "✅ PERFECT" if (fp == 0 and fn == 0) else ("⚠️ IMPERFECT" if precision >= 0.9 and recall >= 0.9 else "❌ FAIL")

        print(f"{status:<12} | {filename:<38} | P: {precision*100:5.1f}% | R: {recall*100:5.1f}% | F1: {f1*100:5.1f}%")

        per_file_metrics.append({
            "filename": filename,
            "status": status,
            "expected_count": len(all_expected),
            "extracted_count": len(all_extracted),
            "tp": tp, "fp": fp, "fn": fn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "missing_fields": list(all_expected - all_extracted),
            "spurious_fields": list(all_extracted - all_expected),
        })

    overall_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 1.0
    overall_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 1.0
    overall_f1 = (2 * overall_precision * overall_recall) / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 1.0

    print("\n" + "=" * 85)
    print(" OVERALL UNSEEN GENERALIZATION METRICS:")
    print(f"   - Total Expected Fields Across All Reports: {total_tp + total_fn}")
    print(f"   - Total Successfully Extracted (TP):        {total_tp}")
    print(f"   - False Positives (FP):                     {total_fp}")
    print(f"   - False Negatives (FN):                     {total_fn}")
    print(f"   - OVERALL PRECISION:                        {overall_precision * 100:.2f}%")
    print(f"   - OVERALL RECALL:                           {overall_recall * 100:.2f}%")
    print(f"   - OVERALL F1 SCORE:                         {overall_f1 * 100:.2f}%")
    print("=" * 85)

    validation_report = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_unseen_reports": len(unseen_files),
        "overall_precision": round(overall_precision, 4),
        "overall_recall": round(overall_recall, 4),
        "overall_f1": round(overall_f1, 4),
        "details": per_file_metrics,
    }

    with open("unseen_validation_report.json", "w", encoding="utf-8") as f:
        json.dump(validation_report, f, indent=2)

    print("📄 Saved detailed unseen report validation to: unseen_validation_report.json")
    return validation_report

if __name__ == "__main__":
    validate_unseen()
