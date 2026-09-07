"""
progress_plan_pdf.py — Real PDF Report Generator for Personalized Progress Plans

Generates a clean, professional, high-contrast PDF document using ReportLab.
Includes:
- Patient info & plan duration
- Validated priority pillars & numerical targets
- Day-by-day / week-by-week checklist with task instructions & suggestions
- Progress status & completion tracking
- Clinical advisory disclaimer
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Dict, Any, List

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable,
)


class ProgressPlanPDFGenerator:
    """Generates downloadable PDF reports for personalized progress plans."""

    @classmethod
    def generate_pdf_bytes(cls, plan_record: Dict[str, Any]) -> bytes:
        """Generates a complete PDF document as bytes."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        # Custom high-contrast styles
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=20,
            leading=24,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=4
        )

        subtitle_style = ParagraphStyle(
            'DocSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            leading=14,
            textColor=colors.HexColor('#475569'),
            spaceAfter=12
        )

        heading2_style = ParagraphStyle(
            'Heading2',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=16,
            textColor=colors.HexColor('#0369a1'),
            spaceBefore=10,
            spaceAfter=6
        )

        day_heading_style = ParagraphStyle(
            'DayHeading',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=14,
            textColor=colors.HexColor('#0f172a')
        )

        task_title_style = ParagraphStyle(
            'TaskTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9.5,
            leading=12,
            textColor=colors.HexColor('#1e293b')
        )

        task_desc_style = ParagraphStyle(
            'TaskDesc',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor('#334155')
        )

        meta_label_style = ParagraphStyle(
            'MetaLabel',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=11,
            textColor=colors.HexColor('#475569')
        )

        meta_val_style = ParagraphStyle(
            'MetaVal',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=11,
            textColor=colors.HexColor('#0f172a')
        )

        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor('#64748b')
        )

        story = []

        # ── 1. HEADER SECTION ────────────────────────────────────────────────
        plan_data = plan_record.get("plan_data", {})
        patient_info = plan_data.get("patient_info", {})
        duration_label = plan_data.get("duration_label", "Personalized Progress Plan")
        p_id = patient_info.get("patient_id", plan_record.get("patient_id", "P001"))
        p_name = patient_info.get("name") or patient_info.get("patient_name") or "Patient"
        p_age = patient_info.get("age") or patient_info.get("patient_age") or "N/A"
        p_gender = patient_info.get("gender") or patient_info.get("patient_gender") or "N/A"

        story.append(Paragraph("Telemedicine Platform", ParagraphStyle('TopBrand', fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#0284c7'))))
        story.append(Paragraph("Personalized Health Progress Plan", title_style))
        story.append(Paragraph(f"Duration: <b>{duration_label}</b> • Structured daily checklist backed by verified clinical guidelines.", subtitle_style))

        # Patient Metadata Table
        meta_data = [
            [
                Paragraph("<b>Patient ID:</b>", meta_label_style), Paragraph(str(p_id), meta_val_style),
                Paragraph("<b>Date:</b>", meta_label_style), Paragraph(datetime.now().strftime("%B %d, %Y"), meta_val_style)
            ],
            [
                Paragraph("<b>Name:</b>", meta_label_style), Paragraph(str(p_name), meta_val_style),
                Paragraph("<b>Age / Gender:</b>", meta_label_style), Paragraph(f"{p_age} yrs / {p_gender}", meta_val_style)
            ]
        ]
        meta_table = Table(meta_data, colWidths=[80, 180, 90, 190])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 10))

        # ── 2. VALIDATED TARGETS SUMMARY ──────────────────────────────────────
        targets = plan_data.get("guideline_targets", {})
        if targets:
            story.append(Paragraph("🎯 Your Verified Guideline Targets", heading2_style))
            target_rows = []
            for k, v in targets.items():
                target_rows.append([
                    Paragraph(f"• <b>{k}</b>", meta_label_style),
                    Paragraph(f"Target: <b>{v}</b>", meta_val_style)
                ])
            t_table = Table(target_rows, colWidths=[240, 300])
            t_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0fdf4')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#86efac')),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(t_table)
            story.append(Spacer(1, 10))

        # ── 3. PROGRESS SUMMARY ───────────────────────────────────────────────
        comp_tasks = set(plan_record.get("completed_tasks", []))
        comp_days = set(plan_record.get("completed_days", []))
        total_tasks = plan_data.get("total_tasks", len(comp_tasks) or 1)
        progress_pct = plan_record.get("overall_progress", 0.0)

        prog_summary = [
            [
                Paragraph("<b>Current Day:</b>", meta_label_style), Paragraph(f"Day {plan_record.get('current_day', 1)}", meta_val_style),
                Paragraph("<b>Completed Tasks:</b>", meta_label_style), Paragraph(f"{len(comp_tasks)} of {total_tasks} ({progress_pct}%)", meta_val_style),
                Paragraph("<b>Days Completed:</b>", meta_label_style), Paragraph(f"{len(comp_days)} of {plan_data.get('total_days', 7)} days", meta_val_style)
            ]
        ]
        prog_table = Table(prog_summary, colWidths=[80, 90, 100, 110, 90, 70])
        prog_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f9ff')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#bae6fd')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(prog_table)
        story.append(Spacer(1, 12))

        # ── 4. DAILY CHECKLISTS ───────────────────────────────────────────────
        story.append(Paragraph("📋 Daily Step-by-Step Task Checklists", heading2_style))
        days = plan_data.get("days", [])

        # Display up to 14 days directly in table format for clean printing
        display_days = days if len(days) <= 14 else days[:14]

        for d in display_days:
            d_num = d["day_number"]
            d_theme = d.get("focus_theme", "")
            d_done = d_num in comp_days
            status_text = "[ COMPLETE ✓ ]" if d_done else "[ IN PROGRESS ]" if d_num == plan_record.get("current_day", 1) else "[ PENDING ]"

            day_header = [
                [
                    Paragraph(f"<b>Day {d_num} — {d_theme}</b>", day_heading_style),
                    Paragraph(f"<b>{status_text}</b>", ParagraphStyle('DStatus', fontName='Helvetica-Bold', fontSize=9, textColor=colors.HexColor('#0284c7') if d_done else colors.HexColor('#475569')))
                ]
            ]
            dh_table = Table(day_header, colWidths=[400, 140])
            dh_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e2e8f0')),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ]))

            task_rows = []
            for t in d.get("tasks", []):
                t_done = t["id"] in comp_tasks
                box_str = "[ X ]" if t_done else "[   ]"
                task_content = f"<b>{t['title']}</b> ({t.get('priority_pillar', '')})<br/>{t.get('instruction', '')} <i>Suggestion: {t.get('suggestion', '')}</i>"
                task_rows.append([
                    Paragraph(f"<b>{box_str}</b>", ParagraphStyle('Box', fontName='Helvetica-Bold', fontSize=10, alignment=1)),
                    Paragraph(task_content, task_desc_style)
                ])

            tasks_table = Table(task_rows, colWidths=[40, 500])
            tasks_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ffffff')),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#f1f5f9')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ]))

            story.append(KeepTogether([dh_table, tasks_table, Spacer(1, 8)]))

        if len(days) > 14:
            story.append(Paragraph(f"<i>Note: Showing first 14 of {len(days)} days in this printout summary. Continue daily checklist in the digital platform.</i>", disclaimer_style))
            story.append(Spacer(1, 8))

        # ── 5. MEDICAL ADVISORY DISCLAIMER ───────────────────────────────────
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e1'), spaceBefore=4, spaceAfter=8))
        disclaimer_text = (
            "<b>Medical Advisory:</b> This personalized health progress plan is generated using verified clinical practice guidelines "
            "(CDC National DPP, WHO Physical Activity, EASL Clinical Guidance) for informational and lifestyle support only. "
            "It is not a substitute for professional medical advice, diagnosis, or treatment. Please consult a qualified healthcare provider for personalized medical decisions."
        )
        story.append(Paragraph(disclaimer_text, disclaimer_style))

        # Build document
        doc.build(story)
        pdf_data = buffer.getvalue()
        buffer.close()
        return pdf_data
