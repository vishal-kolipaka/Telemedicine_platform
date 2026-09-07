"""
generate_7_test_reports.py — Generates 7 authentic, hospital-styled PDF reports
based on the Apollo Clinic reference report template.

The 7 files produced:
  01_Clinical_Only.pdf
  02_Gut_Only.pdf
  03_Wearable_Only.pdf
  04_Clinical_Gut.pdf
  05_Clinical_Wearable.pdf
  06_Gut_Wearable.pdf
  07_Clinical_Gut_Wearable_Full.pdf
"""

import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas

OUTPUT_DIR = os.path.join(os.getcwd(), "generated_test_reports")
ASSETS_DIR = os.path.join(os.getcwd(), "extracted_ref_assets")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Asset paths
HEADER_IMG = os.path.join(ASSETS_DIR, "p1_img1_4.png")
FOOTER_IMG = os.path.join(ASSETS_DIR, "p1_img3_6.jpeg")

# Palette matching Apollo Clinic reference
COLOR_TEAL = colors.HexColor("#007A87")
COLOR_DARK_BLUE = colors.HexColor("#0F2942")
COLOR_SLATE = colors.HexColor("#334155")
COLOR_LIGHT_BG = colors.HexColor("#F8FAFC")
COLOR_BORDER = colors.HexColor("#CBD5E1")
COLOR_AMBER = colors.HexColor("#D97706")
COLOR_ROSE = colors.HexColor("#E11D48")


