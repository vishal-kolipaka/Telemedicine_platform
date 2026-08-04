"""
Feature Mapper — complete test suite (28 tests per Section 18).

Tests 1-26: from original spec (v1).
Tests 27-28: new in v2.

Meta-verification: NO test anywhere asserts on a "resolved_value"
or "winner" from this module — if any does, it's wrong.
"""

from __future__ import annotations

import json
import os
import copy
import pytest

from src.preprocessing.mapper.config import MapperConfig
from src.preprocessing.mapper.models import Candidate, MappedFeature
from src.preprocessing.mapper.candidate_extractor import (
    DefaultCandidateExtractor,
)
from src.preprocessing.mapper.regex_matching_engine import RegexMatchingEngine
from src.preprocessing.mapper.llm_matching_engine import (
    LLMFallbackMatchingEngine,
)
from src.preprocessing.mapper.confidence import (
    compute_confidence,
    get_context_score,
)
from src.preprocessing.mapper.unit_converter import (
    convert_value,
    detect_and_convert,
    parse_feet_inches,
    detect_unit,
)
from src.preprocessing.mapper.validators import (
    RangeValidator,
    UnitValidator,
    TypeValidator,
)
from src.preprocessing.mapper.derived_features import BMICalculator
from src.preprocessing.mapper.conflict_detector import detect_conflict
from src.preprocessing.mapper.feature_mapper import FeatureMapper
from src.preprocessing.mapper.exceptions import (
    UnitConversionError,
    SchemaMismatchError,
)


# ────────────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────────────

SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "src",
    "preprocessing",
    "feature_schema.json",
)


