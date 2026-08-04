"""
Configuration object for the Document Reader module.

All thresholds referenced in the spec (quality check numbers, hash algorithm,
feature toggles) live here — nothing is hardcoded inline in logic code.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReaderConfig:
    """Immutable configuration for the Document Reader.

    Frozen dataclass ensures thread-safety — once created, config values
    cannot be accidentally mutated by any extractor or the orchestrator.
    """

    # Quality check thresholds (Section 8)
    min_nonwhitespace_chars: int = 20
    min_alphanumeric_ratio: float = 0.5
    max_repeated_char_run: int = 8

    # Duplicate detection (Section 5.4)
    duplicate_hash_algorithm: str = "sha256"

    # Feature toggles
    enable_table_extraction: bool = True
    enable_report_date_detection: bool = True
