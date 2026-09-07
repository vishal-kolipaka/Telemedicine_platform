"""
tests/simulate_user_form_answers.py — Test-Only Harness for Form Submission Simulation

IMPORTANT NOTICE:
-----------------
This module is a TEST-ONLY simulation harness for developer and CI/CD validation.
It simulates the behavior of what a future user-facing onboarding form / API endpoint
(e.g., POST /api/submit-user-answers) will do when a patient submits anamnesis answers.

DO NOT import or wire this file into production routes or application runtimes.
Production code must receive real user responses via authenticated API endpoints.

Purpose:
--------
1. Accepts a Contract 2 state where clinical.status == "incomplete" due to missing
   user_form fields (Family_History_Diabetes, Family_History_Hypertension, Family_History_CVD).
2. Directly invokes the core engine function FeatureMapper.apply_user_answer() for each field.
3. Returns the updated Contract 2 state with clinical.status == "complete", allowing
   ModelRouter to dispatch predict_clinical() and Fusion V2 to execute full C+G+W fusion (Case 1/2).
"""

from __future__ import annotations

import os
import sys
import json
import logging
from typing import Any

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.preprocessing.mapper import (
    FeatureMapper,
    MapperConfig,
    DefaultCandidateExtractor,
    RegexMatchingEngine,
    RangeValidator,
    UnitValidator,
    TypeValidator,
    BMICalculator,
)

logger = logging.getLogger("TestHarness.UserFormSimulation")


def _get_default_mapper() -> FeatureMapper:
    """Build a default FeatureMapper instance for simulation if none provided."""
    config = MapperConfig()
    return FeatureMapper(
        candidate_extractor=DefaultCandidateExtractor(),
        regex_engine=RegexMatchingEngine(config),
        llm_engine=None,
        validators=[RangeValidator(), UnitValidator(), TypeValidator()],
        derived_calculators={"BMI": BMICalculator()},
        config=config,
    )


def simulate_family_history_answers(
    current_state: dict,
    schema: dict,
    mapper: FeatureMapper | None = None,
    diabetes: str | bool = "Yes",
    hypertension: str | bool = "Yes",
    cvd: str | bool = "No",
) -> dict:
    """Simulate user-form submission for the 3 clinical family history fields.

    Parameters
    ----------
    current_state : dict
        Current Contract 2 state (post-Mapper run), where clinical.status is typically
        "incomplete" because family history fields are required.
    schema : dict
        The feature_schema.json contents.
    mapper : FeatureMapper, optional
        An existing FeatureMapper instance. If None, a default instance is created.
    diabetes : str or bool, default "Yes"
        User response for Family_History_Diabetes ("Yes", "No", True, False).
    hypertension : str or bool, default "Yes"
        User response for Family_History_Hypertension ("Yes", "No", True, False).
    cvd : str or bool, default "No"
        User response for Family_History_CVD ("Yes", "No", True, False).

    Returns
    -------
    dict
        Updated Contract 2 state with family history values applied, validation status
        marked as "USER_ENTERED", missing_fields updated, and clinical.status recomputed.
    """
    if mapper is None:
        mapper = _get_default_mapper()

    answers = [
        ("Family_History_Diabetes", diabetes),
        ("Family_History_Hypertension", hypertension),
        ("Family_History_CVD", cvd),
    ]

    state = current_state
    for field_name, answer in answers:
        state = mapper.apply_user_answer(
            field_name=field_name,
            value=answer,
            current_state=state,
            schema=schema,
            source="user_form",
        )

    return state


# ─────────────────────────────────────────────────────────────────────────────
# Verification Runner for Scenario 1 End-to-End Test
# ─────────────────────────────────────────────────────────────────────────────

def test_scenario1_with_user_form_simulation():
    """Pytest validation: Scenario 1 with simulated user-form answers triggers Case 1 fusion."""
    result = run_scenario1_with_harness()
    assert result["fusion_version"] == "v2"
    assert result["metadata"]["fallback_triggered"] is False
    assert result["metadata"]["modality_caveat"] is None
    # MetSyn and NAFLD must use cg_lr_stacker (Case 1)
    assert result["diseases"]["Metabolic_Syndrome"]["strategy"] == "cg_lr_stacker"
    assert result["diseases"]["Metabolic_Syndrome"]["confidence_label"] == "FINAL_PREDICTION"
    assert result["diseases"]["NAFLD"]["strategy"] == "cg_lr_stacker"
    assert result["diseases"]["NAFLD"]["confidence_label"] == "FINAL_PREDICTION"
    # Clinical passthrough for T2D, Pre, HAR
    assert result["diseases"]["Type2_Diabetes"]["strategy"] == "clinical_passthrough"
    assert result["diseases"]["Prediabetes"]["strategy"] == "clinical_passthrough"
    assert result["diseases"]["High_Adiposity_Risk"]["strategy"] == "clinical_passthrough"


