"""
FeatureMapper — Orchestrator for the Feature Mapper module (Section 16).

Pipeline:  CandidateExtractor → MatchingEngine → UnitConverter
           → Validators → DerivedFeatureEngine → ConflictDetector → Merge

Design principles enforced:
  - Depends only on abstract interfaces (Dependency Inversion)
  - All engines are constructor-injected, never instantiated internally
  - Stateless — existing_state in, updated state out, no hidden memory
  - Thread-safe — no shared mutable state
  - Deterministic — same input+config = same output (LLM path excepted)
  - Never invents a value
  - Never resolves a conflict itself

Entry-point functions (Section 16):
  map_features()     — process a Reader output against the schema
  apply_user_answer() — integrate a user-provided value
"""

from __future__ import annotations

import copy
import re
import uuid
from datetime import datetime, timezone

from src.preprocessing.mapper.config import MapperConfig
from src.preprocessing.mapper.models import Candidate, MappedFeature
from src.preprocessing.mapper.interfaces import (
    CandidateExtractor,
    MatchingEngine,
    Validator,
    DerivedFeatureCalculator,
)
from src.preprocessing.mapper.unit_converter import (
    detect_and_convert,
    detect_unit,
    parse_feet_inches,
)
from src.preprocessing.mapper.conflict_detector import detect_conflict
from src.preprocessing.mapper.exceptions import (
    MappingError,
    UnitConversionError,
    SchemaMismatchError,
)


