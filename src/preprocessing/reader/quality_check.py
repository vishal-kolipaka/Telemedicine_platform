"""
Quality Check — standalone stateless function.

Implements the 4-check pipeline from Section 8:
1. Non-empty check
2. Character plausibility check (alphanumeric ratio)
3. Repeated-character check
4. Minimum structure check (at least one digit)

Stops at the first failing check. All thresholds come from ReaderConfig.
"""

import re

from src.preprocessing.reader.config import ReaderConfig


def run_quality_check(raw_pages: list[dict], config: ReaderConfig) -> dict:
    """Run quality checks on extracted pages.

    Args:
        raw_pages: List of page dicts, each containing at least 'raw_text'.
        config: ReaderConfig with threshold values.

    Returns:
        {"passed": True, "reason": None} if all checks pass, or
        {"passed": False, "reason": str} with the first failing reason.
    """
    # Concatenate text across all pages
    all_text = "\n".join(page.get("raw_text", "") for page in raw_pages)

    # ── Check 1: Non-empty ──────────────────────────────────────
    non_whitespace = all_text.replace(" ", "").replace("\t", "").replace("\n", "").replace("\r", "")
    if len(non_whitespace) < config.min_nonwhitespace_chars:
        return {"passed": False, "reason": "near-empty output"}

    # ── Check 2: Character plausibility (alphanumeric ratio) ────
    # Use non-whitespace total so layout spaces/formatting padding don't skew the ratio
    total_non_whitespace = len(non_whitespace)
    if total_non_whitespace > 0:
        alphanumeric_count = sum(1 for c in non_whitespace if c.isalnum())
        ratio = alphanumeric_count / total_non_whitespace
        if ratio < config.min_alphanumeric_ratio:
            return {
                "passed": False,
                "reason": "output dominated by non-alphanumeric characters, likely failed OCR",
            }

    # ── Check 3: Repeated-character run ─────────────────────────
    # Scan for any single non-divider character repeated N+ times consecutively.
    # Layout section dividers (---, ===, ___, ***, ~~~, ###, ...) are standard in text reports and excluded.
    pattern = re.compile(r"([^\s\-=\_\*\~\#\.\+])\1{" + str(config.max_repeated_char_run - 1) + r",}")
    if pattern.search(all_text):
        return {
            "passed": False,
            "reason": "long run of repeated characters detected, likely OCR failure",
        }

    # ── Check 4: Minimum structure (at least one digit) ─────────
    if not re.search(r"\d", all_text):
        return {
            "passed": False,
            "reason": "no numeric content found, extraction likely failed",
        }

    # All checks passed
    return {"passed": True, "reason": None}
