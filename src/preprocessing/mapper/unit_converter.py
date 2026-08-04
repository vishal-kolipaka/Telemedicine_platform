"""
Unit conversion for the Feature Mapper.

All conversion formulas come from feature_schema.json's field-level
unit_note entries.  This module detects what unit a value arrived in
and converts it to the schema's canonical unit.

Supported conversions:
  Weight:        lbs → kg
  Height:        ft_in → cm, m → cm
  Waist:         in → cm
  Glucose:       mmol/L → mg/dL  (×18.0)
  Cholesterol:   mmol/L → mg/dL  (×38.67)  [LDL, HDL]
  Triglycerides: mmol/L → mg/dL  (×88.57)
  HbA1c:         mmol/mol → %    ((÷10.929) + 2.15)
"""

from __future__ import annotations

import re
import math

from src.preprocessing.mapper.exceptions import UnitConversionError


# ── Conversion factors ──────────────────────────────────────────

_LBS_TO_KG = 1.0 / 2.20462
_IN_TO_CM = 2.54
_M_TO_CM = 100.0

# Glucose (Fasting_Blood_Glucose, Average_Glucose)
_GLUCOSE_MMOL_TO_MGDL = 18.0

# Cholesterol (LDL, HDL)
_CHOLESTEROL_MMOL_TO_MGDL = 38.67

# Triglycerides
_TRIGLYCERIDES_MMOL_TO_MGDL = 88.57

# HbA1c IFCC → NGSP
_HBA1C_DIVISOR = 10.929
_HBA1C_OFFSET = 2.15


# ── Feet/inches parser ─────────────────────────────────────────

# Matches patterns like: 5'10", 5'10, 5 ft 10 in, 5ft10in, 5'10"
_FT_IN_PATTERN = re.compile(
    r"""
    (\d+)             # feet
    \s*[''′ft.]+\s*   # separator (quote, ft, etc.)
    (\d+\.?\d*)       # inches
    \s*[""″in.]*      # optional trailing (quote, in, etc.)
    """,
    re.VERBOSE,
)


def parse_feet_inches(text: str) -> float | None:
    """Parse a feet/inches string and return centimeters.

    Handles: 5'10", 5'10, 5 ft 10 in, etc.

    Returns:
        Height in cm, or None if parsing fails.
    """
    match = _FT_IN_PATTERN.search(text)
    if match:
        feet = int(match.group(1))
        inches = float(match.group(2))
        total_inches = feet * 12 + inches
        return total_inches * _IN_TO_CM
    return None


# ── Unit detection ──────────────────────────────────────────────

# Map of detected unit text → normalized unit key.
# Lowercase matching.
_UNIT_ALIASES: dict[str, str] = {
    # Weight
    "kg": "kg",
    "kgs": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    "lb": "lbs",
    "lbs": "lbs",
    "pound": "lbs",
    "pounds": "lbs",
    # Height
    "cm": "cm",
    "cms": "cm",
    "centimeter": "cm",
    "centimeters": "cm",
    "m": "m",
    "meter": "m",
    "meters": "m",
    "in": "in",
    "inch": "in",
    "inches": "in",
    # Pressure
    "mmhg": "mmHg",
    "mm hg": "mmHg",
    "mm of hg": "mmHg",
    # Glucose / Cholesterol / Triglycerides
    "mg/dl": "mg/dL",
    "mg%": "mg/dL",
    "mmol/l": "mmol/L",
    "mmol/l": "mmol/L",
    # HbA1c
    "%": "%",
    "percent": "%",
    "mmol/mol": "mmol/mol",
    # Liver enzymes
    "u/l": "U/L",
    "iu/l": "U/L",
    # Wearable
    "steps/day": "steps/day",
    "steps": "steps/day",
    "minutes/day": "minutes/day",
    "min/day": "minutes/day",
    "minutes": "minutes/day",
    "bpm": "bpm",
    "hours": "hours",
    "hrs": "hours",
    "kcal/day": "kcal/day",
    "kcal": "kcal/day",
    "% cv": "% CV",
    # Gut
    "relative abundance %": "relative abundance %",
    "% relative abundance": "relative abundance %",
    "rel abundance %": "relative abundance %",
    "index": "index",
    # Generic
    "years": "years",
    "kg/m2": "kg/m2",
}


