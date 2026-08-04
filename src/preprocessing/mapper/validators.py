"""
Validation Engine — three separate validators per Section 10.

Each validator checks one concern and returns
{"valid": bool, "reason": str | None}.

Split by concern so adding future validators (e.g.
AgeAdjustedRangeValidator) doesn't require touching existing ones.
"""

from __future__ import annotations

from src.preprocessing.mapper.interfaces import Validator


class RangeValidator(Validator):
    """Checks value against the schema's valid_range.

    This is a PLAUSIBILITY range (catches OCR misreads and extraction
    errors), NOT a clinical reference/normal range.  Real extreme-but-true
    values exist (e.g. ALT genuinely reaching 800+ U/L in acute
    hepatitis) — ranges are set wide to allow those through.
    """

    def validate(
        self,
        field_name: str,
        value,
        schema_entry: dict,
    ) -> dict:
        valid_range = schema_entry.get("valid_range")
        if valid_range is None:
            # No range defined → passes by default
            return {"valid": True, "reason": None}

        lo, hi = valid_range
        if not (lo <= value <= hi):
            return {
                "valid": False,
                "reason": (
                    f"Value {value} for '{field_name}' is outside "
                    f"valid_range [{lo}, {hi}]."
                ),
            }
        return {"valid": True, "reason": None}


class UnitValidator(Validator):
    """Confirms the detected/converted unit matches one of the schema's
    accepted_input_units.

    This runs AFTER unit detection but BEFORE conversion — it ensures
    we actually have a conversion path for whatever unit was found.
    """

    def validate(
        self,
        field_name: str,
        value,
        schema_entry: dict,
    ) -> dict:
        # 'value' here is expected to be the detected_unit string,
        # not the numeric value.  The orchestrator passes the unit.
        detected_unit = value
        if detected_unit is None:
            # No unit detected — acceptable for fields without
            # accepted_input_units (e.g. boolean, index)
            if "accepted_input_units" not in schema_entry:
                return {"valid": True, "reason": None}
            # For fields that expect units, no unit is still valid
            # (we assume canonical unit)
            return {"valid": True, "reason": None}

        accepted = schema_entry.get("accepted_input_units", [])
        canonical = schema_entry.get("unit", "")

        if not accepted:
            # No accepted_input_units defined — only canonical is valid
            if detected_unit != canonical:
                return {
                    "valid": False,
                    "reason": (
                        f"Unit '{detected_unit}' is not the canonical "
                        f"unit '{canonical}' for '{field_name}', and no "
                        f"accepted_input_units are defined."
                    ),
                }
            return {"valid": True, "reason": None}

        if detected_unit not in accepted and detected_unit != canonical:
            return {
                "valid": False,
                "reason": (
                    f"Unit '{detected_unit}' for '{field_name}' is not "
                    f"in accepted_input_units {accepted}."
                ),
            }
        return {"valid": True, "reason": None}


class TypeValidator(Validator):
    """Confirms the value's Python type matches the schema's declared type.

    Schema types → Python types:
        "float"       → int or float
        "integer"     → int
        "boolean"     → bool (or int 0/1)
        "categorical" → str matching one of schema's 'categories'
    """

    def validate(
        self,
        field_name: str,
        value,
        schema_entry: dict,
    ) -> dict:
        declared_type = schema_entry.get("type", "float")

        if declared_type == "float":
            if not isinstance(value, (int, float)):
                return {
                    "valid": False,
                    "reason": (
                        f"Value {value!r} for '{field_name}' is not "
                        f"numeric (expected float, got {type(value).__name__})."
                    ),
                }

        elif declared_type == "integer":
            if not isinstance(value, int) or isinstance(value, bool):
                return {
                    "valid": False,
                    "reason": (
                        f"Value {value!r} for '{field_name}' is not an "
                        f"integer (got {type(value).__name__})."
                    ),
                }

        elif declared_type == "boolean":
            if not isinstance(value, (bool, int)):
                return {
                    "valid": False,
                    "reason": (
                        f"Value {value!r} for '{field_name}' is not "
                        f"boolean (got {type(value).__name__})."
                    ),
                }

        elif declared_type == "categorical":
            categories = schema_entry.get("categories", [])
            if str(value) not in categories:
                return {
                    "valid": False,
                    "reason": (
                        f"Value {value!r} for '{field_name}' is not one "
                        f"of the valid categories {categories}."
                    ),
                }

        return {"valid": True, "reason": None}