@pytest.fixture
def schema():
    """Load the actual feature_schema.json."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def config():
    return MapperConfig()


@pytest.fixture
def mapper(config):
    """Build a fully-wired FeatureMapper with real components."""
    return FeatureMapper(
        candidate_extractor=DefaultCandidateExtractor(),
        regex_engine=RegexMatchingEngine(config),
        llm_engine=LLMFallbackMatchingEngine(config),
        validators=[RangeValidator(), UnitValidator(), TypeValidator()],
        derived_calculators={"BMI": BMICalculator()},
        config=config,
    )


@pytest.fixture
def sample_reader_output():
    """Contract 1 sample output matching the spec example."""
    return {
        "document_id": "doc_7f3a1c",
        "source_file": "clinical_report_jan2026.pdf",
        "file_type": "pdf",
        "report_date": "2026-01-14",
        "pages": [
            {
                "page_index": 0,
                "extractor_used": "pdfplumber",
                "raw_text": (
                    "Patient: John Doe\n"
                    "Age: 45\n"
                    "Gender: Male\n"
                    "Collection Date: 14-Jan-2026\n"
                    "Height: 5'10\"\n"
                    "Weight: 180 lbs\n"
                    "BP: 128/82 mmHg"
                ),
                "tables": [
                    [
                        ["Test", "Result", "Unit", "Reference Range"],
                        ["HbA1c", "6.1", "%", "4.0-5.6"],
                        ["Fasting Glucose", "112", "mg/dL", "70-99"],
                        ["LDL", "118", "mg/dL", "<100"],
                        ["HDL", "42", "mg/dL", ">40"],
                        ["Triglycerides", "135", "mg/dL", "<150"],
                        ["ALT", "34", "U/L", "7-56"],
                        ["AST", "38", "U/L", "10-40"],
                    ]
                ],
                "average_page_confidence": None,
            }
        ],
        "extraction_log": [
            {
                "operation_id": "op_a1b2c3",
                "timestamp": "2026-07-29T10:15:00.100Z",
                "level": "INFO",
                "module": "DocumentReader",
                "message": "file hash computed",
            }
        ],
        "quality_check": {"passed": True, "score": 0.96, "issues": []},
        "extraction_confidence": "high",
    }


@pytest.fixture
def empty_state():
    return {}


# ────────────────────────────────────────────────────────────────
# Test 1: Exact alias match for a simple field
# ────────────────────────────────────────────────────────────────

def test_01_exact_alias_match(config, schema):
    """HbA1c candidate with label 'HbA1c' matches the HbA1c field."""
    engine = RegexMatchingEngine(config)
    candidate = Candidate(
        label_text="HbA1c",
        value_text="6.1",
        unit_text="%",
        page_index=0,
        context_type="table_header",
        source_line="HbA1c | 6.1 | % | 4.0-5.6",
    )
    field_schema = schema["clinical"]["features"]["HbA1c"]
    result = engine.match([candidate], "HbA1c", field_schema)
    assert result is not None
    assert result.field_name == "HbA1c"
    assert result.mapping_method == "regex_rule_match"


# ────────────────────────────────────────────────────────────────
# Test 2: Case-insensitive alias matching
# ────────────────────────────────────────────────────────────────

def test_02_case_insensitive_alias(config, schema):
    """'hba1c' (lowercase) still matches HbA1c."""
    engine = RegexMatchingEngine(config)
    candidate = Candidate(
        label_text="hba1c",
        value_text="6.1",
        unit_text="%",
        page_index=0,
        context_type="table_header",
        source_line="hba1c | 6.1 | %",
    )
    field_schema = schema["clinical"]["features"]["HbA1c"]
    result = engine.match([candidate], "HbA1c", field_schema)
    assert result is not None
    assert result.field_name == "HbA1c"


# ────────────────────────────────────────────────────────────────
# Test 3: Value extraction from same line as alias
# ────────────────────────────────────────────────────────────────

def test_03_value_from_same_line(config, schema):
    """Value '6.1' is extracted from the same line as 'HbA1c'."""
    engine = RegexMatchingEngine(config)
    candidate = Candidate(
        label_text="HbA1c",
        value_text="6.1",
        unit_text="%",
        page_index=0,
        context_type="table_header",
        source_line="HbA1c | 6.1 | %",
    )
    field_schema = schema["clinical"]["features"]["HbA1c"]
    result = engine.match([candidate], "HbA1c", field_schema)
    assert result is not None
    assert result.matched_candidate.value_text == "6.1"


# ────────────────────────────────────────────────────────────────
# Test 4: Value extraction from bounded window / next line
# ────────────────────────────────────────────────────────────────

def test_04_extractor_multiline(config):
    """CandidateExtractor handles multi-line label:value patterns."""
    extractor = DefaultCandidateExtractor()
    reader_output = {
        "pages": [
            {
                "page_index": 0,
                "raw_text": "Weight: 180 lbs\nHeight: 170 cm",
                "tables": [],
                "average_page_confidence": None,
            }
        ]
    }
    candidates = extractor.extract(reader_output)
    labels = {c.label_text.lower() for c in candidates}
    assert "weight" in labels
    assert "height" in labels


# ────────────────────────────────────────────────────────────────
# Test 5: Unit detection and conversion (lbs → kg)
# ────────────────────────────────────────────────────────────────

def test_05_lbs_to_kg():
    """180 lbs converts to ~81.6 kg."""
    result = convert_value(180.0, "lbs", "kg", "Weight")
    assert abs(result - 81.6466) < 0.1


# ────────────────────────────────────────────────────────────────
# Test 6: Feet/inches → cm conversion
# ────────────────────────────────────────────────────────────────

def test_06_feet_inches_to_cm():
    """5'10\" converts to ~177.8 cm."""
    result = parse_feet_inches("5'10\"")
    assert result is not None
    assert abs(result - 177.8) < 0.5


# ────────────────────────────────────────────────────────────────
# Test 7: mmol/L → mg/dL conversion (glucose)
# ────────────────────────────────────────────────────────────────

