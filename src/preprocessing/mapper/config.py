"""
Configuration object for the Feature Mapper module.

All thresholds, confidence weights, and policy settings live here —
nothing is hardcoded inline in logic code.  Mirrors the Reader's
ReaderConfig pattern (frozen dataclass, immutable once created).
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MapperConfig:
    """Immutable configuration for the Feature Mapper.

    Frozen dataclass ensures thread-safety — once created, config values
    cannot be accidentally mutated by any component or the orchestrator.
    """

    # ── Matching thresholds (Section 7) ──────────────────────────
    confidence_threshold_accept: float = 0.90
    confidence_threshold_llm_trigger: float = 0.70
    regex_window_chars: int = 40
    enable_llm_fallback: bool = True
    llm_temperature: float = 0.0
    llm_max_retries: int = 1

    # ── Confidence formula weights (Section 9) ───────────────────
    # Tunable without touching code — the formula reads these at runtime.
    weight_alias_quality: float = 0.30
    weight_distance: float = 0.25
    weight_unit_match: float = 0.20
    weight_ambiguity: float = 0.15
    weight_context: float = 0.10

    # ── Source priority (Section 14) ─────────────────────────────
    # Most-trusted LAST.  A user_reconfirm always wins over
    # an automatic extraction.  This is a configurable default,
    # not hardcoded logic — override in config to change policy
    # without code changes.
    source_priority_order: tuple = (
        "derived",
        "report_extraction",
        "user_form",
        "user_reconfirm",
    )
