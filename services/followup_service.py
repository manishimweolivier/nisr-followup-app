"""
Follow-Up and Appointment Management Service for FollowUp
Coordinates scheduling, completion, rescheduling, missed appointment detection,
and chronological interaction logs.
"""

from datetime import datetime, date
from typing import Optional, Dict, Any, List, Tuple
import json

import config
from database.connection import execute_query, execute_single, execute_statement
from utils.security import generate_reference
from utils.helpers import parse_iso_date, is_date_overdue, is_date_due_today
from services.validation_service import validate_appointment_input
from services.auth_service import log_audit_action

def get_next_appointment_ref() -> str:
    """Generate sequential standardized appointment reference."""
    row = execute_single("SELECT MAX(id) as max_id FROM appointments")
    next_id = (row["max_id"] or 0) + 1
    return generate_reference("APT", next_id, year=2026)

def get_next_followup_ref() -> str:
    """Generate sequential standardized follow-up interaction reference."""
    row = execute_single("SELECT MAX(id) as max_id FROM followup_records")
    next_id = (row["max_id"] or 0) + 1
    return generate_reference("FLW", next_id, year=2026)

def schedule_appointment(patient_id: int,
                         facility_id: int,
                         scheduled_date: str,
                         followup_type: str,
                         responsible_worker: str,
                         scheduled_time: Optional[str] = "09:00",
                         notes: Optional[str] = None,
                         actor_username: str = "system",
                         actor_role: str = "Healthcare Provider",
                         is_demo: int = 0) -> Tuple[bool, str, Optional[str]]:
    """Schedule a new follow-up appointment."""
    is_valid, err = validate_appointment_input(
        scheduled_date_str=scheduled_date,
        followup_type=followup_type,
        responsible_worker=responsible_worker
    )
    if not is_valid:
        return False, err, None
        
    sch_date_obj = parse_iso_date(scheduled_date)
    today_obj = date.today()
    
    # Determine initial status
    if sch_date_obj == today_obj:
        initial_status = config.STATUS_DUE
    elif sch_date_obj < today_obj:
        # Never allow scheduling a new future appointment in the past as scheduled
        initial_status = config.STATUS_MISSED
    else:
        initial_status = config.STATUS_SCHEDULED
        
    apt_ref = get_next_appointment_ref()
    now_str = datetime.now().isoformat()
    
    try:
        execute_statement(
            """
            INSERT INTO appointments (
                appointment_ref, patient_id, facility_id, scheduled_date, scheduled_time,
                followup_type, responsible_worker, status, outcome_notes, is_demo,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                apt_ref, patient_id, facility_id, scheduled_date, scheduled_time,
                followup_type, responsible_worker.strip(), initial_status,
                notes.strip() if notes else None, is_demo, now_str, now_str
            )
        )
        
        log_audit_action(
            username=actor_username,
            role=actor_role,
            action="APPOINTMENT_SCHEDULE",
            target_type="Appointment",
            target_ref=apt_ref,
            details=f"Scheduled {followup_type} for patient ID {patient_id} on {scheduled_date} ({responsible_worker})."
        )
        
        return True, f"Appointment {apt_ref} scheduled successfully for {scheduled_date}.", apt_ref
    except Exception as e:
        return False, f"Database error scheduling appointment: {str(e)}", None

def reschedule_appointment(appointment_id: int,
                           new_scheduled_date: str,
                           reason: str,
                           actor_username: str,
                           actor_role: str) -> Tuple[bool, str]:
    """
    Reschedule an appointment, updating the original appointment status to Rescheduled
    and creating a linked follow-up appointment.
    """
    orig = execute_single("SELECT * FROM appointments WHERE id = ?", (appointment_id,))
    if not orig:
        return False, "Original appointment not found."
        
    if not reason or len(reason.strip()) < 3:
        return False, "A clear reason for rescheduling is required."
        
    now_str = datetime.now().isoformat()
    new_date_obj = parse_iso_date(new_scheduled_date)
    today_obj = date.today()
    
    new_status = config.STATUS_DUE if new_date_obj == today_obj else config.STATUS_SCHEDULED
    new_apt_ref = get_next_appointment_ref()
    
    try:
        # Update original appointment
        execute_statement(
            """
            UPDATE appointments SET
                status = ?, rescheduled_reason = ?, updated_at = ?
            WHERE id = ?
            """,
            (config.STATUS_RESCHEDULED, f"Rescheduled to {new_scheduled_date}. Reason: {reason.strip()}", now_str, appointment_id)
        )
        
        # Insert new appointment linked to original
        execute_statement(
            """
            INSERT INTO appointments (
                appointment_ref, patient_id, facility_id, scheduled_date, scheduled_time,
                followup_type, responsible_worker, status, outcome_notes, original_appointment_id,
                is_demo, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_apt_ref, orig["patient_id"], orig["facility_id"], new_scheduled_date,
                orig["scheduled_time"], orig["followup_type"], orig["responsible_worker"],
                new_status, f"Rescheduled from {orig['appointment_ref']}. Reason: {reason.strip()}",
                appointment_id, orig["is_demo"], now_str, now_str
            )
        )
        
        log_audit_action(
            username=actor_username,
            role=actor_role,
            action="APPOINTMENT_RESCHEDULE",
            target_type="Appointment",
            target_ref=orig["appointment_ref"],
            details=f"Rescheduled appointment {orig['appointment_ref']} to {new_scheduled_date} (New Ref: {new_apt_ref})."
        )
        return True, f"Appointment successfully rescheduled to {new_scheduled_date} (New Ref: {new_apt_ref})."
    except Exception as e:
        return False, f"Database error during appointment rescheduling: {str(e)}"

