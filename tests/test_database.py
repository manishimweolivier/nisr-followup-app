"""
Unit Tests for Database Initialization and Models
"""

import unittest
import sqlite3
import os
from pathlib import Path

import config
from database.connection import get_db_connection, execute_single, execute_query
from database.initialization import initialize_database
from utils.security import hash_password, verify_password

class TestDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize database
        initialize_database()
        
    def test_database_tables_exist(self):
        """Verify all core tables exist in the local SQLite database."""
        expected_tables = [
            "users", "facilities", "patients", "discharges",
            "appointments", "followup_records", "support_assessments",
            "tasks", "audit_logs", "statistical_datasets", "nisr_district_indicators"
        ]
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row["name"] for row in cursor.fetchall()]
            
        for t in expected_tables:
            self.assertIn(t, existing_tables, f"Table '{t}' is missing from SQLite schema.")
            
    def test_facilities_seeded(self):
        """Verify baseline Rwandan referral and district partner facilities are seeded."""
        row = execute_single("SELECT COUNT(*) as count FROM facilities")
        self.assertGreater(row["count"], 5, "Baseline facilities not properly seeded.")
        
    def test_users_seeded_and_hashed(self):
        """Verify pre-configured user roles exist and passwords are securely hashed."""
        admin = execute_single("SELECT * FROM users WHERE username = 'admin'")
        self.assertIsNotNone(admin, "Default admin user was not seeded.")
        self.assertTrue(admin["password_hash"].startswith("pbkdf2_sha256$"), "Admin password hash does not use PBKDF2.")
        self.assertTrue(verify_password("AdminSecure2026!", admin["password_hash"]), "Admin password verification failed.")
        
    def test_nisr_indicators_loaded(self):
        """Verify all 30 districts of Rwanda have NISR EICV7 indicators loaded."""
        row = execute_single("SELECT COUNT(*) as count FROM nisr_district_indicators")
        self.assertEqual(row["count"], 30, "NISR 30 district indicators were not loaded.")

if __name__ == "__main__":
    unittest.main()
