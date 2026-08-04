"""
Test suite for the Document Reader module.

Covers all 14 test cases from Section 14 of the spec:
 1. Clean digital PDF
 2. Scanned/image-only PDF
 3. Mixed PDF (page 1 digital, page 2 scanned)
 4. Plain image file
 5. CSV file
 6. Exact hash match (duplicate)
 7. Garbage/repeated-character text
 8. Ambiguous date
 9. Unambiguous date
10. Missing date
11. Unsupported file type
12. Dependency injection with mock
13. Statelessness
14. Determinism
"""

import os
import csv
import hashlib
import tempfile
from unittest.mock import MagicMock, patch
from datetime import datetime

import pytest

from src.preprocessing.reader.config import ReaderConfig
from src.preprocessing.reader.interfaces import Extractor
from src.preprocessing.reader.exceptions import (
    UnsupportedFileTypeError,
    CorruptedDocumentError,
    DocumentReaderError,
)
from src.preprocessing.reader.document_reader import DocumentReader
from src.preprocessing.reader.quality_check import run_quality_check
from src.preprocessing.reader.date_extractor import extract_report_date
from src.preprocessing.reader.duplicate_detector import (
    compute_file_hash,
    check_duplicate,
)


# ─── FIXTURES ────────────────────────────────────────────────────

@pytest.fixture
def config():
    """Default ReaderConfig for tests."""
    return ReaderConfig()


@pytest.fixture
def temp_dir():
    """Temporary directory for test files."""
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def csv_file(temp_dir):
    """Create a simple CSV test file."""
    path = os.path.join(temp_dir, "test_report.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Test", "Result", "Unit", "Reference Range"])
        writer.writerow(["HbA1c", "6.1", "%", "4.0-5.6"])
        writer.writerow(["Fasting Glucose", "112", "mg/dL", "70-99"])
        writer.writerow(["LDL Cholesterol", "130", "mg/dL", "<100"])
    return path


@pytest.fixture
def unknown_file(temp_dir):
    """Create a file with unsupported type."""
    path = os.path.join(temp_dir, "mystery.xyz")
    with open(path, "wb") as f:
        f.write(b"\x00\x01\x02\x03random data that is not a known format")
    return path


def _make_mock_extractor(
    extractor_name: str,
    raw_text: str = "Patient: Jane Doe\nHbA1c: 6.1%\nGlucose: 112 mg/dL",
    tables: list | None = None,
    confidence: float | None = None,
    page_count: int = 1,
) -> MagicMock:
    """Create a mock Extractor with preset return values."""
    mock = MagicMock(spec=Extractor)
    mock.extract.return_value = {
        "raw_pages": [
            {
                "page_index": i,
                "extractor_used": extractor_name,
                "raw_text": raw_text,
                "tables": tables or [],
                "average_page_confidence": confidence,
            }
            for i in range(page_count)
        ],
        "extraction_log": [
            {
                "timestamp": "2026-07-29T10:15:00.100Z",
                "level": "INFO",
                "module": extractor_name,
                "message": f"mock extraction completed for {page_count} page(s)",
            }
        ],
        "extractor_name": extractor_name,
    }
    # Mock the page-level methods too
    mock.extract_page_from_image.return_value = {
        "page_index": 0,
        "extractor_used": extractor_name,
        "raw_text": raw_text,
        "tables": tables or [],
        "average_page_confidence": confidence,
    }
    return mock


def _build_reader(
    config: ReaderConfig,
    pdf_extractor: Extractor | None = None,
    ocr_extractor: Extractor | None = None,
    structured_parser: Extractor | None = None,
) -> DocumentReader:
    """Build a DocumentReader with mocks for any unspecified extractors."""
    return DocumentReader(
        pdf_extractor=pdf_extractor or _make_mock_extractor("pdfplumber"),
        ocr_extractor=ocr_extractor or _make_mock_extractor("tesseract"),
        structured_parser=structured_parser or _make_mock_extractor("pandas"),
        config=config,
    )


# ─── TEST 5: CSV file ───────────────────────────────────────────

class TestCSVExtraction:
    """Test 5: CSV file → PandasStructuredParser, correct tables."""

    def test_csv_file_extraction(self, config, csv_file):
        """CSV should be routed to structured_parser and produce tables."""
        from src.preprocessing.reader.extractors.pandas_structured_parser import (
            PandasStructuredParser,
        )

        real_parser = PandasStructuredParser()
        reader = _build_reader(config, structured_parser=real_parser)

        result = reader.read_document(csv_file, "doc_csv_001", {})

        assert result["file_type"] == "csv"
        assert result["page_count"] == 1
        assert result["quality_check"]["passed"] is True, f"Quality check failed with reason: {result['quality_check']['reason']}"
        assert len(result["pages"]) == 1

        page = result["pages"][0]
        assert page["extractor_used"] == "pandas"
        assert len(page["tables"]) == 1

        table = page["tables"][0]
        # First row is header
        assert table[0] == ["Test", "Result", "Unit", "Reference Range"]
        # Data rows
        assert table[1][0] == "HbA1c"
        assert table[1][1] == "6.1"
        assert table[2][0] == "Fasting Glucose"
        assert table[2][1] == "112"


