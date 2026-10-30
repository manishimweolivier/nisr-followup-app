"""
PDF Report Generation Utility for FollowUp
Generates clean, professional healthcare continuity and follow-up reports.
"""

import io
from datetime import datetime
from typing import Dict, Any, List, Optional
import config

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
    _HAS_REPORTLAB = True
except ImportError:
    _HAS_REPORTLAB = False


def generate_patient_summary_pdf(patient: Dict[str, Any],
                                 appointments: List[Dict[str, Any]],
                                 followups: List[Dict[str, Any]],
                                 assessments: List[Dict[str, Any]]) -> bytes:
    """
    Generate an official clinical continuity summary PDF for an individual patient.
    """
    if not _HAS_REPORTLAB:
        raise RuntimeError("ReportLab is not installed or available in this environment.")
        
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
    
    # Custom Healthcare Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#475569'),
        spaceAfter=12
    )
    
    section_heading = ParagraphStyle(
        'SectionHead',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1e3a8a'),
        spaceBefore=10,
        spaceAfter=6
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#1e293b')
    )
    
    body_bold = ParagraphStyle(
        'DocBodyBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    elements = []
    
    # Header Banner
    elements.append(Paragraph("FollowUp | Continuity of Care System", title_style))
    elements.append(Paragraph(
        f"Individual Patient Continuity Record & Follow-Up Audit Log &bull; Generated on {datetime.now().strftime('%d %b %Y, %H:%M')}",
        subtitle_style
    ))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1e3a8a'), spaceAfter=14))
    
    # Patient Demographics Table
    elements.append(Paragraph("1. Patient Profile & Administrative Demographics", section_heading))
    patient_info = [
        [
            Paragraph("Patient Reference:", body_bold),
            Paragraph(patient.get('patient_ref', 'N/A'), body_style),
            Paragraph("Full Name:", body_bold),
            Paragraph(patient.get('full_name', 'N/A'), body_style)
        ],
        [
            Paragraph("Age / Sex:", body_bold),
            Paragraph(f"{patient.get('age', 'N/A')} yrs / {patient.get('sex', 'N/A')}", body_style),
            Paragraph("Phone Number:", body_bold),
            Paragraph(patient.get('phone_number') or 'Unlisted', body_style)
        ],
        [
            Paragraph("Healthcare Facility:", body_bold),
            Paragraph(patient.get('facility_name', 'N/A'), body_style),
            Paragraph("District / Sector:", body_bold),
            Paragraph(f"{patient.get('district', 'N/A')} / {patient.get('sector') or 'N/A'}", body_style)
        ],
        [
            Paragraph("Condition Category:", body_bold),
            Paragraph(patient.get('condition_category', 'N/A'), body_style),
            Paragraph("Current Status:", body_bold),
            Paragraph(patient.get('followup_status', 'N/A'), body_style)
        ],
        [
            Paragraph("Clinical Summary:", body_bold),
            Paragraph(patient.get('clinical_summary') or 'None recorded', body_style),
            Paragraph("Registration Date:", body_bold),
            Paragraph(patient.get('registration_date', 'N/A'), body_style)
        ]
    ]
    
    t_patient = Table(patient_info, colWidths=[110, 160, 110, 160])
    t_patient.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_patient)
    elements.append(Spacer(1, 12))
    
    # Continuity & Support Assessment Section
    elements.append(Paragraph("2. Social & Logistical Support Assessments", section_heading))
    if assessments:
        ass_data = [
            [
                Paragraph("Assessment Ref", body_bold),
                Paragraph("Date", body_bold),
                Paragraph("Vulnerability Tier", body_bold),
                Paragraph("Assessor", body_bold),
                Paragraph("Key Identified Barriers", body_bold)
            ]
        ]
        for a in assessments[:4]:
            barriers_list = []
            if a.get('financial_difficulties'): barriers_list.append("Financial")
            if a.get('transport_difficulties'): barriers_list.append("Transport")
            if a.get('long_distance_facility'): barriers_list.append("Distance >1hr")
            if a.get('lack_of_caregiver'): barriers_list.append("No Caregiver")
            if a.get('medicine_access_difficulty'): barriers_list.append("Med Refill")
            if a.get('repeated_missed_appointments'): barriers_list.append("Missed Prior")
            b_text = ", ".join(barriers_list) if barriers_list else "None flagged"
            
            ass_data.append([
                Paragraph(a.get('assessment_ref', ''), body_style),
                Paragraph(a.get('assessment_date', ''), body_style),
                Paragraph(a.get('vulnerability_tier', ''), body_style),
                Paragraph(a.get('assessor_name', ''), body_style),
                Paragraph(b_text, body_style)
            ])
        t_ass = Table(ass_data, colWidths=[85, 75, 110, 100, 170])
        t_ass.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(t_ass)
    else:
        elements.append(Paragraph("No structured vulnerability assessments recorded for this patient.", body_style))
    elements.append(Spacer(1, 12))
    
    # Appointments History Table
    elements.append(Paragraph("3. Scheduled Appointments & Continuity Timeline", section_heading))
    if appointments:
        apt_data = [
            [
                Paragraph("Ref", body_bold),
                Paragraph("Date", body_bold),
                Paragraph("Type", body_bold),
                Paragraph("Status", body_bold),
                Paragraph("Responsible Officer", body_bold),
                Paragraph("Clinical Notes / Outcome", body_bold)
            ]
        ]
        for apt in appointments:
            apt_data.append([
                Paragraph(apt.get('appointment_ref', ''), body_style),
                Paragraph(apt.get('scheduled_date', ''), body_style),
                Paragraph(apt.get('followup_type', ''), body_style),
                Paragraph(apt.get('status', ''), body_style),
                Paragraph(apt.get('responsible_worker', ''), body_style),
                Paragraph(apt.get('outcome_notes') or apt.get('rescheduled_reason') or 'Pending', body_style)
            ])
        t_apt = Table(apt_data, colWidths=[70, 70, 95, 75, 95, 135])
        t_apt.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(t_apt)
    else:
        elements.append(Paragraph("No appointments recorded for this patient.", body_style))
    elements.append(Spacer(1, 14))
    
    # Footer Notice
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#94a3b8'), spaceAfter=8))
    elements.append(Paragraph(
        "CONFIDENTIAL MEDICAL RECORD NOTICE: This document contains protected health information intended solely for authorized healthcare providers. "
        "Strict compliance with patient privacy standards and data protection laws is mandatory.",
        ParagraphStyle('FooterNotice', parent=styles['Normal'], fontSize=7.5, leading=10, textColor=colors.HexColor('#64748b'))
    ))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
