# ==============================================================================
# Multi-Stage Production Dockerfile for TeleMed AI Healthcare Platform
# Stage 1: Build React 19 Frontend with Vite
# Stage 2: Unified Python Runtime (FastAPI + ML Models + Fusion + XAI + UI)
# ==============================================================================

# --- Stage 1: Frontend Build ---
FROM node:22-slim AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# --- Stage 2: Production Python Runtime ---
FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    PORT=8000

# Install required system packages for OCR (Tesseract), PDF rendering (Poppler), and OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python production dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source, intelligence modules, ML models, knowledge base, and assets
COPY src/ ./src/
COPY clinical_model/ ./clinical_model/
COPY wearable_model/ ./wearable_model/
COPY gut_model/ ./gut_model/
COPY knowledge_base/ ./knowledge_base/
COPY data/ ./data/
COPY api_server.py run_web_app.py ./

# Ensure uploads and data directories exist with proper permissions
RUN mkdir -p /app/uploads /app/data

# Copy pre-built React frontend assets from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

EXPOSE 8000

CMD ["python", "api_server.py"]
