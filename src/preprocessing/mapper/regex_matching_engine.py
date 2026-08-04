"""
Regex Matching Engine — the primary matching strategy (Sections 6-7).

Layered algorithm:
  1. For each schema field, check each candidate's label_text against aliases
  2. Exact alias match (case-insensitive, word-boundary-safe)
  3. Same-line value+unit extraction
  4. Bounded window search (config.regex_window_chars) or next line
  5. Ambiguity check (multiple plausible numbers → penalize)
  6. Compute confidence (Section 9)
  7. Accept/reject/LLM-fallback based on thresholds

Special-case: Fasting_Blood_Glucose requires the alias text to
explicitly contain "fasting" — otherwise the match is refused
(FASTING_STATUS_UNCONFIRMED).
"""

from __future__ import annotations

import re

from src.preprocessing.mapper.interfaces import MatchingEngine
from src.preprocessing.mapper.models import Candidate, MappedFeature
from src.preprocessing.mapper.config import MapperConfig
from src.preprocessing.mapper.confidence import compute_confidence
def _normalize_ocr_label(text: str) -> str:
    """Normalize common OCR character confusion typos."""
    s = text.lower().strip()
    s = s.replace("trlglycerldes", "triglycerides")
    s = s.replace("trlglycerides", "triglycerides")
    s = s.replace("ch0lesterol", "cholesterol")
    s = s.replace("fastlng", "fasting")
    s = s.replace("glucosc", "glucose")
    s = s.replace("pressurc", "pressure")
    s = s.replace("clrcumference", "circumference")
    s = s.replace("helght", "height")
    s = s.replace("welght", "weight")
    s = s.replace("gcnder", "gender")
    s = s.replace("agc", "age")
    s = s.replace("walst", "waist")
    s = s.replace("dally", "daily")
    s = s.replace("actlve", "active")
    s = s.replace("mlnutes", "minutes")
    s = s.replace("tlme", "time")
    s = s.replace("restlng", "resting")
    s = s.replace("haemolobin", "haemoglobin")
    s = s.replace("haemolobln", "haemoglobin")
    s = s.replace("hemolobin", "hemoglobin")
    s = s.replace("hemolobln", "hemoglobin")
    return s


