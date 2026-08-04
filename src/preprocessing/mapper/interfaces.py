"""
Abstract interfaces for the Feature Mapper pipeline.

The orchestrator depends ONLY on these interfaces (Dependency Inversion).
Concrete implementations are constructor-injected.  New implementations
can be added without modifying the orchestrator or sibling components
(Open/Closed).

Four interfaces, one per pipeline concern:
1. CandidateExtractor  — raw observation extraction
2. MatchingEngine      — schema field matching
3. Validator           — value validation
4. DerivedFeatureCalculator — computed features
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.preprocessing.mapper.models import Candidate, MappedFeature


class CandidateExtractor(ABC):
    """Extracts raw (label, value, unit) observations from Contract 1.

    Has NO knowledge of feature_schema.json — this stage doesn't
    decide what anything means, just what's observably present
    in the text/tables.
    """

    @abstractmethod
    def extract(self, reader_output: dict) -> list[Candidate]:
        """Pull raw candidates from Contract 1's raw_text/tables.

        Args:
            reader_output: A full Contract 1 output dict from the
                           Document Reader.

        Returns:
            A list of Candidate objects, one per observed
            (label, value, unit) triple.
        """
        ...


class MatchingEngine(ABC):
    """Matches Candidate objects to schema fields.

    Each implementation tries a different matching strategy
    (regex rules, LLM fallback, future ClinicalBERT, etc.).
    """

    @abstractmethod
    def match(
        self,
        candidates: list[Candidate],
        field_name: str,
        field_schema: dict,
    ) -> MappedFeature | None:
        """Attempt to match one of the candidates to the given field.

        Args:
            candidates:   All candidates extracted from the document.
            field_name:   The schema field to match (e.g. "HbA1c").
            field_schema: That field's entry from feature_schema.json.

        Returns:
            A MappedFeature if a confident match was found, else None.
        """
        ...


class Validator(ABC):
    """Validates a single aspect of a resolved field value.

    Separate implementations for range, unit, and type validation
    (Section 10).  Future validators (e.g. AgeAdjustedRangeValidator)
    can be added without touching existing ones.
    """

    @abstractmethod
    def validate(
        self,
        field_name: str,
        value,
        schema_entry: dict,
    ) -> dict:
        """Validate a value against a schema constraint.

        Args:
            field_name:   The schema field being validated.
            value:        The value to validate (already unit-converted).
            schema_entry: That field's full schema entry.

        Returns:
            {"valid": True, "reason": None}  on success, or
            {"valid": False, "reason": str}  on failure.
        """
        ...


class DerivedFeatureCalculator(ABC):
    """Computes a derived feature from other resolved values.

    Each subclass handles one derived feature (BMI today,
    HOMA-IR / eGFR / FIB-4 / etc. later).
    """

    @abstractmethod
    def compute(
        self,
        resolved_values: dict,
        schema_entry: dict,
    ) -> float | None:
        """Compute the derived value.

        Args:
            resolved_values: Dict of field_name -> canonical_value
                             for all currently resolved fields.
            schema_entry:    The derived field's schema entry
                             (contains derive_formula, rounding, etc.).

        Returns:
            The computed value, or None if required source fields
            aren't yet resolved.
        """
        ...
