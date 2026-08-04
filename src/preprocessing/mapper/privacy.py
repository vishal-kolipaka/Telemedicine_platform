"""
PII redaction for LLM prompts (Section 8, Privacy).

Before sending ANY text to an LLM, strip patient name and obvious
direct identifiers.  Provenance (document_id, page_index) is kept
for audit but NEVER sent to the LLM.
"""

from __future__ import annotations

import re


# Patterns that match common PII fields in medical reports.
# Each pattern captures the identifying text that should be replaced.
_PII_PATTERNS: list[re.Pattern] = [
    # "Patient: John Doe", "Patient Name: Jane Smith"
    re.compile(
        r"(?i)patient\s*(?:name)?\s*[:=]\s*(.+?)(?:\n|$)"
    ),
    # "Name: John Doe"
    re.compile(
        r"(?i)^name\s*[:=]\s*(.+?)(?:\n|$)",
        re.MULTILINE,
    ),
    # "DOB: 01/15/1980", "Date of Birth: ..."
    re.compile(
        r"(?i)(?:dob|date\s*of\s*birth)\s*[:=]\s*(.+?)(?:\n|$)"
    ),
    # "SSN: 123-45-6789" or similar
    re.compile(
        r"(?i)ssn\s*[:=]\s*(\d[\d\-\s]+)(?:\n|$)"
    ),
    # "MRN: 12345678", "Medical Record Number: ..."
    re.compile(
        r"(?i)(?:mrn|medical\s*record\s*(?:number|no\.?))\s*[:=]\s*(.+?)(?:\n|$)"
    ),
    # Phone number patterns
    re.compile(
        r"(?i)(?:phone|tel|mobile|contact)\s*[:=]\s*([\d\(\)\-\+\s]+)(?:\n|$)"
    ),
    # Email addresses
    re.compile(
        r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    ),
    # Address lines
    re.compile(
        r"(?i)address\s*[:=]\s*(.+?)(?:\n|$)"
    ),
]


def redact_pii(text: str) -> str:
    """Strip patient name and obvious direct identifiers from text.

    This is a MANDATORY step before constructing any LLM prompt.
    The LLM should only see the minimal text needed to resolve
    the field in question — no names, no DOB, no SSN, no contact info.

    Args:
        text: Raw text that may contain PII.

    Returns:
        Text with PII fields replaced with [REDACTED].
    """
    redacted = text
    for pattern in _PII_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted
