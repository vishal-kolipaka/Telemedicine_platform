"""
TeleMed Backend API Server
==========================
FastAPI REST API bridge connecting the React frontend to the Python DocumentReader module.
Supports multi-file batch upload and session-isolated duplicate detection.
"""

import os
import shutil
import uuid
from typing import List, Dict
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

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory for temporary uploads
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

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
schema_path = os.path.join(os.getcwd(), "src", "preprocessing", "feature_schema.json")
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


# Serve Built React Frontend (SPA fallback)
DIST_DIR = os.path.join(os.getcwd(), "frontend", "dist")
if os.path.exists(DIST_DIR):
    assets_dir = os.path.join(DIST_DIR, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        file_path = os.path.join(DIST_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(DIST_DIR, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
