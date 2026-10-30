"""
Validation Service for FollowUp
Ensures clinical and administrative inputs comply with integrity constraints.
"""

import re
from datetime import date, datetime
from typing import Tuple, Optional
from utils.helpers import parse_iso_date

def validate_patient_input(full_name: str, age: int, sex: str, district: str,
                           condition_category: str, phone_number: Optional[str] = None) -> Tuple[bool, str]:
    """Validate registration and update parameters for patient records."""
    if not full_name or len(full_name.strip()) < 3:
        return False, "Patient full name is required and must be at least 3 characters."
        
    if not isinstance(age, int) or age < 0 or age > 130:
        return False, "Age must be a valid integer between 0 and 130 years."
        
    if sex not in ["Female", "Male", "Other"]:
        return False, "Sex must be specified as Female, Male, or Other."
        
    if not district or len(district.strip()) < 2:
        return False, "District of residence is required."
        
    if not condition_category or len(condition_category.strip()) < 3:
        return False, "A valid chronic condition category must be selected."
        
    if phone_number and phone_number.strip():
        # Validate phone format (e.g. +250 78... or 078...)
        clean_phone = re.sub(r'[\s\-\(\)]', '', phone_number.strip())
        if not re.match(r'^\+?[0-9]{9,15}$', clean_phone):
            return False, "Phone number format is invalid. Please enter a valid telephone number."
            
    return True, ""

def validate_discharge_input(admission_date_str: str, discharge_date_str: str,
                             recommended_apt_date_str: str, diagnosis: str,
                             instructions: str) -> Tuple[bool, str]:
    """Validate hospital discharge dates and clinical continuity instructions."""
    adm_dt = parse_iso_date(admission_date_str)
    dis_dt = parse_iso_date(discharge_date_str)
    rec_dt = parse_iso_date(recommended_apt_date_str)
    
    if not adm_dt:
        return False, "A valid hospital admission date is required."
    if not dis_dt:
        return False, "A valid discharge date is required."
    if not rec_dt:
        return False, "A recommended next follow-up appointment date is required."
        
    if dis_dt < adm_dt:
        return False, "Discharge date cannot be earlier than admission date."
        
    if rec_dt < dis_dt:
        return False, "Recommended follow-up appointment date must be on or after discharge date."
        
    if not diagnosis or len(diagnosis.strip()) < 4:
        return False, "A clinical diagnosis summary is required."
        
    if not instructions or len(instructions.strip()) < 5:
        return False, "Discharge follow-up care instructions are required."
        
    return True, ""

def validate_appointment_input(scheduled_date_str: str, followup_type: str,
                               responsible_worker: str) -> Tuple[bool, str]:
    """Validate follow-up appointment parameters."""
    sch_dt = parse_iso_date(scheduled_date_str)
    if not sch_dt:
        return False, "A valid appointment date is required."
        
    if not followup_type or len(followup_type.strip()) < 3:
        return False, "Follow-up modality type must be selected."
        
    if not responsible_worker or len(responsible_worker.strip()) < 2:
        return False, "Responsible healthcare worker or officer must be designated."
        
    return True, ""

def validate_task_input(title: str, assigned_to: str, due_date_str: str) -> Tuple[bool, str]:
    """Validate task creation parameters."""
    if not title or len(title.strip()) < 4:
        return False, "Task title is required and must be at least 4 characters."
    if not assigned_to or len(assigned_to.strip()) < 2:
        return False, "Task must be assigned to a designated healthcare worker or officer."
    if not parse_iso_date(due_date_str):
        return False, "A valid deadline date is required."
    return True, ""
