"""
Database Initialization and Migration System for FollowUp
Creates persistent local tables, default healthcare facilities, system users,
and loads official NISR EICV7 aggregate statistical indicators.
"""

import os
import json
from datetime import datetime
from pathlib import Path
import pandas as pd

import config
from database.connection import get_db_connection, execute_single, execute_statement
from database.models import SCHEMA_SQL
from utils.security import hash_password

def initialize_database(force_recreate: bool = False):
    """
    Initialize SQLite database tables, default facilities, system users,
    and NISR baseline statistical indicators.
    """
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if force_recreate:
            # Drop in reverse foreign-key order
            tables = [
                "tasks", "support_assessments", "followup_records",
                "appointments", "discharges", "patients", "facilities",
                "users", "audit_logs", "statistical_datasets", "nisr_district_indicators"
            ]
            for t in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {t};")
        
        # Execute DDL
        cursor.executescript(SCHEMA_SQL)
    
    # Seed default facilities
    _seed_facilities()
    
    # Seed default system users
    _seed_users()
    
    # Seed NISR official survey dataset
    _seed_nisr_indicators()

def _seed_facilities():
    """Ensure baseline Rwandan referral and district partner facilities exist."""
    facilities_data = [
        ("CHUK", "University Teaching Hospital of Kigali (CHUK)", "Nyarugenge", "City of Kigali", "National Referral Hospital", "+250 788 123 401"),
        ("CHUB", "University Teaching Hospital of Butare (CHUB)", "Huye", "Southern Province", "National Referral Hospital", "+250 788 123 402"),
        ("RMH", "Rwanda Military Hospital (Kanombe)", "Kicukiro", "City of Kigali", "Referral & Teaching Hospital", "+250 788 123 403"),
        ("KBG", "Kibagabaga District Hospital", "Gasabo", "City of Kigali", "District Hospital", "+250 788 123 404"),
        ("MSK", "Masaka District Hospital", "Kicukiro", "City of Kigali", "District Hospital", "+250 788 123 405"),
        ("KCY", "Kacyiru District Hospital", "Gasabo", "City of Kigali", "District Hospital", "+250 788 123 406"),
        ("RWM", "Rwamagana Provincial Hospital", "Rwamagana", "Eastern Province", "Provincial Hospital", "+250 788 123 407"),
        ("RHN", "Ruhengeri Referral Hospital", "Musanze", "Northern Province", "Referral Hospital", "+250 788 123 408"),
        ("BTR", "Butaro Cancer Centre of Excellence", "Burera", "Northern Province", "Specialized Oncology Centre", "+250 788 123 409"),
        ("NYM", "Nyamata District Hospital", "Bugesera", "Eastern Province", "District Hospital", "+250 788 123 410"),
        ("GSN", "Gisenyi District Hospital", "Rubavu", "Western Province", "District Hospital", "+250 788 123 411"),
        ("KBG2", "Kabgayi District Hospital", "Muhanga", "Southern Province", "District Hospital", "+250 788 123 412")
    ]
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        now_str = datetime.now().isoformat()
        for code, name, district, province, ftype, phone in facilities_data:
            cursor.execute(
                """
                INSERT OR IGNORE INTO facilities (code, name, district, province, facility_type, contact_phone, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                """,
                (code, name, district, province, ftype, phone, now_str)
            )

def _seed_users():
    """Seed baseline accounts for each of the 4 defined role tiers."""
    now_str = datetime.now().isoformat()
    
    # Read admin from env or fallback
    admin_user = os.getenv("ADMIN_USERNAME", "admin")
    admin_pass = os.getenv("ADMIN_DEFAULT_PASSWORD", "AdminSecure2026!")
    admin_email = os.getenv("ADMIN_EMAIL", "admin@followup.health.rw")
    
    baseline_users = [
        (admin_user, "System Administrator", admin_email, admin_pass, config.ROLE_ADMIN, "CHUK"),
        ("dr.mucyo", "Dr. David Mucyo, MD", "d.mucyo@followup.health.rw", "Provider2026!", config.ROLE_PROVIDER, "University Teaching Hospital of Kigali (CHUK)"),
        ("nurse.keza", "Nurse Marie Keza, RN", "m.keza@followup.health.rw", "Provider2026!", config.ROLE_PROVIDER, "Masaka District Hospital"),
        ("officer.aline", "Aline Uwase (Follow-Up Coordinator)", "a.uwase@followup.health.rw", "Officer2026!", config.ROLE_OFFICER, "Kibagabaga District Hospital"),
        ("officer.jean", "Jean Claude Ndayisaba (CHW Liaison)", "j.ndayisaba@followup.health.rw", "Officer2026!", config.ROLE_OFFICER, "Rwamagana Provincial Hospital"),
        ("mgmt.director", "Director Eric Mugisha (Planning & M&E)", "e.mugisha@followup.health.rw", "Review2026!", config.ROLE_READONLY, "Ministry of Health Catchment Oversight")
    ]
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        for uname, fname, email, pwd, role, facility in baseline_users:
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE username = ?", (uname,))
            row = cursor.fetchone()
            if not row:
                phash = hash_password(pwd)
                cursor.execute(
                    """
                    INSERT INTO users (username, full_name, email, password_hash, role, facility, is_active, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (uname, fname, email, phash, role, facility, now_str)
                )

def _seed_nisr_indicators():
    """Load NISR EICV7 District Health & Socioeconomic Indicators from CSV into SQLite."""
    csv_path = config.NISR_DATA_DIR / "eicv7_district_indicators.csv"
    if not csv_path.exists():
        return
        
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM nisr_district_indicators")
        count = cursor.fetchone()["count"]
        if count == 0:
            df = pd.read_csv(csv_path)
            for _, row in df.iterrows():
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO nisr_district_indicators 
                    (district, province, poverty_rate_pct, extreme_poverty_rate_pct, 
                     health_insurance_coverage_pct, travel_time_over_1hr_pct, 
                     chronic_illness_reported_pct, unimproved_sanitation_pct, 
                     reference_survey, source_citation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["district"], row["province"], float(row["poverty_rate_pct"]),
                        float(row["extreme_poverty_rate_pct"]), float(row["health_insurance_coverage_pct"]),
                        float(row["travel_time_over_1hr_pct"]), float(row["chronic_illness_reported_pct"]),
                        float(row["unimproved_sanitation_pct"]), str(row["reference_survey"]),
                        str(row["source_citation"])
                    )
                )
            
            # Record metadata in statistical_datasets table
            now_str = datetime.now().isoformat()
            cursor.execute(
                """
                INSERT OR REPLACE INTO statistical_datasets
                (dataset_key, dataset_name, publishing_institution, source_url, reference_period, geographic_coverage, indicator_description, imported_at, row_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "eicv7_district_indicators",
                    "EICV7 District Level Health and Living Conditions Indicators",
                    "National Institute of Statistics of Rwanda (NISR)",
                    "https://www.statistics.gov.rw/data-sources/surveys/EICV/integrated-household-living-conditions-survey-7-eicv-7",
                    "2023 - 2024",
                    "National (30 Districts of Rwanda, 5 Provinces)",
                    "District-level poverty rates, health insurance coverage, travel time to facilities over 1 hr, and chronic illness reporting.",
                    now_str,
                    len(df)
                )
            )