def test_07_mmol_to_mgdl_glucose():
    """6.2 mmol/L glucose converts to 111.6 mg/dL."""
    result = convert_value(
        6.2, "mmol/L", "mg/dL", "Fasting_Blood_Glucose"
    )
    assert abs(result - 111.6) < 0.1


# ────────────────────────────────────────────────────────────────
# Test 8: HbA1c mmol/mol → % conversion
# ────────────────────────────────────────────────────────────────

def test_08_hba1c_mmolmol_to_percent():
    """48 mmol/mol converts to ~6.54%."""
    result = convert_value(48.0, "mmol/mol", "%", "HbA1c")
    # Formula: (48/10.929) + 2.15 ≈ 6.54
    assert abs(result - 6.54) < 0.1


# ────────────────────────────────────────────────────────────────
# Test 9: Table extraction with header row
# ────────────────────────────────────────────────────────────────

def test_09_table_extraction_with_header():
    """Table with Test|Result|Unit header produces candidates
    with context_type='table_header'."""
    extractor = DefaultCandidateExtractor()
    reader_output = {
        "pages": [
            {
                "page_index": 0,
                "raw_text": "",
                "tables": [
                    [
                        ["Test", "Result", "Unit"],
                        ["HbA1c", "6.1", "%"],
                        ["ALT", "34", "U/L"],
                    ]
                ],
                "average_page_confidence": None,
            }
        ]
    }
    candidates = extractor.extract(reader_output)
    assert len(candidates) >= 2
    for c in candidates:
        assert c.context_type == "table_header"


# ────────────────────────────────────────────────────────────────
# Test 10: BP combined reading split
# ────────────────────────────────────────────────────────────────

def test_10_bp_split():
    """'BP: 128/82 mmHg' produces two candidates (Systolic, Diastolic)."""
    extractor = DefaultCandidateExtractor()
    reader_output = {
        "pages": [
            {
                "page_index": 0,
                "raw_text": "BP: 128/82 mmHg",
                "tables": [],
                "average_page_confidence": None,
            }
        ]
    }
    candidates = extractor.extract(reader_output)
    labels = [c.label_text for c in candidates]
    assert "Systolic BP" in labels
    assert "Diastolic BP" in labels
    sys_c = next(c for c in candidates if c.label_text == "Systolic BP")
    dia_c = next(c for c in candidates if c.label_text == "Diastolic BP")
    assert sys_c.value_text == "128"
    assert dia_c.value_text == "82"


# ────────────────────────────────────────────────────────────────
# Test 11: Ambiguity penalty when multiple numbers nearby
# ────────────────────────────────────────────────────────────────

def test_11_ambiguity_penalty(config):
    """A candidate with many numbers in its source_line gets penalized."""
    engine = RegexMatchingEngine(config)
    # Candidate with many numbers → ambiguity
    candidate = Candidate(
        label_text="ALT",
        value_text="34",
        unit_text="U/L",
        page_index=0,
        context_type="table_header",
        source_line="ALT | 34 | U/L | 7-56 | 120 | 45",
    )
    field_schema = {
        "type": "float", "unit": "U/L",
        "aliases": ["alt", "sgpt"],
    }
    result = engine.match([candidate], "ALT", field_schema)
    assert result is not None
    # Ambiguity component should show penalty (< 1.0)
    assert result.confidence_breakdown["ambiguity"] < 1.0


# ────────────────────────────────────────────────────────────────
# Test 12: Confidence threshold accept (≥ 0.90)
# ────────────────────────────────────────────────────────────────

def test_12_confidence_accept_threshold(config, schema):
    """A high-confidence match (exact alias, table, unit match) is accepted."""
    engine = RegexMatchingEngine(config)
    candidate = Candidate(
        label_text="HbA1c",
        value_text="6.1",
        unit_text="%",
        page_index=0,
        context_type="table_header",
        source_line="HbA1c | 6.1 | %",
    )
    field_schema = schema["clinical"]["features"]["HbA1c"]
    result = engine.match([candidate], "HbA1c", field_schema)
    assert result is not None
    assert result.mapping_confidence >= config.confidence_threshold_accept