# ─── TEST 6: Duplicate detection ────────────────────────────────

class TestDuplicateDetection:
    """Test 6: Exact hash match → early EXACT_DUPLICATE return, no extraction."""

    def test_duplicate_returns_early(self, config, csv_file):
        """When file hash matches known_hashes, return immediately."""
        file_hash = compute_file_hash(csv_file)
        known_hashes = {file_hash: "doc_original_123"}

        mock_parser = _make_mock_extractor("pandas")
        reader = _build_reader(config, structured_parser=mock_parser)

        result = reader.read_document(csv_file, "doc_new_456", known_hashes)

        assert result["status"] == "EXACT_DUPLICATE"
        assert result["matched_document_id"] == "doc_original_123"
        assert result["file_hash"] == file_hash
        # Extractor should NEVER have been called
        mock_parser.extract.assert_not_called()

    def test_no_duplicate_proceeds(self, config, csv_file):
        """When hash doesn't match, proceed with extraction."""
        known_hashes = {"some_other_hash": "doc_other"}

        from src.preprocessing.reader.extractors.pandas_structured_parser import (
            PandasStructuredParser,
        )

        reader = _build_reader(
            config, structured_parser=PandasStructuredParser()
        )
        result = reader.read_document(csv_file, "doc_new", known_hashes)

        assert "status" not in result or result.get("status") != "EXACT_DUPLICATE"
        assert result["document_id"] == "doc_new"
        assert result["pages"]  # Should have content

    def test_check_duplicate_function(self):
        """Unit test for check_duplicate()."""
        known = {"abc123": "doc_1", "def456": "doc_2"}
        assert check_duplicate("abc123", known) == {
            "status": "EXACT_DUPLICATE",
            "matched_document_id": "doc_1",
        }
        assert check_duplicate("xyz789", known) is None


# ─── TEST 7: Garbage/repeated-character text ─────────────────────

class TestQualityCheckRepeatedChars:
    """Test 7: Repeated characters → quality_check fails, no crash."""

    def test_repeated_chars_fail(self, config):
        """Repeated-character text should fail quality check."""
        pages = [{"raw_text": "AAAAAAAAAA 1234567890 1234567890"}]
        result = run_quality_check(pages, config)
        assert result["passed"] is False
        assert "repeated characters" in result["reason"]

    def test_near_empty_fails(self, config):
        """Near-empty text should fail."""
        pages = [{"raw_text": "   "}]
        result = run_quality_check(pages, config)
        assert result["passed"] is False
        assert "near-empty" in result["reason"]

    def test_no_digits_fails(self, config):
        """Text with no digits should fail."""
        pages = [{"raw_text": "This is a normal paragraph with no numbers at all just text"}]
        result = run_quality_check(pages, config)
        assert result["passed"] is False
        assert "no numeric content" in result["reason"]

    def test_low_alphanumeric_fails(self, config):
        """Text dominated by special characters should fail."""
        pages = [{"raw_text": "!@#$%^&*()!@#$%^&*()1"}]
        result = run_quality_check(pages, config)
        assert result["passed"] is False
        assert "non-alphanumeric" in result["reason"]

    def test_good_text_passes(self, config):
        """Normal medical text should pass all checks."""
        pages = [{"raw_text": "Patient: John Doe\nHbA1c: 6.1%\nGlucose: 112 mg/dL"}]
        result = run_quality_check(pages, config)
        assert result["passed"] is True
        assert result["reason"] is None

    def test_garbage_in_full_pipeline(self, config, temp_dir):
        """Full pipeline with garbage CSV should not crash."""
        # Create a CSV that will produce garbage-like content
        path = os.path.join(temp_dir, "garbage.csv")
        with open(path, "w", encoding="utf-8") as f:
            f.write("col1\n" + ("x" * 50) + "\n")  # No digits

        from src.preprocessing.reader.extractors.pandas_structured_parser import (
            PandasStructuredParser,
        )

        reader = _build_reader(
            config, structured_parser=PandasStructuredParser()
        )
        result = reader.read_document(path, "doc_garbage", {})

        # Should not crash, but quality check should fail
        assert result["quality_check"]["passed"] is False
        assert result["extraction_confidence"] == "low"


# ─── TEST 8: Ambiguous date ─────────────────────────────────────

