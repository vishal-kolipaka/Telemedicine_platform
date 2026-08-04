"""
Candidate Extraction — pulls raw observations from Contract 1.

Has NO knowledge of feature_schema.json.  This stage doesn't decide
what anything means, just what's observably present in the text/tables.

Two extraction paths:
  1. Table extraction  — iterate tables, detect header rows, emit
     one Candidate per data row.
  2. Text extraction   — parse raw_text line-by-line, find
     "label: value unit" patterns.

Special-case handling:
  - BP "128/82 mmHg" → two Candidates (Systolic, Diastolic)
  - Height "5'10\"" → Candidate with unit_text "ft_in"

Performance (Section 17): single-pass text scan, not per-field re-search.
"""

from __future__ import annotations

import re

from src.preprocessing.mapper.interfaces import CandidateExtractor
from src.preprocessing.mapper.models import Candidate


# ── Table header detection ──────────────────────────────────────

# Words that commonly appear in lab report table headers.
_HEADER_KEYWORDS = {
    "test", "result", "unit", "units", "reference", "range",
    "ref", "normal", "value", "parameter", "analyte", "component",
}


def _is_header_row(row: list[str]) -> bool:
    """Check whether a table row looks like a header row.

    A row is considered a header if ≥2 of its cells contain
    recognized header keywords.
    """
    if not row:
        return False
    keyword_count = 0
    for cell in row:
        if cell and cell.strip().lower() in _HEADER_KEYWORDS:
            keyword_count += 1
    return keyword_count >= 2


# ── Text-line patterns ──────────────────────────────────────────

# Matches "Label: Value Unit", "Label = Value Unit", space-aligned "Label    Value Unit", or "Label 104 mg/dL"
# Group 1: label, Group 2: value (possibly with unit attached).
_LABEL_VALUE_PATTERN = re.compile(
    r"^([A-Za-z0-9 _/().'<>-]*?[A-Za-z][A-Za-z0-9 _/().'<>-]*?)(?:\s*[:=]\s*|\s{2,}|\t+|\s+(?=[+-]?\d+\.?\d*\b))(.*)$"
)

# Known non-numeric labels that should NEVER inherit backward numeric values
_NON_NUMERIC_LABELS = {
    "gender", "sex", "patient name", "patient_name", "patient id",
    "referred by", "sample type", "interpretation", "verified by",
}

# Matches a numeric value with optional unit suffix and qualifier prefixes (<, >, Approx, ~).
# Group 1: number, Group 2: unit (optional).
_VALUE_UNIT_PATTERN = re.compile(
    r"^[^\d+-]*?([+-]?\d+\.?\d*)\s*(.*)$"
)

# BP pattern: "128/82" or "128 / 82"
_BP_PATTERN = re.compile(
    r"(\d{2,3})\s*/\s*(\d{2,3})"
)

# Feet/inches pattern: 5'10", 5'10, 5 ft 10 in
_FT_IN_PATTERN = re.compile(
    r"""(\d+)\s*[''′ft.]+\s*(\d+\.?\d*)\s*[""″in.]*""",
    re.VERBOSE,
)


