"""
Database Schema Definitions and Models for FollowUp
Defines relational schemas for users, facilities, patients, discharges,
appointments, follow-up interactions, vulnerability assessments, tasks,
audit logs, and statistical data.
"""

SCHEMA_SQL = """
-- Facilities Table
CREATE TABLE IF NOT EXISTS facilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    district TEXT NOT NULL,
    province TEXT NOT NULL,
    facility_type TEXT NOT NULL,
    contact_phone TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL
);

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    facility TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    last_login TEXT
);

-- Patients Table
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_ref TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    date_of_birth TEXT,
    age INTEGER NOT NULL,
    sex TEXT NOT NULL,
    phone_number TEXT,
    alternate_phone TEXT,
    district TEXT NOT NULL,
    sector TEXT,
    cell TEXT,
    village TEXT,
    facility_id INTEGER NOT NULL,
    condition_category TEXT NOT NULL,
    clinical_summary TEXT,
    registration_date TEXT NOT NULL,
    followup_status TEXT NOT NULL,
    caregiver_name TEXT,
    caregiver_phone TEXT,
    is_demo INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (facility_id) REFERENCES facilities(id) ON DELETE RESTRICT
);

-- Discharges Table
CREATE TABLE IF NOT EXISTS discharges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    discharge_ref TEXT UNIQUE NOT NULL,
    patient_id INTEGER NOT NULL,
    facility_id INTEGER NOT NULL,
    admission_date TEXT NOT NULL,
    discharge_date TEXT NOT NULL,
    diagnosis_summary TEXT NOT NULL,
    condition_category TEXT NOT NULL,
    followup_instructions TEXT NOT NULL,
    recommended_appointment_date TEXT NOT NULL,
    responsible_clinician TEXT NOT NULL,
    discharge_support_needs TEXT,
    status TEXT NOT NULL DEFAULT 'Open',
    is_demo INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (facility_id) REFERENCES facilities(id) ON DELETE RESTRICT
);

-- Appointments Table
CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    appointment_ref TEXT UNIQUE NOT NULL,
    patient_id INTEGER NOT NULL,
    facility_id INTEGER NOT NULL,
    scheduled_date TEXT NOT NULL,
    scheduled_time TEXT,
    followup_type TEXT NOT NULL,
    responsible_worker TEXT NOT NULL,
    status TEXT NOT NULL,
    completed_date TEXT,
    outcome_notes TEXT,
    next_recommended_date TEXT,
    rescheduled_reason TEXT,
    original_appointment_id INTEGER,
    is_demo INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (facility_id) REFERENCES facilities(id) ON DELETE RESTRICT,
    FOREIGN KEY (original_appointment_id) REFERENCES appointments(id) ON DELETE SET NULL
);

-- Follow-Up Interaction Records Table
CREATE TABLE IF NOT EXISTS followup_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_ref TEXT UNIQUE NOT NULL,
    patient_id INTEGER NOT NULL,
    appointment_id INTEGER,
    interaction_date TEXT NOT NULL,
    followup_type TEXT NOT NULL,
    responsible_worker TEXT NOT NULL,
    patient_status_summary TEXT NOT NULL,
    medication_adherence TEXT,
    reported_barriers TEXT,
    action_taken TEXT NOT NULL,
    next_steps TEXT,
    next_followup_date TEXT,
    is_demo INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE SET NULL
);

-- Patient Support & Continuity Vulnerability Assessments Table
CREATE TABLE IF NOT EXISTS support_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_ref TEXT UNIQUE NOT NULL,
    patient_id INTEGER NOT NULL,
    assessment_date TEXT NOT NULL,
    assessor_name TEXT NOT NULL,
    financial_difficulties INTEGER DEFAULT 0,
    transport_difficulties INTEGER DEFAULT 0,
    long_distance_facility INTEGER DEFAULT 0,
    lack_of_caregiver INTEGER DEFAULT 0,
    medicine_access_difficulty INTEGER DEFAULT 0,
    repeated_missed_appointments INTEGER DEFAULT 0,
    food_insecurity INTEGER DEFAULT 0,
    disability_mobility_barrier INTEGER DEFAULT 0,
    other_barriers TEXT,
    vulnerability_score INTEGER NOT NULL,
    vulnerability_tier TEXT NOT NULL,
    support_actions_recommended TEXT NOT NULL,
    support_status TEXT NOT NULL DEFAULT 'Active',
    review_notes TEXT,
    is_demo INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

-- Follow-Up Tasks Table
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_ref TEXT UNIQUE NOT NULL,
    patient_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    assigned_to TEXT NOT NULL,
    assigned_by TEXT NOT NULL,
    priority TEXT NOT NULL,
    status TEXT NOT NULL,
    due_date TEXT NOT NULL,
    completion_date TEXT,
    action_taken TEXT,
    is_demo INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

-- Audit Logs Table
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    username TEXT NOT NULL,
    role TEXT NOT NULL,
    action TEXT NOT NULL,
    target_type TEXT,
    target_ref TEXT,
    details TEXT
);

-- Statistical Datasets Metadata Table
CREATE TABLE IF NOT EXISTS statistical_datasets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_key TEXT UNIQUE NOT NULL,
    dataset_name TEXT NOT NULL,
    publishing_institution TEXT NOT NULL,
    source_url TEXT NOT NULL,
    reference_period TEXT NOT NULL,
    geographic_coverage TEXT NOT NULL,
    indicator_description TEXT NOT NULL,
    imported_at TEXT NOT NULL,
    row_count INTEGER NOT NULL
);

-- NISR District Health & Socioeconomic Indicators Table (Aggregate Population Data)
CREATE TABLE IF NOT EXISTS nisr_district_indicators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    district TEXT UNIQUE NOT NULL,
    province TEXT NOT NULL,
    poverty_rate_pct REAL NOT NULL,
    extreme_poverty_rate_pct REAL NOT NULL,
    health_insurance_coverage_pct REAL NOT NULL,
    travel_time_over_1hr_pct REAL NOT NULL,
    chronic_illness_reported_pct REAL NOT NULL,
    unimproved_sanitation_pct REAL NOT NULL,
    reference_survey TEXT NOT NULL,
    source_citation TEXT NOT NULL
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_patients_ref ON patients(patient_ref);
CREATE INDEX IF NOT EXISTS idx_patients_facility ON patients(facility_id);
CREATE INDEX IF NOT EXISTS idx_patients_status ON patients(followup_status);
CREATE INDEX IF NOT EXISTS idx_patients_condition ON patients(condition_category);
CREATE INDEX IF NOT EXISTS idx_patients_district ON patients(district);

CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id);
CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);

CREATE INDEX IF NOT EXISTS idx_discharges_patient ON discharges(patient_id);
CREATE INDEX IF NOT EXISTS idx_discharges_status ON discharges(status);

CREATE INDEX IF NOT EXISTS idx_followup_patient ON followup_records(patient_id);
CREATE INDEX IF NOT EXISTS idx_followup_date ON followup_records(interaction_date);

CREATE INDEX IF NOT EXISTS idx_support_patient ON support_assessments(patient_id);
CREATE INDEX IF NOT EXISTS idx_tasks_patient ON tasks(patient_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned ON tasks(assigned_to);

CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(username);
"""