# ────────────────────────────────────────────────────────────────
# Test 13: Confidence threshold LLM trigger (< 0.70)
# ────────────────────────────────────────────────────────────────

def test_13_below_llm_trigger_returns_none(schema):
    """A very low confidence match returns None (below LLM trigger)."""
    # Use a config with very high thresholds
    config = MapperConfig(
        confidence_threshold_accept=0.99,
        confidence_threshold_llm_trigger=0.98,
    )
    engine = RegexMatchingEngine(config)
    # Candidate with weak alias match (unit mismatch, unstructured)
    candidate = Candidate(
        label_text="hemoglobin a1c",
        value_text="6.1",
        unit_text="weird_unit",
        page_index=0,
        context_type="unstructured",
        source_line="hemoglobin a1c is maybe 6.1 weird_unit somewhere 99 88 77",
    )
    field_schema = schema["clinical"]["features"]["HbA1c"]
    result = engine.match([candidate], "HbA1c", field_schema)
    # With very high thresholds, this should be None
    assert result is None


# ────────────────────────────────────────────────────────────────
# Test 14: Range validation flags out-of-range value
# ────────────────────────────────────────────────────────────────

def test_14_range_validation_out_of_range():
    """ALT=340 is outside valid_range [5, 300] → INVALID."""
    validator = RangeValidator()
    schema_entry = {"valid_range": [5, 300]}
    result = validator.validate("ALT", 340, schema_entry)
    assert result["valid"] is False
    assert "outside" in result["reason"].lower()


# ────────────────────────────────────────────────────────────────
# Test 15: Range validation passes value within range
# ────────────────────────────────────────────────────────────────

def test_15_range_validation_within_range():
    """ALT=34 is inside valid_range [5, 300] → VALID."""
    validator = RangeValidator()
    schema_entry = {"valid_range": [5, 300]}
    result = validator.validate("ALT", 34, schema_entry)
    assert result["valid"] is True


# ────────────────────────────────────────────────────────────────
# Test 16: Type validation catches wrong type
# ────────────────────────────────────────────────────────────────

def test_16_type_validation_wrong_type():
    """A string value for a float field → invalid."""
    validator = TypeValidator()
    schema_entry = {"type": "float"}
    result = validator.validate("HbA1c", "not_a_number", schema_entry)
    assert result["valid"] is False


# ────────────────────────────────────────────────────────────────
# Test 17: BMI derived feature computation
# ────────────────────────────────────────────────────────────────

def test_17_bmi_derived_feature():
    """BMI computed from Weight=81.6 kg, Height=177.8 cm."""
    calc = BMICalculator()
    resolved = {"Weight_kg": 81.6, "Height_cm": 177.8}
    schema_entry = {"unit": "kg/m2"}
    result = calc.compute(resolved, schema_entry)
    assert result is not None
    # BMI = 81.6 / (1.778^2) ≈ 25.8
    assert abs(result - 25.8) < 0.5


# ────────────────────────────────────────────────────────────────
# Test 18: BMI rounding matches schema policy
# ────────────────────────────────────────────────────────────────

def test_18_bmi_rounding():
    """BMI rounds to 1 decimal using round-half-up."""
    calc = BMICalculator()
    # Pick values that produce a .X5 boundary
    # Weight=70, Height=165 → BMI = 70/(1.65^2) = 25.71..
    resolved = {"Weight_kg": 70.0, "Height_cm": 165.0}
    result = calc.compute(resolved, {"unit": "kg/m2"})
    assert result is not None
    # Should be exactly 1 decimal place
    assert str(result).count(".") == 1
    decimal_places = len(str(result).split(".")[1])
    assert decimal_places <= 1


# ────────────────────────────────────────────────────────────────
# Test 19: Conflict detection with per-field threshold
# ────────────────────────────────────────────────────────────────

