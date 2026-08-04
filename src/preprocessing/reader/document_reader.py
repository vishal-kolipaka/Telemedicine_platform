"""
DocumentReader — Orchestrator for the Document Reader module.

Three-stage internal pipeline:
1. Extract — duplicate check, format detection, per-page routing to extractors
2. Validate — quality check, report date extraction, metadata enrichment
3. Assemble Output — build the final dict matching Section 9's shape

Design principles enforced:
- Depends only on the abstract Extractor interface (Dependency Inversion)
- Extractors are constructor-injected, not instantiated internally
- Stateless — no data persists between calls
- Thread-safe — no shared mutable state
- Deterministic — same input + config = same output (excluding upload_timestamp)

Sections: 1, 2, 3, 5.2, 6, 7, 9, 12 of the spec.
"""

import os
import uuid
from datetime import datetime, timezone

import filetype
import pdfplumber

from src.preprocessing.reader.interfaces import Extractor
from src.preprocessing.reader.config import ReaderConfig
from src.preprocessing.reader.exceptions import (
    UnsupportedFileTypeError,
    CorruptedDocumentError,
    ExtractionError,
)
from src.preprocessing.reader.duplicate_detector import (
    compute_file_hash,
    check_duplicate,
)
from src.preprocessing.reader.quality_check import run_quality_check
from src.preprocessing.reader.date_extractor import extract_report_date


# Mapping from detected MIME types to our file_type categories
_MIME_TO_FILE_TYPE: dict[str, str] = {
    "application/pdf": "pdf",
    "image/jpeg": "image",
    "image/png": "image",
    "image/tiff": "image",
    "image/bmp": "image",
    "image/gif": "image",
    "image/webp": "image",
    "text/plain": "text",
}

# Extension fallback mapping (Section 6, step 1)
_EXT_TO_FILE_TYPE: dict[str, str] = {
    ".pdf": "pdf",
    ".jpg": "image",
    ".jpeg": "image",
    ".png": "image",
    ".tiff": "image",
    ".tif": "image",
    ".bmp": "image",
    ".gif": "image",
    ".webp": "image",
    ".csv": "csv",
    ".xlsx": "xlsx",
    ".xls": "xlsx",
    ".txt": "text",
}

_EXT_TO_MIME: dict[str, str] = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".tiff": "image/tiff",
    ".tif": "image/tiff",
    ".bmp": "image/bmp",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".csv": "text/csv",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xls": "application/vnd.ms-excel",
    ".txt": "text/plain",
}