def run_scenario1_with_harness():
    """Run full E2E pipeline for Scenario 1 with the test harness inserted."""
    from src.preprocessing.reader import DocumentReader, ReaderConfig
    from src.preprocessing.reader.extractors.pdf_text_extractor import PdfTextExtractor
    from src.preprocessing.reader.extractors.tesseract_ocr_extractor import TesseractOCRExtractor
    from src.preprocessing.reader.extractors.pandas_structured_parser import PandasStructuredParser
    from src.router.router import ModelRouter
    from src.fusion_v2.fusion import fuse_predictions

    schema_path = os.path.join(PROJECT_ROOT, "src", "preprocessing", "feature_schema.json")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    doc_path = os.path.join(PROJECT_ROOT, "testing datas", "scenario1_all_modalities.txt")
    print(f"\n{'=' * 75}")
    print("  SCENARIO 1 E2E VERIFICATION WITH USER-FORM TEST HARNESS")
    print(f"{'=' * 75}")
    print(f"Document: {os.path.basename(doc_path)}")

    # 1. DocumentReader
    reader = DocumentReader(
        pdf_extractor=PdfTextExtractor(),
        ocr_extractor=TesseractOCRExtractor(),
        structured_parser=PandasStructuredParser(),
        config=ReaderConfig(),
    )
    reader_output = reader.read_document(doc_path, document_id="doc_scenario1_test", known_hashes={})
    print(f"\n1. Reader: Extracted {len(reader_output.get('pages', []))} page(s)")

    # 2. FeatureMapper (Initial run on document alone)
    mapper = _get_default_mapper()
    state_after_doc = mapper.map_features(
        reader_output=reader_output,
        existing_state={},
        schema=schema,
    )
    c_status_before = state_after_doc.get("clinical", {}).get("status")
    c_missing_before = state_after_doc.get("clinical", {}).get("missing_fields", [])
    print(f"2. Mapper (post-doc): clinical.status = '{c_status_before}'")
    print(f"   Missing clinical fields ({len(c_missing_before)}): {c_missing_before}")

    # 3. Apply Test Harness (Simulating user filling out form)
    print("\n3. [TEST HARNESS] Simulating user answering family history questions:")
    print("   - Family_History_Diabetes:      'Yes'")
    print("   - Family_History_Hypertension:  'Yes'")
    print("   - Family_History_CVD:           'No'")

    state_after_form = simulate_family_history_answers(
        current_state=state_after_doc,
        schema=schema,
        mapper=mapper,
        diabetes="Yes",
        hypertension="Yes",
        cvd="No",
    )

    c_status_after = state_after_form.get("clinical", {}).get("status")
    c_missing_after = state_after_form.get("clinical", {}).get("missing_fields", [])
    c_values = state_after_form.get("clinical", {}).get("values", {})
    print(f"   Mapper state updated: clinical.status = '{c_status_after}'")
    print(f"   Missing clinical fields: {c_missing_after}")
    print(f"   Total clinical values present: {len(c_values)} / 18")

    # 4. ModelRouter
    router = ModelRouter()
    router_output = router.route(state_after_form)
    print("\n4. Router Execution Results:")
    for domain in ("clinical", "wearable", "gut"):
        res = router_output.get(domain, {})
        status = res.get("status")
        print(f"   - {domain.upper():<10s} status = '{status}'")
        if status == "success":
            for dis, p in res.get("probabilities", {}).items():
                print(f"       {dis:<22s}: p={p:.4f} (decision={res.get('predictions', {}).get(dis)})")

    # 5. Fusion V2
    fusion_output = fuse_predictions(router_output, patient_id="P001001")
    print("\n5. Fusion V2 Output (Case 1 — Full C+G+W Fusion):")
    print(f"   Fallback Triggered: {fusion_output['metadata']['fallback_triggered']}")
    print(f"   Modality Caveat:    {fusion_output['metadata']['modality_caveat']}")
    print("\n   Disease Predictions:")
    for dis_name, dis_res in fusion_output["diseases"].items():
        score = dis_res["risk_score"]
        score_str = f"{score:.4f}" if isinstance(score, float) else str(score)
        dec = dis_res["decision"]
        strat = dis_res["strategy"]
        conf = dis_res["confidence_label"]
        mods = "+".join(dis_res["modalities_used"])
        sup = " [SUPPRESSED]" if dis_res.get("is_suppressed") else ""
        we = dis_res["wearable_evidence"]["raw_score"]
        we_str = f"{we:.4f}" if isinstance(we, float) else str(we)
        print(f"   - {dis_name:<22s}: score={score_str:<7s} dec={str(dec):<5s} strat={strat:<20s} conf={conf:<16s} mods=[{mods}]{sup} (wearable_xai={we_str})")

    print("\n" + "=" * 75)
    print("  VERIFICATION COMPLETE")
    print("=" * 75 + "\n")
    return fusion_output


if __name__ == "__main__":
    run_scenario1_with_harness()
