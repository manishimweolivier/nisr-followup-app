"""
Patient Management Service for FollowUp
Coordinates patient registration, updates, search, filtering, and longitudinal timeline compilation.
"""

from datetime import datetime, date
from typing import Optional, Dict, Any, List, Tuple
import pandas as pd

import config
from database.connection import get_db_connection, execute_query, execute_single, execute_statement, query_to_dataframe
from utils.security import generate_reference
from services.validation_service import validate_patient_input
from services.auth_service import log_audit_action

def get_next_patient_ref() -> str:
    """Generate the next sequential standardized patient reference."""
    row = execute_single("SELECT MAX(id) as max_id FROM patients")
    next_id = (row["max_id"] or 0) + 1
    return generate_reference("FOL", next_id, year=2026)

def register_patient(full_name: str,
                     age: int,
                     sex: str,
                     facility_id: int,
                     condition_category: str,
                     district: str,
                     sector: Optional[str] = None,
                     cell: Optional[str] = None,
                     village: Optional[str] = None,
                     phone_number: Optional[str] = None,
                     alternate_phone: Optional[str] = None,
                     clinical_summary: Optional[str] = None,
                     caregiver_name: Optional[str] = None,
                     caregiver_phone: Optional[str] = None,
                     date_of_birth: Optional[str] = None,
                     initial_status: str = "Active Follow-Up",
                     actor_username: str = "system",
                     actor_role: str = "Healthcare Provider",
                     is_demo: int = 0) -> Tuple[bool, str, Optional[str]]:
    """
    Register a new patient into the continuity-of-care database.
    Returns (success, message, patient_ref).
    """
    is_valid, err = validate_patient_input(
        full_name=full_name,
        age=age,
        sex=sex,
        district=district,
        condition_category=condition_category,
        phone_number=phone_number
    )
    if not is_valid:
        return False, err, None
        
    patient_ref = get_next_patient_ref()
    now_str = datetime.now().isoformat()
    reg_date_str = date.today().isoformat()
    
    try:
        execute_statement(
            """
            INSERT INTO patients (
                patient_ref, full_name, date_of_birth, age, sex, phone_number, alternate_phone,
                district, sector, cell, village, facility_id, condition_category, clinical_summary,
                registration_date, followup_status, caregiver_name, caregiver_phone, is_demo,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                patient_ref, full_name.strip(), date_of_birth, age, sex,
                phone_number.strip() if phone_number else None,
                alternate_phone.strip() if alternate_phone else None,
                district.strip(), sector.strip() if sector else None,
                cell.strip() if cell else None, village.strip() if village else None,
                facility_id, condition_category, clinical_summary.strip() if clinical_summary else None,
                reg_date_str, initial_status, caregiver_name.strip() if caregiver_name else None,
                caregiver_phone.strip() if caregiver_phone else None,
                is_demo, now_str, now_str
            )
        )
        
        log_audit_action(
            username=actor_username,
            role=actor_role,
            action="PATIENT_REGISTER",
            target_type="Patient",
            target_ref=patient_ref,
            details=f"Registered patient {full_name} ({condition_category}) under facility ID {facility_id}."
        )
        
        return True, f"Patient {full_name} successfully registered with reference {patient_ref}.", patient_ref
    except Exception as e:
        return False, f"Database error during patient registration: {str(e)}", None

def update_patient(patient_id: int,
                   full_name: str,
                   age: int,
                   sex: str,
                   facility_id: int,
                   condition_category: str,
                   district: str,
                   followup_status: str,
                   sector: Optional[str] = None,
                   phone_number: Optional[str] = None,
                   clinical_summary: Optional[str] = None,
                   caregiver_name: Optional[str] = None,
                   caregiver_phone: Optional[str] = None,
                   actor_username: str = "system",
                   actor_role: str = "Healthcare Provider") -> Tuple[bool, str]:
    """Update existing patient details."""
    is_valid, err = validate_patient_input(
        full_name=full_name,
        age=age,
        sex=sex,
        district=district,
        condition_category=condition_category,
        phone_number=phone_number
    )
    if not is_valid:
        return False, err
        
    now_str = datetime.now().isoformat()
    try:
        execute_statement(
            """
            UPDATE patients SET
                full_name = ?, age = ?, sex = ?, facility_id = ?,
                condition_category = ?, district = ?, followup_status = ?,
                sector = ?, phone_number = ?, clinical_summary = ?,
                caregiver_name = ?, caregiver_phone = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                full_name.strip(), age, sex, facility_id, condition_category,
                district.strip(), followup_status, sector.strip() if sector else None,
                phone_number.strip() if phone_number else None,
                clinical_summary.strip() if clinical_summary else None,
                caregiver_name.strip() if caregiver_name else None,
                caregiver_phone.strip() if caregiver_phone else None,
                now_str, patient_id
            )
        )
        
        log_audit_action(
            username=actor_username,
            role=actor_role,
            action="PATIENT_UPDATE",
            target_type="Patient",
            target_ref=str(patient_id),
            details=f"Updated demographic/clinical record for patient ID {patient_id}."
        )
        return True, "Patient record updated successfully."
    except Exception as e:
        return False, f"Database error updating patient: {str(e)}"

