"""
Exception hierarchy for the Document Reader module.

Only UnsupportedFileTypeError and CorruptedDocumentError should escape
read_document() as raised exceptions. All others are caught internally,
logged, and converted into a low-quality-but-valid output object.
"""


class DocumentReaderError(Exception):
    """Base class for all Document Reader errors."""


class UnsupportedFileTypeError(DocumentReaderError):
    """Raised when the detected file type has no matching extractor."""


class CorruptedDocumentError(DocumentReaderError):
    """Raised when the file cannot be opened/parsed at all
    (not just low-quality output)."""


class ExtractionError(DocumentReaderError):
    """Generic extraction failure not covered by a more specific subclass."""


class OCRExecutionError(ExtractionError):
    """Raised only if OCR cannot run AT ALL (e.g. Tesseract binary
    missing/crashes) -- NOT for low-confidence OCR output, which is a
    quality_check concern, not an exception.

    Named 'ExecutionError' specifically to avoid confusion with
    low-quality-but-successful OCR, which is not an error condition."""


class ParserFailure(ExtractionError):
    """Raised when pandas cannot parse a CSV/XLSX file at all
    (e.g. malformed encoding)."""
