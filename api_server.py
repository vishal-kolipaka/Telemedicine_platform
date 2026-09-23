"""
TeleMed Backend API Server
==========================
FastAPI REST API bridge connecting the React frontend to the Python DocumentReader module.
Supports multi-file batch upload and session-isolated duplicate detection.
"""

import os
import shutil
import uuid
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

import json
from src.preprocessing.reader import DocumentReader, ReaderConfig
from src.preprocessing.reader.extractors.pdf_text_extractor import PdfTextExtractor
from src.preprocessing.reader.extractors.tesseract_ocr_extractor import TesseractOCRExtractor
from src.preprocessing.reader.extractors.pandas_structured_parser import PandasStructuredParser

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

# Initialize FastAPI App
app = FastAPI(
    title="TeleMed AI Healthcare API",
    description="Backend API service for TeleMed Document Processing Platform",
    version="1.0.0"
)

# Enable CORS (Supports Vercel frontend domains + local dev)
raw_origins = os.environ.get("ALLOWED_ORIGINS", "*")
allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()] if raw_origins != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Directory for temporary uploads and persistent data
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# Initialize DocumentReader Singleton
reader_config = ReaderConfig()
pdf_extractor = PdfTextExtractor(enable_table_extraction=reader_config.enable_table_extraction)
ocr_extractor = TesseractOCRExtractor()
structured_parser = PandasStructuredParser()

document_reader = DocumentReader(
    pdf_extractor=pdf_extractor,
    ocr_extractor=ocr_extractor,
    structured_parser=structured_parser,
    config=reader_config
)

# Initialize FeatureMapper Singleton & Load Schema
schema_path = os.path.join(BASE_DIR, "src", "preprocessing", "feature_schema.json")
with open(schema_path, "r", encoding="utf-8") as f:
    feature_schema = json.load(f)

mapper_config = MapperConfig()
feature_mapper = FeatureMapper(
    candidate_extractor=DefaultCandidateExtractor(),
    regex_engine=RegexMatchingEngine(mapper_config),
    llm_engine=LLMFallbackMatchingEngine(mapper_config),
    validators=[RangeValidator(), UnitValidator(), TypeValidator()],
    derived_calculators={"BMI": BMICalculator()},
    config=mapper_config,
)


@app.get("/api/health")
@app.head("/api/health", include_in_schema=False)
@app.get("/health")
@app.head("/health", include_in_schema=False)
def health_check():
    """Healthcheck endpoint."""
    return {"status": "ok", "service": "TeleMed AI Healthcare Platform", "version": "1.0.0"}


