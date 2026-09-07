"""
validate_7_test_reports.py — Runs the complete DocumentReader -> FeatureMapper ->
Router -> Level-0 Models -> Fusion V2 -> XAI pipeline on all 7 generated reports.
"""

import os
import json
import pytest
from src.preprocessing.reader import DocumentReader, ReaderConfig
from src.preprocessing.reader.extractors.pdf_text_extractor import PdfTextExtractor
from src.preprocessing.reader.extractors.tesseract_ocr_extractor import TesseractOCRExtractor
from src.preprocessing.reader.extractors.pandas_structured_parser import PandasStructuredParser
from src.preprocessing.mapper import (
    FeatureMapper, MapperConfig, DefaultCandidateExtractor,
    RegexMatchingEngine, RangeValidator, UnitValidator, TypeValidator, BMICalculator
)
from src.router.router import ModelRouter
from src.fusion_v2 import fuse_predictions
from src.xai.xai_engine import XAIEngine

def main():
    reader = DocumentReader(
        pdf_extractor=PdfTextExtractor(enable_table_extraction=False),
        ocr_extractor=TesseractOCRExtractor(),
        structured_parser=PandasStructuredParser(),
        config=ReaderConfig()
    )

    with open('src/preprocessing/feature_schema.json') as f:
        schema = json.load(f)

    mapper = FeatureMapper(
        candidate_extractor=DefaultCandidateExtractor(),
        regex_engine=RegexMatchingEngine(MapperConfig()),
        llm_engine=None,
        validators=[RangeValidator(), UnitValidator(), TypeValidator()],
        derived_calculators={'BMI': BMICalculator()},
        config=MapperConfig(),
    )

    router = ModelRouter()
    xai_engine = XAIEngine()

    reports = [
        ('01_Clinical_Only.pdf', {'Family_History_Diabetes': 'Yes', 'Family_History_Hypertension': 'Yes', 'Family_History_CVD': 'No'}),
        ('02_Gut_Only.pdf', {}),
        ('03_Wearable_Only.pdf', {}),
        ('04_Clinical_Gut.pdf', {'Family_History_Diabetes': 'Yes', 'Family_History_Hypertension': 'Yes', 'Family_History_CVD': 'No'}),
        ('05_Clinical_Wearable.pdf', {'Family_History_Diabetes': 'Yes', 'Family_History_Hypertension': 'Yes', 'Family_History_CVD': 'Yes'}),
        ('06_Gut_Wearable.pdf', {}),
        ('07_Clinical_Gut_Wearable_Full.pdf', {'Family_History_Diabetes': 'Yes', 'Family_History_Hypertension': 'Yes', 'Family_History_CVD': 'Yes'}),
    ]

    print("=" * 80)
    print("  7-REPORT PIPELINE VERIFICATION AUDIT")
    print("=" * 80)

    for r, user_ans in reports:
        path = os.path.join('generated_test_reports', r)
        doc_res = reader.read_document(path, r, {})
        contract2 = mapper.map_features(doc_res, {}, schema)

        # Apply user answers for Family History where clinical is present
        if user_ans:
            for field, ans in user_ans.items():
                contract2 = mapper.apply_user_answer(field_name=field, value=ans, current_state=contract2, schema=schema, source="user_form")

        routed = router.route(contract2)
        fusion_out = fuse_predictions(routed, patient_id=f"TEST_{r[:2]}")
        xai_out = xai_engine.explain_assessment(contract2=contract2, router_output=routed, fusion_output=fusion_out)

        clin_stat = contract2['clinical']['status']
        gut_stat = contract2['gut']['status']
        wear_stat = contract2['wearable']['status']

        clin_vals = len(contract2['clinical']['values'])
        gut_vals = len(contract2['gut']['values'])
        wear_vals = len(contract2['wearable']['values'])

        print(f"\n[{r}]")
        print(f"  * Mapped Modalities: Clinical={clin_stat} ({clin_vals}/18), Gut={gut_stat} ({gut_vals}/21), Wearable={wear_stat} ({wear_vals}/15)")
        dispatched = [k for k, v in routed.items() if v.get('status') == 'ran']
        print(f"  * Router Dispatched: {dispatched}")
        print(f"  * Fusion Case: {fusion_out.get('case_applied', fusion_out.get('fusion_case', 'N/A'))}")
        print(f"  * Default Focus: {xai_out.get('default_disease', 'N/A')}")

        print("  * Disease Risk Predictions & XAI Model Signals:")
        for dis in ['Type2_Diabetes', 'Prediabetes', 'High_Adiposity_Risk', 'Metabolic_Syndrome', 'NAFLD']:
            res = fusion_out['diseases'][dis]
            score = res.get('risk_score')
            score_str = f"{score * 100:.2f}%" if score is not None else "N/A"
            supp_str = " (SUPPRESSED)" if res.get('is_suppressed') else ""
            print(f"     - {dis:22s}: {score_str:8s} | Decision={str(res.get('decision')):5s} | Strategy={res.get('strategy')}{supp_str}")

            exp = xai_out['explanations'].get(dis, {})
            if exp.get('available'):
                signals = exp.get('provenance', {}).get('available_signals', [])
                sig_parts = [f"{s['name']}={s['role']} ({s.get('risk_percentage', 'N/A')}%)" for s in signals]
                sources = exp.get('available_sources', [])
                drivers_cnt = len(exp.get('risk_drivers', []))
                print(f"       -> XAI Sources: {sources} | Signals: {', '.join(sig_parts)} | Total Drivers: {drivers_cnt}")

if __name__ == "__main__":
    main()