def get_patient_by_id(patient_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve full patient profile with facility name."""
    row = execute_single(
        """
        SELECT p.*, f.name as facility_name, f.code as facility_code, f.district as facility_district
        FROM patients p
        JOIN facilities f ON p.facility_id = f.id
        WHERE p.id = ?
        """,
        (patient_id,)
    )
    return dict(row) if row else None

def get_patient_by_ref(patient_ref: str) -> Optional[Dict[str, Any]]:
    """Retrieve patient record by system reference code."""
    row = execute_single(
        """
        SELECT p.*, f.name as facility_name, f.code as facility_code, f.district as facility_district
        FROM patients p
        JOIN facilities f ON p.facility_id = f.id
        WHERE LOWER(p.patient_ref) = LOWER(?)
        """,
        (patient_ref.strip(),)
    )
    return dict(row) if row else None

def search_patients(query: Optional[str] = None,
                    condition: Optional[str] = None,
                    facility_id: Optional[int] = None,
                    status: Optional[str] = None,
                    district: Optional[str] = None) -> List[Dict[str, Any]]:
    """Filter and search patient records."""
    sql = """
        SELECT p.id, p.patient_ref, p.full_name, p.age, p.sex, p.phone_number,
               p.district, p.condition_category, p.followup_status, p.registration_date,
               f.name as facility_name, f.code as facility_code
        FROM patients p
        JOIN facilities f ON p.facility_id = f.id
        WHERE 1=1
    """
    params = []
    
    if query and query.strip():
        q = f"%{query.strip()}%"
        sql += " AND (p.full_name LIKE ? OR p.patient_ref LIKE ? OR p.phone_number LIKE ?)"
        params.extend([q, q, q])
        
    if condition and condition != "All Conditions":
        sql += " AND p.condition_category = ?"
        params.append(condition)
        
    if facility_id and facility_id > 0:
        sql += " AND p.facility_id = ?"
        params.append(facility_id)
        
    if status and status != "All Statuses":
        sql += " AND p.followup_status = ?"
        params.append(status)
        
    if district and district != "All Districts":
        sql += " AND p.district = ?"
        params.append(district)
        
    sql += " ORDER BY p.id DESC"
    
    rows = execute_query(sql, tuple(params))
    return [dict(r) for r in rows]

def get_patient_timeline(patient_id: int) -> List[Dict[str, Any]]:
    """
    Compile a chronological history of all clinical, appointment,
    discharge, and support assessment events for a single patient.
    """
    events = []
    
    # 1. Registration
    p = get_patient_by_id(patient_id)
    if p:
        events.append({
            "event_type": "Registration",
            "date": p["registration_date"],
            "title": f"Initial Care Registration ({p['patient_ref']})",
            "summary": f"Registered at {p['facility_name']} for {p['condition_category']}. Initial status: {p['followup_status']}.",
            "status": "Active"
        })
        
    # 2. Discharges
    discharges = execute_query(
        "SELECT * FROM discharges WHERE patient_id = ? ORDER BY discharge_date DESC",
        (patient_id,)
    )
    for d in discharges:
        events.append({
            "event_type": "Hospital Discharge",
            "date": d["discharge_date"],
            "title": f"Discharge ({d['discharge_ref']}) - Admitted {d['admission_date']}",
            "summary": f"Diagnosis: {d['diagnosis_summary']}. Next Follow-Up: {d['recommended_appointment_date']}. Instructions: {d['followup_instructions']}",
            "status": d["status"]
        })
        
    # 3. Appointments
    apts = execute_query(
        "SELECT * FROM appointments WHERE patient_id = ? ORDER BY scheduled_date DESC",
        (patient_id,)
    )
    for a in apts:
        events.append({
            "event_type": "Appointment",
            "date": a["scheduled_date"],
            "title": f"Appointment ({a['appointment_ref']}) - {a['followup_type']}",
            "summary": f"Assigned to: {a['responsible_worker']}. Notes: {a['outcome_notes'] or a['rescheduled_reason'] or 'Scheduled'}",
            "status": a["status"]
        })
        
    # 4. Follow-up interaction records
    flws = execute_query(
        "SELECT * FROM followup_records WHERE patient_id = ? ORDER BY interaction_date DESC",
        (patient_id,)
    )
    for f in flws:
        events.append({
            "event_type": "Follow-Up Interaction",
            "date": f["interaction_date"],
            "title": f"Interaction ({f['record_ref']}) - {f['followup_type']}",
            "summary": f"Adherence: {f['medication_adherence'] or 'N/A'}. Action: {f['action_taken']}. Status: {f['patient_status_summary']}",
            "status": "Completed"
        })
        
    # 5. Support assessments
    assessments = execute_query(
        "SELECT * FROM support_assessments WHERE patient_id = ? ORDER BY assessment_date DESC",
        (patient_id,)
    )
    for s in assessments:
        events.append({
            "event_type": "Support Assessment",
            "date": s["assessment_date"],
            "title": f"Assessment ({s['assessment_ref']}) - {s['vulnerability_tier']}",
            "summary": f"Assessor: {s['assessor_name']}. Recommended: {s['support_actions_recommended']}",
            "status": s["support_status"]
        })
        
    # Sort events by date descending
    events.sort(key=lambda x: str(x["date"]), reverse=True)
    return events