class RegexMatchingEngine(MatchingEngine):
    """Concrete MatchingEngine using regex-based alias matching.

    Constructor-injected with MapperConfig — never reads global state.
    """

    VERSION = "RegexMatchingEngine 1.0"

    def __init__(self, config: MapperConfig) -> None:
        self._config = config

    def match(
        self,
        candidates: list[Candidate],
        field_name: str,
        field_schema: dict,
    ) -> MappedFeature | None:
        """Try to match one of the candidates to the given schema field.

        Returns the best MappedFeature if one passes the confidence
        threshold, else None (caller may try LLM fallback).
        """
        aliases = field_schema.get("aliases", [])
        default_aliases = [
            field_name,
            field_name.lower(),
            field_name.lower().replace("_", " "),
            field_name.lower().replace("_", ""),
        ]
        all_aliases = list(dict.fromkeys(aliases + default_aliases))

        best_match: MappedFeature | None = None
        best_confidence = -1.0

        for candidate in candidates:
            result = self._try_match_candidate(
                candidate, field_name, field_schema, all_aliases
            )
            if result is not None and result.mapping_confidence > best_confidence:
                best_confidence = result.mapping_confidence
                best_match = result

        if best_match is None:
            return None

        # Apply threshold decision
        if best_confidence >= self._config.confidence_threshold_accept:
            return best_match
        elif best_confidence >= self._config.confidence_threshold_llm_trigger:
            # Between the two thresholds — still return but mark for
            # possible LLM confirmation.  The orchestrator decides
            # whether to invoke LLM fallback.
            return best_match
        else:
            # Below LLM trigger threshold — too uncertain
            return None

    def _try_match_candidate(
        self,
        candidate: Candidate,
        field_name: str,
        field_schema: dict,
        aliases: list[str],
    ) -> MappedFeature | None:
        """Attempt to match a single candidate against a field's aliases."""

        label_lower = candidate.label_text.lower().strip()
        cleaned_label = re.sub(r"[\(_](cm|kg|mmHg|mg_dL|mg/dL|g/dL|U/L|mmol/L|%|in|lbs|steps/day|kcal/day|hours|bpm)[_\)]?$", "", label_lower, flags=re.IGNORECASE).strip()
        cleaned_label_spaces = cleaned_label.replace("_", " ")

        norm_label = _normalize_ocr_label(label_lower)
        norm_cleaned_spaces = _normalize_ocr_label(cleaned_label_spaces)

        # Reject ratio/derived ratio candidates for single analyte fields (e.g. "LDL/ HDL CHOLESTEROL" for "LDL")
        if ("/" in candidate.label_text or "ratio" in label_lower) and field_name in ("LDL", "HDL", "Total_Cholesterol", "Cholesterol", "Triglycerides", "Fasting_Blood_Glucose", "HbA1c", "ALT", "AST"):
            return None

        # Filter out invalid values for categorical/boolean fields
        if field_schema.get("type") in ("categorical", "boolean"):
            val_norm = candidate.value_text.lower().strip()
            cats = [c.lower() for c in field_schema.get("categories", [])] + ["m", "f", "yes", "no", "true", "false", "1", "0", "positive", "negative"]
            if field_schema.get("encoding"):
                cats += [k.lower() for k in field_schema.get("encoding").keys()]
            if val_norm not in cats:
                return None

        # ── Step 1: Alias matching ──────────────────────────────
        alias_quality = 0.0
        matched_alias = None

        for alias in aliases:
            alias_lower = alias.lower().strip()

            # Exact match (case-insensitive)
            if label_lower in (alias_lower, alias_lower.replace("_", " ")) or cleaned_label in (alias_lower, alias_lower.replace("_", " ")) or cleaned_label_spaces == alias_lower:
                alias_quality = 1.0
                matched_alias = alias
                break

            # OCR normalized match
            if norm_label in (alias_lower, alias_lower.replace("_", " ")) or norm_cleaned_spaces == alias_lower:
                alias_quality = 0.95
                matched_alias = alias
                break

            # Word-boundary-safe substring match
            pattern = re.compile(
                r"\b" + re.escape(alias_lower) + r"\b", re.IGNORECASE
            )
            if pattern.search(label_lower) or pattern.search(norm_label) or pattern.search(cleaned_label_spaces):
                alias_quality = 0.85
                matched_alias = alias
                # Don't break — keep looking for an exact match

        if matched_alias is None:
            return None

        # ── Fasting glucose special rule ────────────────────────
        if field_name == "Fasting_Blood_Glucose":
            fasting_note = field_schema.get("fasting_status_note", "")
            if fasting_note:
                norm_label = _normalize_ocr_label(candidate.label_text)
                is_fasting = (
                    "fasting" in candidate.label_text.lower()
                    or "fasting" in norm_label
                    or candidate.label_text.lower().strip() in ("fbs", "fpg")
                    or norm_label in ("fbs", "fpg")
                    or "fasting" in candidate.source_line.lower()
                )
                if not is_fasting:
                    # Do NOT auto-accept — this is a non-fasting glucose
                    return None

        # ── Step 2: Value presence ──────────────────────────────
        if not candidate.value_text or not candidate.value_text.strip():
            return None

        # ── Step 3: Distance score ──────────────────────────────
        # For our current extraction model, candidates already have
        # value co-located with label (same cell or same line).
        # Distance is primarily about how the candidate was extracted.
        distance_score = 1.0  # Same-line / same-cell extraction

        # ── Step 4: Unit score ──────────────────────────────────
        unit_score = self._compute_unit_score(candidate, field_schema)

        # ── Step 5: Ambiguity check ─────────────────────────────
        ambiguity_penalty = self._compute_ambiguity(candidate)

        # ── Step 6: Compute confidence ──────────────────────────
        confidence, breakdown = compute_confidence(
            alias_quality=alias_quality,
            distance_score=distance_score,
            unit_score=unit_score,
            ambiguity_penalty=ambiguity_penalty,
            context_type=candidate.context_type,
            config=self._config,
        )

        return MappedFeature(
            field_name=field_name,
            matched_candidate=candidate,
            mapping_method="regex_rule_match",
            mapping_confidence=confidence,
            confidence_breakdown=breakdown,
        )

    @staticmethod
    def _compute_unit_score(
        candidate: Candidate,
        field_schema: dict,
    ) -> float:
        """Score how well the candidate's unit matches expectations.

        1.0 = unit explicitly present and matches an accepted unit
        0.5 = no unit detected (acceptable — assume canonical)
        0.0 = unit present but doesn't match
        """
        if not candidate.unit_text:
            return 0.5

        from src.preprocessing.mapper.unit_converter import detect_unit

        detected = detect_unit(candidate.unit_text)
        canonical_unit = field_schema.get("unit", "")
        canonical_norm = (detect_unit(canonical_unit) or canonical_unit.lower()).strip()

        accepted = field_schema.get(
            "accepted_input_units", [canonical_unit]
        )
        accepted_norm = [
            (detect_unit(u) or u.lower()).strip() for u in accepted
        ]

        unit_str_raw = candidate.unit_text.lower().strip()

        if detected:
            if detected == canonical_norm or detected in accepted_norm:
                return 1.0
        else:
            if unit_str_raw == canonical_norm or unit_str_raw in accepted_norm or any(u in unit_str_raw for u in accepted_norm):
                return 1.0

        return 0.0

    @staticmethod
    def _compute_ambiguity(candidate: Candidate) -> float:
        """Compute ambiguity penalty based on the source line.

        Multiple plausible numbers in the same source line → higher
        penalty.  Single number → no penalty.
        """
        # Count distinct numbers in the source line
        numbers = re.findall(r"\b\d+\.?\d*\b", candidate.source_line)
        # Exclude the candidate's own value from the count
        other_numbers = [
            n for n in numbers if n != candidate.value_text
        ]

        if len(other_numbers) == 0:
            return 0.0
        elif len(other_numbers) == 1:
            return 0.1  # One other number — slight penalty
        elif len(other_numbers) == 2:
            return 0.3  # Two other numbers — moderate
        else:
            return 0.5  # Many numbers — significant ambiguity