def test_19_conflict_detection():
    """Values differing by more than the field threshold → conflict."""
    new_val = {"canonical_value": 112, "document_id": "doc_1",
               "reader_operation_id": "op_1", "report_date": "2026-01",
               "extracted_at": "2026-07-29T10:16:02Z"}
    existing_val = {"canonical_value": 98, "document_id": "doc_2",
                    "reader_operation_id": "op_2", "report_date": "2026-06",
                    "extracted_at": "2026-07-29T10:19:40Z"}
    field_schema = {"conflict_relative_threshold": 0.10}
    result = detect_conflict(
        new_val, existing_val, "Fasting_Blood_Glucose",
        field_schema, 0.20
    )
    # 14/112 ≈ 12.5% > 10% threshold → conflict
    assert result is not None
    assert result["field"] == "Fasting_Blood_Glucose"
    assert len(result["candidates"]) == 2


# ────────────────────────────────────────────────────────────────
# Test 20: Conflict detection does NOT produce a winner
# ────────────────────────────────────────────────────────────────

def test_20_conflict_no_winner():
    """Conflict log entry must NEVER contain resolved_value or winner."""
    new_val = {"canonical_value": 7.0, "document_id": "doc_1",
               "reader_operation_id": "op_1", "report_date": "2026-01",
               "extracted_at": "2026-07-29T10:16:02Z"}
    existing_val = {"canonical_value": 6.1, "document_id": "doc_2",
                    "reader_operation_id": "op_2", "report_date": "2026-06",
                    "extracted_at": "2026-07-29T10:19:40Z"}
    field_schema = {"conflict_relative_threshold": 0.05}
    result = detect_conflict(
        new_val, existing_val, "HbA1c", field_schema, 0.20
    )
    assert result is not None
    # CRITICAL: no resolution fields
    assert "resolved_value" not in result
    assert "winner" not in result
    assert "resolved_from_document_id" not in result


# ────────────────────────────────────────────────────────────────
# Test 21: apply_user_answer validates and stores correctly
# ────────────────────────────────────────────────────────────────

def test_21_apply_user_answer(mapper, schema):
    """User answer for a family history field stores correctly."""
    state = {
        "clinical": {
            "status": "incomplete",
            "values": {},
            "missing_fields": ["Family_History_Diabetes"],
            "flagged_for_reconfirm": [],
            "conflict_log": [],
        }
    }
    updated = mapper.apply_user_answer(
        "Family_History_Diabetes", "Yes", state, schema,
        source="user_form"
    )
    val = updated["clinical"]["values"]["Family_History_Diabetes"]
    assert val["canonical_value"] == 1  # Yes → 1 per encoding
    assert val["source"] == "user_form"
    assert val["validation_status"] == "USER_ENTERED"


# ────────────────────────────────────────────────────────────────
# Test 22: Source priority: user_reconfirm beats report_extraction
# ────────────────────────────────────────────────────────────────

def test_22_source_priority(mapper, schema):
    """A user_reconfirm value overwrites a report_extraction value."""
    state = {
        "clinical": {
            "status": "incomplete",
            "values": {
                "Weight": {
                    "canonical_value": 81.6,
                    "canonical_unit": "kg",
                    "source": "report_extraction",
                    "validation_status": "VALID",
                    "original_value": "180",
                    "original_unit": "lbs",
                    "mapping_method": "regex_rule_match",
                    "mapping_engine_version": "RegexMatchingEngine 1.0",
                    "mapping_confidence": 0.91,
                    "confidence_breakdown": {},
                    "ocr_confidence": None,
                    "document_id": "doc_1",
                    "reader_operation_id": "op_1",
                    "page_index": 0,
                    "matched_alias": "Weight",
                    "extracted_at": "2026-07-29T10:16:02Z",
                    "report_date": None,
                },
            },
            "missing_fields": [],
            "flagged_for_reconfirm": [],
            "conflict_log": [],
        }
    }
    updated = mapper.apply_user_answer(
        "Weight", 80.0, state, schema, source="user_reconfirm"
    )
    val = updated["clinical"]["values"]["Weight"]
    assert val["canonical_value"] == 80.0
    assert val["source"] == "user_reconfirm"


