"""
Core data models for the Feature Mapper pipeline.

Candidate  — a raw (label, value, unit) observation pulled from
             Contract 1's text/tables, with NO schema knowledge.
MappedFeature — a Candidate that has been matched to a schema field,
                with confidence and provenance attached.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Candidate:
    """A raw observation extracted from a document page.

    Created by CandidateExtractor (Section 5).  At this stage the
    pipeline doesn't know what schema field (if any) this belongs to —
    it only knows what's observably present in the text/tables.

    Attributes:
        label_text: The label/header text found near the value
                    (e.g. "HbA1c", "Weight", "BP").
        value_text: The raw value string (e.g. "6.1", "180", "128/82").
        unit_text:  The unit string if detected, else None
                    (e.g. "%", "lbs", "mmHg").
        page_index: Zero-based page index within the document.
        context_type: One of "table_header", "lab_report_section",
                      "generic_paragraph", "unstructured" — drives
                      context_score in confidence formula (Section 9).
        source_line: The raw line/row this came from, for debugging.
    """

    label_text: str
    value_text: str
    unit_text: str | None
    page_index: int
    context_type: str
    source_line: str


@dataclass
class MappedFeature:
    """A Candidate that has been matched to a specific schema field.

    Created by MatchingEngine (Section 6).  Carries confidence and
    provenance so downstream validators and the orchestrator can
    make accept/reject/fallback decisions.

    Attributes:
        field_name:           The schema field this matched to
                              (e.g. "HbA1c", "Weight_kg").
        matched_candidate:    The Candidate object that was matched.
        mapping_method:       How the match was made —
                              "regex_rule_match" | "llm_fallback".
        mapping_confidence:   Float 0-1, the weighted confidence score.
        confidence_breakdown: Dict of raw component scores before
                              weighting, for debugging:
                              {"alias": float, "distance": float,
                               "unit": float, "ambiguity": float,
                               "context": float}
    """

    field_name: str
    matched_candidate: Candidate
    mapping_method: str
    mapping_confidence: float
    confidence_breakdown: dict
