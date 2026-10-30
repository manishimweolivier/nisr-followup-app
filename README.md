# FollowUp: Patient Continuity-of-Care and Follow-Up Management System

A self-contained, fully local Python application engineered for healthcare providers to track chronic disease patients, coordinate hospital discharge transitions, manage appointments, screen for social and logistical barriers to care, assign outreach tasks, and contextualize continuity patterns using official population statistics from Rwanda's National Institute of Statistics (NISR).

---

## 1. System Overview

Patients with chronic conditions such as diabetes, hypertension, cardiovascular illness, and oncology post-acute care often encounter severe disruptions in continuity of care following hospital discharge. Barriers include:

- Financial constraints and out-of-pocket costs for medications.
- Geographic isolation and long travel times to health facilities (> 1 hour).
- Impassable secondary feeder roads and lack of reliable transit.
- Absence of family or caregiver support.
- Prescription stock-outs and refill hurdles.
- Repeated missed clinical appointments leading to care abandonment.

**FollowUp** provides clinical teams and community follow-up officers with an integrated local workstation to identify patients needing proactive outreach, track appointments, evaluate continuity barriers using transparent rule-based criteria, assign tasks, and generate verifiable audit reports.

---

## 2. Key Architecture & Design Principles

- **Completely Local & Offline-First:** Operates independently without requiring internet connectivity or external cloud backends. All data is persisted in a local SQLite database (`data/patient_care.db`) utilizing Write-Ahead Logging (WAL) and foreign key integrity.
- **Strict Data Distinction:** 
  - **Statistical Survey Data (NISR EICV7):** Describes aggregate, population-level socioeconomic and geographic conditions across Rwanda's 30 districts.
  - **Clinical Patient Records:** Confidential individual patient charts and appointment histories.
  - *These sources are kept strictly separate; survey statistics are never presented as individual patient data.*
- **Human Decision Support:** Continuity vulnerability tiers (Low, Moderate, High Continuity Risk) are calculated transparently using an 8-point barrier screening model to prioritize outreach. These are **never** medical diagnoses or automated clinical prognostications.
- **Role-Based Access Control (RBAC):** Granular permissions for Administrators, Healthcare Providers, Follow-Up Officers, and Read-Only Management, secured with salted PBKDF2-HMAC-SHA256 password hashing and audit logs.

---

## 3. Core Modules

| Module | Purpose & Core Capabilities |
|---|---|
| **Overview Dashboard** | Real-time operational KPIs: registered cohort, active follow-up, appointments due today, missed visits, review flags, and completion rates strictly computed from database records. |
| **Patient Management** | Unique sequential references (`FOL-2026-XXXX`), intake registration, search and multi-criteria filters, and longitudinal timeline compilation. |
| **Discharge Management** | Inpatient discharge records, care regimens, attending clinician directives, and automatic scheduling of initial post-discharge follow-up visits. |
| **Follow-Up Appointments** | Active tracking for upcoming and due appointments, chronological visit history, rescheduling with audit logs, and automatic overdue detection based on scheduled dates. |
| **Visits & Encounters** | Documentation of facility consultations, CHW home tracer visits, and phone check-ins including medication adherence, barrier checkboxes, and next steps. |
| **Support & Vulnerability** | Structured 8-point social determinants screening (transport, distance, finances, caregiver support, food security, mobility) with rule-based triage and task escalation. |
| **Task Management** | Allocation of outreach tasks to healthcare workers, deadline monitoring, priority flags (Routine, Medium, High Priority, Urgent Review), and completion logs. |
| **Reports & Analytics** | Quality analytics, comparative facility benchmarks across catchment hospitals, barrier frequency distributions, and CSV / PDF data exports. |
| **NISR Population Statistics** | Integration of official Rwanda NISR EICV7 (2023/24) indicators covering 30 districts (travel time >1hr, poverty, health insurance coverage, chronic illness) with CSV import capabilities. |
| **User Admin & Security** | Administrator console for user accounts, role allocation, immutable audit logs, and fictional demonstration dataset controls. |

