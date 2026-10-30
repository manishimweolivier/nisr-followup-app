"""
Application Configuration for FollowUp
Patient Continuity-of-Care and Follow-Up Management System
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables if available
load_dotenv(BASE_DIR / ".env")

# App Brand & Meta
APP_NAME = "FollowUp"
APP_SUBTITLE = "Patient Continuity-of-Care and Follow-Up Management System"
APP_VERSION = "1.0.0"

# Local Storage Paths
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

NISR_DATA_DIR = DATA_DIR / "nisr_datasets"
NISR_DATA_DIR.mkdir(exist_ok=True)

REPORTS_DIR = DATA_DIR / "generated_reports"
REPORTS_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "patient_care.db"

# Session Keys
SESSION_USER = "current_user"
SESSION_ROLE = "user_role"
SESSION_AUTH = "authenticated"

# User Roles
ROLE_ADMIN = "Administrator"
ROLE_PROVIDER = "Healthcare Provider"
ROLE_OFFICER = "Follow-Up Officer"
ROLE_READONLY = "Read-Only Management"

ALL_ROLES = [ROLE_ADMIN, ROLE_PROVIDER, ROLE_OFFICER, ROLE_READONLY]

# Clinical Condition Categories (Non-communicable diseases & high-risk chronic continuity cases)
CONDITION_CATEGORIES = [
    "Hypertension",
    "Type 2 Diabetes",
    "Type 1 Diabetes",
    "Cardiovascular Disease",
    "Cancer (Oncology Continuing Care)",
    "Chronic Respiratory Disease (Asthma / COPD)",
    "Chronic Kidney Disease",
    "Post-Surgical Follow-Up",
    "Maternal High-Risk Postpartum Care",
    "Other Chronic Condition"
]

# Follow-Up Types
FOLLOWUP_TYPES = [
    "Facility Clinical Consultation",
    "Community Health Worker Home Visit",
    "Phone Follow-Up Call",
    "Medication Adherence Check",
    "Laboratory & Diagnostic Review",
    "Support & Social Welfare Assessment"
]

# Follow-Up & Appointment Statuses
STATUS_SCHEDULED = "Scheduled"
STATUS_DUE = "Due"
STATUS_COMPLETED = "Completed"
STATUS_MISSED = "Missed"
STATUS_RESCHEDULED = "Rescheduled"
STATUS_REQUIRES_REVIEW = "Requires Review"

ALL_FOLLOWUP_STATUSES = [
    STATUS_SCHEDULED,
    STATUS_DUE,
    STATUS_COMPLETED,
    STATUS_MISSED,
    STATUS_RESCHEDULED,
    STATUS_REQUIRES_REVIEW
]

# Task Statuses & Priorities
TASK_STATUS_PENDING = "Pending"
TASK_STATUS_IN_PROGRESS = "In Progress"
TASK_STATUS_COMPLETED = "Completed"
TASK_STATUS_CANCELLED = "Cancelled"

ALL_TASK_STATUSES = [
    TASK_STATUS_PENDING,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_COMPLETED,
    TASK_STATUS_CANCELLED
]

TASK_PRIORITY_ROUTINE = "Routine"
TASK_PRIORITY_MEDIUM = "Medium"
TASK_PRIORITY_HIGH = "High Priority"
TASK_PRIORITY_URGENT = "Urgent Review"

ALL_TASK_PRIORITIES = [
    TASK_PRIORITY_ROUTINE,
    TASK_PRIORITY_MEDIUM,
    TASK_PRIORITY_HIGH,
    TASK_PRIORITY_URGENT
]

# Standard Partner Healthcare Facilities in Rwanda Catchment Network
DEFAULT_FACILITIES = [
    "University Teaching Hospital of Kigali (CHUK)",
    "University Teaching Hospital of Butare (CHUB)",
    "Rwanda Military Hospital (Kanombe)",
    "Kibagabaga District Hospital",
    "Masaka District Hospital",
    "Kacyiru District Hospital",
    "Rwamagana Provincial Hospital",
    "Ruhengeri Referral Hospital",
    "Butaro Cancer Centre of Excellence",
    "Nyamata District Hospital",
    "Gisenyi District Hospital",
    "Kabgayi District Hospital"
]

# Continuity Barriers (Social Determinants of Health)
BARRIER_TYPES = [
    "Financial constraints / Out-of-pocket costs",
    "Long distance to healthcare facility (> 1 hour)",
    "Lack of reliable transportation",
    "Lack of family or caregiver support",
    "Difficulty accessing or refilling prescribed medication",
    "Physical disability or mobility limitation",
    "Work or livelihood conflict",
    "Language, literacy or communication barrier",
    "Fear, stigma or psychological distress"
]

# Risk / Continuity Vulnerability Tiers
VULNERABILITY_LOW = "Low Vulnerability"
VULNERABILITY_MODERATE = "Moderate Vulnerability"
VULNERABILITY_HIGH = "High Continuity Risk"