def detect_unit(unit_text: str | None) -> str | None:
    """Normalize a raw unit text string to a canonical unit key.

    Args:
        unit_text: The unit string as extracted (may be messy).

    Returns:
        Normalized unit key, or None if unrecognized.
    """
    if not unit_text:
        return None
    # Clean leading/trailing spaces, digits, and divider characters like "=", "-", "_"
    cleaned = re.sub(r"^\d+\s*", "", unit_text.strip())
    cleaned = re.sub(r"[\s=\-_*]+$", "", cleaned).strip().lower()
    res = _UNIT_ALIASES.get(cleaned)
    if res:
        return res

    # Fallback: search for known unit substrings (handles lab codes like "mg/dL EN", "g/dL EEN")
    for key, norm in _UNIT_ALIASES.items():
        if key != "m" and key != "in" and key != "cm" and key != "%": # Avoid overly short accidental matches
            if key in cleaned:
                return norm
    if "mg/dl" in cleaned:
        return "mg/dL"
    elif "mmol/l" in cleaned:
        return "mmol/L"
    elif "g/dl" in cleaned:
        return "g/dL"
    elif "u/l" in cleaned or "iu/l" in cleaned:
        return "U/L"
    elif "mmhg" in cleaned or "mm hg" in cleaned:
        return "mmHg"
    elif "kg" in cleaned:
        return "kg"
    elif "cm" in cleaned:
        return "cm"
    elif "%" in cleaned:
        return "%"
    return None


# ── Conversion dispatch ────────────────────────────────────────

# Keyed by (from_unit, to_unit) → conversion function.
# Each function takes a float value and returns the converted float.
_CONVERSIONS: dict[tuple[str, str], callable] = {
    ("lbs", "kg"): lambda v: v * _LBS_TO_KG,
    ("m", "cm"): lambda v: v * _M_TO_CM,
    ("in", "cm"): lambda v: v * _IN_TO_CM,
    # Glucose
    ("mmol/L", "mg/dL"): lambda v: v * _GLUCOSE_MMOL_TO_MGDL,
    # HbA1c
    ("mmol/mol", "%"): lambda v: (v / _HBA1C_DIVISOR) + _HBA1C_OFFSET,
    # Gut Relative Abundance
    ("%", "relative abundance %"): lambda v: v,
    ("% relative abundance", "relative abundance %"): lambda v: v,
    ("rel abundance %", "relative abundance %"): lambda v: v,
}


def get_conversion_func(
    from_unit: str,
    to_unit: str,
    field_name: str,
) -> callable | None:
    """Get the conversion function for a specific field + unit pair.

    Some unit pairs have field-specific multipliers (cholesterol vs
    glucose both use mmol/L → mg/dL but with different factors).

    Args:
        from_unit:  The detected input unit.
        to_unit:    The schema's canonical unit.
        field_name: The schema field name (for field-specific factors).

    Returns:
        A callable(float) → float, or None if no conversion needed
        (units already match).
    """
    if from_unit == to_unit:
        return None

    # Field-specific mmol/L → mg/dL conversions
    cholesterol_fields = {"LDL", "HDL", "LDL_Cholesterol", "HDL_Cholesterol"}
    triglyceride_fields = {"Triglycerides"}

    if from_unit == "mmol/L" and to_unit == "mg/dL":
        if field_name in cholesterol_fields:
            return lambda v: v * _CHOLESTEROL_MMOL_TO_MGDL
        elif field_name in triglyceride_fields:
            return lambda v: v * _TRIGLYCERIDES_MMOL_TO_MGDL
        else:
            # Default glucose conversion
            return _CONVERSIONS.get(("mmol/L", "mg/dL"))

    return _CONVERSIONS.get((from_unit, to_unit))


