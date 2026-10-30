"""
Patient Support and Continuity Vulnerability Assessment Service for FollowUp
Evaluates social determinants of health, logistical barriers, and continuity risks
to assist healthcare workers in proactive outreach and support planning.
"""

from datetime import datetime, date
from typing import Optional, Dict, Any, List, Tuple
import json

import config
from database.connection import execute_query, execute_single, execute_statement
from utils.security import generate_reference
from services.auth_service import log_audit_action

def get_next_assessment_ref() -> str:
    """Generate sequential standardized assessment reference."""
    row = execute_single("SELECT MAX(id) as max_id FROM support_assessments")
    next_id = (row["max_id"] or 0) + 1
    return generate_reference("ASS", next_id, year=2026)

def calculate_vulnerability_tier(score: int) -> str:
    """
    Transparent, rule-based tier assignment for continuity support planning.
    Notice: Strictly decision-support for continuity; NOT a clinical diagnosis.
    """
    if score >= 4:
        return config.VULNERABILITY_HIGH
    elif score >= 2:
        return config.VULNERABILITY_MODERATE
    else:
        return config.VULNERABILITY_LOW

def record_support_assessment(patient_id: int,
                               assessor_name: str,
                               financial_difficulties: bool = False,
                               transport_difficulties: bool = False,
                               long_distance_facility: bool = False,
                               lack_of_caregiver: bool = False,
                               medicine_access_difficulty: bool = False,
                               repeated_missed_appointments: bool = False,
                               food_insecurity: bool = False,
                               disability_mobility_barrier: bool = False,
                               other_barriers: Optional[str] = None,
                               support_actions_recommended: Optional[str] = None,
                               review_notes: Optional[str] = None,
                               auto_create_task: bool = True,
                               actor_username: str = "system",
                               actor_role: str = "Healthcare Provider",
                               is_demo: int = 0) -> Tuple[bool, str, Optional[str]]:
    """
    Record structured social and logistical continuity assessment.
    """
    if not assessor_name or len(assessor_name.strip()) < 2:
        return False, "Assessor name or clinician identifier is required.", None
        
    # Calculate score
    flags = [
        financial_difficulties, transport_difficulties, long_distance_facility,
        lack_of_caregiver, medicine_access_difficulty, repeated_missed_appointments,
        food_insecurity, disability_mobility_barrier
    ]
    score = sum(1 for f in flags if f)
    tier = calculate_vulnerability_tier(score)
    
    ass_ref = get_next_assessment_ref()
    now_str = datetime.now().isoformat()
    ass_date_str = date.today().isoformat()
    
    actions_text = (support_actions_recommended or "").strip()
    if not actions_text:
        if tier == config.VULNERABILITY_HIGH:
            actions_text = "Urgent: Assign community health worker visit and coordinate transport/medication assistance."
        elif tier == config.VULNERABILITY_MODERATE:
            actions_text = "Conduct follow-up check-in call and verify caregiver availability."
        else:
            actions_text = "Continue routine scheduled follow-up appointments."
            
    try:
        execute_statement(
            """
            INSERT INTO support_assessments (
                assessment_ref, patient_id, assessment_date, assessor_name,
                financial_difficulties, transport_difficulties, long_distance_facility,
                lack_of_caregiver, medicine_access_difficulty, repeated_missed_appointments,
                food_insecurity, disability_mobility_barrier, other_barriers,
                vulnerability_score, vulnerability_tier, support_actions_recommended,
                support_status, review_notes, is_demo, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Active', ?, ?, ?)
            """,
            (
                ass_ref, patient_id, ass_date_str, assessor_name.strip(),
                1 if financial_difficulties else 0,
                1 if transport_difficulties else 0,
                1 if long_distance_facility else 0,
                1 if lack_of_caregiver else 0,
                1 if medicine_access_difficulty else 0,
                1 if repeated_missed_appointments else 0,
                1 if food_insecurity else 0,
                1 if disability_mobility_barrier else 0,
                other_barriers.strip() if other_barriers else None,
                score, tier, actions_text,
                review_notes.strip() if review_notes else None,
                is_demo, now_str
            )
        )
        
        # If high continuity risk or repeated missed appointments, update patient status to Requires Review
        if tier == config.VULNERABILITY_HIGH:
            execute_statement(
                "UPDATE patients SET followup_status = 'Requires Review', updated_at = ? WHERE id = ?",
                (now_str, patient_id)
            )
            
            # Automatically create high-priority follow-up task
            if auto_create_task:
                from services.task_service import create_task
                create_task(
                    patient_id=patient_id,
                    title=f"Continuity Review: {tier} ({score} barriers detected)",
                    description=f"Automated risk review task for assessment {ass_ref}. Actions recommended: {actions_text}",
                    assigned_to=assessor_name,
                    assigned_by=actor_username,
                    priority=config.TASK_PRIORITY_HIGH,
                    due_date_str=date.today().isoformat(),
                    actor_username=actor_username,
                    actor_role=actor_role,
                    is_demo=is_demo
                )
                
        log_audit_action(
            username=actor_username,
            role=actor_role,
            action="SUPPORT_ASSESSMENT",
            target_type="SupportAssessment",
            target_ref=ass_ref,
            details=f"Assessed patient ID {patient_id}: Score {score} ({tier})."
        )
        
        return True, f"Vulnerability assessment {ass_ref} recorded ({tier}).", ass_ref
    except Exception as e:
        return False, f"Database error recording assessment: {str(e)}", None

def list_support_assessments(patient_id: Optional[int] = None,
                             tier: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve support assessments with patient information."""
    sql = """
        SELECT s.*, p.patient_ref, p.full_name as patient_name, p.condition_category,
               p.district as patient_district, f.name as facility_name
        FROM support_assessments s
        JOIN patients p ON s.patient_id = p.id
        JOIN facilities f ON p.facility_id = f.id
        WHERE 1=1
    """
    params = []
    
    if patient_id:
        sql += " AND s.patient_id = ?"
        params.append(patient_id)
        
    if tier and tier != "All Tiers":
        sql += " AND s.vulnerability_tier = ?"
        params.append(tier)
        
    sql += " ORDER BY s.assessment_date DESC, s.vulnerability_score DESC"
    
    rows = execute_query(sql, tuple(params))
    return [dict(r) for r in rows]

def get_continuity_barrier_breakdown() -> Dict[str, int]:
    """Aggregate counts for each social/logistical barrier across all stored assessments."""
    sql = """
        SELECT
            SUM(financial_difficulties) as financial,
            SUM(transport_difficulties) as transport,
            SUM(long_distance_facility) as distance,
            SUM(lack_of_caregiver) as caregiver,
            SUM(medicine_access_difficulty) as medicine,
            SUM(repeated_missed_appointments) as missed_prior,
            SUM(food_insecurity) as food,
            SUM(disability_mobility_barrier) as disability
        FROM support_assessments
    """
    row = execute_single(sql)
    if not row:
        return {}
    return {
        "Financial Constraints": row["financial"] or 0,
        "Transportation Difficulties": row["transport"] or 0,
        "Long Distance (>1 hr)": row["distance"] or 0,
        "Lack of Caregiver Support": row["caregiver"] or 0,
        "Medication Access / Refill": row["medicine"] or 0,
        "Repeated Missed Visits": row["missed_prior"] or 0,
        "Food Insecurity": row["food"] or 0,
        "Mobility / Disability": row["disability"] or 0
    }
