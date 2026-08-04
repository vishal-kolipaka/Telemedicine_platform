"""
run_mapper.py — End-to-end pipeline: Reader → Mapper.

Usage:
    python run_mapper.py <file_path>
    python run_mapper.py                   (uses the sample test file)

This wires together the Document Reader and Feature Mapper,
runs them in sequence, and prints a human-readable summary
showing found/missing/flagged fields per model.
"""

import sys
import os
import json

# Force UTF-8 stdout encoding for Windows terminals
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.preprocessing.reader import DocumentReader, ReaderConfig
from src.preprocessing.reader.extractors.pdf_text_extractor import (
    PdfTextExtractor,
)
from src.preprocessing.reader.extractors.tesseract_ocr_extractor import (
    TesseractOCRExtractor,
)
from src.preprocessing.reader.extractors.pandas_structured_parser import (
    PandasStructuredParser,
)
from src.preprocessing.mapper import (
    FeatureMapper,
    MapperConfig,
    DefaultCandidateExtractor,
    RegexMatchingEngine,
    LLMFallbackMatchingEngine,
    RangeValidator,
    UnitValidator,
    TypeValidator,
    BMICalculator,
)


def load_schema():
    """Load the feature schema."""
    schema_path = os.path.join(
        os.path.dirname(__file__),
        "src", "preprocessing", "feature_schema.json",
    )
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_reader():
    """Build a fully-wired Document Reader."""
    config = ReaderConfig()
    return DocumentReader(
        pdf_extractor=PdfTextExtractor(),
        ocr_extractor=TesseractOCRExtractor(),
        structured_parser=PandasStructuredParser(),
        config=config,
    )


def build_mapper():
    """Build a fully-wired Feature Mapper."""
    config = MapperConfig()
    return FeatureMapper(
        candidate_extractor=DefaultCandidateExtractor(),
        regex_engine=RegexMatchingEngine(config),
        llm_engine=LLMFallbackMatchingEngine(config),
        validators=[RangeValidator(), UnitValidator(), TypeValidator()],
        derived_calculators={"BMI": BMICalculator()},
        config=config,
    )


def print_summary(mapper_output: dict):
    """Print a human-readable summary of the mapper output."""
    print("\n" + "=" * 70)
    print("  FEATURE MAPPER — RESULTS SUMMARY")
    print("=" * 70)

    for model_name in ("clinical", "wearable", "gut"):
        model = mapper_output.get(model_name)
        if model is None:
            continue

        status = model.get("status", "unknown")
        values = model.get("values", {})
        missing = model.get("missing_fields", [])
        flagged = model.get("flagged_for_reconfirm", [])
        conflicts = model.get("conflict_log", [])

        # Status indicator
        status_icon = {
            "complete": "✅",
            "incomplete": "🔶",
            "not_available": "⬜",
        }.get(status, "❓")

        print(f"\n{'─' * 70}")
        print(f"  {status_icon}  {model_name.upper()} MODEL — {status.upper()}")
        print(f"{'─' * 70}")

        # ── Found fields ────────────────────────────────────────
        if values:
            print(f"\n  ✅ FOUND ({len(values)} fields):")
            for field_name, val in values.items():
                cv = val.get("canonical_value")
                cu = val.get("canonical_unit", "")
                conf = val.get("mapping_confidence", 0)
                method = val.get("mapping_method", "")
                source = val.get("source", "")
                orig = val.get("original_value")
                orig_u = val.get("original_unit", "")
                vs = val.get("validation_status", "")

                # Format the line
                value_str = f"{cv} {cu}".strip()
                conf_bar = "█" * int(conf * 10) + "░" * (10 - int(conf * 10))

                line = f"     {field_name:<30s} = {value_str:<15s}"
                line += f" [{conf_bar}] {conf:.0%}"

                # Show conversion if unit changed
                if orig and orig_u and orig_u != cu:
                    line += f"  (was {orig} {orig_u})"

                # Show source
                if source == "derived":
                    line += "  [derived]"
                elif source == "user_form":
                    line += "  [user]"

                print(line)

        # ── Missing fields ──────────────────────────────────────
        if missing:
            print(f"\n  ❌ MISSING ({len(missing)} fields):")
            for field_name in missing:
                print(f"     {field_name}")

        # ── Flagged fields ──────────────────────────────────────
        if flagged:
            print(f"\n  ⚠️  FLAGGED FOR RECONFIRMATION ({len(flagged)}):")
            for entry in flagged:
                field = entry.get("field", "")
                cv = entry.get("canonical_value")
                vr = entry.get("valid_range", [])
                code = entry.get("message_code", "")
                print(
                    f"     {field:<30s} = {cv}  "
                    f"(valid range: {vr}, code: {code})"
                )

        # ── Conflicts ──────────────────────────────────────────
        if conflicts:
            print(f"\n  ⚡ CONFLICTS ({len(conflicts)}):")
            for entry in conflicts:
                field = entry.get("field", "")
                candidates = entry.get("candidates", [])
                vals = [str(c.get("canonical_value")) for c in candidates]
                print(f"     {field}: {' vs '.join(vals)}")

        if not values and not missing and not flagged:
            print("     (no data for this model)")

    print(f"\n{'=' * 70}\n")


def main():
    # Determine file to process
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        # Default to the sample test file
        file_path = os.path.join(
            os.path.dirname(__file__),
            "testing datas", "crt-1.txt",
        )

    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    print(f"\n📄 Processing: {os.path.basename(file_path)}")
    print(f"   Path: {file_path}")

    # ── STEP 1: Document Reader ─────────────────────────────────
    print("\n🔍 Step 1: Running Document Reader...")
    reader = build_reader()
    reader_output = reader.read_document(
        file_path=file_path,
        document_id=f"doc_{os.path.basename(file_path)}",
        known_hashes={},
    )

    # Check for duplicate
    if reader_output.get("status") == "EXACT_DUPLICATE":
        print("   ⚠️  Exact duplicate detected — skipping.")
        return

    pages = reader_output.get("pages", [])
    print(f"   ✅ Reader done — {len(pages)} page(s) extracted")

    # Show a preview of what was extracted
    for page in pages[:1]:
        text = page.get("raw_text", "")[:200]
        print(f"   📝 Text preview: {text}...")

    # ── STEP 2: Feature Mapper ──────────────────────────────────
    print("\n🗺️  Step 2: Running Feature Mapper...")
    schema = load_schema()
    mapper = build_mapper()

    existing_state = {}  # First document — no prior state
    mapper_output = mapper.map_features(
        reader_output=reader_output,
        existing_state=existing_state,
        schema=schema,
    )

    print("   ✅ Mapper done")

    # ── STEP 3: Print results ───────────────────────────────────
    print_summary(mapper_output)

    # ── Optional: save full JSON output ─────────────────────────
    output_path = os.path.join(
        os.path.dirname(__file__), "mapper_output.json"
    )
    # Remove non-serializable items
    clean_output = {
        k: v for k, v in mapper_output.items()
        if k != "_mapper_log"
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(clean_output, f, indent=2, default=str)
    print(f"💾 Full JSON output saved to: {output_path}")


if __name__ == "__main__":
    main()