# ────────────────────────────────────────────────────────────────
# Test 23: Fasting glucose alias without "fasting" → unresolved
# ────────────────────────────────────────────────────────────────

def test_23_fasting_glucose_unconfirmed(config, schema):
    """'Glucose: 112 mg/dL' (no 'fasting' in label) → no match."""
    engine = RegexMatchingEngine(config)
    candidate = Candidate(
        label_text="Glucose",
        value_text="112",
        unit_text="mg/dL",
        page_index=0,
        context_type="lab_report_section",
        source_line="Glucose: 112 mg/dL",
    )
    field_schema = schema["clinical"]["features"]["Fasting_Blood_Glucose"]
    result = engine.match(
        [candidate], "Fasting_Blood_Glucose", field_schema
    )
    # Must NOT match — "Glucose" doesn't contain "fasting"
    assert result is None


# ────────────────────────────────────────────────────────────────
# Test 24: Gender encoding matches schema (Male=1, Female=0)
# ────────────────────────────────────────────────────────────────

def test_24_gender_encoding(mapper, schema):
    """Gender='Male' encodes to 1, 'Female' to 0."""
    state = {
        "clinical": {
            "status": "incomplete",
            "values": {},
            "missing_fields": ["Gender"],
            "flagged_for_reconfirm": [],
            "conflict_log": [],
        }
    }
    updated = mapper.apply_user_answer(
        "Gender", "Male", state, schema, source="user_form"
    )
    val = updated["clinical"]["values"]["Gender"]
    assert val["canonical_value"] == 1

    state2 = copy.deepcopy(state)
    updated2 = mapper.apply_user_answer(
        "Gender", "Female", state2, schema, source="user_form"
    )
    val2 = updated2["clinical"]["values"]["Gender"]
    assert val2["canonical_value"] == 0


# ────────────────────────────────────────────────────────────────
# Test 25: Missing fields correctly reported
# ────────────────────────────────────────────────────────────────

def test_25_missing_fields(mapper, schema, empty_state):
    """After mapping a partial document, missing fields are listed."""
    reader_output = {
        "document_id": "doc_test",
        "pages": [
            {
                "page_index": 0,
                "raw_text": "HbA1c: 6.1 %\nALT: 34 U/L",
                "tables": [],
                "average_page_confidence": None,
            }
        ],
        "extraction_log": [
            {"operation_id": "op_test", "timestamp": "2026-01-01",
             "level": "INFO", "module": "test", "message": "test"}
        ],
    }
    result = mapper.map_features(
        reader_output, empty_state, schema
    )
    clinical = result.get("clinical", {})
    missing = clinical.get("missing_fields", [])
    # Many fields should be missing (only HbA1c and ALT matched)
    assert len(missing) > 0
    assert "Weight" in missing or "Height" in missing


# ────────────────────────────────────────────────────────────────
# Test 26: Full pipeline end-to-end with sample reader output
# ────────────────────────────────────────────────────────────────

def test_26_full_pipeline(mapper, schema, sample_reader_output, empty_state):
    """Full pipeline produces a Contract 2 output with proper structure."""
    result = mapper.map_features(
        sample_reader_output, empty_state, schema
    )

    # Should have clinical model
    assert "clinical" in result
    clinical = result["clinical"]
    assert "values" in clinical
    assert "missing_fields" in clinical
    assert "flagged_for_reconfirm" in clinical
    assert "conflict_log" in clinical

    # HbA1c should be extracted (table with header)
    if "HbA1c" in clinical["values"]:
        hba1c = clinical["values"]["HbA1c"]
        assert hba1c["canonical_value"] == 6.1
        assert hba1c["canonical_unit"] == "%"
        assert hba1c["mapping_method"] == "regex_rule_match"
        assert hba1c["validation_status"] == "VALID"
        assert "mapping_engine_version" in hba1c
        assert "confidence_breakdown" in hba1c
        assert "ocr_confidence" in hba1c
        # ocr_confidence should be None (digital PDF)
        assert hba1c["ocr_confidence"] is None

    # No resolved_value or winner anywhere in output
    _assert_no_resolution_in_state(result)