class NumberedCanvas(canvas.Canvas):
    """Adds running headers, footers, and page numbers to every page."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        
        # Header image banner (top)
        if os.path.exists(HEADER_IMG):
            self.drawImage(HEADER_IMG, 36, 735, width=140, height=45, preserveAspectRatio=True, mask='auto')
        
        # Header text
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(COLOR_TEAL)
        self.drawRightString(576, 765, "APOLLO CLINIC COMPREHENSIVE HEALTH REPORT")
        self.setFont("Helvetica", 7)
        self.setFillColor(COLOR_SLATE)
        self.drawRightString(576, 753, "National Accreditation Board for Testing & Calibration Laboratories (NABL)")
        self.setStrokeColor(COLOR_TEAL)
        self.setLineWidth(0.75)
        self.line(36, 732, 576, 732)

        # Footer divider and footer image
        self.setStrokeColor(COLOR_BORDER)
        self.setLineWidth(0.5)
        self.line(36, 50, 576, 50)
        
        if os.path.exists(FOOTER_IMG):
            self.drawImage(FOOTER_IMG, 36, 12, width=280, height=35, preserveAspectRatio=True, mask='auto')

        self.setFont("Helvetica", 7)
        self.setFillColor(COLOR_SLATE)
        self.drawRightString(576, 32, f"Page {self._pageNumber} of {page_count}")
        self.drawRightString(576, 22, "Confidential Medical Diagnostic Document — Apollo Diagnostics")
        
        self.restoreState()


def get_styles():
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        'CoverTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=COLOR_DARK_BLUE,
        alignment=0,
        spaceAfter=8
    ))
    
    styles.add(ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=COLOR_TEAL,
        alignment=0,
        spaceAfter=15
    ))

    styles.add(ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=COLOR_TEAL,
        spaceBefore=10,
        spaceAfter=6
    ))

    styles.add(ParagraphStyle(
        'SubSectionHeader',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=COLOR_DARK_BLUE,
        spaceBefore=6,
        spaceAfter=4
    ))

    styles.add(ParagraphStyle(
        'ReportText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=COLOR_SLATE
    ))

    styles.add(ParagraphStyle(
        'ReportTextBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=COLOR_DARK_BLUE
    ))

    styles.add(ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=0
    ))

    styles.add(ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=COLOR_SLATE
    ))

    styles.add(ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=10,
        textColor=COLOR_DARK_BLUE
    ))

    styles.add(ParagraphStyle(
        'TableCellFlagged',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=10,
        textColor=COLOR_ROSE
    ))

    return styles


def create_patient_header_table(patient_info, styles):
    """Creates top patient demographic bar."""
    data = [
        [
            Paragraph(f"<b>Patient Name:</b> {patient_info['name']}", styles['TableCell']),
            Paragraph(f"<b>Age:</b> {patient_info['age']} Years", styles['TableCell']),
            Paragraph(f"<b>Gender:</b> {patient_info['gender']}", styles['TableCell']),
        ],
        [
            Paragraph(f"<b>Patient ID:</b> {patient_info['id']}", styles['TableCell']),
            Paragraph(f"<b>Collection Date:</b> {patient_info['date']}", styles['TableCell']),
            Paragraph(f"<b>Report Status:</b> Final Verified", styles['TableCell']),
        ]
    ]
    t = Table(data, colWidths=[180, 180, 180])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 0.75, COLOR_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    return t


def build_lab_table(rows, styles, col_widths=[190, 80, 80, 190]):
    """Standard 4-column lab parameter table."""
    table_data = [[
        Paragraph("TEST PARAMETER", styles['TableHeader']),
        Paragraph("RESULT", styles['TableHeader']),
        Paragraph("UNITS", styles['TableHeader']),
        Paragraph("REFERENCE INTERVAL", styles['TableHeader']),
    ]]
    
    for row in rows:
        name, val, unit, ref, is_flagged = row
        val_style = styles['TableCellFlagged'] if is_flagged else styles['TableCellBold']
        table_data.append([
            Paragraph(name, styles['TableCellBold']),
            Paragraph(str(val), val_style),
            Paragraph(unit, styles['TableCell']),
            Paragraph(ref, styles['TableCell']),
        ])

    t = Table(table_data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_TEAL),
        ('BOX', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_LIGHT_BG]),
    ]))
    return t


def build_report_pdf(filename, patient_info, include_clinical=True, include_gut=False, include_wearable=False):
    pdf_path = os.path.join(OUTPUT_DIR, filename)
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=68,
        bottomMargin=60,
    )
    
    styles = get_styles()
    story = []

    # ═════════════════════════════════════════════════════════════════
    # PAGE 1: COVER & EXECUTIVE HEALTH SUMMARY
    # ═════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 10))
    story.append(Paragraph("APOLLO PROHEALTH COMPREHENSIVE MEDICAL REPORT", styles['CoverTitle']))
    
    subtitle_text = "Integrated Multi-System Diagnostic Evaluation"
    if include_clinical and include_gut and include_wearable:
        subtitle_text = "Comprehensive Clinical, Metagenomic Gut Microbiome & Ambulatory Sensor Diagnostics"
    elif include_clinical and include_gut:
        subtitle_text = "Clinical Biochemistry, Hematology & Gut Microbiome Metagenomic Profile"
    elif include_clinical and include_wearable:
        subtitle_text = "Clinical Biochemistry & Ambulatory Continuous Wearable / CGM Monitoring"
    elif include_gut and include_wearable:
        subtitle_text = "Gut Microbiome Metagenomic & Continuous Ambulatory Physiological Assessment"
    elif include_gut:
        subtitle_text = "Comprehensive Gut Microbiome Metagenomic Sequencing & Abundance Analysis"
    elif include_wearable:
        subtitle_text = "Ambulatory Wearable Sensor & Continuous Glucose Monitoring (CGM) Summary"
    elif include_clinical:
        subtitle_text = "Comprehensive Clinical Biochemistry, Hematology & Metabolic Risk Profile"
    
    story.append(Paragraph(subtitle_text, styles['CoverSubtitle']))
    story.append(create_patient_header_table(patient_info, styles))
    story.append(Spacer(1, 12))

    story.append(Paragraph("EXECUTIVE CLINICAL SUMMARY & INVESTIGATION OUTLINE", styles['SectionHeader']))
    story.append(Paragraph(
        f"Dear {patient_info['name']}, thank you for completing your comprehensive health assessment at Apollo Diagnostics. "
        "This diagnostic report collates your verified laboratory evaluations, physical examinations, and authorized physiological testing. "
        "All investigations have been performed adhering strictly to standardized clinical biochemistry and molecular diagnostics guidelines.",
        styles['ReportText']
    ))
    story.append(Spacer(1, 8))

    # Summary Panel Highlights
    summary_data = [
        [
            Paragraph("<b>Diagnostic Domain</b>", styles['TableHeader']),
            Paragraph("<b>Tests Performed</b>", styles['TableHeader']),
            Paragraph("<b>Evaluation Status</b>", styles['TableHeader']),
        ],
        [
            Paragraph("Clinical Biochemistry & Hematology", styles['TableCellBold']),
            Paragraph("Lipid Profile, Glycaemic Index, LFT, RFT, CBC, Thyroid, Electrolytes" if include_clinical else "Standard Urinalysis & Routine Baseline Only", styles['TableCell']),
            Paragraph("Complete Panel Evaluated" if include_clinical else "Partial / Non-Metabolic Scope", styles['TableCellBold'] if include_clinical else styles['TableCell']),
        ],
        [
            Paragraph("Gut Microbiome Metagenomics", styles['TableCellBold']),
            Paragraph("16S rRNA High-Throughput Taxonomic Relative Abundance (21 Taxa)" if include_gut else "Not Requested / Not Included in this Profile", styles['TableCell']),
            Paragraph("Complete Metagenomic Panel" if include_gut else "Not Available", styles['TableCellBold'] if include_gut else styles['TableCell']),
        ],
        [
            Paragraph("Continuous Ambulatory & Wearable Sensors", styles['TableCellBold']),
            Paragraph("30-Day Ambulatory Activity, HRV, Sleep Architecture & CGM Glycaemic Metrics" if include_wearable else "Not Linked / Not Included in this Profile", styles['TableCell']),
            Paragraph("Complete Sensor Telemetry Evaluated" if include_wearable else "Not Available", styles['TableCellBold'] if include_wearable else styles['TableCell']),
        ],
    ]
    t_sum = Table(summary_data, colWidths=[160, 260, 120])
    t_sum.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_DARK_BLUE),
        ('BOX', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_LIGHT_BG]),
    ]))
    story.append(t_sum)
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Physician Notes:</b> Patient findings must be clinically correlated with patient symptoms, medical history, and clinical follow-up.", styles['ReportText']))

    # ═════════════════════════════════════════════════════════════════
    # PAGE 2: CLINICAL BIOCHEMISTRY (LIPIDS, GLYCAEMIC, THYROID, VITAMINS)
    # ═════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(create_patient_header_table(patient_info, styles))
    story.append(Spacer(1, 8))

    if include_clinical:
        clin = patient_info['clinical']
        story.append(Paragraph("LIPID PROFILE", styles['SectionHeader']))
        story.append(Paragraph("Serum lipid evaluation by enzymatic photometric assay.", styles['ReportText']))
        story.append(Spacer(1, 4))
        
        lipid_rows = [
            ("TOTAL CHOLESTEROL", clin.get('total_chol', 195), "mg/dL", "125 - 200", clin.get('total_chol', 195) > 200),
            ("TRIGLYCERIDES", clin['triglycerides'], "mg/dL", "0 - 150", clin['triglycerides'] > 150),
            ("HDL CHOLESTEROL", clin['hdl'], "mg/dL", "40 - 60", clin['hdl'] < 40),
            ("LDL CHOLESTEROL", clin['ldl'], "mg/dL", "0 - 100", clin['ldl'] > 100),
            ("VLDL CHOLESTEROL", round(clin['triglycerides'] / 5, 1), "mg/dL", "5 - 30", (clin['triglycerides'] / 5) > 30),
            ("NON-HDL CHOLESTEROL", clin.get('total_chol', 195) - clin['hdl'], "mg/dL", "0 - 130", (clin.get('total_chol', 195) - clin['hdl']) > 130),
            ("CHOL / HDL RATIO", round(clin.get('total_chol', 195) / max(1, clin['hdl']), 2), "ratio", "0 - 4.5", (clin.get('total_chol', 195) / max(1, clin['hdl'])) > 4.5),
        ]
        story.append(build_lab_table(lipid_rows, styles))
        story.append(Spacer(1, 8))

        story.append(Paragraph("GLYCAEMIC PROFILE & DIABETES SCREENING", styles['SectionHeader']))
        story.append(Paragraph("Fasting plasma glucose (Hexokinase method) and Glycated Hemoglobin (HPLC method).", styles['ReportText']))
        story.append(Spacer(1, 4))
        
        glyc_rows = [
            ("FASTING BLOOD GLUCOSE", clin['fasting_glucose'], "mg/dL", "70 - 100", clin['fasting_glucose'] > 100),
            ("HbA1c", clin['hba1c'], "%", "4.0 - 5.6", clin['hba1c'] >= 5.7),
            ("ESTIMATED GLUCOSE (eAG)", round((28.7 * clin['hba1c']) - 46.7, 1), "mg/dL", "70 - 126", clin['hba1c'] >= 5.7),
            ("POST PRANDIAL GLUCOSE (2 HR)", clin.get('pp_glucose', 135), "mg/dL", "70 - 140", clin.get('pp_glucose', 135) > 140),
        ]
        story.append(build_lab_table(glyc_rows, styles))
        story.append(Spacer(1, 8))

        story.append(Paragraph("THYROID & ESSENTIAL VITAMINS", styles['SectionHeader']))
        thyroid_rows = [
            ("THYROID STIMULATING HORMONE (TSH)", clin.get('tsh', 2.45), "uIU/mL", "0.35 - 4.94", False),
            ("TOTAL TRIIODOTHYRONINE (T3)", clin.get('t3', 1.12), "ng/mL", "0.70 - 2.04", False),
            ("TOTAL THYROXINE (T4)", clin.get('t4', 7.80), "ug/dL", "5.48 - 14.28", False),
            ("VITAMIN D - 25 HYDROXY", clin.get('vit_d', 22.4), "ng/mL", "30 - 100", True),
            ("VITAMIN B12", clin.get('vit_b12', 280), "pg/mL", "197 - 771", False),
        ]
        story.append(build_lab_table(thyroid_rows, styles))

    else:
        # Non-clinical placeholder routine tests to maintain authentic multi-page appearance
        story.append(Paragraph("ROUTINE PRE-ASSESSMENT SCREENING", styles['SectionHeader']))
        story.append(Paragraph("Routine urinalysis and general biochemical indicators.", styles['ReportText']))
        story.append(Spacer(1, 4))
        routine_rows = [
            ("URINE SPECIFIC GRAVITY", "1.020", "ratio", "1.005 - 1.030", False),
            ("URINE pH", "6.0", "pH", "5.0 - 7.5", False),
            ("URINE PROTEIN", "NEGATIVE", "", "NEGATIVE", False),
            ("URINE GLUCOSE", "NEGATIVE", "", "NEGATIVE", False),
            ("URINE BILIRUBIN", "NEGATIVE", "", "NEGATIVE", False),
            ("URINE UROBILINOGEN", "NORMAL", "", "NORMAL", False),
            ("VITAMIN D - 25 HYDROXY", "24.5", "ng/mL", "30 - 100", True),
            ("VITAMIN B12", "310", "pg/mL", "197 - 771", False),
        ]
        story.append(build_lab_table(routine_rows, styles))

    # ═════════════════════════════════════════════════════════════════
    # PAGE 3: LIVER, RENAL FUNCTION & COMPLETE BLOOD COUNT (CBC)
    # ═════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(create_patient_header_table(patient_info, styles))
    story.append(Spacer(1, 8))

    if include_clinical:
        clin = patient_info['clinical']
        story.append(Paragraph("LIVER FUNCTION TEST (LFT)", styles['SectionHeader']))
        story.append(Paragraph("Hepatic cellular integrity and biliary enzyme panel.", styles['ReportText']))
        story.append(Spacer(1, 4))
        
        lft_rows = [
            ("ALT (SGPT)", clin['alt'], "U/L", "0 - 35", clin['alt'] > 35),
            ("AST (SGOT)", clin['ast'], "U/L", "0 - 35", clin['ast'] > 35),
            ("TOTAL BILIRUBIN", clin.get('bili_total', 0.85), "mg/dL", "0.3 - 1.2", False),
            ("DIRECT BILIRUBIN", clin.get('bili_direct', 0.20), "mg/dL", "0.0 - 0.3", False),
            ("INDIRECT BILIRUBIN", clin.get('bili_indirect', 0.65), "mg/dL", "0.2 - 0.9", False),
            ("ALKALINE PHOSPHATASE (ALP)", clin.get('alp', 72), "U/L", "30 - 120", False),
            ("TOTAL PROTEIN", clin.get('protein_total', 7.4), "g/dL", "6.6 - 8.3", False),
            ("ALBUMIN", clin.get('albumin', 4.3), "g/dL", "3.5 - 5.2", False),
            ("GLOBULIN", clin.get('globulin', 3.1), "g/dL", "2.0 - 3.5", False),
            ("A/G RATIO", round(clin.get('albumin', 4.3) / max(0.1, clin.get('globulin', 3.1)), 2), "ratio", "0.9 - 2.0", False),
        ]
        story.append(build_lab_table(lft_rows, styles))
        story.append(Spacer(1, 8))

        story.append(Paragraph("RENAL PROFILE / KIDNEY FUNCTION TEST (RFT/KFT)", styles['SectionHeader']))
        rft_rows = [
            ("SERUM CREATININE", clin.get('creatinine', 0.92), "mg/dL", "0.70 - 1.20", False),
            ("BLOOD UREA NITROGEN (BUN)", clin.get('bun', 14.5), "mg/dL", "8.0 - 23.0", False),
            ("SERUM UREA", clin.get('urea', 31.0), "mg/dL", "17.0 - 43.0", False),
            ("SERUM URIC ACID", clin.get('uric_acid', 5.4), "mg/dL", "3.5 - 7.2", False),
            ("SODIUM", 140, "mmol/L", "136 - 146", False),
            ("POTASSIUM", 4.3, "mmol/L", "3.5 - 5.1", False),
            ("CHLORIDE", 102, "mmol/L", "101 - 109", False),
            ("CALCIUM", 9.6, "mg/dL", "8.8 - 10.6", False),
        ]
        story.append(build_lab_table(rft_rows, styles))

    # Complete Blood Count (CBC) is included in all reports for genuine clinical realism
    story.append(Spacer(1, 8))
    story.append(Paragraph("COMPLETE BLOOD COUNT (CBC / HEMOGRAM)", styles['SectionHeader']))
    cbc_rows = [
        ("TOTAL LEUCOCYTE COUNT (TLC)", "7,400", "cells/cu.mm", "4,000 - 10,000", False),
        ("HAEMOGLOBIN", "14.2", "g/dL", "13.0 - 17.0", False),
        ("PACKED CELL VOLUME (PCV)", "42.5", "%", "40.0 - 50.0", False),
        ("RBC COUNT", "4.65", "Million/cu.mm", "4.5 - 5.5", False),
        ("MCV", "89.2", "fL", "83.0 - 101.0", False),
        ("MCH", "30.1", "pg", "27.0 - 32.0", False),
        ("MCHC", "33.8", "g/dL", "31.5 - 34.5", False),
        ("NEUTROPHILS", "58.4", "%", "40.0 - 75.0", False),
        ("LYMPHOCYTES", "32.1", "%", "20.0 - 40.0", False),
        ("MONOCYTES", "5.8", "%", "2.0 - 10.0", False),
        ("EOSINOPHILS", "3.1", "%", "1.0 - 6.0", False),
        ("BASOPHILS", "0.6", "%", "0.0 - 2.0", False),
        ("PLATELET COUNT", "245,000", "cells/cu.mm", "150,000 - 410,000", False),
    ]
    story.append(build_lab_table(cbc_rows, styles))

    # ═════════════════════════════════════════════════════════════════
    # PAGE 4: PHYSICAL EXAMINATION, ANTHROPOMETRICS & VITALS
    # ═════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(create_patient_header_table(patient_info, styles))
    story.append(Spacer(1, 8))

    story.append(Paragraph("PHYSICAL EXAMINATION, VITALS & ANTHROPOMETRIC MEASUREMENTS", styles['SectionHeader']))
    story.append(Paragraph("Standardized clinical biometrics and physiological vitals recorded during examination.", styles['ReportText']))
    story.append(Spacer(1, 6))

    if include_clinical:
        clin = patient_info['clinical']
        ht = int(clin['height'])
        wt = int(clin['weight'])
        bmi = clin['bmi']
        wc = int(clin['waist'])
        sbp = int(clin['systolic_bp'])
        dbp = int(clin['diastolic_bp'])

        vitals_table_data = [
            ("Height", ht, "cm", "Adult Baseline", False),
            ("Weight", wt, "kg", "Adult Baseline", False),
            ("Body Mass Index (BMI)", bmi, "kg/m²", "18.5 - 24.9", bmi >= 25),
            ("Waist Circumference", wc, "cm", "< 90", wc >= 90),
            ("Systolic Blood Pressure", sbp, "mmHg", "< 120", sbp >= 130),
            ("Diastolic Blood Pressure", dbp, "mmHg", "< 80", dbp >= 85),
            ("Resting Pulse Rate", clin.get('pulse', 76), "bpm", "60 - 100", False),
            ("Oxygen Saturation (SpO2)", 98, "%", "95 - 100", False),
            ("Body Temperature", 98.4, "°F", "97.0 - 99.0", False),
        ]
        story.append(build_lab_table(vitals_table_data, styles))
        story.append(Spacer(1, 8))

        # Personal & Family History Table
        story.append(Paragraph("PERSONAL & FAMILY MEDICAL HISTORY", styles['SectionHeader']))
        fh_diabetes = clin.get('fh_diabetes', 'No')
        fh_htn = clin.get('fh_hypertension', 'No')
        fh_cvd = clin.get('fh_cvd', 'No')

        fh_data = [
            [
                Paragraph("<b>MEDICAL HISTORY ITEM</b>", styles['TableHeader']),
                Paragraph("<b>STATUS / REPORTED FINDING</b>", styles['TableHeader']),
                Paragraph("<b>CLINICAL RELEVANCE</b>", styles['TableHeader']),
            ],
            [
                Paragraph("Family History of Diabetes", styles['TableCellBold']),
                Paragraph(f"<b>{fh_diabetes}</b>", styles['TableCellFlagged'] if fh_diabetes == 'Yes' else styles['TableCellBold']),
                Paragraph("First-degree blood relative with Type 2 Diabetes Mellitus", styles['TableCell']),
            ],
            [
                Paragraph("Family History of Hypertension", styles['TableCellBold']),
                Paragraph(f"<b>{fh_htn}</b>", styles['TableCellFlagged'] if fh_htn == 'Yes' else styles['TableCellBold']),
                Paragraph("First-degree blood relative with diagnosed Essential Hypertension", styles['TableCell']),
            ],
            [
                Paragraph("Family History of CVD", styles['TableCellBold']),
                Paragraph(f"<b>{fh_cvd}</b>", styles['TableCellFlagged'] if fh_cvd == 'Yes' else styles['TableCellBold']),
                Paragraph("Family history of early coronary artery disease or stroke", styles['TableCell']),
            ],
        ]
        t_fh = Table(fh_data, colWidths=[200, 120, 220])
        t_fh.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COLOR_DARK_BLUE),
            ('BOX', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_LIGHT_BG]),
        ]))
        story.append(t_fh)

    else:
        # Non-clinical report vitals placeholder
        story.append(Paragraph("BASIC CLINICAL ENCOUNTER VITALS", styles['SectionHeader']))
        basic_vitals = [
            ("Resting Pulse Rate", "74", "bpm", "60 - 100", False),
            ("Oxygen Saturation (SpO2)", "99", "%", "95 - 100", False),
            ("Body Temperature", "98.2", "°F", "97.0 - 99.0", False),
            ("Respiration Rate", "16", "breaths/min", "12 - 20", False),
        ]
        story.append(build_lab_table(basic_vitals, styles, col_widths=[200, 80, 80, 180]))

    # ═════════════════════════════════════════════════════════════════
    # PAGE 5: GUT MICROBIOME PANEL (FOR GUT-ENABLED REPORTS)
    # ═════════════════════════════════════════════════════════════════
    if include_gut:
        story.append(PageBreak())
        story.append(create_patient_header_table(patient_info, styles))
        story.append(Spacer(1, 8))

        gut = patient_info['gut']
        story.append(Paragraph("GUT MICROBIOME METAGENOMIC ABUNDANCE PROFILE", styles['SectionHeader']))
        story.append(Paragraph(
            "High-throughput 16S rRNA next-generation sequencing metagenomic analysis of stool specimen. "
            "Relative abundances of bacterial taxa are expressed as percentage of total microbial DNA.",
            styles['ReportText']
        ))
        story.append(Spacer(1, 6))

        taxa_order = [
            ("Akkermansia", "Akkermansia", "0.5 - 5.0 %"),
            ("Faecalibacterium", "Faecalibacterium", "3.0 - 12.0 %"),
            ("Roseburia", "Roseburia", "1.5 - 8.0 %"),
            ("Bifidobacterium", "Bifidobacterium", "1.0 - 7.0 %"),
            ("Bacteroides", "Bacteroides", "10.0 - 30.0 %"),
            ("Prevotella", "Prevotella", "2.0 - 18.0 %"),
            ("Ruminococcus", "Ruminococcus", "2.0 - 10.0 %"),
            ("Blautia", "Blautia", "3.0 - 12.0 %"),
            ("Collinsella", "Collinsella", "0.5 - 5.0 %"),
            ("Escherichia/Shigella", "Escherichia/Shigella", "0.1 - 3.0 %"),
            ("Coprococcus", "Coprococcus", "0.5 - 5.0 %"),
            ("Alistipes", "Alistipes", "1.0 - 6.0 %"),
            ("Subdoligranulum", "Subdoligranulum", "0.5 - 4.0 %"),
            ("Enterococcus", "Enterococcus", "0.1 - 2.0 %"),
            ("Eubacterium", "Eubacterium", "1.0 - 6.0 %"),
            ("Parabacteroides", "Parabacteroides", "0.5 - 5.0 %"),
            ("Lactobacillus", "Lactobacillus", "0.2 - 3.0 %"),
            ("Klebsiella", "Klebsiella", "0.0 - 2.0 %"),
            ("Streptococcus", "Streptococcus", "0.2 - 3.0 %"),
            ("Eggerthella", "Eggerthella", "0.1 - 2.0 %"),
            ("Other Taxa", "Other Taxa", "5.0 - 20.0 %"),
        ]

        total_abundance = sum(gut[k if k != "Escherichia/Shigella" and k != "Other Taxa" else ("Escherichia_Shigella" if k == "Escherichia/Shigella" else "Other_Taxa")] for k, _, _ in taxa_order)

        gut_rows = []
        for key, display, ref in taxa_order:
            dict_key = "Escherichia_Shigella" if key == "Escherichia/Shigella" else ("Other_Taxa" if key == "Other Taxa" else key)
            val = gut[dict_key]
            gut_rows.append((display, f"{val:.2f}", "%", ref, False))

        story.append(build_lab_table(gut_rows, styles))
        story.append(Spacer(1, 6))

        # Additional Non-Model Gut Ecology Parameters
        story.append(Paragraph("MICROBIOME ECOLOGY & STOOL PARAMETERS", styles['SubSectionHeader']))
        stool_metrics = [
            ("Total Relative Abundance Sum", f"{total_abundance:.2f}", "%", "95.0 - 105.0 %", False),
            ("Shannon Diversity Index", f"{patient_info.get('shannon', 3.32):.2f}", "index", "2.80 - 4.20", False),
            ("Bacteroidetes / Firmicutes Ratio", f"{patient_info.get('bf_ratio', 1.35):.2f}", "ratio", "0.80 - 2.50", False),
            ("Fecal Calprotectin", "< 30.0", "mcg/g", "< 50.0", False),
            ("Fecal Occult Blood (FIT)", "NEGATIVE", "", "NEGATIVE", False),
        ]
        story.append(build_lab_table(stool_metrics, styles, col_widths=[220, 80, 60, 180]))

    # ═════════════════════════════════════════════════════════════════
    # PAGE 6: WEARABLE & CGM PANEL (FOR WEARABLE-ENABLED REPORTS)
    # ═════════════════════════════════════════════════════════════════
    if include_wearable:
        story.append(PageBreak())
        story.append(create_patient_header_table(patient_info, styles))
        story.append(Spacer(1, 8))

        wear = patient_info['wearable']
        story.append(Paragraph("CONTINUOUS AMBULATORY PHYSIOMETRICS & CGM GLYCEMIC REPORT", styles['SectionHeader']))
        story.append(Paragraph(
            "Continuous multi-sensor telemetry recorded over a 30-day ambulatory monitoring window. "
            "Aggregates physical activity, autonomic cardiovascular biometrics, sleep architecture, and continuous glucose monitoring (CGM).",
            styles['ReportText']
        ))
        story.append(Spacer(1, 6))

        wearable_rows = [
            ("Average Daily Steps", str(int(wear['steps'])), "steps/day", "> 7500", wear['steps'] < 6000),
            ("Active Minutes", str(int(wear['active_mins'])), "minutes/day", "> 30", wear['active_mins'] < 20),
            ("Sedentary Time", str(int(wear['sedentary_mins'])), "minutes/day", "< 480", wear['sedentary_mins'] > 600),
            ("Resting Heart Rate", str(int(wear['rhr'])), "bpm", "60 - 75", wear['rhr'] > 75),
            ("Heart Rate Variability (RMSSD)", str(int(wear['hrv'])), "ms", "> 35", wear['hrv'] < 30),
            ("Sleep Duration", f"{wear['sleep_hours']:.1f}", "hours", "7.0 - 9.0", wear['sleep_hours'] < 6.5),
            ("Sleep Efficiency Score", str(int(wear['sleep_efficiency'])), "%", "> 85", wear['sleep_efficiency'] < 80),
            ("Autonomic Stress Score", str(int(wear['stress_score'])), "", "< 40", wear['stress_score'] > 50),
            ("Activity Energy Expenditure", str(int(wear['energy_exp'])), "kcal/day", "400 - 800", False),
            ("Exercise Frequency", str(int(wear['exercise_freq'])), "days/week", ">= 3", wear['exercise_freq'] < 3),
            ("CGM Average Glucose", str(int(wear['cgm_avg_glucose'])), "mg/dL", "70 - 120", wear['cgm_avg_glucose'] > 120),
            ("CGM Glucose CV", f"{wear['cgm_cv']:.1f}", "%", "< 36.0", wear['cgm_cv'] > 36),
            ("CGM Time In Range", f"{wear['cgm_tir']:.1f}", "%", "> 70.0", wear['cgm_tir'] < 70),
            ("CGM Time Above Range", f"{wear['cgm_tar']:.1f}", "%", "< 25.0", wear['cgm_tar'] > 25),
            ("CGM Time Below Range", f"{wear['cgm_tbr']:.1f}", "%", "< 4.0", wear['cgm_tbr'] > 4),
        ]
        story.append(build_lab_table(wearable_rows, styles))
        story.append(Spacer(1, 6))

        # Additional Non-Model Wearable Metrics
        story.append(Paragraph("SECONDARY SENSOR & SLEEP ARCHITECTURE METRICS", styles['SubSectionHeader']))
        secondary_wear_rows = [
            ("Total Daily Distance", f"{wear.get('distance', 3.8):.1f}", "km/day", "> 5.0 km/day", False),
            ("Deep Sleep Duration", f"{wear.get('deep_sleep', 16):.0f}", "%", "15 - 25 %", False),
            ("REM Sleep Duration", f"{wear.get('rem_sleep', 19):.0f}", "%", "20 - 25 %", False),
            ("Cardio Fitness Score (VO2 Max Est.)", f"{wear.get('vo2_max', 35):.0f}", "mL/kg/min", "35 - 45", False),
        ]
        story.append(build_lab_table(secondary_wear_rows, styles, col_widths=[220, 70, 70, 180]))

    # Build PDF with NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated: {pdf_path}")
    return pdf_path


def main():
    print("Generating 7 hospital-styled medical reports...")
    
    # ── Report 1: Clinical Only ──────────────────────────────────────────
    # Profile: 54M, Type 2 Diabetes pattern with elevated glycemic labs, dyslipidemia, Stage 1 HTN
    p1 = {
        'name': 'Rajesh Sharma',
        'id': 'P010001',
        'age': 54,
        'gender': 'Male',
        'date': '29-Aug-2026',
        'clinical': {
            'height': 172.0, 'weight': 86.0, 'bmi': 29.07, 'waist': 98.0,
            'systolic_bp': 142.0, 'diastolic_bp': 90.0,
            'fasting_glucose': 148.0, 'hba1c': 7.6,
            'triglycerides': 245.0, 'hdl': 36.0, 'ldl': 152.0, 'total_chol': 237,
            'alt': 48.0, 'ast': 38.0,
            'fh_diabetes': 'Yes', 'fh_hypertension': 'Yes', 'fh_cvd': 'No',
            'creatinine': 0.95, 'bun': 16.0, 'urea': 34.0, 'vit_d': 18.2, 'tsh': 2.65
        }
    }
    build_report_pdf("01_Clinical_Only.pdf", p1, include_clinical=True, include_gut=False, include_wearable=False)

    # ── Report 2: Gut Only ───────────────────────────────────────────────
    # Profile: 46F, Gut dysbiosis with low Akkermansia/Faecalibacterium, elevated Collinsella & Enterobacteria
    p2 = {
        'name': 'Sunita Patel',
        'id': 'P020002',
        'age': 46,
        'gender': 'Female',
        'date': '29-Aug-2026',
        'shannon': 3.12,
        'bf_ratio': 1.45,
        'gut': {
            'Akkermansia': 0.60, 'Faecalibacterium': 3.80, 'Roseburia': 2.40, 'Bifidobacterium': 2.10,
            'Bacteroides': 22.50, 'Prevotella': 11.20, 'Ruminococcus': 6.40, 'Blautia': 7.80,
            'Collinsella': 6.50, 'Escherichia_Shigella': 4.90, 'Coprococcus': 1.80, 'Alistipes': 3.20,
            'Subdoligranulum': 1.50, 'Enterococcus': 2.20, 'Eubacterium': 2.80, 'Parabacteroides': 3.10,
            'Lactobacillus': 1.20, 'Klebsiella': 3.60, 'Streptococcus': 3.10, 'Eggerthella': 2.40,
            'Other_Taxa': 7.00
        }
    }
    build_report_pdf("02_Gut_Only.pdf", p2, include_clinical=False, include_gut=True, include_wearable=False)

    # ── Report 3: Wearable Only ──────────────────────────────────────────
    # Profile: 42M, Sedentary, reduced HRV, suboptimal sleep, elevated CGM glycemic excursions (Prediabetic sensor pattern)
    p3 = {
        'name': 'Vikram Malhotra',
        'id': 'P030003',
        'age': 42,
        'gender': 'Male',
        'date': '29-Aug-2026',
        'wearable': {
            'steps': 4100.0, 'active_mins': 14.0, 'sedentary_mins': 690.0, 'rhr': 76.0, 'hrv': 26.0,
            'sleep_hours': 6.1, 'sleep_efficiency': 72.0, 'stress_score': 65.0,
            'energy_exp': 1850.0, 'exercise_freq': 1.0,
            'cgm_avg_glucose': 122.0, 'cgm_cv': 28.0, 'cgm_tir': 68.0, 'cgm_tar': 29.0, 'cgm_tbr': 3.0,
            'distance': 3.1, 'deep_sleep': 14, 'rem_sleep': 18, 'vo2_max': 34
        }
    }
    build_report_pdf("03_Wearable_Only.pdf", p3, include_clinical=False, include_gut=False, include_wearable=True)

    # ── Report 4: Clinical + Gut ─────────────────────────────────────────
    # Profile: 51F, Metabolic Syndrome & NAFLD profile with elevated triglycerides, low HDL, elevated ALT & dysbiotic gut
    p4 = {
        'name': 'Meera Nambiar',
        'id': 'P040004',
        'age': 51,
        'gender': 'Female',
        'date': '29-Aug-2026',
        'clinical': {
            'height': 160.0, 'weight': 78.0, 'bmi': 30.47, 'waist': 94.0,
            'systolic_bp': 138.0, 'diastolic_bp': 88.0,
            'fasting_glucose': 114.0, 'hba1c': 6.1,
            'triglycerides': 215.0, 'hdl': 41.0, 'ldl': 135.0, 'total_chol': 219,
            'alt': 46.0, 'ast': 37.0,
            'fh_diabetes': 'Yes', 'fh_hypertension': 'Yes', 'fh_cvd': 'No',
            'creatinine': 0.88, 'bun': 14.0, 'urea': 29.0, 'vit_d': 21.0, 'tsh': 2.15
        },
        'shannon': 3.28,
        'bf_ratio': 1.50,
        'gut': {
            'Akkermansia': 1.10, 'Faecalibacterium': 4.20, 'Roseburia': 2.80, 'Bifidobacterium': 3.00,
            'Bacteroides': 20.40, 'Prevotella': 9.80, 'Ruminococcus': 5.60, 'Blautia': 7.40,
            'Collinsella': 5.80, 'Escherichia_Shigella': 4.10, 'Coprococcus': 2.00, 'Alistipes': 3.50,
            'Subdoligranulum': 1.80, 'Enterococcus': 1.90, 'Eubacterium': 3.10, 'Parabacteroides': 2.80,
            'Lactobacillus': 1.60, 'Klebsiella': 3.10, 'Streptococcus': 2.80, 'Eggerthella': 2.10,
            'Other_Taxa': 11.10
        }
    }
    build_report_pdf("04_Clinical_Gut.pdf", p4, include_clinical=True, include_gut=True, include_wearable=False)

    # ── Report 5: Clinical + Wearable ────────────────────────────────────
    # Profile: 49M, T2D & High Adiposity Risk with confirmed high CGM sensor glucose & elevated clinical HbA1c
    p5 = {
        'name': 'Amitav Sen',
        'id': 'P050005',
        'age': 49,
        'gender': 'Male',
        'date': '29-Aug-2026',
        'clinical': {
            'height': 176.0, 'weight': 91.0, 'bmi': 29.38, 'waist': 101.0,
            'systolic_bp': 140.0, 'diastolic_bp': 88.0,
            'fasting_glucose': 136.0, 'hba1c': 7.2,
            'triglycerides': 230.0, 'hdl': 37.0, 'ldl': 148.0, 'total_chol': 231,
            'alt': 44.0, 'ast': 35.0,
            'fh_diabetes': 'Yes', 'fh_hypertension': 'Yes', 'fh_cvd': 'Yes',
            'creatinine': 1.05, 'bun': 17.0, 'urea': 36.0, 'vit_d': 19.5, 'tsh': 3.10
        },
        'wearable': {
            'steps': 4500.0, 'active_mins': 20.0, 'sedentary_mins': 640.0, 'rhr': 75.0, 'hrv': 25.0,
            'sleep_hours': 6.3, 'sleep_efficiency': 73.0, 'stress_score': 64.0,
            'energy_exp': 1980.0, 'exercise_freq': 1.0,
            'cgm_avg_glucose': 148.0, 'cgm_cv': 34.0, 'cgm_tir': 62.0, 'cgm_tar': 35.0, 'cgm_tbr': 3.0,
            'distance': 3.5, 'deep_sleep': 15, 'rem_sleep': 18, 'vo2_max': 35
        }
    }
    build_report_pdf("05_Clinical_Wearable.pdf", p5, include_clinical=True, include_gut=False, include_wearable=True)

    # ── Report 6: Gut + Wearable ─────────────────────────────────────────
    # Profile: 44F, Gut dysbiosis with moderate physical activity and prediabetic CGM pattern
    p6 = {
        'name': 'Ananya Roy',
        'id': 'P060006',
        'age': 44,
        'gender': 'Female',
        'date': '29-Aug-2026',
        'shannon': 3.35,
        'bf_ratio': 1.40,
        'gut': {
            'Akkermansia': 1.40, 'Faecalibacterium': 4.50, 'Roseburia': 3.20, 'Bifidobacterium': 3.50,
            'Bacteroides': 19.50, 'Prevotella': 9.20, 'Ruminococcus': 5.40, 'Blautia': 6.80,
            'Collinsella': 5.20, 'Escherichia_Shigella': 3.80, 'Coprococcus': 2.20, 'Alistipes': 3.80,
            'Subdoligranulum': 2.00, 'Enterococcus': 1.70, 'Eubacterium': 3.40, 'Parabacteroides': 2.90,
            'Lactobacillus': 1.80, 'Klebsiella': 2.80, 'Streptococcus': 2.60, 'Eggerthella': 1.90,
            'Other_Taxa': 12.80
        },
        'wearable': {
            'steps': 5200.0, 'active_mins': 24.0, 'sedentary_mins': 610.0, 'rhr': 73.0, 'hrv': 28.0,
            'sleep_hours': 6.6, 'sleep_efficiency': 76.0, 'stress_score': 58.0,
            'energy_exp': 2100.0, 'exercise_freq': 2.0,
            'cgm_avg_glucose': 118.0, 'cgm_cv': 26.0, 'cgm_tir': 74.0, 'cgm_tar': 22.0, 'cgm_tbr': 4.0,
            'distance': 4.0, 'deep_sleep': 17, 'rem_sleep': 20, 'vo2_max': 37
        }
    }
    build_report_pdf("06_Gut_Wearable.pdf", p6, include_clinical=False, include_gut=True, include_wearable=True)

    # ── Report 7: Clinical + Gut + Wearable (Full Multi-Modality) ─────────
    # Profile: 56M, Severe metabolic risk across all 3 domains (Clinical T2D/MetSyn + Gut Dysbiosis + CGM Hyperglycemia)
    p7 = {
        'name': 'Kothandaram R.',
        'id': 'P070007',
        'age': 56,
        'gender': 'Male',
        'date': '29-Aug-2026',
        'clinical': {
            'height': 171.0, 'weight': 88.0, 'bmi': 30.09, 'waist': 103.0,
            'systolic_bp': 144.0, 'diastolic_bp': 92.0,
            'fasting_glucose': 154.0, 'hba1c': 7.9,
            'triglycerides': 260.0, 'hdl': 35.0, 'ldl': 156.0, 'total_chol': 243,
            'alt': 52.0, 'ast': 42.0,
            'fh_diabetes': 'Yes', 'fh_hypertension': 'Yes', 'fh_cvd': 'Yes',
            'creatinine': 1.12, 'bun': 18.5, 'urea': 39.0, 'vit_d': 16.8, 'tsh': 3.45
        },
        'shannon': 3.05,
        'bf_ratio': 1.62,
        'gut': {
            'Akkermansia': 0.50, 'Faecalibacterium': 3.40, 'Roseburia': 2.20, 'Bifidobacterium': 1.90,
            'Bacteroides': 23.00, 'Prevotella': 12.00, 'Ruminococcus': 6.80, 'Blautia': 8.00,
            'Collinsella': 7.10, 'Escherichia_Shigella': 5.20, 'Coprococcus': 1.60, 'Alistipes': 3.00,
            'Subdoligranulum': 1.40, 'Enterococcus': 2.40, 'Eubacterium': 2.60, 'Parabacteroides': 3.20,
            'Lactobacillus': 1.10, 'Klebsiella': 4.00, 'Streptococcus': 3.40, 'Eggerthella': 2.50,
            'Other_Taxa': 6.70
        },
        'wearable': {
            'steps': 3800.0, 'active_mins': 12.0, 'sedentary_mins': 710.0, 'rhr': 78.0, 'hrv': 21.0,
            'sleep_hours': 5.9, 'sleep_efficiency': 68.0, 'stress_score': 72.0,
            'energy_exp': 1750.0, 'exercise_freq': 0.0,
            'cgm_avg_glucose': 162.0, 'cgm_cv': 41.0, 'cgm_tir': 54.0, 'cgm_tar': 42.0, 'cgm_tbr': 4.0,
            'distance': 2.9, 'deep_sleep': 12, 'rem_sleep': 15, 'vo2_max': 31
        }
    }
    build_report_pdf("07_Clinical_Gut_Wearable_Full.pdf", p7, include_clinical=True, include_gut=True, include_wearable=True)

    print("\nAll 7 test PDF reports generated successfully in 'generated_test_reports/'!")

if __name__ == "__main__":
    main()