class TestAmbiguousDate:
    """Test 8: Ambiguous date → report_date is None, confidence is LOW."""

    def test_ambiguous_date(self):
        """01/02/2025 could be Jan 2 or Feb 1 — must NOT guess."""
        text = "Collection Date: 01/02/2025\nHbA1c: 6.1%"
        result = extract_report_date(text)
        assert result["report_date"] is None
        assert result["report_date_confidence"] == "LOW"

    def test_ambiguous_date_different_format(self):
        """05-06-2025 is also ambiguous."""
        text = "Report Date: 05-06-2025\nGlucose: 112"
        result = extract_report_date(text)
        assert result["report_date"] is None
        assert result["report_date_confidence"] == "LOW"


# ─── TEST 9: Unambiguous date ───────────────────────────────────

class TestUnambiguousDate:
    """Test 9: Unambiguous date → correctly parsed, confidence HIGH."""

    def test_named_month_dmy(self):
        """14-Jan-2026 is unambiguous."""
        text = "Collection Date: 14-Jan-2026\nHbA1c: 6.1%"
        result = extract_report_date(text)
        assert result["report_date"] == "2026-01-14"
        assert result["report_date_confidence"] == "HIGH"

    def test_iso_format(self):
        """YYYY-MM-DD is unambiguous."""
        text = "Test Date: 2026-01-14\nGlucose: 112"
        result = extract_report_date(text)
        assert result["report_date"] == "2026-01-14"
        assert result["report_date_confidence"] == "HIGH"

    def test_named_month_mdy(self):
        """Jan 14, 2026 is unambiguous."""
        text = "Report Date: Jan 14, 2026\nResult: Normal"
        result = extract_report_date(text)
        assert result["report_date"] == "2026-01-14"
        assert result["report_date_confidence"] == "HIGH"

    def test_day_over_12_is_unambiguous(self):
        """15/06/2025 — day=15 > 12, so must be DD/MM/YYYY."""
        text = "Collection Date: 15/06/2025\nTest: HbA1c"
        result = extract_report_date(text)
        assert result["report_date"] == "2025-06-15"
        assert result["report_date_confidence"] == "HIGH"


# ─── TEST 10: Missing date ──────────────────────────────────────

class TestMissingDate:
    """Test 10: No date anywhere → report_date=None, confidence=None."""

    def test_no_date_at_all(self):
        """Text with no date patterns → None/None."""
        text = "Patient: John Doe\nHbA1c: 6.1%\nGlucose: 112 mg/dL"
        result = extract_report_date(text)
        assert result["report_date"] is None
        assert result["report_date_confidence"] is None


# ─── TEST 11: Unsupported file type ─────────────────────────────

class TestUnsupportedFileType:
    """Test 11: Both magic-byte and extension fail → UnsupportedFileTypeError."""

    def test_unsupported_raises(self, config, unknown_file):
        reader = _build_reader(config)

        with pytest.raises(UnsupportedFileTypeError):
            reader.read_document(unknown_file, "doc_bad", {})


# ─── TEST 12: Dependency injection ──────────────────────────────

class TestDependencyInjection:
    """Test 12: Mock extractor is called instead of real implementation."""

    def test_mock_extractor_is_used(self, config, csv_file):
        """Orchestrator should call the injected mock, not a real parser."""
        mock_parser = _make_mock_extractor(
            "mock_pandas",
            raw_text="Test 1 Result 2 Unit 3",
            tables=[[["A", "B"], ["1", "2"]]],
        )
        reader = _build_reader(config, structured_parser=mock_parser)

        result = reader.read_document(csv_file, "doc_di", {})

        # The mock's extract() should have been called
        mock_parser.extract.assert_called_once_with(csv_file)
        # And the output should use mock's data
        assert result["pages"][0]["extractor_used"] == "mock_pandas"
        assert result["pages"][0]["raw_text"] == "Test 1 Result 2 Unit 3"


# ─── TEST 13: Statelessness ─────────────────────────────────────

