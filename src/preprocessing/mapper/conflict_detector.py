"""
Multi-document conflict detection — DETECTION ONLY (Section 12).

This function NEVER returns a "resolved_value" or "winner."
That is the Conflict Resolver's job — a separate component, entirely
out of scope for this module.

Thresholds are PER-FIELD via feature_schema.json's
'conflict_relative_threshold', NOT a single global number — different
biomarkers need different tolerances (e.g. HbA1c changing 10% is
clinically significant; Weight changing 1% is not).
"""

from __future__ import annotations


def detect_conflict(
    new_value: dict,
    existing_value: dict,
    field_name: str,
    field_schema: dict,
    default_threshold: float,
) -> dict | None:
    """Detect whether a new value conflicts with an existing value.

    Compares canonical_value using relative difference against the
    field's own conflict_relative_threshold.

    Args:
        new_value:         The newly extracted field value dict
                           (Contract 2 field_value_shape).
        existing_value:    The existing value dict from current state.
        field_name:        The schema field name.
        field_schema:      The field's schema entry (may contain
                           'conflict_relative_threshold').
        default_threshold: The schema-level default_conflict_relative_threshold
                           (fallback if the field doesn't override).

    Returns:
        A conflict_log entry dict (BOTH candidates, NO winner) if the
        relative difference exceeds the threshold, else None.

        The returned dict structure:
        {
            "field": str,
            "candidates": [
                {"canonical_value": ..., "document_id": ...,
                 "reader_operation_id": ..., "report_date": ...,
                 "extracted_at": ...},
                {"canonical_value": ..., ...}
            ],
            "field_conflict_relative_threshold_used": float,
            "note": "Both candidates retained for the Conflict Resolver."
        }
    """
    new_cv = new_value.get("canonical_value")
    existing_cv = existing_value.get("canonical_value")

    if new_cv is None or existing_cv is None:
        return None

    # Only compare numeric values
    try:
        new_num = float(new_cv)
        existing_num = float(existing_cv)
    except (TypeError, ValueError):
        # Non-numeric (categorical, boolean) — exact equality check
        if new_cv != existing_cv:
            threshold = field_schema.get(
                "conflict_relative_threshold", default_threshold
            )
            return _build_conflict_entry(
                field_name, new_value, existing_value, threshold
            )
        return None

    # Relative difference: |a - b| / max(|a|, |b|)
    # Guard against division by zero
    denominator = max(abs(new_num), abs(existing_num))
    if denominator == 0:
        return None

    relative_diff = abs(new_num - existing_num) / denominator

    threshold = field_schema.get(
        "conflict_relative_threshold", default_threshold
    )

    if relative_diff > threshold:
        return _build_conflict_entry(
            field_name, new_value, existing_value, threshold
        )

    return None


def _build_conflict_entry(
    field_name: str,
    new_value: dict,
    existing_value: dict,
    threshold_used: float,
) -> dict:
    """Build a conflict_log entry with BOTH candidates, NO winner.

    This is the exact shape from Contract 2's
    example_conflict_log_entry — candidates only.
    """
    return {
        "field": field_name,
        "candidates": [
            {
                "canonical_value": existing_value.get("canonical_value"),
                "document_id": existing_value.get("document_id"),
                "reader_operation_id": existing_value.get(
                    "reader_operation_id"
                ),
                "report_date": existing_value.get("report_date"),
                "extracted_at": existing_value.get("extracted_at"),
            },
            {
                "canonical_value": new_value.get("canonical_value"),
                "document_id": new_value.get("document_id"),
                "reader_operation_id": new_value.get("reader_operation_id"),
                "report_date": new_value.get("report_date"),
                "extracted_at": new_value.get("extracted_at"),
            },
        ],
        "field_conflict_relative_threshold_used": threshold_used,
        "note": (
            "Both candidates retained for the Conflict Resolver "
            "(a separate component, out of scope for this contract) "
            "to resolve later. This module does not and must not "
            "decide which one is correct."
        ),
    }