def convert_value(
    value: float,
    from_unit: str,
    to_unit: str,
    field_name: str,
) -> float:
    """Convert a value from one unit to another.

    Args:
        value:      The numeric value to convert.
        from_unit:  The detected input unit.
        to_unit:    The schema's canonical unit.
        field_name: The schema field name.

    Returns:
        The converted value.

    Raises:
        UnitConversionError: If no conversion rule exists for this
                             unit pair.
    """
    if from_unit == to_unit:
        return value
    if (from_unit, to_unit) in (("%", "% CV"), ("% CV", "%"), ("%", "relative abundance %"), ("relative abundance %", "%")):
        return value

    func = get_conversion_func(from_unit, to_unit, field_name)
    if func is None:
        raise UnitConversionError(
            f"No conversion rule from '{from_unit}' to '{to_unit}' "
            f"for field '{field_name}'."
        )
    return func(value)


def detect_and_convert(
    value_text: str,
    unit_text: str | None,
    field_name: str,
    schema_entry: dict,
) -> tuple[float, str, float | None, str | None]:
    """Detect unit, parse value, and convert to canonical unit.

    Handles the full pipeline: detect unit → parse numeric value →
    convert if needed.

    Args:
        value_text:   Raw value string from the document.
        unit_text:    Raw unit string (may be None).
        field_name:   Schema field name.
        schema_entry: Field's schema entry (has 'unit',
                      'accepted_input_units').

    Returns:
        Tuple of (canonical_value, canonical_unit,
                  original_value_float, detected_unit).

    Raises:
        UnitConversionError: If unit is detected but not convertible.
        ValueError: If value_text is not a valid number.
    """
    canonical_unit = schema_entry.get("unit", "")
    accepted_units = schema_entry.get("accepted_input_units", [canonical_unit])

    # Detect the input unit
    detected = detect_unit(unit_text)

    # Special case: feet/inches for height
    if field_name in ("Height", "Height_cm") and "ft_in" in accepted_units:
        # Try to parse feet/inches from the value_text itself
        ft_in_cm = parse_feet_inches(value_text)
        if ft_in_cm is not None:
            return ft_in_cm, canonical_unit, None, "ft_in"

    # Non-numeric types (categorical, boolean, string)
    field_type = schema_entry.get("type", "float")
    if field_type in ("categorical", "boolean", "string"):
        if field_type == "boolean":
            val_lower = str(value_text).strip().lower()
            b_val = False if val_lower in ("no", "false", "negative", "0", "-") else True
            return b_val, canonical_unit, b_val, detected
        return value_text.strip(), canonical_unit, value_text.strip(), detected

    # Parse numeric value
    # Strip common non-numeric chars (commas, spaces)
    cleaned_value = value_text.strip().replace(",", "")
    try:
        numeric_value = float(cleaned_value)
    except ValueError:
        raise ValueError(
            f"Cannot parse '{value_text}' as a number for field "
            f"'{field_name}'."
        )

    # If no unit detected, assume canonical unit
    if detected is None:
        return numeric_value, canonical_unit, numeric_value, None

    # Check if detected unit is accepted
    if detected not in accepted_units and detected != canonical_unit:
        raise UnitConversionError(
            f"Unit '{detected}' (from text '{unit_text}') is not in "
            f"accepted_input_units {accepted_units} for field "
            f"'{field_name}'."
        )

    # Convert if needed
    if detected != canonical_unit:
        converted = convert_value(
            numeric_value, detected, canonical_unit, field_name
        )
        return converted, canonical_unit, numeric_value, detected

    return numeric_value, canonical_unit, numeric_value, detected
