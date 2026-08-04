"""
Derived Feature Engine — computed features separate from matching.

BMI is the only derived feature today, but this project will plausibly
add Waist-to-Hip Ratio, HOMA-IR, eGFR, FIB-4, APRI, or a composite
Metabolic Syndrome Score later.  Keeping derived features in their own
engine means adding a new one means adding a new DerivedFeatureCalculator
subclass, not touching the Matching Engine at all.
"""

from __future__ import annotations

import math
from decimal import Decimal, ROUND_HALF_UP

from src.preprocessing.mapper.interfaces import DerivedFeatureCalculator


class BMICalculator(DerivedFeatureCalculator):
    """BMI = Weight_kg / (Height_cm / 100)^2

    Rounding policy (from schema):
        Round to 1 decimal place using standard round-half-up.
        e.g. 25.849 → 25.8, 25.85 → 25.9

    This matches how the training CSV's BMI column was generated,
    preventing a systematic offset between training-time and
    inference-time BMI.
    """

    VERSION = "BMICalculator 1.0"

    def compute(
        self,
        resolved_values: dict,
        schema_entry: dict,
    ) -> float | None:
        """Compute BMI from Weight_kg and Height_cm.

        Args:
            resolved_values: Dict of field_name → canonical_value.
            schema_entry:    The BMI field's schema entry.

        Returns:
            BMI rounded to 1 decimal place, or None if required
            source fields aren't resolved.
        """
        weight = resolved_values.get("Weight") if resolved_values.get("Weight") is not None else resolved_values.get("Weight_kg")
        height = resolved_values.get("Height") if resolved_values.get("Height") is not None else resolved_values.get("Height_cm")

        if weight is None or height is None:
            return None

        if height <= 0:
            return None

        height_m = height / 100.0
        bmi_raw = weight / (height_m ** 2)

        # Round to 1 decimal using round-half-up (Decimal for precision)
        bmi_rounded = float(
            Decimal(str(bmi_raw)).quantize(
                Decimal("0.1"), rounding=ROUND_HALF_UP
            )
        )

        return bmi_rounded
