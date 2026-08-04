"""
Abstract interface for document extractors.

The orchestrator depends ONLY on this interface (Dependency Inversion).
Concrete extractors implement it. New extractors can be added without
modifying the orchestrator or existing extractors (Open/Closed).
"""

from abc import ABC, abstractmethod


class Extractor(ABC):
    """Abstract base class that every extractor must implement.

    Return contract:
        {
            "raw_pages": list[dict],      # page dicts per Section 9
            "extraction_log": list[dict],  # structured log entries per Section 7
            "extractor_name": str          # e.g. "pdfplumber", "tesseract", "pandas"
        }

    Each page dict in raw_pages must contain:
        {
            "page_index": int,
            "extractor_used": str,
            "raw_text": str,
            "tables": list,
            "average_page_confidence": float | None
        }
    """

    @abstractmethod
    def extract(self, file_path: str) -> dict:
        """Extract content from the given file.

        Args:
            file_path: Absolute path to the file to extract from.

        Returns:
            A dict with keys: raw_pages, extraction_log, extractor_name.
        """
        ...

    @abstractmethod
    def extract_page_from_image(self, image, page_index: int) -> dict:
        """Extract content from a single page image (used for per-page
        PDF routing where scanned pages are converted to images).

        Args:
            image: A PIL Image object for a single page.
            page_index: The zero-based page index within the document.

        Returns:
            A single page dict with keys: page_index, extractor_used,
            raw_text, tables, average_page_confidence.

        Raises:
            NotImplementedError: If this extractor does not support
            single-page image extraction (e.g. PandasStructuredParser).
        """
        ...
