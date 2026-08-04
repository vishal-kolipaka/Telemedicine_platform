"""
TesseractOCRExtractor — extracts text from scanned PDFs and image files.

Uses pytesseract when system Tesseract binary is available, with an automatic
RapidOCR (ONNX) engine fallback for robust cross-platform image processing.

Single Responsibility: OCR extraction only. Does NOT validate quality, does NOT
detect duplicates, does NOT handle digital PDFs.
"""

import numpy as np
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from datetime import datetime, timezone

from src.preprocessing.reader.interfaces import Extractor
from src.preprocessing.reader.exceptions import (
    CorruptedDocumentError,
    OCRExecutionError,
)

# RapidOCR Singleton Lazy Loader
_RAPID_OCR_ENGINE = None

def _get_rapid_ocr():
    global _RAPID_OCR_ENGINE
    if _RAPID_OCR_ENGINE is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
            _RAPID_OCR_ENGINE = RapidOCR()
        except ImportError:
            _RAPID_OCR_ENGINE = False
    return _RAPID_OCR_ENGINE if _RAPID_OCR_ENGINE else None


class TesseractOCRExtractor(Extractor):
    """Extracts text from images and scanned PDF pages using Tesseract OCR or RapidOCR."""

    EXTRACTOR_NAME = "tesseract"

    def extract(self, file_path: str) -> dict:
        """Extract text from an image file or scanned PDF.

        Args:
            file_path: Path to the image or scanned PDF file.

        Returns:
            Dict with raw_pages, extraction_log, extractor_name.
        """
        raw_pages: list[dict] = []
        extraction_log: list[dict] = []

        lower_path = file_path.lower()
        is_pdf = lower_path.endswith(".pdf")

        try:
            if is_pdf:
                try:
                    images = convert_from_path(file_path)
                except Exception as exc:
                    raise CorruptedDocumentError(
                        f"pdf2image cannot convert PDF to images: {exc}"
                    ) from exc

                for page_index, image in enumerate(images):
                    page_result = self._ocr_single_image(image, page_index)
                    raw_pages.append(page_result["page"])
                    extraction_log.extend(page_result["log_entries"])
            else:
                try:
                    image = Image.open(file_path)
                except Exception as exc:
                    raise CorruptedDocumentError(
                        f"Cannot open image file: {exc}"
                    ) from exc

                page_result = self._ocr_single_image(image, page_index=0)
                raw_pages.append(page_result["page"])
                extraction_log.extend(page_result["log_entries"])

        except (CorruptedDocumentError, OCRExecutionError):
            raise
        except Exception as exc:
            raise OCRExecutionError(
                f"OCR execution failed unexpectedly: {exc}"
            ) from exc

        return {
            "raw_pages": raw_pages,
            "extraction_log": extraction_log,
            "extractor_name": self.EXTRACTOR_NAME,
        }

    def extract_page_from_image(self, image, page_index: int) -> dict:
        """Extract text from a single page image."""
        result = self._ocr_single_image(image, page_index)
        return result["page"]

    def _ocr_single_image(self, image: Image.Image, page_index: int) -> dict:
        """Run OCR on a PIL Image using Tesseract, falling back to RapidOCR."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        log_entries: list[dict] = []

        raw_text = ""
        average_confidence = None
        engine_used = self.EXTRACTOR_NAME

        # 1. Try pytesseract first
        tesseract_succeeded = False
        try:
            ocr_data = pytesseract.image_to_data(
                image, output_type=pytesseract.Output.DICT
            )
            words = []
            confidences = []
            for i, text in enumerate(ocr_data["text"]):
                stripped = text.strip()
                if stripped:
                    words.append(stripped)
                    conf = ocr_data["conf"][i]
                    if isinstance(conf, (int, float)) and conf >= 0:
                        confidences.append(float(conf))

            raw_text = " ".join(words)
            if confidences:
                average_confidence = round(sum(confidences) / len(confidences), 2)
            tesseract_succeeded = True
        except Exception as exc:
            log_entries.append({
                "timestamp": timestamp,
                "level": "WARNING",
                "module": "TesseractOCRExtractor",
                "message": f"Pytesseract unavailable ({exc}), attempting RapidOCR fallback",
            })

        # 2. If pytesseract failed or missing, use RapidOCR
        if not tesseract_succeeded:
            rapid_engine = _get_rapid_ocr()
            if rapid_engine:
                engine_used = "rapidocr"
                try:
                    img_np = np.array(image.convert("RGB"))
                    ocr_results, _ = rapid_engine(img_np)

                    words = []
                    confidences = []
                    if ocr_results:
                        for item in ocr_results:
                            # item format: [box, text_str, confidence_0_to_1]
                            text_str = str(item[1]).strip()
                            conf = float(item[2]) * 100.0  # Convert to percentage 0-100
                            if text_str:
                                words.append(text_str)
                                confidences.append(conf)

                    raw_text = "\n".join(words)
                    if confidences:
                        average_confidence = round(sum(confidences) / len(confidences), 2)

                except Exception as exc:
                    log_entries.append({
                        "timestamp": timestamp,
                        "level": "ERROR",
                        "module": "TesseractOCRExtractor",
                        "message": f"RapidOCR execution failed: {exc}",
                    })
            else:
                raise OCRExecutionError(
                    "No working OCR engine available (Tesseract binary missing and RapidOCR unavailable)."
                )

        log_entries.append({
            "timestamp": timestamp,
            "level": "INFO",
            "module": "TesseractOCRExtractor",
            "message": (
                f"page {page_index}: {engine_used} extracted {len(raw_text)} chars, "
                f"avg confidence={average_confidence}%"
            ),
        })

        return {
            "page": {
                "page_index": page_index,
                "extractor_used": engine_used,
                "raw_text": raw_text,
                "tables": [],
                "average_page_confidence": average_confidence,
            },
            "log_entries": log_entries,
        }
