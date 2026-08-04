# BUILD PROMPT — Feature Mapper Module (v2)

**Read this entire document before writing any code. This is the highest-stakes module in the preprocessing unit. Every instruction here is a hard requirement.**

*v2 changes from v1: split candidate extraction, validation, and derived-feature computation into their own interfaces; defined context_score concretely; moved confidence weights and per-field conflict thresholds into config/schema instead of hardcoding; separated ocr_confidence from mapping_confidence; replaced language-dependent `prompt_to_user` with a `message_code`; added `canonical_value`/`canonical_unit` naming, `mapping_engine_version`, `reader_operation_id`, `confidence_breakdown`, `source_priority`; added structured logging and a privacy section; and — importantly — REMOVED `resolution`/`resolved_value` from the Mapper's own output, since that field genuinely contradicted the "Mapper never resolves conflicts" boundary this document itself declares. That data now belongs to a separate Conflict Resolver output, referenced but not owned here.*

---

## 1. Module Contract

- **Inputs:** the Document Reader's output (Contract 1 shape, including its `operation_id` for traceability), the patient's `existing_state` (a Contract 2 object from prior uploads this session), `feature_schema.json`, and a `MapperConfig` object.
- **Outputs:** an updated Contract 2 object — per-model status, resolved values with full provenance, missing fields, flagged-for-reconfirm items, and a conflict log (candidates only, no resolution — see Section 11).
- **Responsibilities:** extract candidate observations; match candidates to schema fields; detect/convert units; validate; compute derived features; record full provenance; **detect** (never resolve) multi-document conflicts; merge new document results into existing session state.
- **Non-responsibilities:** does NOT decide conflict resolution policy (separate Conflict Resolver component, entirely out of scope here — this module's conflict_log must never contain a "winner"). Does NOT read files. Does NOT run predictions. Does NOT generate user-facing text/wording (returns `message_code`s, not sentences — see Section 13).
- **Dependencies:** `feature_schema.json`, an LLM API client (only if enabled), `re`.
- **Failure modes:** ambiguous match, unconvertible unit, malformed LLM response, invalid user value, cross-document conflict, malformed schema.
- **Guarantees:** stateless, thread-safe, deterministic given identical inputs+config (LLM path is the one inherent exception), never invents a value, **never resolves a conflict itself.**

---

## 2. Design Principles (Mandatory)

1. **Single Responsibility** — candidate extraction, matching, unit conversion, range validation, derived-feature computation, and conflict *detection* are separate components. None do each other's job.
2. **Open/Closed** — new implementations of any interface below must be addable without modifying the orchestrator or sibling components.
3. **Dependency Inversion** — the orchestrator depends only on abstract interfaces (Sections 5-9), never concrete implementations directly.
4. **No policy ownership, no wording ownership** — the Mapper detects but never resolves conflicts, and returns codes but never user-facing sentences.
5. **Stateless** — `existing_state` in, updated state out, no hidden memory between calls.

---

## 3. Exception hierarchy (unchanged from v1)

```python
class MappingError(Exception): pass
class AmbiguousMatchError(MappingError): pass
class UnitConversionError(MappingError): pass
class InvalidUserValueError(MappingError): pass
class SchemaMismatchError(MappingError): pass  # only this one should ever propagate unhandled
```

---

## 4. MapperConfig — now includes confidence weights (previously hardcoded)

```python
class MapperConfig:
    confidence_threshold_accept: float = 0.90
    confidence_threshold_llm_trigger: float = 0.70
    regex_window_chars: int = 40
    enable_llm_fallback: bool = True
    llm_temperature: float = 0.0
    llm_max_retries: int = 1

    # Confidence formula weights -- tunable without touching code (Section 8)
    weight_alias_quality: float = 0.30
    weight_distance: float = 0.25
    weight_unit_match: float = 0.20
    weight_ambiguity: float = 0.15
    weight_context: float = 0.10

    # Default source priority when a conflict must be broken by "which source wins" as a
    # separate axis from date-based resolution (Section 14) -- most-trusted last:
    source_priority_order: list = ["derived", "report_extraction", "user_form", "user_reconfirm"]
```

**Note on conflict thresholds:** the per-field relative-difference threshold (e.g. HbA1c changing by 10% is clinically significant, Weight changing by 1% is not) now lives in `feature_schema.json` per field as `conflict_relative_threshold`, NOT as a single global number in this config — different biomarkers genuinely need different tolerances. See Section 11.

---

## 5. Candidate Extraction — now its own interface, separate from matching

```python
from dataclasses import dataclass

@dataclass
class Candidate:
    label_text: str
    value_text: str
    unit_text: str | None
    page_index: int
    context_type: str    # "table_header" | "lab_report_section" | "generic_paragraph" | "unstructured"
    source_line: str     # the raw line/row this came from, for debugging

class CandidateExtractor(ABC):
    @abstractmethod
    def extract(self, reader_output: dict) -> list[Candidate]:
        """Pulls raw (label, value, unit) observations from Contract 1's raw_text/tables,
        with NO knowledge of feature_schema.json -- this stage doesn't decide what anything means,
        just what's observably present in the text/tables."""
        ...
```

Pipeline is now: `Reader output -> CandidateExtractor -> MatchingEngine -> ValidationEngine -> DerivedFeatureEngine -> Merger`.

---

## 6. Matching Engine — unchanged interface, now consumes `Candidate` objects

```python
@dataclass
class MappedFeature:
    field_name: str
    matched_candidate: Candidate
    mapping_method: str          # "regex_rule_match" | "llm_fallback"
    mapping_confidence: float
    confidence_breakdown: dict   # {"alias": 0.30, "distance": 0.8, "unit": 1.0, "ambiguity": 0.9, "context": 1.0} -- raw component scores before weighting, for debugging (per external review request)

class MatchingEngine(ABC):
    @abstractmethod
    def match(self, candidates: list[Candidate], field_schema: dict) -> MappedFeature | None:
        ...
```

Concrete implementations: `RegexMatchingEngine` (Section 7), `LLMFallbackMatchingEngine` (Section 8) — both constructor-injected into the orchestrator, never instantiated internally.

---

## 7. Regex Matching Engine — layered algorithm (unchanged sequence from v1)

1. Exact alias match (case-insensitive, word-boundary-safe).
2. Same-line search for value+unit.
3. Bounded window search (`config.regex_window_chars`) or next line.
4. Extract candidate value + unit.
5. Ambiguity check (multiple plausible numbers nearby → penalize, don't guess).
6. Compute confidence (Section 9).
7. `>= confidence_threshold_accept` → accept. `< confidence_threshold_llm_trigger` → LLM fallback if enabled, else unresolved. Between the two → still send to LLM for confirmation.

---

## 8. LLM Fallback Matching Engine — unchanged requirements from v1, plus privacy section

- Return ONLY valid JSON, no markdown/explanation.
- Provide only the relevant field schema + relevant text slice — never the full document or full patient identifiers.
- **Privacy (new, explicit):** before sending any text to the LLM, redact/strip patient name and any obvious direct identifiers (not just "avoid sending unnecessary" as a vague guideline — actually run a redaction step, e.g. regex-strip anything matching a "Patient: <name>" pattern, before constructing the prompt). Provenance (document_id, page_index) is kept for audit but never sent to the LLM itself — the LLM only sees the minimal text needed to resolve the one field in question.
- Instruct: "If the value is not present, return null. Never invent or guess."
- `temperature = 0`, retry once on invalid JSON, then degrade to unresolved (not a crash).
- Resolved fields get `mapping_method = "llm_fallback"`, generally lower confidence than an equivalent regex match.

---

## 9. Confidence scoring — weights from config, context_score now concretely defined

```python
confidence = (
    config.weight_alias_quality * alias_quality
  + config.weight_distance      * distance_score
  + config.weight_unit_match    * unit_score
  + config.weight_ambiguity     * (1 - ambiguity_penalty)
  + config.weight_context       * context_score
)
```

**`context_score` — previously vague, now concrete (per external review):** based on the `Candidate.context_type` field set during candidate extraction (Section 5):
- `1.0` — matched inside a table with a recognizable header row (e.g. "Test | Result | Unit").
- `0.8` — matched within a clearly lab-report-structured section (labeled fields, consistent formatting).
- `0.5` — matched in a generic paragraph of prose.
- `0.2` — matched in what looks like an unrelated/random sentence with no report-like structure nearby.

`confidence_breakdown` (Section 6) stores each raw component score (`alias_quality`, `distance_score`, `unit_score`, `1 - ambiguity_penalty`, `context_score`) alongside the final weighted result, so a developer can see exactly which factor drove a low score, rather than only seeing one opaque number.

---

## 10. Validation Engine — now its own interface, split by concern

```python
class Validator(ABC):
    @abstractmethod
    def validate(self, field_name: str, value, schema_entry: dict) -> dict:
        """Returns {"valid": bool, "reason": str | None}"""
        ...

class RangeValidator(Validator):
    """Checks value against schema's valid_range (plausibility range, not clinical reference range)."""

class UnitValidator(Validator):
    """Confirms the detected/converted unit matches one of schema's accepted_input_units."""

class TypeValidator(Validator):
    """Confirms the value's Python type matches schema's declared type (float/int/boolean/categorical)."""
```

**Why split from a single validation step:** the schema will likely grow age-specific, gender-specific, or condition-specific range rules later (e.g. pediatric ranges, pregnancy-adjusted ranges). Splitting validators now means adding `AgeAdjustedRangeValidator` later doesn't require touching `UnitValidator` or `TypeValidator` at all.

---

## 11. Derived Feature Engine — now its own interface, separate from the Mapper's core matching logic

```python
class DerivedFeatureCalculator(ABC):
    @abstractmethod
    def compute(self, resolved_values: dict, schema_entry: dict) -> float | None:
        """Returns the computed value, or None if required source fields aren't yet resolved."""
        ...

class BMICalculator(DerivedFeatureCalculator):
    """BMI = Weight_kg / (Height_cm/100)^2, rounded per schema's rounding policy."""
```

**Why separate now:** BMI is the only derived feature today, but this project will very plausibly add Waist-to-Hip Ratio, HOMA-IR, eGFR, FIB-4, APRI, or a composite Metabolic Syndrome Score later. None of that is "matching" logic — keeping it in its own engine means adding a new derived feature later means adding a new `DerivedFeatureCalculator` subclass, not touching the Matching Engine at all.

---

## 12. Multi-document conflict handling — DETECTION ONLY, thresholds now per-field via schema

```python
def detect_conflict(new_value: MappedFeature, existing_value: dict, field_schema: dict) -> dict | None:
    """
    field_schema['conflict_relative_threshold'] -- per-field, from feature_schema.json, NOT a global
    config number, since different biomarkers need different tolerances (e.g. HbA1c changing 10%
    is clinically significant; Weight changing 1% is not).
    Returns a conflict_log entry (BOTH candidates, no winner picked) if the relative difference
    exceeds that field's threshold, else None.
    """
```

**This function NEVER returns a "resolved_value" or "winner."** That is the Conflict Resolver's job — a separate component, out of scope for this build, that consumes `conflict_log` afterward. If you find yourself writing code here that picks between two conflicting values, stop — that logic does not belong in this module.

---

## 13. Output shape — Contract 2, corrected naming and separated concerns

```python
{
  "canonical_value": 81.6,               # renamed from "value"/"converted_value" -- these were redundant; this IS the usable, schema-unit value
  "canonical_unit": "kg",                # NEW -- the schema's target unit this value is now expressed in (previously missing -- "81.6" alone doesn't tell you kg vs lbs)
  "original_value": "180",
  "original_unit": "lbs",
  "source": "report_extraction",          # "report_extraction" | "user_form" | "derived" | "user_reconfirm"
  "mapping_method": "regex_rule_match",   # "regex_rule_match" | "llm_fallback" | "user" | "derived"
  "mapping_engine_version": "RegexMatchingEngine 1.0",  # NEW -- so a future Regex v2 / ClinicalBERT swap doesn't make old results ambiguous to interpret
  "mapping_confidence": 0.91,
  "confidence_breakdown": {"alias": 1.0, "distance": 0.8, "unit": 1.0, "ambiguity": 0.9, "context": 0.8},  # NEW
  "ocr_confidence": null,                 # NEW -- SEPARATE from mapping_confidence. If this value came from an OCR'd page, this is that page's average_page_confidence from Contract 1. Conflating OCR uncertainty with matching uncertainty made it impossible to tell "was this wrong because OCR misread it, or because matching picked the wrong candidate?"
  "document_id": "doc_7f3a1c",
  "reader_operation_id": "op_a1b2c3",      # NEW -- traces back to the exact Reader run that produced this, for full Reader-to-Mapper-to-Model auditability
  "page_index": 0,
  "matched_alias": "HbA1c",
  "validation_status": "VALID",
  "extracted_at": "2026-07-29T10:16:02Z"
}
```

**For `flagged_for_reconfirm` entries, `prompt_to_user` is REMOVED and replaced with `message_code`:**

```python
{
  "field": "ALT",
  "canonical_value": 340,
  "original_value": "340",
  "original_unit": "U/L",
  "valid_range": [5, 300],
  "message_code": "OUT_OF_RANGE",    # matches error_codes.json's existing code -- the UI layer generates the actual sentence in whatever language/channel it needs (web, mobile, voice), NOT this contract. Contracts must stay language- and presentation-independent.
  "validation_status": "INVALID"
}
```

---

## 14. Source priority (new — for when a user answer and a report value disagree)

`MapperConfig.source_priority_order` (Section 4) defines the default trust order when the SAME field has values from different sources within the SAME session (not the cross-document date-based conflict handling in Section 12 — this is specifically "user typed something different than what a report said"): `derived < report_extraction < user_form < user_reconfirm`. A `user_reconfirm` (the person explicitly correcting a flagged value) always wins over an automatically extracted one. This is a default policy setting, not hardcoded logic — it lives in config so it can be overridden later without code changes.

---

## 15. Structured logging (mirrors the Reader)

```python
{
  "operation_id": "op_9f2e01",
  "timestamp": "2026-07-29T10:16:02.500Z",
  "level": "INFO",
  "module": "RegexMatchingEngine",
  "message": "matched HbA1c via alias 'HbA1c', confidence 0.97, mapping_method=regex_rule_match"
}
```
Log at minimum: every candidate extraction summary, every match attempt (success/fail/fallback-triggered), every unit conversion applied, every derived feature computed, every conflict detected.

---

## 16. Entry-point functions (unchanged signatures from v1)

```python
def map_features(reader_output: dict, existing_state: dict, schema: dict, config: MapperConfig) -> dict: ...
def apply_user_answer(field_name: str, value, current_state: dict, schema: dict, source: str = "user_form") -> dict: ...
```

---

## 17. Performance note (new)

For schemas with many fields and long documents (this project's current 38 fields is modest, but this should still be built correctly): avoid re-scanning the full raw text once per field naively. Build a lightweight index/single pass over the text (e.g. tokenize once, or build a position index of all recognized alias keywords in one scan) that `CandidateExtractor` uses, rather than each field independently re-searching the entire text from scratch. This becomes important if the schema grows significantly later.

---

## 18. Testing requirements — 28 tests (26 from v1 + 2 new)

All 26 tests from the original spec, PLUS:

27. `context_score` correctly assigns 1.0 for a table-header match vs 0.2 for a random-sentence match (verify the concrete scoring rule from Section 9, not just "some score changes").
28. Conflict detection uses the FIELD's own `conflict_relative_threshold` from schema (e.g. HbA1c's tighter threshold correctly flags a conflict that Weight's looser threshold would NOT flag for an equivalent percentage difference) -- confirms thresholds are genuinely per-field, not a leftover global number.

**Also explicitly verify:** no test or example anywhere produces a "resolved_value" or "winner" from this module — if any test asserts on a resolution outcome rather than a conflict_log entry, that test is wrong and indicates the module has taken on a responsibility it shouldn't have.

---

## 19. Definition of done

All items from v1, plus:
- [ ] `CandidateExtractor`, `MatchingEngine`, `ValidationEngine` (3 validators), and `DerivedFeatureEngine` are 4 genuinely separate interfaces/components, not folded together.
- [ ] `context_score` follows the concrete 1.0/0.8/0.5/0.2 rule in Section 9, not an ad-hoc number.
- [ ] Confidence weights and per-field conflict thresholds are read from `MapperConfig`/schema respectively — nothing hardcoded.
- [ ] Output uses `canonical_value`/`canonical_unit` naming (not the old redundant `value`/`converted_value`).
- [ ] `ocr_confidence` and `mapping_confidence` are stored as separate, independent fields.
- [ ] `message_code` is used instead of any hardcoded user-facing sentence anywhere in this module's output.
- [ ] **No output anywhere in this module contains a conflict "resolution" or "winner"** — conflict_log entries are candidates only.
- [ ] All 28 tests in Section 18 pass.

Do not consider this module finished until every checkbox is genuinely true.
