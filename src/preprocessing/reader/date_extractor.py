"""
Report Date Extraction — with confidence levels.

Scans extracted text for date labels and parses dates with confidence:
- HIGH: unambiguous format (YYYY-MM-DD, DD-Mon-YYYY, etc.)
- LOW:  ambiguous format (DD/MM/YYYY vs MM/DD/YYYY) — date NOT stored
- None: no date label/pattern found at all

Section 10 of the spec.
"""

import re
from datetime import datetime
from typing import Optional


# Date labels to search for, in priority order
# "Collection Date" is preferred over "Report Date" per spec
_DATE_LABELS = [
    "Collection Date",
    "Date Collected",
    "Date of Test",
    "Test Date",
    "Report Date",
]

# Unambiguous date patterns (order matters — try most specific first)
_UNAMBIGUOUS_PATTERNS = [
    # YYYY-MM-DD (ISO 8601)
    (r"(\d{4})-(\d{1,2})-(\d{1,2})", "ymd"),
    # DD-Mon-YYYY or DD Mon YYYY (e.g. 14-Jan-2026, 14 Jan 2026)
    (r"(\d{1,2})[\s\-]+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\-,]+(\d{4})", "dmy_named"),
    # Mon DD, YYYY (e.g. Jan 14, 2026)
    (r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\-]+(\d{1,2})[\s\-,]+(\d{4})", "mdy_named"),
    # YYYY/MM/DD
    (r"(\d{4})/(\d{1,2})/(\d{1,2})", "ymd_slash"),
]

# Ambiguous pattern: DD/MM/YYYY or MM/DD/YYYY — cannot distinguish
_AMBIGUOUS_PATTERN = re.compile(
    r"(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})"
)

_MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def extract_report_date(raw_text: str) -> dict:
    """Extract report date from text with confidence level.

    Args:
        raw_text: Concatenated text from all pages.

    Returns:
        {
            "report_date": str|None (ISO 8601 date),
            "report_date_confidence": "HIGH"|"LOW"|None
        }
    """
    # Search for each date label in priority order
    for label in _DATE_LABELS:
        # Find the label followed by some text on the same or next line
        pattern = re.compile(
            re.escape(label) + r"[\s:;\-]*(.{5,30})",
            re.IGNORECASE,
        )
        match = pattern.search(raw_text)
        if match:
            date_region = match.group(1).strip()
            result = _try_parse_date(date_region)
            if result is not None:
                return result

    # No labeled date found — try scanning the full text for any date-like pattern
    # (but only return if unambiguous, since without a label we need higher certainty)
    result = _try_parse_date(raw_text)
    if result is not None and result["report_date_confidence"] == "HIGH":
        return result

    # Check if there's an ambiguous date anywhere (even without label)
    if _AMBIGUOUS_PATTERN.search(raw_text):
        return {"report_date": None, "report_date_confidence": "LOW"}

    # Nothing found at all
    return {"report_date": None, "report_date_confidence": None}


def _try_parse_date(text: str) -> Optional[dict]:
    """Try to parse a date from text, returning confidence-tagged result."""

    # Try unambiguous patterns first
    for pattern_str, fmt_type in _UNAMBIGUOUS_PATTERNS:
        match = re.search(pattern_str, text, re.IGNORECASE)
        if match:
            try:
                date = _parse_match(match, fmt_type)
                if date and _is_plausible_date(date):
                    return {
                        "report_date": date.strftime("%Y-%m-%d"),
                        "report_date_confidence": "HIGH",
                    }
            except (ValueError, KeyError):
                continue

    # Check for ambiguous numeric date
    match = _AMBIGUOUS_PATTERN.search(text)
    if match:
        part1, part2 = int(match.group(1)), int(match.group(2))
        year = int(match.group(3))

        # If one part > 12, format is unambiguous
        if part1 > 12 and part2 <= 12:
            # Must be DD/MM/YYYY
            try:
                date = datetime(year, part2, part1)
                if _is_plausible_date(date):
                    return {
                        "report_date": date.strftime("%Y-%m-%d"),
                        "report_date_confidence": "HIGH",
                    }
            except ValueError:
                pass
        elif part2 > 12 and part1 <= 12:
            # Must be MM/DD/YYYY
            try:
                date = datetime(year, part1, part2)
                if _is_plausible_date(date):
                    return {
                        "report_date": date.strftime("%Y-%m-%d"),
                        "report_date_confidence": "HIGH",
                    }
            except ValueError:
                pass
        else:
            # Truly ambiguous — both parts ≤ 12, both interpretations valid
            return {"report_date": None, "report_date_confidence": "LOW"}

    return None


def _parse_match(match: re.Match, fmt_type: str) -> Optional[datetime]:
    """Convert a regex match to a datetime based on the format type."""
    if fmt_type == "ymd":
        return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    elif fmt_type == "ymd_slash":
        return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    elif fmt_type == "dmy_named":
        month = _MONTH_MAP[match.group(2).lower()[:3]]
        return datetime(int(match.group(3)), month, int(match.group(1)))
    elif fmt_type == "mdy_named":
        month = _MONTH_MAP[match.group(1).lower()[:3]]
        return datetime(int(match.group(3)), month, int(match.group(2)))
    return None


def _is_plausible_date(date: datetime) -> bool:
    """Check if a date is plausible (not in the far future or distant past)."""
    return 1900 <= date.year <= 2100