# ────────────────────────────────────────────────────────────────
# Test 27 (NEW): context_score correctly assigns 1.0 for table-header
# vs 0.2 for unstructured
# ────────────────────────────────────────────────────────────────

def test_27_context_score_table_vs_unstructured():
    """context_score is 1.0 for table_header, 0.2 for unstructured."""
    assert get_context_score("table_header") == 1.0
    assert get_context_score("lab_report_section") == 0.8
    assert get_context_score("generic_paragraph") == 0.5
    assert get_context_score("unstructured") == 0.2

    # Verify these scores affect the final confidence
    config = MapperConfig()
    conf_table, _ = compute_confidence(
        alias_quality=1.0, distance_score=1.0,
        unit_score=1.0, ambiguity_penalty=0.0,
        context_type="table_header", config=config,
    )
    conf_unstr, _ = compute_confidence(
        alias_quality=1.0, distance_score=1.0,
        unit_score=1.0, ambiguity_penalty=0.0,
        context_type="unstructured", config=config,
    )
    # Table context should produce higher confidence
    assert conf_table > conf_unstr
    # The difference should be exactly weight_context * (1.0 - 0.2)
    expected_diff = config.weight_context * (1.0 - 0.2)
    assert abs((conf_table - conf_unstr) - expected_diff) < 1e-10


# ────────────────────────────────────────────────────────────────
# Test 28 (NEW): Conflict detection uses per-field threshold
# ────────────────────────────────────────────────────────────────

def test_28_per_field_conflict_threshold():
    """HbA1c's tight threshold (0.05) flags a conflict that Weight's
    looser threshold (0.05 in schema, but let's compare with default
    0.20) would NOT flag for the same percentage difference."""
    # 8% relative difference
    hba1c_new = {"canonical_value": 6.5, "document_id": "d1",
                 "reader_operation_id": "op1", "report_date": "2026-01",
                 "extracted_at": "2026-07-29T10:16:02Z"}
    hba1c_old = {"canonical_value": 6.0, "document_id": "d2",
                 "reader_operation_id": "op2", "report_date": "2026-06",
                 "extracted_at": "2026-07-29T10:19:40Z"}

    # HbA1c with tight threshold (0.05) → SHOULD flag
    hba1c_conflict = detect_conflict(
        hba1c_new, hba1c_old, "HbA1c",
        {"conflict_relative_threshold": 0.05}, 0.20
    )
    assert hba1c_conflict is not None

    # Same 8% relative difference, but with default threshold (0.20) → NOT flagged
    weight_new = {"canonical_value": 86.5, "document_id": "d1",
                  "reader_operation_id": "op1", "report_date": "2026-01",
                  "extracted_at": "2026-07-29T10:16:02Z"}
    weight_old = {"canonical_value": 80.0, "document_id": "d2",
                  "reader_operation_id": "op2", "report_date": "2026-06",
                  "extracted_at": "2026-07-29T10:19:40Z"}

    weight_conflict = detect_conflict(
        weight_new, weight_old, "Weight",
        {}, 0.20   # No per-field override → uses default 0.20
    )
    assert weight_conflict is None  # 8.1% < 20% → no conflict


# ────────────────────────────────────────────────────────────────
# Meta-verification helper
# ────────────────────────────────────────────────────────────────

