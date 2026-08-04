"""
Regression test suite for OCR multi-line text layouts.

Verifies that CandidateExtractor and FeatureMapper cleanly handle
common OCR multi-line splitting artifacts:
1. Label & colon on separate lines (e.g. Height \n : 178 cm, Weight \n : 82 kg)
2. Label, value, unit on separate lines (e.g. HbA1c \n 6.2 \n %)
3. Lab test, result, unit on separate lines (e.g. LDL Cholesterol \n 118 \n mg/dL)
4. Blood pressure values split across lines (e.g. Blood Pressure \n 128 \n / \n 82 \n mmHg)
"""

from __future__ import annotations

import json
import os
import pytest

from src.preprocessing.mapper.config import MapperConfig
from src.preprocessing.mapper.candidate_extractor import DefaultCandidateExtractor
from src.preprocessing.mapper.regex_matching_engine import RegexMatchingEngine
from src.preprocessing.mapper.llm_matching_engine import LLMFallbackMatchingEngine
from src.preprocessing.mapper.validators import RangeValidator, UnitValidator, TypeValidator
from src.preprocessing.mapper.derived_features import BMICalculator
from src.preprocessing.mapper.feature_mapper import FeatureMapper


SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "src", "preprocessing", "feature_schema.json"
)


@pytest.fixture
def schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def mapper():
    config = MapperConfig()
    return FeatureMapper(
        candidate_extractor=DefaultCandidateExtractor(),
        regex_engine=RegexMatchingEngine(config),
        llm_engine=LLMFallbackMatchingEngine(config),
        validators=[RangeValidator(), UnitValidator(), TypeValidator()],
        derived_calculators={"BMI": BMICalculator()},
        config=config,
    )


def test_multiline_ocr_height_and_weight(mapper, schema):
    """Case 1: Height and Weight with colon split across lines."""
    reader_output = {
        "document_id": "ocr_doc_1",
        "pages": [
            {
                "page_index": 0,
                "raw_text": "Height\n: 178 cm\n\nWeight\n: 82 kg",
                "tables": [],
                "average_page_confidence": 0.85,
            }
        ],
        "extraction_log": [],
    }

    result = mapper.map_features(reader_output, {}, schema)
    clinical_values = result["clinical"]["values"]

    assert "Height" in clinical_values
    assert clinical_values["Height"]["canonical_value"] == 178.0
    assert clinical_values["Height"]["canonical_unit"] == "cm"

    assert "Weight" in clinical_values
    assert clinical_values["Weight"]["canonical_value"] == 82.0
    assert clinical_values["Weight"]["canonical_unit"] == "kg"

    # Verify BMI was auto-derived
    assert "BMI" in clinical_values
    assert clinical_values["BMI"]["canonical_value"] == 25.9


def test_multiline_ocr_hba1c(mapper, schema):
    """Case 2: HbA1c, value, and unit split across 3 lines."""
    reader_output = {
        "document_id": "ocr_doc_2",
        "pages": [
            {
                "page_index": 0,
                "raw_text": "HbA1c\n6.2\n%",
                "tables": [],
                "average_page_confidence": 0.82,
            }
        ],
        "extraction_log": [],
    }

    result = mapper.map_features(reader_output, {}, schema)
    clinical_values = result["clinical"]["values"]

    assert "HbA1c" in clinical_values
    assert clinical_values["HbA1c"]["canonical_value"] == 6.2
    assert clinical_values["HbA1c"]["canonical_unit"] == "%"


def test_multiline_ocr_ldl_cholesterol(mapper, schema):
    """Case 3: LDL Cholesterol, value, and unit split across lines."""
    reader_output = {
        "document_id": "ocr_doc_3",
        "pages": [
            {
                "page_index": 0,
                "raw_text": "LDL Cholesterol\n118\nmg/dL",
                "tables": [],
                "average_page_confidence": 0.90,
            }
        ],
        "extraction_log": [],
    }

    result = mapper.map_features(reader_output, {}, schema)
    clinical_values = result["clinical"]["values"]

    assert "LDL" in clinical_values
    assert clinical_values["LDL"]["canonical_value"] == 118.0
    assert clinical_values["LDL"]["canonical_unit"] == "mg/dL"