@app.post("/api/analyze")
async def analyze_documents(files: List[UploadFile] = File(...)):
    """Accepts multiple uploaded files for a session, runs DocumentReader per file,
    automatically passes extracted output into FeatureMapper, and returns both
    raw reader output and structured mapped features.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    results = []
    session_hashes: Dict[str, str] = {}
    session_pages = []
    session_logs = []

    for file in files:
        if not file.filename:
            continue

        doc_id = f"doc_{uuid.uuid4().hex[:10]}"
        temp_path = os.path.join(UPLOAD_DIR, f"{doc_id}_{file.filename}")

        try:
            # Save file to disk
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Step 1: Execute DocumentReader per file
            result = document_reader.read_document(
                file_path=temp_path,
                document_id=doc_id,
                known_hashes=session_hashes
            )

            # Record hash in session map for duplicate checking within this batch
            if "file_hash" in result and result.get("status") != "EXACT_DUPLICATE":
                session_hashes[result["file_hash"]] = doc_id

            # Collect pages & extraction logs for session aggregation
            if result.get("status") != "EXACT_DUPLICATE" and not result.get("error"):
                for page in result.get("pages", []):
                    session_pages.append(page)
                for log in result.get("extraction_log", []):
                    session_logs.append(log)

            results.append(result)

        except Exception as exc:
            results.append({
                "document_id": doc_id,
                "source_file": file.filename,
                "error": str(exc),
                "quality_check": {"passed": False, "reason": str(exc)}
            })
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    # Step 2: Combine ALL Reader outputs from the session into one consolidated session_reader_output
    session_reader_output = {
        "document_id": "session_consolidated",
        "pages": session_pages,
        "extraction_log": session_logs,
    }

    # Step 3: Run Feature Mapper ONCE over the aggregated session_reader_output
    session_mapper_output = None
    session_mapper_error = None
    if session_pages:
        try:
            session_mapper_output = feature_mapper.map_features(
                reader_output=session_reader_output,
                existing_state={},
                schema=feature_schema,
            )
        except Exception as map_exc:
            session_mapper_error = str(map_exc)

    # Step 4: Attach consolidated session_mapper_output to each document result for unified dashboard rendering
    for res in results:
        res["mapper_output"] = session_mapper_output
        if session_mapper_error:
            res["mapper_output_error"] = session_mapper_error

    return JSONResponse(content=results)


from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from fastapi import Response
from src.router.router import ModelRouter
from src.fusion_v2.fusion import fuse_predictions
from src.xai.xai_engine import XAIEngine
from src.recommendations.plan_generator import PlanGenerator
from src.recommendations import (
    ProgressPlanGenerator,
    ProgressPlanStore,
    ProgressPlanPDFGenerator,
)

# Initialize Router, XAI, and PlanGenerator singletons
model_router = ModelRouter()
xai_engine = XAIEngine()
plan_generator = PlanGenerator()

LABEL_MAPPING = {
    "FINAL_PREDICTION": "Assessment Available",
    "REDUCED_MODALITY": "Limited Data Assessment",
    "INSUFFICIENT_EVIDENCE": "Not Enough Information",
}

DISEASE_DISPLAY_NAMES = {
    "Type2_Diabetes": "Type 2 Diabetes",
    "Prediabetes": "Prediabetes",
    "High_Adiposity_Risk": "High Adiposity Risk",
    "Metabolic_Syndrome": "Metabolic Syndrome",
    "NAFLD": "Non-Alcoholic Fatty Liver Disease (NAFLD)",
}


class RunAssessmentPayload(BaseModel):
    contract2: Dict[str, Any]
    user_answers: Optional[Dict[str, Any]] = None
    patient_id: Optional[str] = None


@app.post("/api/run-assessment")
async def run_assessment(payload: RunAssessmentPayload):
    """Executes the full clinical inference and fusion pipeline from Contract 2 state:
    Contract 2 + User Answers → apply_user_answer() → ModelRouter → Level-0 Models → Fusion V2 → XAI → PlanGenerator.
    Returns a clean, patient-safe summary with comprehensive XAI explanations and governed health plan.
    """
    contract2 = payload.contract2
    user_answers = payload.user_answers or {}
    patient_id = payload.patient_id or "unknown"

    # Step 1: Apply user-provided answers to Contract 2 using FeatureMapper engine
    if user_answers:
        for field_name, user_val in user_answers.items():
            if user_val is not None and str(user_val).strip() != "":
                # Extract clean string/boolean/numeric value
                val = user_val
                if isinstance(user_val, dict) and "canonical_value" in user_val:
                    val = user_val["canonical_value"]
                try:
                    contract2 = feature_mapper.apply_user_answer(
                        field_name=field_name,
                        value=val,
                        current_state=contract2,
                        schema=feature_schema,
                        source="user_form",
                    )
                except Exception as exc:
                    # Non-fatal: log and continue
                    pass

    # Extract patient identity if available in contract2
    pi = contract2.get("patient_info", {})
    patient_name = pi.get("Name") or pi.get("name")
    patient_age = pi.get("Age") or pi.get("age")
    patient_gender = pi.get("Gender") or pi.get("gender")

    # Step 2: Route through authoritative ModelRouter
    router_output = model_router.route(contract2)

    # Step 3: Run Fusion V2
    fusion_output = fuse_predictions(router_output, patient_id=patient_id)

    # Step 4: Run XAI Engine
    xai_output = None
    try:
        xai_output = xai_engine.explain_assessment(
            contract2=contract2,
            router_output=router_output,
            fusion_output=fusion_output,
        )
    except Exception as xai_exc:
        # Non-fatal fallback for XAI
        xai_output = {
            "default_disease": None,
            "has_usable_explanations": False,
            "explanations": {},
            "error": str(xai_exc),
        }

    # Step 5: Construct patient-facing response boundary
    diseases_list = []
    has_any_usable_data = False

    for dis_key in ("Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk", "Metabolic_Syndrome", "NAFLD"):
        dis_info = fusion_output.get("diseases", {}).get(dis_key, {})
        raw_score = dis_info.get("risk_score")
        dec = dis_info.get("decision")
        conf_label = dis_info.get("confidence_label", "INSUFFICIENT_EVIDENCE")
        is_sup = dis_info.get("is_suppressed", False)

        patient_status_label = LABEL_MAPPING.get(conf_label, "Not Enough Information")
        risk_pct = round(raw_score * 100, 2) if raw_score is not None and isinstance(raw_score, (int, float)) else None
        decision_text = "Positive" if dec is True else ("Negative" if dec is False else "N/A")

        if raw_score is not None:
            has_any_usable_data = True

        # Generate friendly explanation
        if conf_label == "INSUFFICIENT_EVIDENCE":
            explanation = "Additional health records or laboratory biomarkers are required to evaluate this condition."
        elif is_sup:
            explanation = "Type 2 Diabetes criteria met; secondary prediabetes indicator suppressed."
        elif dec is True:
            explanation = "Elevated risk detected based on the analyzed health markers."
        else:
            explanation = "Risk score is within normal parameters based on the analyzed health markers."

        diseases_list.append({
            "key": dis_key,
            "display_name": DISEASE_DISPLAY_NAMES.get(dis_key, dis_key),
            "risk_score": raw_score,
            "risk_percentage": risk_pct,
            "decision": dec,
            "decision_text": decision_text,
            "status_label": patient_status_label,
            "is_suppressed": is_sup,
            "explanation": explanation,
        })

    # Step 6: Generate Governed Personalized Health Plan
    health_plan_output = None
    if has_any_usable_data:
        try:
            merged_features = {}
            for domain in ("clinical", "wearable", "gut"):
                domain_data = contract2.get(domain, {})
                if isinstance(domain_data, dict):
                    # Check Contract 2 'values' dict (canonical structure)
                    vals = domain_data.get("values", {})
                    if isinstance(vals, dict):
                        for k, v in vals.items():
                            if isinstance(v, dict) and "canonical_value" in v:
                                merged_features[k] = v["canonical_value"]
                            else:
                                merged_features[k] = v
                    # Also check direct 'features' dict if provided
                    feats = domain_data.get("features", {})
                    if isinstance(feats, dict):
                        merged_features.update(feats)

            disease_eval_list = []
            for d_item in diseases_list:
                d_k = d_item["key"]
                d_score = d_item.get("risk_score")
                d_dec = d_item.get("decision")
                d_prob = d_score if (d_score is not None and isinstance(d_score, (int, float))) else 0.0
                disease_eval_list.append({
                    "disease": d_k,
                    "prediction": 1 if d_dec is True else 0,
                    "probability": d_prob,
                    "risk_level": d_item.get("status_label", "Moderate")
                })

            xai_exps = xai_output.get("explanations", {}) if isinstance(xai_output, dict) else {}
            health_plan_output = plan_generator.generate_personalized_plan(
                patient_features=merged_features,
                xai_explanations=xai_exps,
                disease_results=disease_eval_list,
            )
        except Exception as plan_exc:
            health_plan_output = {
                "summary_title": "Your Personalized Health Plan",
                "status": "GENERATION_UNAVAILABLE",
                "message": "Your health assessment is ready, but we couldn't generate your personalized action plan right now.",
                "sections": None,
                "recommendation_items": [],
                "total_validated_recommendations": 0
            }

    response_data = {
        "patient_id": patient_id,
        "patient_name": patient_name,
        "patient_age": patient_age,
        "patient_gender": patient_gender,
        "assessment_timestamp": datetime.now(timezone.utc).isoformat(),
        "has_any_usable_data": has_any_usable_data,
        "summary_message": (
            "Assessment successfully generated using available health evidence."
            if has_any_usable_data
            else "Insufficient clinical data provided across all modalities to generate health risk scores."
        ),
        "diseases": diseases_list,
        "xai": xai_output,
        "health_plan": health_plan_output,
    }

    return JSONResponse(content=response_data)


# ── PROGRESS PLAN REST API ENDPOINTS ─────────────────────────────────────────

class GenerateProgressPlanPayload(BaseModel):
    patient_id: str
    patient_name: Optional[str] = None
    patient_age: Optional[Any] = None
    patient_gender: Optional[str] = None
    duration: str = "1_week"  # "1_week", "1_month", "3_months"
    health_plan: Dict[str, Any]


class ToggleTaskPayload(BaseModel):
    task_id: str
    completed: Optional[bool] = None


@app.post("/api/progress-plan/generate")
async def generate_progress_plan(payload: GenerateProgressPlanPayload):
    """Generates a structured, actionable daily progress plan for the given duration and persists it."""
    patient_info = {
        "patient_id": payload.patient_id,
        "name": payload.patient_name,
        "patient_name": payload.patient_name,
        "age": payload.patient_age,
        "gender": payload.patient_gender,
    }

    try:
        plan_data = ProgressPlanGenerator.generate_progress_plan(
            health_plan=payload.health_plan,
            patient_info=patient_info,
            duration=payload.duration,
        )
        saved_record = ProgressPlanStore.save_plan(plan_data)
        return JSONResponse(content=saved_record)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate progress plan: {str(exc)}")


@app.get("/api/progress-plan/{plan_id}")
async def get_progress_plan(plan_id: str):
    """Retrieves an existing progress plan and its current progress state."""
    record = ProgressPlanStore.get_plan(plan_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Progress plan '{plan_id}' not found.")
    return JSONResponse(content=record)


@app.post("/api/progress-plan/{plan_id}/toggle-task")
async def toggle_progress_task(plan_id: str, payload: ToggleTaskPayload):
    """Toggles task completion state, updates day completion, and unlocks subsequent days."""
    updated_record = ProgressPlanStore.toggle_task(
        plan_id=plan_id,
        task_id=payload.task_id,
        completed=payload.completed,
    )
    if not updated_record:
        raise HTTPException(status_code=404, detail=f"Progress plan '{plan_id}' not found.")
    return JSONResponse(content=updated_record)


@app.post("/api/progress-plan/{plan_id}/reset")
async def reset_progress_plan(plan_id: str):
    """Resets progress back to Day 1 with 0 completed tasks and re-locked future days."""
    updated_record = ProgressPlanStore.reset_plan(plan_id)
    if not updated_record:
        raise HTTPException(status_code=404, detail=f"Progress plan '{plan_id}' not found.")
    return JSONResponse(content=updated_record)


@app.get("/api/progress-plan/{plan_id}/pdf")
async def download_progress_plan_pdf(plan_id: str):
    """Generates and streams a downloadable PDF report for the progress plan."""
    record = ProgressPlanStore.get_plan(plan_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Progress plan '{plan_id}' not found.")

    try:
        pdf_bytes = ProgressPlanPDFGenerator.generate_pdf_bytes(record)
        duration = record.get("duration", "plan")
        filename = f"progress_plan_{duration}_{record.get('patient_id', 'patient')}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "application/pdf"
            }
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(exc)}")


# Serve Built React Frontend (SPA fallback)
DIST_DIR = os.path.join(BASE_DIR, "frontend", "dist")
if not os.path.exists(DIST_DIR):
    frontend_dir = os.path.join(BASE_DIR, "frontend")
    if os.path.exists(os.path.join(frontend_dir, "package.json")):
        try:
            import subprocess
            print("[INFO] Building React frontend assets in frontend/dist...")
            subprocess.run("npm run build", shell=True, cwd=frontend_dir, check=True)
        except Exception as e:
            print(f"[WARNING] Could not build frontend automatically: {e}")

if os.path.exists(DIST_DIR):
    assets_dir = os.path.join(DIST_DIR, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    @app.head("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        file_path = os.path.join(DIST_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(DIST_DIR, "index.html"))


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("api_server:app", host="0.0.0.0", port=port, reload=False)