def record_followup_interaction(patient_id: int,
                                interaction_date: str,
                                followup_type: str,
                                responsible_worker: str,
                                patient_status_summary: str,
                                action_taken: str,
                                appointment_id: Optional[int] = None,
                                medication_adherence: Optional[str] = "Full",
                                reported_barriers: Optional[List[str]] = None,
                                next_steps: Optional[str] = None,
                                next_followup_date: Optional[str] = None,
                                actor_username: str = "system",
                                actor_role: str = "Healthcare Provider",
                                is_demo: int = 0) -> Tuple[bool, str, Optional[str]]:
    """
    Record completed follow-up interaction (visit, call, clinical consultation).
    Marks linked appointment as Completed.
    """
    if not patient_status_summary or len(patient_status_summary.strip()) < 3:
        return False, "Patient clinical/continuity status summary is required.", None
    if not action_taken or len(action_taken.strip()) < 3:
        return False, "Action taken must be recorded.", None
        
    flw_ref = get_next_followup_ref()
    now_str = datetime.now().isoformat()
    barriers_str = json.dumps(reported_barriers or [])
    
    try:
        execute_statement(
            """
            INSERT INTO followup_records (
                record_ref, patient_id, appointment_id, interaction_date, followup_type,
                responsible_worker, patient_status_summary, medication_adherence,
                reported_barriers, action_taken, next_steps, next_followup_date,
                is_demo, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                flw_ref, patient_id, appointment_id, interaction_date, followup_type,
                responsible_worker.strip(), patient_status_summary.strip(),
                medication_adherence, barriers_str, action_taken.strip(),
                next_steps.strip() if next_steps else None,
                next_followup_date, is_demo, now_str
            )
        )
        
        # If linked to an appointment, mark it completed
        if appointment_id:
            execute_statement(
                """
                UPDATE appointments SET
                    status = 'Completed', completed_date = ?, outcome_notes = ?,
                    next_recommended_date = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    interaction_date,
                    f"Completed: {action_taken[:100]} | Status: {patient_status_summary[:60]}",
                    next_followup_date,
                    now_str,
                    appointment_id
                )
            )
            
        # If next follow-up date given, optionally schedule the next appointment
        if next_followup_date:
            p = execute_single("SELECT facility_id FROM patients WHERE id = ?", (patient_id,))
            facility_id = p["facility_id"] if p else 1
            schedule_appointment(
                patient_id=patient_id,
                facility_id=facility_id,
                scheduled_date=next_followup_date,
                followup_type=followup_type,
                responsible_worker=responsible_worker,
                notes=f"Follow-up scheduled from visit {flw_ref}: {next_steps or 'Routine continuing care'}",
                actor_username=actor_username,
                actor_role=actor_role,
                is_demo=is_demo
            )
            
        log_audit_action(
            username=actor_username,
            role=actor_role,
            action="FOLLOWUP_RECORD",
            target_type="FollowUpRecord",
            target_ref=flw_ref,
            details=f"Recorded {followup_type} for patient ID {patient_id} ({responsible_worker})."
        )
        
        return True, f"Follow-up visit record {flw_ref} saved successfully.", flw_ref
    except Exception as e:
        return False, f"Database error recording follow-up interaction: {str(e)}", None

