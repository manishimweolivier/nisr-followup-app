"""
Hospital Discharge Management Service for FollowUp
Coordinates post-discharge continuity of care, care plans, and transition to follow-up.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

import config
from database.connection import execute_query, execute_single, execute_statement
from utils.security import generate_reference
from services.validation_service import validate_discharge_input
from services.auth_service import log_audit_action

def get_next_discharge_ref() -> str:
    """Generate the next sequential standardized discharge reference."""
    row = execute_single("SELECT MAX(id) as max_id FROM discharges")
    next_id = (row["max_id"] or 0) + 1
    return generate_reference("DIS", next_id, year=2026)

def record_discharge(patient_id: int,
                     facility_id: int,
                     admission_date: str,
                     discharge_date: str,
                     diagnosis_summary: str,
                     condition_category: str,
                     followup_instructions: str,
                     recommended_appointment_date: str,
                     responsible_clinician: str,
                     discharge_support_needs: Optional[str] = None,
                     auto_schedule_appointment: bool = True,
                     actor_username: str = "system",
                     actor_role: str = "Healthcare Provider",
                     is_demo: int = 0) -> Tuple[bool, str, Optional[str]]:
    """
    Record a hospital discharge for continued outpatient care.
    Optionally auto-schedules the initial continuity appointment.
    """
    is_valid, err = validate_discharge_input(
        admission_date_str=admission_date,
        discharge_date_str=discharge_date,
        recommended_apt_date_str=recommended_appointment_date,
        diagnosis=diagnosis_summary,
        instructions=followup_instructions
    )
    if not is_valid:
        return False, err, None
        
    discharge_ref = get_next_discharge_ref()
    now_str = datetime.now().isoformat()
    
    try:
        execute_statement(
            """
            INSERT INTO discharges (
                discharge_ref, patient_id, facility_id, admission_date, discharge_date,
                diagnosis_summary, condition_category, followup_instructions,
                recommended_appointment_date, responsible_clinician,
                discharge_support_needs, status, is_demo, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Open', ?, ?)
            """,
            (
                discharge_ref, patient_id, facility_id, admission_date, discharge_date,
                diagnosis_summary.strip(), condition_category, followup_instructions.strip(),
                recommended_appointment_date, responsible_clinician.strip(),
                discharge_support_needs.strip() if discharge_support_needs else None,
                is_demo, now_str
            )
        )
        
        # Ensure patient status remains Active Follow-Up
        execute_statement(
            "UPDATE patients SET followup_status = 'Active Follow-Up', updated_at = ? WHERE id = ?",
            (now_str, patient_id)
        )
        
        # Auto-schedule the post-discharge appointment if requested
        if auto_schedule_appointment:
            from services.followup_service import schedule_appointment
            schedule_appointment(
                patient_id=patient_id,
                facility_id=facility_id,
                scheduled_date=recommended_appointment_date,
                followup_type="Facility Clinical Consultation",
                responsible_worker=responsible_clinician,
                notes=f"Auto-scheduled from hospital discharge {discharge_ref}: {followup_instructions[:100]}",
                actor_username=actor_username,
                actor_role=actor_role,
                is_demo=is_demo
            )
            
        log_audit_action(
            username=actor_username,
            role=actor_role,
            action="DISCHARGE_RECORD",
            target_type="Discharge",
            target_ref=discharge_ref,
            details=f"Recorded discharge for patient ID {patient_id} with follow-up on {recommended_appointment_date}."
        )
        
        return True, f"Discharge record {discharge_ref} created successfully.", discharge_ref
    except Exception as e:
        return False, f"Database error recording discharge: {str(e)}", None

def list_discharges(facility_id: Optional[int] = None,
                    status: Optional[str] = None,
                    condition: Optional[str] = None) -> List[Dict[str, Any]]:
    """List discharges with joined patient and facility details."""
    sql = """
        SELECT d.*, p.patient_ref, p.full_name as patient_name, p.phone_number as patient_phone,
               p.district as patient_district, f.name as facility_name
        FROM discharges d
        JOIN patients p ON d.patient_id = p.id
        JOIN facilities f ON d.facility_id = f.id
        WHERE 1=1
    """
    params = []
    
    if facility_id and facility_id > 0:
        sql += " AND d.facility_id = ?"
        params.append(facility_id)
        
    if status and status != "All Statuses":
        sql += " AND d.status = ?"
        params.append(status)
        
    if condition and condition != "All Conditions":
        sql += " AND d.condition_category = ?"
        params.append(condition)
        
    sql += " ORDER BY d.discharge_date DESC"
    
    rows = execute_query(sql, tuple(params))
    return [dict(r) for r in rows]

def close_discharge(discharge_id: int, actor_username: str, actor_role: str) -> bool:
    """Close an open discharge process once follow-up obligations are fulfilled."""
    execute_statement("UPDATE discharges SET status = 'Completed' WHERE id = ?", (discharge_id,))
    log_audit_action(
        username=actor_username,
        role=actor_role,
        action="DISCHARGE_CLOSE",
        target_type="Discharge",
        target_ref=str(discharge_id),
        details="Discharge continuity case closed."
    )
    return True
