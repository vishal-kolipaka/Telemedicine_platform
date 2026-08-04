"""
Document Reader Module
======================
Converts uploaded documents (PDF, images, CSV, XLSX) into raw machine-readable
content with structured logging, quality checks, and duplicate detection.

This module is the first stage of the Preprocessing Unit pipeline.
It extracts — it never interprets medical meaning.
"""

from src.preprocessing.reader.exceptions import (
    DocumentReaderError,
    UnsupportedFileTypeError,
    CorruptedDocumentError,
    ExtractionError,
    OCRExecutionError,
    ParserFailure,
)
from src.preprocessing.reader.config import ReaderConfig
from src.preprocessing.reader.interfaces import Extractor
from src.preprocessing.reader.document_reader import DocumentReader

__all__ = [
    "DocumentReader",
    "ReaderConfig",
    "Extractor",
    "DocumentReaderError",
    "UnsupportedFileTypeError",
    "CorruptedDocumentError",
    "ExtractionError",
    "OCRExecutionError",
    "ParserFailure",
]