---

## 4. Fictional Demonstration Dataset

The application includes pre-configured, realistic demonstration patient records reflecting Rwandan healthcare contexts:

1. **Scenario 1 (Approaching Appointment):** *Jean-Pierre Habimana* (`FOL-2026-0001`) - Discharged from CHUK post diabetic ketoacidosis; next scheduled metabolic review in 4 days.
2. **Scenario 2 (Missed Appointment with Transport Barrier):** *Claudine Mukamana* (`FOL-2026-0002`) - Stage 3b CKD at Masaka Hospital; missed visit due to impassable feeder roads and transit fares; high continuity risk assessment logged.
3. **Scenario 3 (Routine Chronic Follow-Up):** *Emmanuel Nkurunziza* (`FOL-2026-0003`) - Hypertension at Rwamagana Hospital; regular 3-month clinic visits with full adherence.
4. **Scenario 4 (Repeated Missed Visits Requiring Review):** *Agnes Nyirahabimana* (`FOL-2026-0004`) - Oncology continuing care at Kibagabaga Hospital; two missed surveillance cycles; urgent CHW home tracer task dispatched.
5. **Scenario 5 (Completed Trajectory):** *Théogène Bizimana* (`FOL-2026-0005`) - Post-surgical orthopedic care at Rwanda Military Hospital; full radiological union confirmed; case successfully closed.

> **Safeguard:** Demonstration records are tagged with `is_demo = 1`. In the Administrator console, users can reset or re-seed demonstration data without affecting any genuine user records (`is_demo = 0`).

---

## 5. Pre-Configured System Accounts

| Role | Username | Default Password | Permissions |
|---|---|---|---|
| **Administrator** | `admin` | `AdminSecure2026!` | Full administrative control, user creation, system settings, demo reset. |
| **Healthcare Provider** | `dr.mucyo` | `Provider2026!` | Patient registration, discharge recording, clinical evaluations, task assignment. |
| **Healthcare Provider** | `nurse.keza` | `Provider2026!` | Clinical appointments, support assessments, care coordination. |
| **Follow-Up Officer** | `officer.aline` | `Officer2026!` | Community visits, phone check-ins, task progress updates, outreach logs. |
| **Read-Only Management** | `mgmt.director` | `Review2026!` | Operational dashboards, analytics, NISR indicators, and reporting exports. |

---

## 6. Installation and Execution

### System Requirements
- Python 3.10, 3.11, 3.12, or 3.13.
- Windows 10/11, macOS, or Linux.
- No external database server or remote API keys required.

### Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-org/nisr-followup-app.git
   cd nisr-followup-app
   ```

2. **Create and activate a virtual environment:**
   - **Windows:**
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **macOS / Linux:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the application:**
   ```bash
   streamlit run app.py
   ```

5. The system will automatically:
   - Initialize the persistent SQLite database at `data/patient_care.db`.
   - Seed baseline partner facilities and user accounts.
   - Load official NISR EICV7 district indicators.
   - Populate fictional demonstration clinical scenarios.
   - Open your default browser at `http://localhost:8501`.

---

## 7. Automated Unit Tests

Execute the automated test suite covering database models, clinical validation logic, and appointment overdue calculations:

```bash
python -m unittest discover tests
```

To run individual test modules:
```bash
python -m unittest tests/test_database.py
python -m unittest tests/test_validation.py
python -m unittest tests/test_followups.py
```

---

## 8. Data Privacy & Confidentiality Notice

This software is designed to handle protected health information (PHI). 
- All data is maintained strictly on the local host machine.
- Passwords are encrypted with salt and PBKDF2 hashing.
- Administrative audit logs capture all record modifications.
- Fictional demonstration data is clearly marked and isolated from official NISR statistics.