class DocumentReader:
    """Orchestrator that routes files to the correct extractor(s).

    Constructor-injected with concrete Extractor implementations and config.
    Never instantiates extractors internally.
    """

    def __init__(
        self,
        pdf_extractor: Extractor,
        ocr_extractor: Extractor,
        structured_parser: Extractor,
        config: ReaderConfig,
    ) -> None:
        self._pdf_extractor = pdf_extractor
        self._ocr_extractor = ocr_extractor
        self._structured_parser = structured_parser
        self._config = config

    def read_document(
        self,
        file_path: str,
        document_id: str,
        known_hashes: dict[str, str],
    ) -> dict:
        """Process a document through the full Reader pipeline.

        Args:
            file_path: Absolute path to the file.
            document_id: Caller-assigned unique identifier.
            known_hashes: Dict mapping {file_hash: document_id} for
                          duplicate detection.

        Returns:
            A JSON-serializable dict matching Section 9's shape, OR
            an early-return duplicate signal dict.

        Raises:
            UnsupportedFileTypeError: If the file type has no extractor.
            CorruptedDocumentError: If the file cannot be opened at all.
        """
        # Generate a unique operation_id for this entire call
        operation_id = f"op_{uuid.uuid4().hex[:8]}"
        upload_timestamp = datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%S.%f"
        )[:-3] + "Z"
        extraction_log: list[dict] = []

        def log(level: str, module: str, message: str) -> None:
            """Append a structured log entry (Section 7)."""
            extraction_log.append({
                "operation_id": operation_id,
                "timestamp": datetime.now(timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%S.%f"
                )[:-3] + "Z",
                "level": level,
                "module": module,
                "message": message,
            })

        # ────────────────────────────────────────────────────────
        # STAGE 1: EXTRACT
        # ────────────────────────────────────────────────────────

        # 1a. File size
        file_size_bytes = os.path.getsize(file_path)

        # 1b. Compute hash + duplicate check (MUST run before extraction)
        file_hash = compute_file_hash(
            file_path, self._config.duplicate_hash_algorithm
        )
        log("INFO", "DocumentReader", "file hash computed")

        dup_result = check_duplicate(file_hash, known_hashes)
        if dup_result is not None:
            log(
                "INFO",
                "DocumentReader",
                f"EXACT_DUPLICATE detected, matches document_id="
                f"{dup_result['matched_document_id']}",
            )
            file_type, mime_type = "pdf", "application/pdf"
            try:
                file_type, mime_type = self._detect_file_type(file_path)
            except Exception:
                pass

            # Early return — full structured response with duplicate status
            return {
                "status": "EXACT_DUPLICATE",
                "matched_document_id": dup_result["matched_document_id"],
                "document_id": document_id,
                "source_file": os.path.basename(file_path),
                "file_type": file_type,
                "mime_type": mime_type,
                "file_size_bytes": file_size_bytes,
                "page_count": 1,
                "report_date": None,
                "report_date_confidence": None,
                "upload_timestamp": upload_timestamp,
                "file_hash": file_hash,
                "pages": [],
                "extraction_log": extraction_log,
                "quality_check": {
                    "passed": True,
                    "reason": f"Exact duplicate document detected — matches document ID: {dup_result['matched_document_id']}"
                },
                "extraction_confidence": "high"
            }

        log("INFO", "DocumentReader", "no duplicate match found, proceeding")

        # 1c. Detect file type (magic bytes first, extension fallback)
        file_type, mime_type = self._detect_file_type(file_path)
        log(
            "INFO",
            "DocumentReader",
            f"file type detected: {file_type} (mime: {mime_type})",
        )

        # 1d. Route to extractor(s) and get raw pages
        raw_pages: list[dict] = []
        page_count = 0

        try:
            if file_type in ("csv", "xlsx"):
                result = self._structured_parser.extract(file_path)
                raw_pages = result["raw_pages"]
                self._merge_log_entries(
                    extraction_log, result["extraction_log"], operation_id
                )
                page_count = 1

            elif file_type == "text":
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    text_content = f.read()
                raw_pages = [{
                    "page_index": 0,
                    "extractor_used": "text_file_reader",
                    "raw_text": text_content,
                    "tables": [],
                    "average_page_confidence": None,
                }]
                page_count = 1
                log("INFO", "DocumentReader", f"read plain text file ({len(text_content)} chars)")

            elif file_type == "image":
                result = self._ocr_extractor.extract(file_path)
                raw_pages = result["raw_pages"]
                self._merge_log_entries(
                    extraction_log, result["extraction_log"], operation_id
                )
                page_count = 1

            elif file_type == "pdf":
                raw_pages, page_count = self._extract_pdf_per_page(
                    file_path, extraction_log, operation_id, log
                )

        except (UnsupportedFileTypeError, CorruptedDocumentError):
            raise
        except ExtractionError as exc:
            # Log but don't crash — produce a low-quality output
            log("ERROR", "DocumentReader", f"extraction error: {exc}")
            # Proceed with whatever pages we have (possibly empty)
        except Exception as exc:
            # Catch-all for unexpected errors — still don't crash
            log("ERROR", "DocumentReader", f"unexpected extraction error: {exc}")

        # ────────────────────────────────────────────────────────
        # STAGE 2: VALIDATE
        # ────────────────────────────────────────────────────────

        # 2a. Quality check
        quality_result = run_quality_check(raw_pages, self._config)
        log(
            "INFO" if quality_result["passed"] else "WARNING",
            "DocumentReader",
            f"quality check {'passed' if quality_result['passed'] else 'FAILED'}"
            + (f": {quality_result['reason']}" if quality_result["reason"] else ""),
        )

        # 2b. Report date extraction
        report_date_info = {"report_date": None, "report_date_confidence": None}
        if self._config.enable_report_date_detection and raw_pages:
            all_text = "\n".join(p.get("raw_text", "") for p in raw_pages)
            report_date_info = extract_report_date(all_text)

        # 2c. Extraction confidence (document-level rollup)
        extraction_confidence = self._compute_extraction_confidence(
            raw_pages, quality_result
        )

        # ────────────────────────────────────────────────────────
        # STAGE 3: ASSEMBLE OUTPUT
        # ────────────────────────────────────────────────────────

        return {
            "document_id": document_id,
            "source_file": os.path.basename(file_path),
            "file_type": file_type,
            "mime_type": mime_type,
            "file_size_bytes": file_size_bytes,
            "page_count": page_count if page_count > 0 else len(raw_pages),
            "report_date": report_date_info["report_date"],
            "report_date_confidence": report_date_info["report_date_confidence"],
            "upload_timestamp": upload_timestamp,
            "file_hash": file_hash,
            "pages": raw_pages,
            "extraction_log": extraction_log,
            "quality_check": quality_result,
            "extraction_confidence": extraction_confidence,
        }

    def _detect_file_type(self, file_path: str) -> tuple[str, str]:
        """Detect file type via magic bytes first, then extension fallback.

        Returns:
            Tuple of (file_type, mime_type).

        Raises:
            UnsupportedFileTypeError: If both detection methods fail.
        """
        # Try magic bytes first
        kind = filetype.guess(file_path)
        if kind is not None:
            mime = kind.mime
            if mime in _MIME_TO_FILE_TYPE:
                return _MIME_TO_FILE_TYPE[mime], mime
            # CSV/XLSX won't have magic bytes that filetype recognizes,
            # so fall through to extension check

        # Fallback to extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        if ext in _EXT_TO_FILE_TYPE:
            file_type = _EXT_TO_FILE_TYPE[ext]
            mime_type = _EXT_TO_MIME.get(ext, "application/octet-stream")
            return file_type, mime_type

        raise UnsupportedFileTypeError(
            f"Cannot determine file type for '{os.path.basename(file_path)}' "
            f"— magic bytes and extension both failed."
        )

    def _extract_pdf_per_page(
        self,
        file_path: str,
        extraction_log: list[dict],
        operation_id: str,
        log,
    ) -> tuple[list[dict], int]:
        """Per-page PDF extraction (Section 6, step 4).

        For each page: try pdfplumber text layer first. If empty/whitespace,
        convert to image and route to OCR extractor.

        Returns:
            Tuple of (raw_pages list, page_count).
        """
        raw_pages: list[dict] = []

        try:
            pdf = pdfplumber.open(file_path)
        except Exception as exc:
            raise CorruptedDocumentError(
                f"Cannot open PDF: {exc}"
            ) from exc

        try:
            page_count = len(pdf.pages)

            for page_index, page in enumerate(pdf.pages):
                # Try digital text layer first
                text = page.extract_text() or ""

                if text.strip():
                    # Digital page — use PDF extractor
                    log(
                        "INFO",
                        "DocumentReader",
                        f"page {page_index}: text layer found, routed to pdfplumber",
                    )
                    page_result = self._pdf_extractor.extract_page_from_pdf(
                        page, page_index
                    )
                    raw_pages.append(page_result["page"])
                    self._merge_log_entries(
                        extraction_log,
                        page_result["log_entries"],
                        operation_id,
                    )
                else:
                    # Scanned page — convert to image, route to OCR
                    log(
                        "INFO",
                        "DocumentReader",
                        f"page {page_index}: no text layer, routed to tesseract OCR",
                    )
                    try:
                        from pdf2image import convert_from_path

                        images = convert_from_path(
                            file_path,
                            first_page=page_index + 1,
                            last_page=page_index + 1,
                        )
                        if images:
                            page_dict = self._ocr_extractor.extract_page_from_image(
                                images[0], page_index
                            )
                            raw_pages.append(page_dict)
                        else:
                            log(
                                "WARNING",
                                "DocumentReader",
                                f"page {page_index}: pdf2image returned no images",
                            )
                            raw_pages.append(self._empty_page(page_index, "tesseract"))
                    except Exception as exc:
                        log(
                            "ERROR",
                            "DocumentReader",
                            f"page {page_index}: OCR failed: {exc}",
                        )
                        raw_pages.append(self._empty_page(page_index, "tesseract"))
        finally:
            pdf.close()

        return raw_pages, page_count

    @staticmethod
    def _empty_page(page_index: int, extractor_used: str) -> dict:
        """Create an empty page dict for when extraction fails."""
        return {
            "page_index": page_index,
            "extractor_used": extractor_used,
            "raw_text": "",
            "tables": [],
            "average_page_confidence": None,
        }

    @staticmethod
    def _merge_log_entries(
        target: list[dict],
        source: list[dict],
        operation_id: str,
    ) -> None:
        """Merge extractor log entries into the main log, adding operation_id."""
        for entry in source:
            merged = dict(entry)
            if "operation_id" not in merged:
                merged["operation_id"] = operation_id
            target.append(merged)

    @staticmethod
    def _compute_extraction_confidence(
        raw_pages: list[dict], quality_result: dict
    ) -> str:
        """Compute document-level extraction confidence.

        Returns "high" if confidence >= 80%, "medium" if between 50%-80%,
        and "low" if quality check failed or confidence < 50%.
        """
        if not quality_result["passed"]:
            return "low"

        if not raw_pages:
            return "low"

        # Check OCR confidence across pages
        ocr_confidences = [
            p["average_page_confidence"]
            for p in raw_pages
            if p.get("average_page_confidence") is not None
        ]
        if ocr_confidences:
            avg_confidence = sum(ocr_confidences) / len(ocr_confidences)
            if avg_confidence >= 80.0:
                return "high"
            elif avg_confidence >= 50.0:
                return "medium"
            else:
                return "low"

        return "high"
