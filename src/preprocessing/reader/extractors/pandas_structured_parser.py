"""
PandasStructuredParser — extracts data from CSV and XLSX files.

Uses pandas + openpyxl. Treats the entire file as a single "page" containing
one table (the DataFrame).

Single Responsibility: structured data extraction only. Does NOT validate
quality, does NOT detect duplicates.
"""

import pandas as pd
from datetime import datetime, timezone

from src.preprocessing.reader.interfaces import Extractor
from src.preprocessing.reader.exceptions import ParserFailure


class PandasStructuredParser(Extractor):
    """Extracts tabular data from CSV and XLSX files using pandas."""

    EXTRACTOR_NAME = "pandas"

    def extract(self, file_path: str) -> dict:
        """Extract content from a CSV or XLSX file.

        The entire file is treated as page_index=0 with one table.
        raw_text is a string representation of the DataFrame.

        Args:
            file_path: Path to the CSV or XLSX file.

        Returns:
            Dict with raw_pages, extraction_log, extractor_name.

        Raises:
            ParserFailure: If pandas cannot parse the file at all.
        """
        raw_pages: list[dict] = []
        extraction_log: list[dict] = []
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        lower_path = file_path.lower()

        try:
            if lower_path.endswith(".xlsx") or lower_path.endswith(".xls"):
                df = pd.read_excel(file_path, engine="openpyxl", dtype=str)
            elif lower_path.endswith(".csv"):
                df = pd.read_csv(file_path, dtype=str)
            else:
                # Fallback: try CSV first
                try:
                    df = pd.read_csv(file_path, dtype=str)
                except Exception:
                    df = pd.read_excel(file_path, engine="openpyxl", dtype=str)
        except Exception as exc:
            raise ParserFailure(
                f"pandas cannot parse file: {exc}"
            ) from exc

        # Convert DataFrame to table format:
        # list of rows, each row a list of cell strings
        # First row is the header
        header_row = [str(col) for col in df.columns.tolist()]
        data_rows = [
            [str(cell) for cell in row]
            for row in df.values.tolist()
        ]
        table = [header_row] + data_rows

        # Generate raw_text as a readable string representation
        raw_text = df.to_string(index=False)

        extraction_log.append({
            "timestamp": timestamp,
            "level": "INFO",
            "module": "PandasStructuredParser",
            "message": (
                f"parsed successfully: {len(df)} rows, "
                f"{len(df.columns)} columns"
            ),
        })

        raw_pages.append({
            "page_index": 0,
            "extractor_used": self.EXTRACTOR_NAME,
            "raw_text": raw_text,
            "tables": [table],
            "average_page_confidence": None,  # Not OCR, no confidence
        })

        return {
            "raw_pages": raw_pages,
            "extraction_log": extraction_log,
            "extractor_name": self.EXTRACTOR_NAME,
        }

    def extract_page_from_image(self, image, page_index: int) -> dict:
        """Not supported — PandasStructuredParser works with CSV/XLSX, not images.

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError(
            "PandasStructuredParser does not support image-based extraction."
        )
