"""
PdfTextExtractor — extracts text and tables from digital (text-layer) PDFs.

Uses pdfplumber. This extractor handles ONLY pages that have a text layer.
Scanned/image pages are handled by TesseractOCRExtractor via the orchestrator's
per-page routing logic (Section 6).

Single Responsibility: extract digital PDF content. Does NOT do OCR, does NOT
validate quality, does NOT detect duplicates.
"""

import pdfplumber
from datetime import datetime, timezone

from src.preprocessing.reader.interfaces import Extractor
from src.preprocessing.reader.exceptions import CorruptedDocumentError


import re

def _clean_duplicate_chars(text: str) -> str:
    """Clean duplicated/quadrupled character runs caused by overlapping PDF font layers.

    Handles canvas/HTML PDF font layering where every character is repeated N times
    (e.g., CCCClllliiiieeeennntttt -> Client, TTTTeeeesssstttt -> Test).
    """
    if not text:
        return text

    def clean_word(word: str) -> str:
        if re.search(r"([A-Za-z0-9])\1{2,}", word):
            w = re.sub(r"([A-Za-z0-9])\1{3}", r"\1", word)
            w = re.sub(r"([A-Za-z0-9])\1{2}", r"\1", w)
            if len(w) >= 4:
                doubles = len(re.findall(r"([A-Za-z])\1", w))
                singles = len(re.sub(r"([A-Za-z])\1", r"\1", w))
                if doubles > 0 and doubles >= (singles / 2):
                    w = re.sub(r"([A-Za-z])\1", r"\1", w)
            return w
        return word

    lines = []
    for line in text.split("\n"):
        if re.search(r"([A-Za-z0-9])\1{2,}", line):
            words = line.split(" ")
            cleaned_words = [clean_word(w) for w in words]
            lines.append(" ".join(cleaned_words))
        else:
            lines.append(line)
    return "\n".join(lines)


class PdfTextExtractor(Extractor):
    """Extracts text and tables from digital PDF pages using pdfplumber."""

    EXTRACTOR_NAME = "pdfplumber"

    def __init__(self, enable_table_extraction: bool = True) -> None:
        self._enable_table_extraction = enable_table_extraction

    def extract(self, file_path: str) -> dict:
        """Extract all pages from a digital PDF.

        Args:
            file_path: Path to the PDF file.

        Returns:
            Dict with raw_pages, extraction_log, extractor_name.

        Raises:
            CorruptedDocumentError: If pdfplumber cannot open the file at all.
        """
        raw_pages: list[dict] = []
        extraction_log: list[dict] = []

        try:
            pdf = pdfplumber.open(file_path)
        except Exception as exc:
            raise CorruptedDocumentError(
                f"pdfplumber cannot open file: {exc}"
            ) from exc

        try:
            for page_index, page in enumerate(pdf.pages):
                page_result = self._extract_single_page(page, page_index)
                raw_pages.append(page_result["page"])
                extraction_log.extend(page_result["log_entries"])
        finally:
            pdf.close()

        return {
            "raw_pages": raw_pages,
            "extraction_log": extraction_log,
            "extractor_name": self.EXTRACTOR_NAME,
        }

    def extract_page_from_pdf(
        self, page: "pdfplumber.page.Page", page_index: int
    ) -> dict:
        """Extract a single pdfplumber page (used by orchestrator for
        per-page routing).

        Args:
            page: A pdfplumber Page object.
            page_index: Zero-based page index.

        Returns:
            Dict with 'page' and 'log_entries' keys.
        """
        return self._extract_single_page(page, page_index)

    def extract_page_from_image(self, image, page_index: int) -> dict:
        """Not supported — PdfTextExtractor works with text layers, not images.

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError(
            "PdfTextExtractor does not support image-based extraction. "
            "Use TesseractOCRExtractor for scanned pages."
        )

    def _extract_single_page(self, page, page_index: int) -> dict:
        """Internal: extract text and tables from one pdfplumber page."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        log_entries: list[dict] = []

        # Extract text
        raw_text = page.extract_text() or ""
        if re.search(r"([A-Za-z0-9])\1{2,}", raw_text):
            raw_text = _clean_duplicate_chars(raw_text)

        log_entries.append({
            "timestamp": timestamp,
            "level": "INFO",
            "module": "PdfTextExtractor",
            "message": (
                f"page {page_index}: extracted {len(raw_text)} chars"
                f"{' (empty)' if not raw_text.strip() else ''}"
            ),
        })

        # Extract tables
        tables: list[list[list[str]]] = []
        if self._enable_table_extraction:
            try:
                raw_tables = page.extract_tables() or []
                for table in raw_tables:
                    # Normalize: convert None cells to empty strings and clean duplicate chars
                    cleaned_table = [
                        [_clean_duplicate_chars(str(cell)) if cell is not None else "" for cell in row]
                        for row in table
                    ]
                    tables.append(cleaned_table)

                if tables:
                    total_rows = sum(len(t) for t in tables)
                    log_entries.append({
                        "timestamp": timestamp,
                        "level": "INFO",
                        "module": "PdfTextExtractor",
                        "message": (
                            f"page {page_index}: table extraction succeeded: "
                            f"{len(tables)} table(s), {total_rows} total rows"
                        ),
                    })
            except Exception as exc:
                log_entries.append({
                    "timestamp": timestamp,
                    "level": "WARNING",
                    "module": "PdfTextExtractor",
                    "message": (
                        f"page {page_index}: table extraction failed: {exc}"
                    ),
                })

        return {
            "page": {
                "page_index": page_index,
                "extractor_used": self.EXTRACTOR_NAME,
                "raw_text": raw_text,
                "tables": tables,
                "average_page_confidence": None,  # Not OCR, no confidence score
            },
            "log_entries": log_entries,
        }