def sync_overdue_appointments():
    """
    CRITICAL HEALTHCARE CONTINUITY LOGIC:
    Scans appointments with status Scheduled or Due.
    - If scheduled_date < today: update status to 'Missed'.
    - If scheduled_date == today: update status to 'Due'.
    - If scheduled_date > today and status == 'Due': keep as 'Scheduled'.
    Strict rule: Never marks an appointment as missed before its scheduled date has passed.
    """
    today_str = date.today().isoformat()
    now_str = datetime.now().isoformat()
    
    # 1. Update Scheduled to Due for today
    execute_statement(
        """
        UPDATE appointments
        SET status = 'Due', updated_at = ?
        WHERE scheduled_date = ? AND status = 'Scheduled'
        """,
        (now_str, today_str)
    )
    
    # 2. Update past due/scheduled appointments to Missed
    execute_statement(
        """
        UPDATE appointments
        SET status = 'Missed', updated_at = ?
        WHERE scheduled_date < ? AND status IN ('Scheduled', 'Due')
        """,
        (now_str, today_str)
    )

def list_appointments(patient_id: Optional[int] = None,
                      status: Optional[str] = None,
                      facility_id: Optional[int] = None,
                      date_from: Optional[str] = None,
                      date_to: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve appointments with patient and facility joins."""
    sync_overdue_appointments()
    
    sql = """
        SELECT a.*, p.patient_ref, p.full_name as patient_name, p.phone_number as patient_phone,
               p.condition_category, p.district as patient_district, f.name as facility_name
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN facilities f ON a.facility_id = f.id
        WHERE 1=1
    """
    params = []
    
    if patient_id:
        sql += " AND a.patient_id = ?"
        params.append(patient_id)
        
    if status and status != "All Statuses":
        sql += " AND a.status = ?"
        params.append(status)
        
    if facility_id and facility_id > 0:
        sql += " AND a.facility_id = ?"
        params.append(facility_id)
        
    if date_from:
        sql += " AND a.scheduled_date >= ?"
        params.append(date_from)
        
    if date_to:
        sql += " AND a.scheduled_date <= ?"
        params.append(date_to)
        
    sql += " ORDER BY a.scheduled_date ASC"
    
    rows = execute_query(sql, tuple(params))
    return [dict(r) for r in rows]

def get_followup_records_for_patient(patient_id: int) -> List[Dict[str, Any]]:
    """Retrieve all logged follow-up visits for a patient."""
    rows = execute_query(
        """
        SELECT f.*, a.appointment_ref
        FROM followup_records f
        LEFT JOIN appointments a ON f.appointment_id = a.id
        WHERE f.patient_id = ?
        ORDER BY f.interaction_date DESC
        """,
        (patient_id,)
    )
    return [dict(r) for r in rows]