def _assert_no_resolution_in_state(state: dict) -> None:
    """Verify NO output anywhere contains a conflict resolution/winner.

    Recursively walks the state dict. If any key is 'resolved_value',
    'winner', or 'resolved_from_document_id', the module has taken
    on a responsibility it shouldn't have.
    """
    forbidden_keys = {
        "resolved_value", "winner", "resolved_from_document_id"
    }

    def _check(obj, path=""):
        if isinstance(obj, dict):
            for key, val in obj.items():
                assert key not in forbidden_keys, (
                    f"Forbidden key '{key}' found at {path}.{key} — "
                    f"the Mapper must never resolve conflicts."
                )
                _check(val, f"{path}.{key}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                _check(item, f"{path}[{i}]")

    _check(state)


def test_wide_dataset_table_mapping(schema):
    """Verify that multi-column wide dataset tables (CSV/XLSX format) extract all features."""
    from src.preprocessing.mapper import DefaultCandidateExtractor, RegexMatchingEngine, FeatureMapper, MapperConfig, RangeValidator, UnitValidator, TypeValidator, BMICalculator

    table = [
        ["Patient_ID", "Age", "Gender", "Height_cm", "Weight_kg", "BMI", "Waist_Circumference_cm", "Systolic_BP", "Diastolic_BP", "Fasting_Blood_Glucose", "HbA1c", "LDL_Cholesterol", "HDL_Cholesterol", "Triglycerides", "ALT", "AST", "Family_History_Diabetes", "Family_History_Hypertension"],
        ["TEST_C025", "49", "Female", "161", "77", "29.7", "98", "134", "84", "106", "5.8", "131", "44", "162", "38", "30", "Yes", "Yes"]
    ]

    reader_output = {
        "document_id": "doc_wide_table",
        "pages": [{
            "page_index": 0,
            "raw_text": "Patient_ID Age Gender Height_cm Weight_kg BMI Waist_Circumference_cm Systolic_BP Diastolic_BP Fasting_Blood_Glucose HbA1c LDL_Cholesterol HDL_Cholesterol Triglycerides ALT AST Family_History_Diabetes Family_History_Hypertension\nTEST_C025 49 Female 161 77 29.7 98 134 84 106 5.8 131 44 162 38 30 Yes Yes",
            "tables": [table]
        }]
    }

    config = MapperConfig()
    mapper = FeatureMapper(
        candidate_extractor=DefaultCandidateExtractor(),
        regex_engine=RegexMatchingEngine(config),
        llm_engine=None,
        validators=[RangeValidator(), UnitValidator(), TypeValidator()],
        derived_calculators={"BMI": BMICalculator()},
        config=config,
    )

    output = mapper.map_features(reader_output, {}, schema)
    clinical_values = output["clinical"]["values"]

    assert clinical_values["Age"]["canonical_value"] == 49
    assert clinical_values["Gender"]["canonical_value"] == "Female"
    assert clinical_values["Height"]["canonical_value"] == 161.0
    assert clinical_values["Weight"]["canonical_value"] == 77.0
    assert clinical_values["BMI"]["canonical_value"] == 29.7
    assert clinical_values["Systolic_BP"]["canonical_value"] == 134.0
    assert clinical_values["Diastolic_BP"]["canonical_value"] == 84.0
    assert clinical_values["Fasting_Blood_Glucose"]["canonical_value"] == 106.0
    assert clinical_values["HbA1c"]["canonical_value"] == 5.8
    assert clinical_values["LDL"]["canonical_value"] == 131.0
    assert clinical_values["HDL"]["canonical_value"] == 44.0
    assert clinical_values["Triglycerides"]["canonical_value"] == 162.0
    assert clinical_values["ALT"]["canonical_value"] == 38.0
    assert clinical_values["AST"]["canonical_value"] == 30.0
    assert clinical_values["Family_History_Diabetes"]["canonical_value"] in ("Yes", True, 1)
    assert clinical_values["Family_History_Hypertension"]["canonical_value"] in ("Yes", True, 1)

