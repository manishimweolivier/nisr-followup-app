"""
Fictional Demonstration Dataset for FollowUp
Strictly fictional patient records designed for clinical testing and workflow demonstrations.
Contains realistic Rwandan healthcare continuity scenarios clearly flagged as fictional.
"""

from datetime import datetime, date, timedelta
from typing import Dict, Any, List
import json

import config
from database.connection import execute_statement, execute_single, get_db_connection
from utils.security import generate_reference

def seed_demo_data(force_reset: bool = False) -> int:
    """
    Populate or reset fictional demonstration patient records, discharges,
    appointments, follow-up interactions, vulnerability assessments, and tasks.
    Returns the number of demonstration patients seeded.
    """
    if force_reset:
        reset_demo_data()
        
    # Check if demo data already exists
    row = execute_single("SELECT COUNT(*) as count FROM patients WHERE is_demo = 1")
    if row and row["count"] > 0 and not force_reset:
        return row["count"]
        
    today = date.today()
    now_str = datetime.now().isoformat()
    
    # 1. Fetch facility IDs by code
    fac_map = {}
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, code FROM facilities")
        for r in cursor.fetchall():
            fac_map[r["code"]] = r["id"]
            
    chuk_id = fac_map.get("CHUK", 1)
    chub_id = fac_map.get("CHUB", 2)
    rmh_id = fac_map.get("RMH", 3)
    kbg_id = fac_map.get("KBG", 4)
    msk_id = fac_map.get("MSK", 5)
    kcy_id = fac_map.get("KCY", 6)
    rwm_id = fac_map.get("RWM", 7)
    btr_id = fac_map.get("BTR", 9)
    
    # Demonstration Patient Definitions
    # Scenario 1: Discharged from hospital, next appointment approaching in 4 days
    # Scenario 2: Missed appointment, documented transportation difficulties
    # Scenario 3: Chronic condition, routine follow-up
    # Scenario 4: Repeated missed appointments, requires human review
    # Scenario 5: Completed follow-up trajectory
    demo_patients = [
        # 1. Discharged patient with upcoming appointment (Scenario 1)
        {
            "ref": "FOL-2026-0001",
            "name": "Jean-Pierre Habimana",
            "dob": "1972-04-12",
            "age": 54,
            "sex": "Male",
            "phone": "+250 788 412 801",
            "facility_id": chuk_id,
            "condition": "Type 2 Diabetes",
            "district": "Nyarugenge",
            "sector": "Nyamirambo",
            "cell": "Mumena",
            "village": "Rugarama",
            "clinical_summary": "Discharged post acute diabetic ketoacidosis stabilization. Transitioned to basal-bolus insulin regimen.",
            "reg_date": (today - timedelta(days=20)).isoformat(),
            "status": "Active Follow-Up",
            "caregiver": "Marie Claire Mukamana (Wife)",
            "caregiver_phone": "+250 788 412 802",
            "scenario": 1
        },
        # 2. Missed appointment with transportation barrier (Scenario 2)
        {
            "ref": "FOL-2026-0002",
            "name": "Claudine Mukamana",
            "dob": "1980-08-25",
            "age": 46,
            "sex": "Female",
            "phone": "+250 783 551 204",
            "facility_id": msk_id,
            "condition": "Chronic Kidney Disease",
            "district": "Kicukiro",
            "sector": "Masaka",
            "cell": "Rango",
            "village": "Gako",
            "clinical_summary": "Stage 3b CKD secondary to hypertension. Strict nephrology monitoring required.",
            "reg_date": (today - timedelta(days=45)).isoformat(),
            "status": "Active Follow-Up",
            "caregiver": "Patrick Bizimungu (Son)",
            "caregiver_phone": "+250 783 551 205",
            "scenario": 2
        },
        # 3. Chronic condition routine follow-up (Scenario 3)
        {
            "ref": "FOL-2026-0003",
            "name": "Emmanuel Nkurunziza",
            "dob": "1963-11-03",
            "age": 63,
            "sex": "Male",
            "phone": "+250 782 109 874",
            "facility_id": rwm_id,
            "condition": "Hypertension",
            "district": "Rwamagana",
            "sector": "Kigabiro",
            "cell": "Nyagasenyi",
            "village": "Mubuga",
            "clinical_summary": "Essential hypertension managed on Amlodipine 10mg + Losartan 50mg. Stable blood pressure trajectory.",
            "reg_date": (today - timedelta(days=90)).isoformat(),
            "status": "Active Follow-Up",
            "caregiver": None,
            "caregiver_phone": None,
            "scenario": 3
        },
        # 4. Repeated missed appointments requiring human review (Scenario 4)
        {
            "ref": "FOL-2026-0004",
            "name": "Agnes Nyirahabimana",
            "dob": "1975-02-18",
            "age": 51,
            "sex": "Female",
            "phone": "+250 781 990 312",
            "facility_id": kbg_id,
            "condition": "Cancer (Oncology Continuing Care)",
            "district": "Gasabo",
            "sector": "Kimironko",
            "cell": "Bibare",
            "village": "Kibagabaga",
            "clinical_summary": "Post-mastectomy breast cancer undergoing adjuvant hormonal therapy. Two missed surveillance cycles.",
            "reg_date": (today - timedelta(days=75)).isoformat(),
            "status": "Requires Review",
            "caregiver": "Alice Uwera (Sister)",
            "caregiver_phone": "+250 781 990 313",
            "scenario": 4
        },
        # 5. Completed follow-up trajectory (Scenario 5)
        {
            "ref": "FOL-2026-0005",
            "name": "Théogène Bizimana",
            "dob": "1988-06-30",
            "age": 38,
            "sex": "Male",
            "phone": "+250 785 224 991",
            "facility_id": rmh_id,
            "condition": "Post-Surgical Follow-Up",
            "district": "Kicukiro",
            "sector": "Kanombe",
            "cell": "Busanza",
            "village": "Rebero",
            "clinical_summary": "Open reduction internal fixation (ORIF) right tibia fracture. Complete radiological union confirmed.",
            "reg_date": (today - timedelta(days=120)).isoformat(),
            "status": "Completed",
            "caregiver": "Jeanne Mukarugwiro (Spouse)",
            "caregiver_phone": "+250 785 224 992",
            "scenario": 5
        },
        # 6. Additional realistic patient: Oncology continuing care with long distance
        {
            "ref": "FOL-2026-0006",
            "name": "Innocent Gasana",
            "dob": "1969-09-14",
            "age": 57,
            "sex": "Male",
            "phone": "+250 788 901 234",
            "facility_id": btr_id,
            "condition": "Cancer (Oncology Continuing Care)",
            "district": "Burera",
            "sector": "Rugarama",
            "cell": "Gafumba",
            "village": "Kagogo",
            "clinical_summary": "Chronic lymphocytic leukemia under maintenance chemotherapy. Remote residence with long mountain walk.",
            "reg_date": (today - timedelta(days=60)).isoformat(),
            "status": "Active Follow-Up",
            "caregiver": "Donatha Nyiraneza (Daughter)",
            "caregiver_phone": "+250 788 901 235",
            "scenario": 6
        },
        # 7. Additional realistic patient: Maternal high-risk postpartum care
        {
            "ref": "FOL-2026-0007",
            "name": "Chantal Mutoni",
            "dob": "1994-12-05",
            "age": 31,
            "sex": "Female",
            "phone": "+250 787 654 321",
            "facility_id": kcy_id,
            "condition": "Maternal High-Risk Postpartum Care",
            "district": "Gasabo",
            "sector": "Kacyiru",
            "cell": "Kamatamu",
            "village": "Inyange",
            "clinical_summary": "Postpartum pre-eclampsia follow-up. Monitoring proteinuria and titration of antihypertensive medications.",
            "reg_date": (today - timedelta(days=14)).isoformat(),
            "status": "Active Follow-Up",
            "caregiver": "Eric Kalisa (Husband)",
            "caregiver_phone": "+250 787 654 322",
            "scenario": 7
        }
    ]
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Insert Patients
        for p in demo_patients:
            cursor.execute(
                """
                INSERT OR REPLACE INTO patients (
                    patient_ref, full_name, date_of_birth, age, sex, phone_number,
                    district, sector, cell, village, facility_id, condition_category,
                    clinical_summary, registration_date, followup_status, caregiver_name,
                    caregiver_phone, is_demo, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (
                    p["ref"], p["name"], p["dob"], p["age"], p["sex"], p["phone"],
                    p["district"], p["sector"], p["cell"], p["village"], p["facility_id"],
                    p["condition"], p["clinical_summary"], p["reg_date"], p["status"],
                    p["caregiver"], p["caregiver_phone"], now_str, now_str
                )
            )
            
            # Fetch generated patient id
            cursor.execute("SELECT id FROM patients WHERE patient_ref = ?", (p["ref"],))
            p_id = cursor.fetchone()["id"]
            
            # --- Scenario 1 Specific Seeding (Discharged, upcoming appointment) ---
            if p["scenario"] == 1:
                # Discharge record
                cursor.execute(
                    """
                    INSERT INTO discharges (
                        discharge_ref, patient_id, facility_id, admission_date, discharge_date,
                        diagnosis_summary, condition_category, followup_instructions,
                        recommended_appointment_date, responsible_clinician,
                        discharge_support_needs, status, is_demo, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Open', 1, ?)
                    """,
                    (
                        "DIS-2026-0001", p_id, chuk_id,
                        (today - timedelta(days=15)).isoformat(),
                        (today - timedelta(days=8)).isoformat(),
                        "Type 2 Diabetes Mellitus with Ketoacidosis and Grade II Essential Hypertension.",
                        "Type 2 Diabetes",
                        "Maintain insulin glargine 18 units at bedtime, lispro 4 units with meals. Check fasting capillary glucose daily. Return in 2 weeks.",
                        (today + timedelta(days=4)).isoformat(),
                        "Dr. David Mucyo, MD",
                        "Patient requires glucometer test strips voucher and dietary counseling follow-up.",
                        now_str
                    )
                )
                # Upcoming appointment (approaching in 4 days)
                cursor.execute(
                    """
                    INSERT INTO appointments (
                        appointment_ref, patient_id, facility_id, scheduled_date, scheduled_time,
                        followup_type, responsible_worker, status, outcome_notes, is_demo, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, '10:00', 'Facility Clinical Consultation', 'Dr. David Mucyo, MD', 'Scheduled', 'Post-discharge 2-week metabolic review.', 1, ?, ?)
                    """,
                    ("APT-2026-0001", p_id, chuk_id, (today + timedelta(days=4)).isoformat(), now_str, now_str)
                )
                
            # --- Scenario 2 Specific Seeding (Missed appointment + Transport difficulty) ---
            elif p["scenario"] == 2:
                # Past missed appointment (scheduled 3 days ago)
                cursor.execute(
                    """
                    INSERT INTO appointments (
                        appointment_ref, patient_id, facility_id, scheduled_date, scheduled_time,
                        followup_type, responsible_worker, status, outcome_notes, is_demo, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, '09:30', 'Facility Clinical Consultation', 'Nurse Marie Keza, RN', 'Missed', 'Patient did not arrive. Phone call placed; reported inability to afford transport fare from Masaka rural sector.', 1, ?, ?)
                    """,
                    ("APT-2026-0002", p_id, msk_id, (today - timedelta(days=3)).isoformat(), now_str, now_str)
                )
                # Vulnerability Assessment documenting transport & financial barrier
                cursor.execute(
                    """
                    INSERT INTO support_assessments (
                        assessment_ref, patient_id, assessment_date, assessor_name,
                        financial_difficulties, transport_difficulties, long_distance_facility,
                        lack_of_caregiver, medicine_access_difficulty, repeated_missed_appointments,
                        food_insecurity, disability_mobility_barrier, other_barriers,
                        vulnerability_score, vulnerability_tier, support_actions_recommended,
                        support_status, review_notes, is_demo, created_at
                    ) VALUES (?, ?, ?, 'Nurse Marie Keza, RN', 1, 1, 1, 0, 1, 0, 0, 0, 'Heavy rain made unpaved feeder road impassable by public moto.', 4, 'High Continuity Risk', 'Coordinate community health worker home visit and provide community transport subsidy assistance.', 'Active', 'Patient motivated to continue treatment but restricted by transport expenditure.', 1, ?)
                    """,
                    ("ASS-2026-0001", p_id, (today - timedelta(days=2)).isoformat(), now_str)
                )
                # Follow-up task to assist patient
                cursor.execute(
                    """
                    INSERT INTO tasks (
                        task_ref, patient_id, title, description, assigned_to, assigned_by,
                        priority, status, due_date, is_demo, created_at, updated_at
                    ) VALUES (?, ?, 'Arrange Community Health Worker Home Check & Transport Voucher', 'Contact cell CHW coordinator to deliver blood pressure check and organize clinic transport assistance.', 'officer.aline', 'nurse.keza', 'High Priority', 'Pending', ?, 1, ?, ?)
                    """,
                    ("TSK-2026-0001", p_id, (today + timedelta(days=1)).isoformat(), now_str, now_str)
                )
                
            # --- Scenario 3 Specific Seeding (Chronic condition routine follow-up) ---
            elif p["scenario"] == 3:
                # Past completed appointment
                cursor.execute(
                    """
                    INSERT INTO appointments (
                        appointment_ref, patient_id, facility_id, scheduled_date, scheduled_time,
                        followup_type, responsible_worker, status, completed_date, outcome_notes,
                        next_recommended_date, is_demo, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, '11:00', 'Facility Clinical Consultation', 'Jean Claude Ndayisaba (CHW Liaison)', 'Completed', ?, 'Blood pressure controlled at 128/82 mmHg. Adherence confirmed. 90-day refill dispensed.', ?, 1, ?, ?)
                    """,
                    (
                        "APT-2026-0003", p_id, rwm_id,
                        (today - timedelta(days=30)).isoformat(),
                        (today - timedelta(days=30)).isoformat(),
                        (today + timedelta(days=60)).isoformat(),
                        now_str, now_str
                    )
                )
                # Next scheduled routine appointment
                cursor.execute(
                    """
                    INSERT INTO appointments (
                        appointment_ref, patient_id, facility_id, scheduled_date, scheduled_time,
                        followup_type, responsible_worker, status, outcome_notes, is_demo, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, '11:00', 'Facility Clinical Consultation', 'Jean Claude Ndayisaba (CHW Liaison)', 'Scheduled', 'Routine 3-month cardiovascular follow-up.', 1, ?, ?)
                    """,
                    ("APT-2026-0004", p_id, rwm_id, (today + timedelta(days=60)).isoformat(), now_str, now_str)
                )
                # Followup interaction log
                cursor.execute(
                    """
                    INSERT INTO followup_records (
                        record_ref, patient_id, interaction_date, followup_type, responsible_worker,
                        patient_status_summary, medication_adherence, reported_barriers, action_taken,
                        next_steps, next_followup_date, is_demo, created_at
                    ) VALUES (?, ?, ?, 'Facility Clinical Consultation', 'Jean Claude Ndayisaba', 'Stable and asymptomatic.', 'Full', '[]', 'Refilled amlodipine, checked BP, scheduled next routine review.', 'Continue low sodium diet and regular walking.', ?, 1, ?)
                    """,
                    (
                        "FLW-2026-0001", p_id, (today - timedelta(days=30)).isoformat(),
                        (today + timedelta(days=60)).isoformat(), now_str
                    )
                )
                
            # --- Scenario 4 Specific Seeding (Repeated missed appointments, requires review) ---
            elif p["scenario"] == 4:
                # Two missed appointments in the past
                cursor.execute(
                    """
                    INSERT INTO appointments (
                        appointment_ref, patient_id, facility_id, scheduled_date, scheduled_time,
                        followup_type, responsible_worker, status, outcome_notes, is_demo, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, '08:30', 'Facility Clinical Consultation', 'Dr. David Mucyo, MD', 'Missed', 'First missed oncology surveillance cycle. Patient uncontactable on registered phone number.', 1, ?, ?)
                    """,
                    ("APT-2026-0005", p_id, kbg_id, (today - timedelta(days=40)).isoformat(), now_str, now_str)
                )
                cursor.execute(
                    """
                    INSERT INTO appointments (
                        appointment_ref, patient_id, facility_id, scheduled_date, scheduled_time,
                        followup_type, responsible_worker, status, outcome_notes, is_demo, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, '09:00', 'Facility Clinical Consultation', 'Dr. David Mucyo, MD', 'Missed', 'Second consecutive missed visit. Serious concern regarding discontinuation of endocrine therapy.', 1, ?, ?)
                    """,
                    ("APT-2026-0006", p_id, kbg_id, (today - timedelta(days=10)).isoformat(), now_str, now_str)
                )
                # High Risk Assessment
                cursor.execute(
                    """
                    INSERT INTO support_assessments (
                        assessment_ref, patient_id, assessment_date, assessor_name,
                        financial_difficulties, transport_difficulties, long_distance_facility,
                        lack_of_caregiver, medicine_access_difficulty, repeated_missed_appointments,
                        food_insecurity, disability_mobility_barrier, other_barriers,
                        vulnerability_score, vulnerability_tier, support_actions_recommended,
                        support_status, review_notes, is_demo, created_at
                    ) VALUES (?, ?, ?, 'Aline Uwase (Follow-Up Coordinator)', 1, 0, 0, 1, 1, 1, 0, 0, 'Caregiver relocated out of district; patient reports high emotional burden and medication side effects.', 4, 'High Continuity Risk', 'Escalate case to oncology multidisciplinary team; conduct physical home tracer visit with community health worker.', 'In Review', 'Case escalated to Hospital Follow-Up Review Board.', 1, ?)
                    """,
                    ("ASS-2026-0002", p_id, (today - timedelta(days=8)).isoformat(), now_str)
                )
                # Urgent Task
                cursor.execute(
                    """
                    INSERT INTO tasks (
                        task_ref, patient_id, title, description, assigned_to, assigned_by,
                        priority, status, due_date, is_demo, created_at, updated_at
                    ) VALUES (?, ?, 'URGENT: Home Tracer Visit for Missed Oncology Care', 'Dispatch community health officer to Bibare cell to locate patient and assess well-being.', 'officer.aline', 'dr.mucyo', 'Urgent Review', 'In Progress', ?, 1, ?, ?)
                    """,
                    ("TSK-2026-0002", p_id, today.isoformat(), now_str, now_str)
                )
                
            # --- Scenario 5 Specific Seeding (Completed follow-up trajectory) ---
            elif p["scenario"] == 5:
                # Past discharge
                cursor.execute(
                    """
                    INSERT INTO discharges (
                        discharge_ref, patient_id, facility_id, admission_date, discharge_date,
                        diagnosis_summary, condition_category, followup_instructions,
                        recommended_appointment_date, responsible_clinician,
                        discharge_support_needs, status, is_demo, created_at
                    ) VALUES (?, ?, ?, ?, ?, 'Closed tibial shaft fracture, treated with intramedullary nailing.', 'Post-Surgical Follow-Up', 'Progressive weight bearing with crutches. Wound care. Stitches removal in 14 days.', ?, 'Dr. Jean Paul Habineza (Orthopedic Surgeon)', 'Short-term crutches support.', 'Completed', 1, ?)
                    """,
                    (
                        "DIS-2026-0002", p_id, rmh_id,
                        (today - timedelta(days=120)).isoformat(),
                        (today - timedelta(days=115)).isoformat(),
                        (today - timedelta(days=100)).isoformat(),
                        now_str
                    )
                )
                # Completed appointment 1
                cursor.execute(
                    """
                    INSERT INTO appointments (
                        appointment_ref, patient_id, facility_id, scheduled_date, scheduled_time,
                        followup_type, responsible_worker, status, completed_date, outcome_notes, is_demo, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, '09:00', 'Facility Clinical Consultation', 'Dr. Jean Paul Habineza', 'Completed', ?, 'Wound clean, sutures removed without complications.', 1, ?, ?)
                    """,
                    ("APT-2026-0007", p_id, rmh_id, (today - timedelta(days=100)).isoformat(), (today - timedelta(days=100)).isoformat(), now_str, now_str)
                )
                # Completed appointment 2 (Final discharge)
                cursor.execute(
                    """
                    INSERT INTO appointments (
                        appointment_ref, patient_id, facility_id, scheduled_date, scheduled_time,
                        followup_type, responsible_worker, status, completed_date, outcome_notes, is_demo, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, '10:30', 'Facility Clinical Consultation', 'Dr. Jean Paul Habineza', 'Completed', ?, 'Radiographs confirm full bone consolidation. Full weight bearing restored. Follow-up program discharged.', 1, ?, ?)
                    """,
                    ("APT-2026-0008", p_id, rmh_id, (today - timedelta(days=20)).isoformat(), (today - timedelta(days=20)).isoformat(), now_str, now_str)
                )
                # Completed task
                cursor.execute(
                    """
                    INSERT INTO tasks (
                        task_ref, patient_id, title, description, assigned_to, assigned_by,
                        priority, status, due_date, completion_date, action_taken, is_demo, created_at, updated_at
                    ) VALUES (?, ?, 'Final Post-Surgical Functional Assessment', 'Verify full gait recovery and radiological healing prior to closing care trajectory.', 'officer.aline', 'dr.mucyo', 'Routine', 'Completed', ?, ?, 'Full mobility achieved. Case closed.', 1, ?, ?)
                    """,
                    ("TSK-2026-0003", p_id, (today - timedelta(days=20)).isoformat(), (today - timedelta(days=20)).isoformat(), now_str, now_str)
                )
                
            # --- Scenario 6: Oncology continuing care with long distance ---
            elif p["scenario"] == 6:
                # Due today appointment
                cursor.execute(
                    """
                    INSERT INTO appointments (
                        appointment_ref, patient_id, facility_id, scheduled_date, scheduled_time,
                        followup_type, responsible_worker, status, outcome_notes, is_demo, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, '08:00', 'Laboratory & Diagnostic Review', 'Aline Uwase', 'Due', 'Complete blood count and liver function panel before cycle 4.', 1, ?, ?)
                    """,
                    ("APT-2026-0009", p_id, btr_id, today.isoformat(), now_str, now_str)
                )
                # Assessment documenting distance barrier
                cursor.execute(
                    """
                    INSERT INTO support_assessments (
                        assessment_ref, patient_id, assessment_date, assessor_name,
                        financial_difficulties, transport_difficulties, long_distance_facility,
                        lack_of_caregiver, medicine_access_difficulty, repeated_missed_appointments,
                        food_insecurity, disability_mobility_barrier, other_barriers,
                        vulnerability_score, vulnerability_tier, support_actions_recommended,
                        support_status, review_notes, is_demo, created_at
                    ) VALUES (?, ?, ?, 'Aline Uwase', 1, 1, 1, 0, 0, 0, 0, 0, 'Resides in steep terrain in Burera district; takes >2.5 hours to reach tarmac road.', 3, 'Moderate Vulnerability', 'Coordinate decentralized lab sample pickup at nearest health center.', 'Active', 'Monitoring lab schedule.', 1, ?)
                    """,
                    ("ASS-2026-0003", p_id, (today - timedelta(days=15)).isoformat(), now_str)
                )
                
            # --- Scenario 7: Maternal high-risk postpartum care ---
            elif p["scenario"] == 7:
                # Scheduled appointment in 2 days
                cursor.execute(
                    """
                    INSERT INTO appointments (
                        appointment_ref, patient_id, facility_id, scheduled_date, scheduled_time,
                        followup_type, responsible_worker, status, outcome_notes, is_demo, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, '14:00', 'Facility Clinical Consultation', 'Nurse Marie Keza, RN', 'Scheduled', 'Day 16 postpartum blood pressure and proteinuria evaluation.', 1, ?, ?)
                    """,
                    ("APT-2026-0010", p_id, kcy_id, (today + timedelta(days=2)).isoformat(), now_str, now_str)
                )

    return len(demo_patients)

def reset_demo_data():
    """
    Safely delete ONLY fictional demonstration records (is_demo = 1).
    Preserves all actual user-created records (is_demo = 0) without loss.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE is_demo = 1")
        cursor.execute("DELETE FROM support_assessments WHERE is_demo = 1")
        cursor.execute("DELETE FROM followup_records WHERE is_demo = 1")
        cursor.execute("DELETE FROM appointments WHERE is_demo = 1")
        cursor.execute("DELETE FROM discharges WHERE is_demo = 1")
        cursor.execute("DELETE FROM patients WHERE is_demo = 1")