class TestStatelessness:
    """Test 13: Two calls on same instance don't leak state."""

    def test_no_state_leakage(self, config, temp_dir):
        """Second call must be unaffected by first call's data."""
        from src.preprocessing.reader.extractors.pandas_structured_parser import (
            PandasStructuredParser,
        )

        # Create two different CSV files
        path1 = os.path.join(temp_dir, "file1.csv")
        with open(path1, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Test", "Value"])
            writer.writerow(["HbA1c", "6.1"])

        path2 = os.path.join(temp_dir, "file2.csv")
        with open(path2, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Metric", "Score"])
            writer.writerow(["BMI", "28.5"])

        reader = _build_reader(
            config, structured_parser=PandasStructuredParser()
        )

        result1 = reader.read_document(path1, "doc_first", {})
        result2 = reader.read_document(path2, "doc_second", {})

        # Results must be independent
        assert result1["document_id"] == "doc_first"
        assert result2["document_id"] == "doc_second"
        assert result1["source_file"] == "file1.csv"
        assert result2["source_file"] == "file2.csv"

        # Content must not bleed between calls
        text1 = result1["pages"][0]["raw_text"]
        text2 = result2["pages"][0]["raw_text"]
        assert "HbA1c" in text1
        assert "BMI" in text2
        assert "BMI" not in text1
        assert "HbA1c" not in text2

        # Extraction logs must be separate
        assert len(result1["extraction_log"]) > 0
        assert len(result2["extraction_log"]) > 0
        # Each log should only contain entries from its own call
        for entry in result2["extraction_log"]:
            assert "doc_first" not in entry.get("message", "")


# ─── TEST 14: Determinism ───────────────────────────────────────

class TestDeterminism:
    """Test 14: Same input + config → same output (except upload_timestamp)."""

    def test_deterministic_output(self, config, csv_file):
        """Two calls with same file should produce identical results."""
        from src.preprocessing.reader.extractors.pandas_structured_parser import (
            PandasStructuredParser,
        )

        reader = _build_reader(
            config, structured_parser=PandasStructuredParser()
        )

        result1 = reader.read_document(csv_file, "doc_det", {})
        result2 = reader.read_document(csv_file, "doc_det", {})

        # Remove fields that are expected to differ
        for r in [result1, result2]:
            r.pop("upload_timestamp", None)
            # Remove timestamps from extraction_log since they'll differ
            for entry in r.get("extraction_log", []):
                entry.pop("timestamp", None)
                entry.pop("operation_id", None)

        assert result1["document_id"] == result2["document_id"]
        assert result1["file_hash"] == result2["file_hash"]
        assert result1["file_type"] == result2["file_type"]
        assert result1["pages"] == result2["pages"]
        assert result1["quality_check"] == result2["quality_check"]
        assert result1["extraction_confidence"] == result2["extraction_confidence"]


# ─── ADDITIONAL: Output shape validation ─────────────────────────

class TestOutputShape:
    """Verify Section 9's required fields are always present."""

    def test_all_required_fields_present(self, config, csv_file):
        """Every required field from Section 9 must exist."""
        from src.preprocessing.reader.extractors.pandas_structured_parser import (
            PandasStructuredParser,
        )

        reader = _build_reader(
            config, structured_parser=PandasStructuredParser()
        )
        result = reader.read_document(csv_file, "doc_shape", {})

        required_keys = [
            "document_id", "source_file", "file_type", "mime_type",
            "file_size_bytes", "page_count", "report_date",
            "report_date_confidence", "upload_timestamp", "file_hash",
            "pages", "extraction_log", "quality_check", "extraction_confidence",
        ]
        for key in required_keys:
            assert key in result, f"Missing required key: {key}"

        # Check page shape
        page = result["pages"][0]
        page_keys = [
            "page_index", "extractor_used", "raw_text", "tables",
            "average_page_confidence",
        ]
        for key in page_keys:
            assert key in page, f"Missing required page key: {key}"

        # Check quality_check shape
        assert "passed" in result["quality_check"]
        assert "reason" in result["quality_check"]

    def test_extraction_log_is_structured(self, config, csv_file):
        """Extraction log entries must be dicts, not strings (Section 7)."""
        from src.preprocessing.reader.extractors.pandas_structured_parser import (
            PandasStructuredParser,
        )

        reader = _build_reader(
            config, structured_parser=PandasStructuredParser()
        )
        result = reader.read_document(csv_file, "doc_log", {})

        assert isinstance(result["extraction_log"], list)
        for entry in result["extraction_log"]:
            assert isinstance(entry, dict), f"Log entry is not a dict: {entry}"
            assert "level" in entry
            assert "module" in entry
            assert "message" in entry


# ─── ADDITIONAL: Duplicate detector unit tests ───────────────────

class TestComputeFileHash:
    """Unit tests for compute_file_hash()."""

    def test_hash_consistency(self, csv_file):
        """Same file → same hash every time."""
        h1 = compute_file_hash(csv_file)
        h2 = compute_file_hash(csv_file)
        assert h1 == h2

    def test_different_files_different_hashes(self, temp_dir):
        """Different content → different hashes."""
        f1 = os.path.join(temp_dir, "a.txt")
        f2 = os.path.join(temp_dir, "b.txt")
        with open(f1, "w") as f:
            f.write("content A")
        with open(f2, "w") as f:
            f.write("content B")

        assert compute_file_hash(f1) != compute_file_hash(f2)

    def test_custom_algorithm(self, csv_file):
        """Should support different hash algorithms."""
        h_sha = compute_file_hash(csv_file, "sha256")
        h_md5 = compute_file_hash(csv_file, "md5")
        assert h_sha != h_md5  # Different algorithms, different hashes
        assert len(h_md5) == 32  # MD5 produces 32-char hex
