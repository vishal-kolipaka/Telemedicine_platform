"""
Confidence scoring for the Feature Mapper.

Implements the weighted formula from Section 9 of the spec.
All weights come from MapperConfig — nothing hardcoded.

context_score mapping (now concretely defined):
    1.0 — table_header (table with recognizable header row)
    0.8 — lab_report_section (labeled fields, consistent formatting)
    0.5 — generic_paragraph (prose text)
    0.2 — unstructured (no report-like structure nearby)
"""

from __future__ import annotations

from src.preprocessing.mapper.config import MapperConfig


# Concrete context_score values per Section 9.
_CONTEXT_SCORES: dict[str, float] = {
    "table_header": 1.0,
    "lab_report_section": 0.8,
    "generic_paragraph": 0.5,
    "unstructured": 0.2,
}


def get_context_score(context_type: str) -> float:
    """Return the context_score for a given context_type string.

    Falls back to 0.2 (unstructured) if the context_type is unknown.
    """
    return _CONTEXT_SCORES.get(context_type, 0.2)


def compute_confidence(
    alias_quality: float,
    distance_score: float,
    unit_score: float,
    ambiguity_penalty: float,
    context_type: str,
    config: MapperConfig,
) -> tuple[float, dict]:
    """Compute the weighted confidence score and breakdown.

    Args:
        alias_quality:    0-1, how well the alias matched
                          (1.0 = exact, lower = partial).
        distance_score:   0-1, proximity of value to alias
                          (1.0 = same cell/line, decays with distance).
        unit_score:       0-1, whether the detected unit matches
                          an accepted input unit (1.0 = match, 0.0 = no unit).
        ambiguity_penalty: 0-1, penalty for multiple plausible numbers
                           nearby (0.0 = no ambiguity, 1.0 = fully ambiguous).
        context_type:     Candidate.context_type string.
        config:           MapperConfig with weight values.

    Returns:
        Tuple of (final_confidence, breakdown_dict).
        breakdown_dict has the raw component scores for debugging.
    """
    ctx_score = get_context_score(context_type)
    amb_score = 1.0 - ambiguity_penalty

    confidence = (
        config.weight_alias_quality * alias_quality
        + config.weight_distance * distance_score
        + config.weight_unit_match * unit_score
        + config.weight_ambiguity * amb_score
        + config.weight_context * ctx_score
    )

    # Clamp to [0, 1]
    confidence = max(0.0, min(1.0, confidence))

    breakdown = {
        "alias": alias_quality,
        "distance": distance_score,
        "unit": unit_score,
        "ambiguity": amb_score,
        "context": ctx_score,
    }

    return confidence, breakdown