def test_multiline_ocr_blood_pressure(mapper, schema):
    """Case 4: Blood Pressure split across separate lines."""
    reader_output = {
        "document_id": "ocr_doc_4",
        "pages": [
            {
                "page_index": 0,
                "raw_text": "Blood Pressure\n128\n/\n82\nmmHg",
                "tables": [],
                "average_page_confidence": 0.88,
            }
        ],
        "extraction_log": [],
    }

    result = mapper.map_features(reader_output, {}, schema)
    clinical_values = result["clinical"]["values"]

    assert "Systolic_BP" in clinical_values
    assert clinical_values["Systolic_BP"]["canonical_value"] == 128.0
    assert clinical_values["Systolic_BP"]["canonical_unit"] == "mmHg"

    assert "Diastolic_BP" in clinical_values
    assert clinical_values["Diastolic_BP"]["canonical_value"] == 82.0
    assert clinical_values["Diastolic_BP"]["canonical_unit"] == "mmHg"


def test_cbc_biochemistry_style_report(mapper, schema):
    """Case 5: CBC + Biochemistry style report with space-aligned two-column key-values."""
    raw_text = (
        "BIOCHEMISTRY\n\n"
        "Test            Result    Unit\n\n"
        "Fasting Blood Glucose 104 mg/dL\n"
        "HbA1c                 5.9 %\n"
        "LDL Cholesterol       122 mg/dL\n"
        "HDL Cholesterol       48  mg/dL\n"
        "Triglycerides         136 mg/dL\n"
        "ALT                   28  U/L\n"
        "AST                   24  U/L\n\n"
        "Vitals\n\n"
        "Age                   43 Years\n"
        "Gender                Female\n"
        "Height                165 cm\n"
        "Weight                67 kg\n"
        "Waist Circumference   81 cm\n"
        "Blood Pressure        118/76 mmHg\n"
    )

    reader_output = {
        "document_id": "ocr_biochem_doc",
        "pages": [
            {
                "page_index": 0,
                "raw_text": raw_text,
                "tables": [],
                "average_page_confidence": 0.95,
            }
        ],
        "extraction_log": [],
    }

    result = mapper.map_features(reader_output, {}, schema)
    clinical_values = result["clinical"]["values"]

    # Verify Gender is "Female" (NOT 43!)
    assert "Gender" in clinical_values
    assert clinical_values["Gender"]["canonical_value"] == "Female"

    # Verify Age = 43
    assert "Age" in clinical_values
    assert clinical_values["Age"]["canonical_value"] == 43

    # Verify Height, Weight, BMI
    assert clinical_values["Height"]["canonical_value"] == 165.0
    assert clinical_values["Weight"]["canonical_value"] == 67.0
    assert clinical_values["BMI"]["canonical_value"] == 24.6  # 67 / (1.65^2) ≈ 24.6

    # Verify Blood Pressure
    assert "Systolic_BP" in clinical_values
    assert clinical_values["Systolic_BP"]["canonical_value"] == 118.0
    assert "Diastolic_BP" in clinical_values
    assert clinical_values["Diastolic_BP"]["canonical_value"] == 76.0

    # Verify Labs
    assert clinical_values["Fasting_Blood_Glucose"]["canonical_value"] == 104.0
    assert clinical_values["HbA1c"]["canonical_value"] == 5.9
    assert clinical_values["LDL"]["canonical_value"] == 122.0
    assert clinical_values["HDL"]["canonical_value"] == 48.0
    assert clinical_values["Triglycerides"]["canonical_value"] == 136.0
    assert clinical_values["ALT"]["canonical_value"] == 28.0
    assert clinical_values["AST"]["canonical_value"] == 24.0