def _clean_unit(unit_str: str | None) -> str | None:
    """Strip trailing report divider lines, status words, and reference range bounds from unit strings."""
    if not unit_str:
        return None
    # Strip reference ranges like 70.0 - 99.0, 4.0 - 5.6, <100, >40, 6-29
    cleaned = re.sub(r"[<>]?\s*\d+\.?\d*\s*[-–:]\s*\d+\.?\d*", "", unit_str)
    cleaned = re.sub(r"[<>]\s*\d+\.?\d*", "", cleaned)
    # Strip status words like Yes, No, In Range, Out of Range
    cleaned = re.sub(r"\b(yes|no|in range|out of range|normal|high|low|pass|flag)\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"[\s=\-_*]{2,}.*$", "", cleaned.strip()).strip()
    return cleaned if cleaned else None


def _classify_context(
    raw_text: str,
    line_index: int,
    total_lines: int,
) -> str:
    """Classify the structural context of a text line.

    Simple heuristic:
    - If the text has consistent "Label: Value" formatting
      across multiple lines → "lab_report_section"
    - Single isolated match in prose → "generic_paragraph"
    - Otherwise → "unstructured"
    """
    lines = raw_text.split("\n")
    # Count how many lines in the surrounding context match
    # the label:value pattern.
    window = 5
    start = max(0, line_index - window)
    end = min(total_lines, line_index + window)
    label_count = sum(
        1 for i in range(start, end)
        if i < len(lines) and _LABEL_VALUE_PATTERN.match(lines[i].strip())
    )
    if label_count >= 3:
        return "lab_report_section"
    elif label_count >= 1:
        return "generic_paragraph"
    return "unstructured"


class DefaultCandidateExtractor(CandidateExtractor):
    """Concrete CandidateExtractor that handles tables + text.

    Pipeline: Tables first (higher confidence context), then text
    lines for anything not already covered.
    """

    VERSION = "DefaultCandidateExtractor 1.0"

    def extract(self, reader_output: dict) -> list[Candidate]:
        """Extract all candidates from a Contract 1 output.

        Args:
            reader_output: Full Contract 1 dict from the Document Reader.

        Returns:
            List of Candidate objects — one per observed
            (label, value, unit) triple.
        """
        candidates: list[Candidate] = []
        pages = reader_output.get("pages", [])

        for page in pages:
            page_index = page.get("page_index", 0)
            tables = page.get("tables", [])
            raw_text = page.get("raw_text", "")

            # ── Path 1: Table extraction ────────────────────────
            for table in tables:
                table_candidates = self._extract_from_table(
                    table, page_index
                )
                candidates.extend(table_candidates)

            # ── Path 2: Text extraction ─────────────────────────
            text_candidates = self._extract_from_text(
                raw_text, page_index
            )
            candidates.extend(text_candidates)

        return candidates

    def _extract_from_table(
        self,
        table: list[list[str]],
        page_index: int,
    ) -> list[Candidate]:
        """Extract candidates from a single table.

        If the first row is a header row, use column positions to
        map Test→label, Result→value, Unit→unit.  Otherwise treat
        each row as [label, value, ...].
        """
        candidates: list[Candidate] = []
        if not table or len(table) < 2:
            return candidates

        first_row = table[0]
        has_header = _is_header_row(first_row)

        if has_header:
            # Find column indices for test/result/unit
            col_map = self._map_header_columns(first_row)
            data_rows = table[1:]
        elif len(first_row) >= 3:
            # Wide dataset table (CSV/XLSX/dataframe) where each column header is a feature name
            headers = [str(h).strip() for h in first_row]
            for row in table[1:]:
                if not row or all(not str(c).strip() for c in row):
                    continue
                source_line = " | ".join([str(c).strip() for c in row])
                for col_idx, label in enumerate(headers):
                    if col_idx >= len(row):
                        continue
                    val_str = str(row[col_idx]).strip()
                    if not label or not val_str:
                        continue
                    if val_str.lower() in ("nan", "n/a", "na", "null", "none", "", "-"):
                        continue

                    unit = None
                    unit_m = re.search(r"[\(_](cm|kg|mmHg|mg/dL|g/dL|U/L|mmol/L|%|in|lbs|steps/day|kcal/day|hours|bpm)[_\)]?$", label, re.IGNORECASE)
                    if unit_m:
                        unit = unit_m.group(1)

                    val_unit_m = _VALUE_UNIT_PATTERN.match(val_str)
                    if val_unit_m:
                        numeric_val = val_unit_m.group(1)
                        unit_part = val_unit_m.group(2).strip() or unit
                        val_str = numeric_val
                        unit = unit_part

                    bp_m = _BP_PATTERN.search(val_str)
                    if bp_m and ("pressure" in label.lower() or "bp" in label.lower() or "/" in val_str):
                        unit_bp = unit or "mmHg"
                        candidates.append(Candidate(
                            label_text="Systolic BP", value_text=bp_m.group(1), unit_text=unit_bp,
                            page_index=page_index, context_type="table_header", source_line=source_line
                        ))
                        candidates.append(Candidate(
                            label_text="Diastolic BP", value_text=bp_m.group(2), unit_text=unit_bp,
                            page_index=page_index, context_type="table_header", source_line=source_line
                        ))
                        continue

                    candidates.append(Candidate(
                        label_text=label,
                        value_text=val_str,
                        unit_text=_clean_unit(unit),
                        page_index=page_index,
                        context_type="table_header",
                        source_line=source_line,
                    ))
            return candidates
        else:
            # Assume first two columns are label, value
            col_map = {"test": 0, "result": 1, "unit": 2}
            data_rows = table

        test_col = col_map.get("test", 0)
        result_col = col_map.get("result", 1)
        unit_col = col_map.get("unit")

        for row in data_rows:
            if len(row) <= test_col:
                continue

            label = row[test_col].strip() if test_col < len(row) else ""
            curr_result_col = result_col
            curr_unit_col = unit_col

            # Detect 3-column colon table: ["Weight", ":", "69 Kgs"]
            if curr_result_col < len(row) and row[curr_result_col].strip() in (":", "=", ":=", "-"):
                curr_result_col += 1
                curr_unit_col = curr_result_col + 1 if curr_unit_col is not None else curr_result_col + 1

            if len(row) <= curr_result_col:
                continue

            value = row[curr_result_col].strip() if curr_result_col < len(row) else ""
            unit = None
            if curr_unit_col is not None and curr_unit_col < len(row):
                unit = row[curr_unit_col].strip() or None

            # Clean leading colons/equals from value (e.g. ": 69 Kgs" -> "69 Kgs")
            value = re.sub(r"^\s*[:=]\s*", "", value).strip()

            # If value contains embedded unit (e.g. "69 Kgs" or "157 Cms"), split value and unit
            val_unit_m = _VALUE_UNIT_PATTERN.match(value)
            if val_unit_m:
                numeric_val = val_unit_m.group(1)
                unit_part = val_unit_m.group(2).strip() or unit
                value = numeric_val
                unit = unit_part

            if not label or not value:
                continue

            source_line = " | ".join(row)

            # Handle combined Age / Gender cell (e.g. ['Age / Gender', '52 years / Male'])
            if re.search(r"age\s*[\/\\]\s*(gender|sex)", label, re.IGNORECASE) or ("age" in label.lower() and re.search(r"\d+\s*(?:years?|yrs?)\s*[\/\\,]\s*(?:male|female|m|f)", value, re.IGNORECASE)):
                age_m = re.search(r"(\d{1,3})\s*(?:years?|yrs?)", f"{value} {label}", re.IGNORECASE)
                if not age_m:
                    age_m = re.search(r"(\d{1,3})", value)
                if age_m:
                    candidates.append(Candidate(
                        label_text="Age",
                        value_text=age_m.group(1),
                        unit_text="years",
                        page_index=page_index,
                        context_type="table_header" if has_header else "unstructured",
                        source_line=source_line,
                    ))
                gen_m = re.search(r"\b(Male|Female)\b", f"{value} {label}", re.IGNORECASE)
                if not gen_m:
                    gen_m = re.search(r"\b(M|F)\b", value)
                    if gen_m:
                        g_val = "Male" if gen_m.group(1).upper() == "M" else "Female"
                        candidates.append(Candidate(
                            label_text="Gender",
                            value_text=g_val,
                            unit_text=None,
                            page_index=page_index,
                            context_type="table_header" if has_header else "unstructured",
                            source_line=source_line,
                        ))
                else:
                    candidates.append(Candidate(
                        label_text="Gender",
                        value_text=gen_m.group(1).capitalize(),
                        unit_text=None,
                        page_index=page_index,
                        context_type="table_header" if has_header else "unstructured",
                        source_line=source_line,
                    ))
                continue

            candidates.append(Candidate(
                label_text=label,
                value_text=value,
                unit_text=_clean_unit(unit),
                page_index=page_index,
                context_type="table_header" if has_header else "unstructured",
                source_line=source_line,
            ))

        return candidates

    @staticmethod
    def _map_header_columns(header_row: list[str]) -> dict[str, int]:
        """Map header cell text to column indices."""
        col_map: dict[str, int] = {}
        for i, cell in enumerate(header_row):
            lower = cell.strip().lower()
            if lower in ("test", "parameter", "analyte", "component"):
                col_map.setdefault("test", i)
            elif lower in ("result", "value"):
                col_map.setdefault("result", i)
            elif lower in ("unit", "units"):
                col_map.setdefault("unit", i)
        # Default fallbacks
        col_map.setdefault("test", 0)
        col_map.setdefault("result", 1)
        return col_map

    def _extract_from_text(
        self,
        raw_text: str,
        page_index: int,
    ) -> list[Candidate]:
        """Extract candidates from raw_text.

        Handles:
        - OCR line splits (e.g. 'Height' on line N, ': 178 cm' on line N+1)
        - Multi-line lab outputs (e.g. 'HbA1c' -> '6.2' -> '%')
        - BP '128/82 mmHg' → two candidates (Systolic, Diastolic)
        - Height '5'10"' → candidate with unit_text 'ft_in'
        """
        candidates: list[Candidate] = []
        # Pre-split single long lines (> 120 chars) before common field headers (unless CSV line)
        if any(len(l) > 120 and "," not in l for l in raw_text.splitlines()):
            pattern = r"\b(?=Height|Weight|BMI|Waist circumference|Systolic BP|Diastolic BP|Fasting blood glucose|HbA1c|LDL cholesterol|HDL cholesterol|Triglycerides|ALT|AST|Family history|Age\s*[\/\\]\s*Gender|Age|Gender|Patient ID|Report ID|Collection date|RESULTS)"
            raw_text = re.sub(pattern, "\n", raw_text, flags=re.IGNORECASE)

        raw_lines = [l.strip() for l in raw_text.split("\n") if l.strip()]

        # ── Step 0: Check for CSV or Space/Tab-delimited Wide Table formatted text ──
        if len(raw_lines) >= 2:
            if "," in raw_text and ("name" in raw_text.lower() or "age" in raw_text.lower() or "gender" in raw_text.lower()):
                csv_lines = [l.strip() for l in raw_text.split("\n") if "," in l]
                if len(csv_lines) >= 2:
                    headers = [h.strip() for h in csv_lines[0].split(",")]
                    for csv_row in csv_lines[1:]:
                        vals = [v.strip() for v in csv_row.split(",")]
                        if len(vals) == len(headers):
                            for h, v in zip(headers, vals):
                                if h and v and v.lower() not in ("nan", "n/a", "na", "null", "none", "", "-"):
                                    if "pressure" in h.lower() or "bp" in h.lower():
                                        bp_m = _BP_PATTERN.search(v)
                                        if bp_m:
                                            candidates.append(Candidate(
                                                label_text="Systolic BP", value_text=bp_m.group(1), unit_text="mmHg",
                                                page_index=page_index, context_type="table_header", source_line=f"{h}: {v}"
                                            ))
                                            candidates.append(Candidate(
                                                label_text="Diastolic BP", value_text=bp_m.group(2), unit_text="mmHg",
                                                page_index=page_index, context_type="table_header", source_line=f"{h}: {v}"
                                            ))
                                            continue
                                    candidates.append(Candidate(
                                        label_text=h, value_text=v, unit_text=None,
                                        page_index=page_index, context_type="table_header", source_line=f"{h}: {v}"
                                    ))

            first_line_tokens = raw_lines[0].split()
            if len(first_line_tokens) >= 3 and any(k in raw_lines[0].lower() for k in ("age", "gender", "height", "weight", "bmi", "systolic", "diastolic", "glucose", "hba1c", "ldl", "hdl", "triglycerides", "alt", "ast", "family_history", "patient_id")):
                headers = first_line_tokens
                for row_line in raw_lines[1:]:
                    vals = row_line.split()
                    if len(vals) == len(headers):
                        for h, v in zip(headers, vals):
                            if h and v and v.lower() not in ("nan", "n/a", "na", "null", "none", "", "-"):
                                unit = None
                                unit_m = re.search(r"[\(_](cm|kg|mmHg|mg/dL|g/dL|U/L|mmol/L|%|in|lbs)[_\)]?$", h, re.IGNORECASE)
                                if unit_m:
                                    unit = unit_m.group(1)

                                bp_m = _BP_PATTERN.search(v)
                                if bp_m and ("pressure" in h.lower() or "bp" in h.lower() or "/" in v):
                                    candidates.append(Candidate(
                                        label_text="Systolic BP", value_text=bp_m.group(1), unit_text=unit or "mmHg",
                                        page_index=page_index, context_type="table_header", source_line=f"{h}: {v}"
                                    ))
                                    candidates.append(Candidate(
                                        label_text="Diastolic BP", value_text=bp_m.group(2), unit_text=unit or "mmHg",
                                        page_index=page_index, context_type="table_header", source_line=f"{h}: {v}"
                                    ))
                                    continue
                                candidates.append(Candidate(
                                    label_text=h, value_text=v, unit_text=_clean_unit(unit),
                                    page_index=page_index, context_type="table_header", source_line=f"{h}: {v}"
                                ))

        # ── Step 1: Normalize OCR line breaks (join label + colon-value & split BP) ──
        normalized_lines: list[tuple[str, int]] = []
        i = 0
        while i < len(raw_lines):
            curr = raw_lines[i]
            curr_lower = curr.lower().strip()

            # Multi-pair line with inline field keywords (e.g. "Jane Doe HD930304 BMI 19.2 Waist 26 in")
            if re.search(r"\b(bmi|waist|height|weight|age|gender|sex|bp)\b", curr, re.IGNORECASE):
                sub_parts = [p.strip() for p in re.split(r"\s+(?=\b(?:BMI|Waist|Height|Weight|Age|Gender|Sex|(?<!Systolic\s)(?<!Diastolic\s)BP|DOB|Patient ID)\b)", curr, flags=re.IGNORECASE) if p and p.strip()]
                if len(sub_parts) > 1:
                    for p in sub_parts:
                        age_m = re.search(r"\((\d{1,3})\s*(?:yrs|years|yo|yr|years old)\)", p, re.IGNORECASE)
                        if age_m:
                            normalized_lines.append((f"Age: {age_m.group(1)} years", i))
                        normalized_lines.append((p, i))
                    i += 1
                    continue

            # Extract standalone inline "(24 yrs)" or "(Age 45)"
            inline_age = re.search(r"\((\d{1,3})\s*(?:yrs|years|yo|yr|years old)\)", curr, re.IGNORECASE)
            if inline_age:
                normalized_lines.append((f"Age: {inline_age.group(1)} years", i))

            # Multi-pair line with pipe, tab, or double-space having multiple colons (e.g. "Age:46Y  Sex:M" or "Ht:179cm  Wt:83kg")
            if curr.count(":") >= 2 or curr.count("=") >= 2 or "|" in curr or "\t" in curr:
                parts = [p.strip() for p in re.split(r"\s*\|\s*|\s{2,}|\t+", curr) if p.strip()]
                if len(parts) > 1 and any(":" in p or "=" in p for p in parts):
                    for part in parts:
                        # Extract inline "(Age 45)" if present
                        age_m = re.search(r"\(age\s*(\d+)\)", part, re.IGNORECASE)
                        if age_m:
                            normalized_lines.append((f"Age: {age_m.group(1)} years", i))
                        normalized_lines.append((part, i))
                    i += 1
                    continue

            # Special case "Age / Gender : 48 Yrs / Male" or "Age/Sex: 45 / Male" or "58Y/Female"
            if re.search(r"\bage\s*[\/\\]\s*(gender|sex)\b", curr_lower):
                if i + 1 < len(raw_lines) and not re.search(r"[:=]", curr):
                    joined = f"{curr} : {raw_lines[i + 1]}"
                    normalized_lines.append((joined, i))
                    i += 2
                    continue
                ag_match = re.match(r"^age\s*[\/\\]\s*(gender|sex)\s*[:=]\s*(\d+)\s*(?:yrs|years|yo|yr|y)?\s*[\/\\]\s*(\w+)", curr_lower)
                if ag_match:
                    normalized_lines.append((f"Age: {ag_match.group(2)} years", i))
                    normalized_lines.append((f"Gender: {ag_match.group(3)}", i))
                    i += 1
                    continue

            # Check for label + colon line: e.g. "Height" + ": 178 cm" (skip reference range lines)
            if not curr.strip().startswith("(") and i + 1 < len(raw_lines) and re.match(r"^\s*[:=]\s*", raw_lines[i + 1]):
                joined = f"{curr} {raw_lines[i + 1]}"
                normalized_lines.append((joined, i))
                i += 2
                continue
            # Check for BP label + BP value on next line: e.g. "Blood Pressure" + "118/76 mmHg"
            if curr_lower in ("blood pressure", "bp", "b.p.", "b.p", "systolic/diastolic", "blood pressure (mmhg)") and i + 1 < len(raw_lines):
                if _BP_PATTERN.search(raw_lines[i + 1]):
                    joined = f"{curr} : {raw_lines[i + 1]}"
                    normalized_lines.append((joined, i))
                    i += 2
                    continue
            # Check for split BP lines: e.g. "Blood Pressure" + "128" + "/" + "82" + "mmHg"
            if curr_lower in ("blood pressure", "bp", "b.p.", "b.p", "blood pressure (mmhg)") and i + 3 < len(raw_lines):
                l1, l2, l3 = raw_lines[i + 1], raw_lines[i + 2], raw_lines[i + 3]
                if re.match(r"^\d{2,3}$", l1) and l2 == "/" and re.match(r"^\d{2,3}$", l3):
                    unit_str = raw_lines[i + 4] if (i + 4 < len(raw_lines) and "mmhg" in raw_lines[i + 4].lower()) else "mmHg"
                    joined = f"{curr} : {l1}/{l3} {unit_str}"
                    normalized_lines.append((joined, i))
                    i += 5 if "mmhg" in unit_str.lower() else 4
                    continue
            normalized_lines.append((curr, i))
            i += 1

        total_lines = len(normalized_lines)

        # ── Step 2: Line-by-line label-value pattern extraction ──
        for line_idx, (raw_stripped, original_idx) in enumerate(normalized_lines):
            # Clean divider lines and leading bullet/asterisk symbols (*, •, +, -)
            stripped = re.sub(r"^[\s*•+\-:]+", "", re.sub(r"\s*[=\-_*]{3,}.*$", "", raw_stripped)).strip()
            if not stripped:
                continue

            context = _classify_context(raw_text, line_idx, total_lines)

            label = None
            value_part = None

            match = _LABEL_VALUE_PATTERN.match(stripped)
            if match:
                label = match.group(1).strip()
                value_part = match.group(2).strip()
            elif "  " in stripped or "\t" in stripped:
                parts = [p.strip() for p in re.split(r"\s{2,}|\t+", stripped) if p.strip()]
                if len(parts) >= 2 and re.match(r"^[A-Za-z]", parts[0]):
                    label = parts[0]
                    value_part = " ".join(parts[1:])

            if label and value_part:
                label = re.sub(r"^[\s*•+\-:]+", "", label).strip()

                # Compact Age/Gender pattern in patient headers e.g. "A.SRINIVAS 49Y/M" or "49 Y/M"
                compact_ag = re.search(r"\b(\d{1,3})\s*Y(?:rs?|ears?)?\s*[\/\\]\s*(M|F|Male|Female)\b", stripped, re.IGNORECASE)
                if compact_ag:
                    candidates.append(Candidate(
                        label_text="Age",
                        value_text=compact_ag.group(1),
                        unit_text="years",
                        page_index=page_index,
                        context_type=context,
                        source_line=stripped,
                    ))
                    g_raw = compact_ag.group(2).strip().upper()
                    g_val = "Female" if g_raw in ("F", "FEMALE") else "Male"
                    candidates.append(Candidate(
                        label_text="Gender",
                        value_text=g_val,
                        unit_text=None,
                        page_index=page_index,
                        context_type=context,
                        source_line=stripped,
                    ))

                # Special case: BP combined reading
                bp_match = _BP_PATTERN.search(value_part)
                if bp_match and ("blood pressure" in label.lower() or "bp" in label.lower() or "b.p." in label.lower() or "systolic/diastolic" in label.lower()):
                    remainder = value_part[bp_match.end():].strip()
                    unit = _clean_unit(remainder) if remainder else "mmHg"

                    candidates.append(Candidate(
                        label_text="Systolic BP",
                        value_text=bp_match.group(1),
                        unit_text=unit,
                        page_index=page_index,
                        context_type=context,
                        source_line=stripped,
                    ))
                    candidates.append(Candidate(
                        label_text="Diastolic BP",
                        value_text=bp_match.group(2),
                        unit_text=unit,
                        page_index=page_index,
                        context_type=context,
                        source_line=stripped,
                    ))
                    continue

                # Special case: Feet/inches height
                ft_match = _FT_IN_PATTERN.search(value_part)
                if ft_match and label.lower() in (
                    "height", "ht", "height (cm)", "pt height",
                ):
                    candidates.append(Candidate(
                        label_text=label,
                        value_text=value_part,
                        unit_text="ft_in",
                        page_index=page_index,
                        context_type=context,
                        source_line=stripped,
                    ))
                    continue

                # Special case: Gender/Sex / Age/Gender — extract gender and age tokens
                # Handles lines like "Age / Gender 52 years / Male" or "Age /Gender 49years/Female"
                if re.search(r"age\s*[\/\\]\s*(gender|sex)", label, re.IGNORECASE) or label.lower().strip() in ("gender", "sex", "gcnder"):
                    age_m = re.search(r"(\d{1,3})\s*(?:years?|yrs?)", value_part, re.IGNORECASE)
                    if not age_m and ("age" in label.lower() or "year" in value_part.lower()):
                        age_m = re.search(r"(\d{1,3})", value_part)
                    if age_m:
                        candidates.append(Candidate(
                            label_text="Age",
                            value_text=age_m.group(1),
                            unit_text="years",
                            page_index=page_index,
                            context_type=context,
                            source_line=stripped,
                        ))

                    gender_m = re.search(r"\b(Female|Male|F|M)\b", value_part, re.IGNORECASE)
                    if gender_m:
                        g_raw = gender_m.group(1).strip()
                        g_val = "Female" if g_raw.upper() in ("F", "FEMALE") else "Male"
                        candidates.append(Candidate(
                            label_text="Gender",
                            value_text=g_val,
                            unit_text=None,
                            page_index=page_index,
                            context_type=context,
                            source_line=stripped,
                        ))
                        continue

                # If label is Glucose and report text / surrounding context contains 'fasting'
                if label.lower().strip() == "glucose" and "fasting" in raw_text.lower():
                    label = "Glucose (Fasting)"

                # General case: value + optional unit
                vm = _VALUE_UNIT_PATTERN.match(value_part)
                if vm:
                    value_text = vm.group(1)
                    unit_text = _clean_unit(vm.group(2))
                    if not unit_text and label:
                        u_m = re.search(r"\((mg/dL|U/L|g/dL|mmol/L|kg|cm|mmHg|%|hours|bpm|steps/day|kcal/day|index|in|lbs|ft_in)\)", label, re.IGNORECASE)
                        if u_m:
                            unit_text = u_m.group(1)
                    candidates.append(Candidate(
                        label_text=label,
                        value_text=value_text,
                        unit_text=unit_text,
                        page_index=page_index,
                        context_type=context,
                        source_line=stripped,
                    ))
                else:
                    # Skip non-numeric labels that would produce garbage candidates
                    if label.lower().strip() in _NON_NUMERIC_LABELS:
                        continue
                    unit_text = None
                    if label:
                        u_m = re.search(r"\((mg/dL|U/L|g/dL|mmol/L|kg|cm|mmHg|%|hours|bpm|steps/day|kcal/day|index|in|lbs|ft_in)\)", label, re.IGNORECASE)
                        if u_m:
                            unit_text = u_m.group(1)
                    candidates.append(Candidate(
                        label_text=label,
                        value_text=value_part,
                        unit_text=unit_text,
                        page_index=page_index,
                        context_type=context,
                        source_line=stripped,
                    ))

        # ── Step 3: Consecutive multi-line OCR pattern extraction ──
        # Handles OCR output where label, value, unit are on separate lines:
        # e.g., Line i: "Gender", Line i+1: "Female"
        # e.g., Line i-1: "6.2" / "%", Line i: "HbA1c", Line i+1: "4.0 - 5.6"
        for i in range(len(raw_lines)):
            curr_line = raw_lines[i]
            curr_lower = curr_line.lower().strip()

            # Check if curr_line looks like a non-numeric analyte/field label
            if not _LABEL_VALUE_PATTERN.match(curr_line) and not re.match(r"^[+-]?\d+\.?\d*$", curr_line):
                val_text = None
                unit_text = None

                # Special handling for Blood Pressure
                if curr_lower in ("blood pressure", "bp", "b.p.", "b.p", "blood pressure (mmhg)"):
                    if i + 1 < len(raw_lines):
                        bp_m = _BP_PATTERN.search(raw_lines[i + 1])
                        if bp_m:
                            context = _classify_context(raw_text, i, len(raw_lines))
                            unit_str = "mmHg"
                            candidates.append(Candidate(
                                label_text="Systolic BP", value_text=bp_m.group(1), unit_text=unit_str,
                                page_index=page_index, context_type=context, source_line=f"{curr_line} {raw_lines[i + 1]}"
                            ))
                            candidates.append(Candidate(
                                label_text="Diastolic BP", value_text=bp_m.group(2), unit_text=unit_str,
                                page_index=page_index, context_type=context, source_line=f"{curr_line} {raw_lines[i + 1]}"
                            ))
                            continue

                # Special handling for Family History section (e.g. "Family History of" followed by "Diabetes No")
                if "family history" in curr_lower:
                    for j in range(i + 1, min(len(raw_lines), i + 7)):
                        next_l = raw_lines[j].strip()
                        if not next_l or next_l.startswith("==") or next_l.startswith("--"):
                            break
                        fh_m = re.match(r"^(diabetes|obesity|hypertension|high blood pressure|fatty liver|nafld|heart disease|cancer)\s*[:=]?\s*(yes|no|positive|negative|\+|\-)", next_l, re.IGNORECASE)
                        if fh_m:
                            context = _classify_context(raw_text, j, len(raw_lines))
                            candidates.append(Candidate(
                                label_text=f"Family History of {fh_m.group(1)}",
                                value_text=fh_m.group(2).capitalize(),
                                unit_text=None,
                                page_index=page_index,
                                context_type=context,
                                source_line=f"Family History of {next_l}",
                            ))

                # Special handling for categorical/text labels like "Gender"
                if any(k in curr_lower for k in ("gender", "sex")):
                    if i + 1 < len(raw_lines):
                        next_line = raw_lines[i + 1].strip()
                        m_gen = re.match(r"^\s*([FM]|Female|Male)\b", next_line, re.IGNORECASE)
                        if m_gen:
                            g_val = m_gen.group(1).upper()
                            val_text = "Female" if g_val in ("F", "FEMALE") else ("Male" if g_val in ("M", "MALE") else next_line)
                        elif not _LABEL_VALUE_PATTERN.match(next_line) and not re.match(r"^[+-]?\d+\.?\d*$", next_line):
                            val_text = next_line
                    if val_text:
                        context = _classify_context(raw_text, i, len(raw_lines))
                        candidates.append(Candidate(
                            label_text="Gender",
                            value_text=val_text,
                            unit_text=None,
                            page_index=page_index,
                            context_type=context,
                            source_line=f"{curr_line} {val_text}".strip(),
                        ))
                    continue

                # Option A: Check forward line (i+1) if it's a single number (not a range like 4.0 - 5.6 or <150)
                if i + 1 < len(raw_lines):
                    next_line = raw_lines[i + 1]
                    if not re.search(r"[-–<>]", next_line):
                        val_match = re.match(r"^([+-]?\d+\.?\d*)\s*(.*)$", next_line)
                        if val_match:
                            val_text = val_match.group(1)
                            unit_text = val_match.group(2).strip() or None
                            if not unit_text and i + 2 < len(raw_lines):
                                possible_unit = raw_lines[i + 2]
                                if possible_unit in ("%", "mg/dL", "U/L", "g/dL", "mmol/L", "kg", "cm", "mmHg"):
                                    unit_text = possible_unit

                # Option B: Check backward lines (i-1, i-2) if forward failed or was a range
                if not val_text and i > 0:
                    for prev_idx in range(i - 1, max(-1, i - 3), -1):
                        prev_line = raw_lines[prev_idx]
                        if not re.search(r"[-–<>]", prev_line):
                            val_match = re.match(r"^([+-]?\d+\.?\d*)\s*(.*)$", prev_line)
                            if val_match:
                                val_text = val_match.group(1)
                                unit_text = val_match.group(2).strip() or None
                                # Check line near prev_line for unit
                                if not unit_text and prev_idx + 1 < len(raw_lines):
                                    pu = raw_lines[prev_idx + 1]
                                    if pu in ("%", "mg/dL", "U/L", "g/dL", "mmol/L", "kg", "cm", "mmHg"):
                                        unit_text = pu
                                break

                if val_text:
                    if not unit_text and curr_line:
                        u_m = re.search(r"\((mg/dL|U/L|g/dL|mmol/L|kg|cm|mmHg|%|hours|bpm|steps/day|kcal/day|index|in|lbs|ft_in)\)", curr_line, re.IGNORECASE)
                        if u_m:
                            unit_text = u_m.group(1)
                    context = _classify_context(raw_text, i, len(raw_lines))
                    candidates.append(Candidate(
                        label_text=curr_line,
                        value_text=val_text,
                        unit_text=unit_text,
                        page_index=page_index,
                        context_type=context,
                        source_line=f"{curr_line} {val_text} {unit_text or ''}".strip(),
                    ))

        # ── Step 4: Infer candidates for unlabeled lines under section headers ──
        current_section = None
        sec_lines: list[tuple[str, str, str | None]] = []

        b_map = ["Fasting Blood Glucose", "HbA1c", "LDL Cholesterol", "HDL Cholesterol", "Triglycerides", "ALT", "AST"]
        w_map = ["Average Daily Steps", "Active Minutes", "Sedentary Time", "Resting Heart Rate", "Sleep Duration", "Calories Burned", "Average Glucose", "Glucose Variability", "Time In Range", "Time Above Range"]
        g_map = ["Akkermansia", "Faecalibacterium", "Bifidobacterium", "Roseburia", "Alistipes", "Escherichia_Shigella", "Collinsella", "Prevotella", "Blautia", "Shannon Diversity Index"]
        p_map = ["Age", "Gender", "Height", "Weight", "Waist Circumference"]

        for line in raw_lines:
            l_lower = line.lower().strip()
            if "biochemistry" in l_lower or "biochem" in l_lower:
                current_section = "biochemistry"
                sec_lines = []
                continue
            elif "google fit" in l_lower or "fitbit" in l_lower or "wearable" in l_lower:
                current_section = "wearable"
                sec_lines = []
                continue
            elif "gut profile" in l_lower or "microbiome" in l_lower or "gut report" in l_lower:
                current_section = "gut"
                sec_lines = []
                continue
            elif "vitals section" in l_lower:
                current_section = "vitals"
                sec_lines = []
                continue
            elif l_lower.startswith("==") or l_lower.startswith("--"):
                continue

            # Only process lines that are purely unlabeled numbers/values
            if current_section and not _LABEL_VALUE_PATTERN.match(line):
                # Ensure line is purely numeric value + unit or categorical, not a label name
                if re.match(r"^\d", line.strip()) or line.strip() in ("Male", "Female", "M", "F", "Yes", "No"):
                    vm = _VALUE_UNIT_PATTERN.match(line)
                    if vm:
                        v_text = vm.group(1)
                        u_text = _clean_unit(vm.group(2))
                        sec_lines.append((line, v_text, u_text))
                    elif line.strip() in ("Male", "Female", "M", "F", "Yes", "No"):
                        sec_lines.append((line, line.strip(), None))

                    idx = len(sec_lines) - 1
                    if idx >= 0:
                        target_map = None
                        if current_section == "biochemistry":
                            target_map = b_map
                        elif current_section == "wearable":
                            target_map = w_map
                        elif current_section == "gut":
                            target_map = g_map
                        elif current_section == "patient":
                            target_map = p_map

                        if target_map and idx < len(target_map):
                            lbl = target_map[idx]
                            orig, val, unt = sec_lines[idx]
                            candidates.append(Candidate(
                                label_text=lbl, value_text=val, unit_text=unt,
                                page_index=page_index, context_type="lab_report_section", source_line=orig
                            ))

        return candidates