class FeatureMapper:
    """Orchestrator that wires together all mapper components.

    Constructor-injected with concrete implementations of every
    interface.  Never instantiates components internally.
    """

    def __init__(
        self,
        candidate_extractor: CandidateExtractor,
        regex_engine: MatchingEngine,
        llm_engine: MatchingEngine | None,
        validators: list[Validator],
        derived_calculators: dict[str, DerivedFeatureCalculator],
        config: MapperConfig,
    ) -> None:
        self._extractor = candidate_extractor
        self._regex_engine = regex_engine
        self._llm_engine = llm_engine
        self._validators = validators
        self._derived_calculators = derived_calculators
        self._config = config

    # ────────────────────────────────────────────────────────────
    # PUBLIC API
    # ────────────────────────────────────────────────────────────

    def map_features(
        self,
        reader_output: dict,
        existing_state: dict,
        schema: dict,
        config: MapperConfig | None = None,
    ) -> dict:
        """Process a Document Reader output and produce Contract 2.

        Args:
            reader_output:  Contract 1 output from the Document Reader.
            existing_state: Current Contract 2 state (may be empty for
                            first document).
            schema:         feature_schema.json contents.
            config:         Optional override config (uses constructor
                            config if None).

        Returns:
            Updated Contract 2 dict with per-model status, values,
            missing_fields, flagged_for_reconfirm, and conflict_log.
        """
        cfg = config or self._config
        operation_id = f"op_{uuid.uuid4().hex[:8]}"
        mapper_log: list[dict] = []

        def log(level: str, module: str, message: str) -> None:
            mapper_log.append({
                "operation_id": operation_id,
                "timestamp": datetime.now(timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%S.%f"
                )[:-3] + "Z",
                "level": level,
                "module": module,
                "message": message,
            })

        # Validate schema structure
        self._validate_schema(schema)

        # Deep-copy existing state so we don't mutate the input
        state = copy.deepcopy(existing_state) if existing_state else {}

        # Extract reader provenance
        document_id = reader_output.get("document_id")
        reader_op_id = self._get_reader_operation_id(reader_output)
        report_date = reader_output.get("report_date")

        # ── Stage 1: Candidate Extraction ───────────────────────
        candidates = self._extractor.extract(reader_output)
        log(
            "INFO",
            "FeatureMapper",
            f"extracted {len(candidates)} candidates from document "
            f"{document_id}",
        )

        # ── Stage 2-5: Per-model processing ─────────────────────
        default_threshold = schema.get(
            "default_conflict_relative_threshold", 0.20
        )
        shared_features = schema.get("shared_features", {})

        for model_name in ("clinical", "wearable", "gut"):
            model_schema = schema.get(model_name)
            if model_schema is None:
                continue

            # Initialize model state if needed
            if model_name not in state:
                state[model_name] = {
                    "status": "not_available",
                    "values": {},
                    "missing_fields": [],
                    "flagged_for_reconfirm": [],
                    "conflict_log": [],
                }

            model_state = state[model_name]
            features = model_schema.get("features", {})
            column_order = model_schema.get("column_order", [])

            # Merge shared features into the feature set for matching
            all_features = {}
            for fname in column_order:
                if fname in shared_features:
                    all_features[fname] = shared_features[fname]
                elif fname in features:
                    all_features[fname] = features[fname]

            # ── Match each field ────────────────────────────────
            for field_name, field_schema in all_features.items():
                source = field_schema.get("source", "report_extraction")

                # Skip system_generated fields (e.g. derived BMI)
                if source == "system_generated":
                    continue

                # Skip already-resolved fields (unless conflict check)
                existing_val = model_state["values"].get(field_name)

                # Try regex match
                matched = self._regex_engine.match(
                    candidates, field_name, field_schema
                )

                # Try LLM fallback if regex didn't clear accept threshold
                if matched is not None and self._config.enable_llm_fallback:
                    if (matched.mapping_confidence
                            < cfg.confidence_threshold_accept
                            and self._llm_engine is not None):
                        llm_result = self._llm_engine.match(
                            candidates, field_name, field_schema
                        )
                        if llm_result is not None:
                            matched = llm_result
                            log(
                                "INFO",
                                "FeatureMapper",
                                f"LLM fallback used for {field_name}",
                            )
                elif matched is None and self._config.enable_llm_fallback:
                    if self._llm_engine is not None:
                        matched = self._llm_engine.match(
                            candidates, field_name, field_schema
                        )
                        if matched is not None:
                            log(
                                "INFO",
                                "FeatureMapper",
                                f"LLM fallback resolved {field_name}",
                            )

                if matched is None:
                    log(
                        "INFO",
                        "FeatureMapper",
                        f"no match found for {field_name}",
                    )
                    continue

                log(
                    "INFO",
                    matched.mapping_method.replace("_", " ").title(),
                    f"matched {field_name} via alias "
                    f"'{matched.matched_candidate.label_text}', "
                    f"confidence {matched.mapping_confidence:.2f}, "
                    f"mapping_method={matched.mapping_method}",
                )

                # ── Unit conversion ─────────────────────────────
                try:
                    (
                        canonical_value,
                        canonical_unit,
                        original_value_num,
                        detected_unit,
                    ) = detect_and_convert(
                        matched.matched_candidate.value_text,
                        matched.matched_candidate.unit_text,
                        field_name,
                        field_schema,
                    )
                except (UnitConversionError, ValueError) as exc:
                    log(
                        "WARNING",
                        "FeatureMapper",
                        f"unit conversion failed for {field_name}: {exc}",
                    )
                    continue

                if detected_unit is not None:
                    log(
                        "INFO",
                        "UnitConverter",
                        f"converted {field_name}: "
                        f"{matched.matched_candidate.value_text} "
                        f"{detected_unit} → {canonical_value} "
                        f"{canonical_unit}",
                    )

                # ── Type coercion ───────────────────────────────
                canonical_value = self._coerce_type(
                    canonical_value, field_schema
                )

                # ── Validation ──────────────────────────────────
                validation_failed = False
                fail_reason = None
                fail_message_code = None

                for validator in self._validators:
                    # RangeValidator and TypeValidator get the value;
                    # UnitValidator gets the unit
                    from src.preprocessing.mapper.validators import (
                        UnitValidator,
                    )
                    if isinstance(validator, UnitValidator):
                        result = validator.validate(
                            field_name, detected_unit, field_schema
                        )
                    else:
                        result = validator.validate(
                            field_name, canonical_value, field_schema
                        )

                    if not result["valid"]:
                        validation_failed = True
                        fail_reason = result["reason"]
                        # Determine message_code
                        from src.preprocessing.mapper.validators import (
                            RangeValidator,
                            TypeValidator,
                        )
                        if isinstance(validator, RangeValidator):
                            fail_message_code = "OUT_OF_RANGE"
                        elif isinstance(validator, TypeValidator):
                            fail_message_code = "TYPE_MISMATCH"
                        elif isinstance(validator, UnitValidator):
                            fail_message_code = "INVALID_UNIT"
                        break

                # Get OCR confidence for this page (pass-through)
                ocr_confidence = self._get_ocr_confidence(
                    reader_output,
                    matched.matched_candidate.page_index,
                )

                now_ts = datetime.now(timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                )

                if validation_failed:
                    # Add to flagged_for_reconfirm
                    flag_entry = {
                        "field": field_name,
                        "canonical_value": canonical_value,
                        "original_value": matched.matched_candidate.value_text,
                        "original_unit": (
                            matched.matched_candidate.unit_text
                        ),
                        "valid_range": field_schema.get("valid_range"),
                        "message_code": fail_message_code,
                        "validation_status": "INVALID",
                    }
                    # Remove existing flag for same field if any
                    model_state["flagged_for_reconfirm"] = [
                        f for f in model_state["flagged_for_reconfirm"]
                        if f["field"] != field_name
                    ]
                    model_state["flagged_for_reconfirm"].append(flag_entry)
                    log(
                        "WARNING",
                        "FeatureMapper",
                        f"{field_name} flagged: {fail_message_code} — "
                        f"{fail_reason}",
                    )
                    continue

                # ── Build field value entry (Contract 2 shape) ──
                new_value = {
                    "canonical_value": canonical_value,
                    "canonical_unit": field_schema.get("unit", ""),
                    "source": "report_extraction",
                    "validation_status": "VALID",
                    "original_value": (
                        matched.matched_candidate.value_text
                    ),
                    "original_unit": (
                        matched.matched_candidate.unit_text
                    ),
                    "mapping_method": matched.mapping_method,
                    "mapping_engine_version": self._get_engine_version(
                        matched.mapping_method
                    ),
                    "mapping_confidence": matched.mapping_confidence,
                    "confidence_breakdown": matched.confidence_breakdown,
                    "ocr_confidence": ocr_confidence,
                    "document_id": document_id,
                    "reader_operation_id": reader_op_id,
                    "page_index": matched.matched_candidate.page_index,
                    "matched_alias": (
                        matched.matched_candidate.label_text
                    ),
                    "extracted_at": now_ts,
                    "report_date": report_date,
                }

                # ── Conflict detection ──────────────────────────
                if existing_val is not None:
                    # Check for source priority first (Section 14)
                    existing_source = existing_val.get("source", "")
                    new_source = new_value["source"]
                    existing_priority = self._get_source_priority(
                        existing_source, cfg
                    )
                    new_priority = self._get_source_priority(
                        new_source, cfg
                    )

                    if existing_source != new_source:
                        # Same field, different sources — apply priority
                        if new_priority > existing_priority:
                            log(
                                "INFO",
                                "FeatureMapper",
                                f"source priority override for "
                                f"{field_name}: {new_source} "
                                f"(priority {new_priority}) overwrites "
                                f"{existing_source} "
                                f"(priority {existing_priority}). "
                                f"Previous value: "
                                f"{existing_val.get('canonical_value')}, "
                                f"New value: {canonical_value}",
                            )
                            model_state["values"][field_name] = new_value
                        else:
                            log(
                                "INFO",
                                "FeatureMapper",
                                f"source priority kept existing for "
                                f"{field_name}: {existing_source} "
                                f"(priority {existing_priority}) over "
                                f"{new_source} "
                                f"(priority {new_priority})",
                            )
                        continue

                    # Same source, different documents → conflict check
                    conflict = detect_conflict(
                        new_value,
                        existing_val,
                        field_name,
                        field_schema,
                        default_threshold,
                    )
                    if conflict is not None:
                        model_state["conflict_log"].append(conflict)
                        log(
                            "WARNING",
                            "ConflictDetector",
                            f"conflict detected for {field_name}: "
                            f"existing={existing_val.get('canonical_value')}"
                            f", new={canonical_value}",
                        )
                        # Do NOT overwrite — both candidates in log,
                        # no resolution
                        continue

                # Store the value
                model_state["values"][field_name] = new_value

            # ── Derived features ────────────────────────────────
            resolved_vals = {
                fname: v["canonical_value"]
                for fname, v in model_state["values"].items()
                if v.get("validation_status") in (
                    "VALID", "USER_ENTERED", "DERIVED"
                )
            }

            for field_name, calculator in self._derived_calculators.items():
                if field_name not in all_features:
                    continue
                field_schema_d = all_features[field_name]

                # Only compute if the field isn't already resolved
                # with a report-extracted value
                if field_name in model_state["values"]:
                    existing_src = model_state["values"][field_name].get(
                        "source"
                    )
                    if existing_src == "report_extraction":
                        continue

                derivable_from = field_schema_d.get("derivable_from", [])
                if not all(f in resolved_vals for f in derivable_from):
                    continue

                computed = calculator.compute(resolved_vals, field_schema_d)
                if computed is not None:
                    now_ts = datetime.now(timezone.utc).strftime(
                        "%Y-%m-%dT%H:%M:%SZ"
                    )
                    model_state["values"][field_name] = {
                        "canonical_value": computed,
                        "canonical_unit": field_schema_d.get("unit", ""),
                        "source": "derived",
                        "validation_status": "DERIVED",
                        "original_value": None,
                        "original_unit": None,
                        "mapping_method": "derived",
                        "mapping_engine_version": getattr(
                            calculator, "VERSION", "unknown"
                        ),
                        "mapping_confidence": 1.0,
                        "confidence_breakdown": None,
                        "ocr_confidence": None,
                        "document_id": None,
                        "reader_operation_id": None,
                        "page_index": None,
                        "matched_alias": None,
                        "extracted_at": now_ts,
                        "report_date": None,
                    }
                    log(
                        "INFO",
                        "DerivedFeatureEngine",
                        f"computed {field_name} = {computed}",
                    )

            # ── Compute missing fields ──────────────────────────
            missing = []
            for field_name in column_order:
                if field_name in model_state["values"]:
                    continue
                # Check if it's flagged for reconfirm
                flagged_fields = {
                    f["field"]
                    for f in model_state["flagged_for_reconfirm"]
                }
                if field_name in flagged_fields:
                    continue
                # Get the field schema to check source
                f_schema = all_features.get(field_name)
                if f_schema and f_schema.get("source") == "system_generated":
                    continue
                missing.append(field_name)

            model_state["missing_fields"] = missing

            # ── Compute model status ────────────────────────────
            if not missing and not model_state["flagged_for_reconfirm"]:
                model_state["status"] = "complete"
            elif model_state["values"]:
                model_state["status"] = "incomplete"
            else:
                model_state["status"] = "not_available"

        # ── Stage 6: patient_info (UI metadata — not a domain) ───
        # patient_info is populated after all domain passes are done.
        # It shares Age/Gender from the clinical domain values so there
        # is exactly ONE extraction path for those shared fields.
        # It never produces a status, missing_fields, or conflict_log.
        patient_info_schema = schema.get("patient_info")
        if patient_info_schema is not None:
            if "patient_info" not in state:
                state["patient_info"] = {}
            pi = state["patient_info"]

            # ── Name: extract directly from candidates via aliases ──
            if "Name" not in pi:
                name_field = patient_info_schema.get("fields", {}).get("Name", {})
                name_aliases = [
                    a.lower() for a in name_field.get("aliases", [])
                ]
                for cand in candidates:
                    label_lower = cand.label_text.strip().lower()
                    if label_lower in name_aliases:
                        raw_name = cand.value_text.strip()
                        # Reject pure-numeric values (Patient ID leak etc.)
                        if raw_name and not re.match(r"^[\d\s\-]+$", raw_name):
                            pi["Name"] = raw_name
                            log(
                                "INFO",
                                "FeatureMapper",
                                f"patient_info.Name extracted: '{raw_name}'",
                            )
                            break

            # ── Age / Gender: mirror from clinical domain values ──
            # We intentionally do NOT re-run the extraction pipeline.
            # The clinical domain already resolved these from the same
            # candidates; we simply read from there.
            clinical_vals = state.get("clinical", {}).get("values", {})
            for shared_field in ("Age", "Gender"):
                if shared_field not in pi and shared_field in clinical_vals:
                    pi[shared_field] = clinical_vals[shared_field].get(
                        "canonical_value"
                    )

        # Attach mapper log to state
        state["_mapper_log"] = state.get("_mapper_log", []) + mapper_log

        return state

    def apply_user_answer(
        self,
        field_name: str,
        value,
        current_state: dict,
        schema: dict,
        source: str = "user_form",
    ) -> dict:
        """Integrate a user-provided value into the current state.

        Args:
            field_name: The schema field being answered.
            value:      The user's value.
            current_state: Current Contract 2 state.
            schema:     feature_schema.json contents.
            source:     "user_form" | "user_reconfirm".

        Returns:
            Updated Contract 2 state.
        """
        state = copy.deepcopy(current_state)
        shared = schema.get("shared_features", {})

        now_ts = datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

        for model_name in ("clinical", "wearable", "gut"):
            model_schema = schema.get(model_name)
            if model_schema is None:
                continue

            if model_name not in state:
                continue

            model_state = state[model_name]
            features = model_schema.get("features", {})
            column_order = model_schema.get("column_order", [])

            if field_name not in column_order:
                continue

            # Find the field schema
            field_schema = features.get(
                field_name, shared.get(field_name)
            )
            if field_schema is None:
                continue

            # Handle encoding for categorical/boolean fields
            canonical_value = value
            canonical_unit = field_schema.get("unit", "")

            # Type coercion on the RAW value first (e.g. "Male" →
            # matched against categories) BEFORE encoding to numeric.
            canonical_value = self._coerce_type(
                canonical_value, field_schema
            )

            # Validate the raw/coerced value BEFORE encoding —
            # e.g. "Male" should pass categorical validation,
            # not the encoded integer 1.
            for validator in self._validators:
                from src.preprocessing.mapper.validators import UnitValidator
                if isinstance(validator, UnitValidator):
                    continue  # No unit for user-entered values

                result = validator.validate(
                    field_name, canonical_value, field_schema
                )
                if not result["valid"]:
                    # For user_reconfirm, accept anyway (user is
                    # explicitly overriding)
                    if source == "user_reconfirm":
                        break
                    raise MappingError(
                        f"User value for '{field_name}' failed "
                        f"validation: {result['reason']}"
                    )

            # Now apply encoding (e.g. Male→1, Female→0, Yes→1, No→0)
            encoding = field_schema.get("encoding")
            if encoding and str(canonical_value) in encoding:
                canonical_value = encoding[str(canonical_value)]

            # Check source priority — user answers may override
            existing_val = model_state["values"].get(field_name)
            if existing_val is not None:
                existing_source = existing_val.get("source", "")
                new_priority = self._get_source_priority(
                    source, self._config
                )
                existing_priority = self._get_source_priority(
                    existing_source, self._config
                )
                if new_priority < existing_priority:
                    # Existing value has higher priority — don't overwrite
                    continue

            # Build value entry
            validation_status = "USER_ENTERED"
            model_state["values"][field_name] = {
                "canonical_value": canonical_value,
                "canonical_unit": canonical_unit,
                "source": source,
                "validation_status": validation_status,
                "original_value": str(value),
                "original_unit": None,
                "mapping_method": "user",
                "mapping_engine_version": "user_input",
                "mapping_confidence": 1.0,
                "confidence_breakdown": None,
                "ocr_confidence": None,
                "document_id": None,
                "reader_operation_id": None,
                "page_index": None,
                "matched_alias": None,
                "extracted_at": now_ts,
                "report_date": None,
            }

            # Remove from flagged_for_reconfirm if present
            model_state["flagged_for_reconfirm"] = [
                f for f in model_state["flagged_for_reconfirm"]
                if f["field"] != field_name
            ]

            # Recompute missing fields
            all_features = {}
            for fname in column_order:
                if fname in shared:
                    all_features[fname] = shared[fname]
                elif fname in features:
                    all_features[fname] = features[fname]

            missing = []
            for fname in column_order:
                if fname in model_state["values"]:
                    continue
                flagged = {
                    f["field"]
                    for f in model_state["flagged_for_reconfirm"]
                }
                if fname in flagged:
                    continue
                f_sch = all_features.get(fname)
                if f_sch and f_sch.get("source") == "system_generated":
                    continue
                missing.append(fname)

            model_state["missing_fields"] = missing

            # Recompute status
            if (not missing
                    and not model_state["flagged_for_reconfirm"]):
                model_state["status"] = "complete"
            elif model_state["values"]:
                model_state["status"] = "incomplete"

        # ── patient_info: allow user to supply Name directly ──
        # Age/Gender in patient_info are always mirrored from the clinical
        # domain (map_features does this); they are not accepted here as
        # user-entered values to avoid two independent update paths.
        patient_info_schema = schema.get("patient_info")
        if patient_info_schema is not None and field_name == "Name":
            if "patient_info" not in state:
                state["patient_info"] = {}
            state["patient_info"]["Name"] = str(value).strip()

        return state

    # ────────────────────────────────────────────────────────────
    # PRIVATE HELPERS
    # ────────────────────────────────────────────────────────────

    @staticmethod
    def _validate_schema(schema: dict) -> None:
        """Validate basic schema structure."""
        if not isinstance(schema, dict):
            raise SchemaMismatchError(
                "Schema must be a dict."
            )
        # At minimum, one model section must exist
        if not any(
            k in schema for k in ("clinical", "wearable", "gut")
        ):
            raise SchemaMismatchError(
                "Schema must contain at least one model section "
                "(clinical, wearable, or gut)."
            )

    @staticmethod
    def _get_reader_operation_id(reader_output: dict) -> str | None:
        """Extract the Reader's operation_id from its extraction_log."""
        log_entries = reader_output.get("extraction_log", [])
        if log_entries:
            return log_entries[0].get("operation_id")
        return None

    @staticmethod
    def _get_ocr_confidence(
        reader_output: dict,
        page_index: int,
    ) -> float | None:
        """Get OCR confidence for a specific page (pass-through)."""
        pages = reader_output.get("pages", [])
        for page in pages:
            if page.get("page_index") == page_index:
                return page.get("average_page_confidence")
        return None

    def _get_engine_version(self, mapping_method: str) -> str:
        """Get the version string for a mapping method."""
        if mapping_method == "regex_rule_match":
            return getattr(
                self._regex_engine, "VERSION", "RegexMatchingEngine 1.0"
            )
        elif mapping_method == "llm_fallback":
            if self._llm_engine is not None:
                return getattr(
                    self._llm_engine, "VERSION",
                    "LLMFallbackMatchingEngine 1.0",
                )
            return "LLMFallbackMatchingEngine 1.0 (stub)"
        return "unknown"

    @staticmethod
    def _get_source_priority(source: str, config: MapperConfig) -> int:
        """Get the priority index for a source type.

        Higher index = higher trust.  Returns -1 for unknown sources.
        """
        try:
            return list(config.source_priority_order).index(source)
        except ValueError:
            return -1

    @staticmethod
    def _coerce_type(value, field_schema: dict):
        """Coerce a value to the schema's declared type."""
        declared_type = field_schema.get("type", "float")

        if declared_type == "integer":
            try:
                return int(float(value))
            except (TypeError, ValueError):
                return value

        elif declared_type == "float":
            try:
                return float(value)
            except (TypeError, ValueError):
                return value

        elif declared_type == "categorical":
            categories = field_schema.get("categories", [])
            str_val = str(value).strip()
            # Case-insensitive category matching
            for cat in categories:
                if str_val.lower() == cat.lower():
                    return cat
            # Shorthand matching (e.g. 'm' -> 'Male', 'f' -> 'Female')
            if str_val.lower() in ("m", "male"):
                return "Male"
            elif str_val.lower() in ("f", "female"):
                return "Female"
            return str_val

        elif declared_type == "boolean":
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return bool(value)
            str_val = str(value).strip().lower()
            if str_val in ("yes", "true", "1"):
                return True
            elif str_val in ("no", "false", "0"):
                return False
            return value

        return value
