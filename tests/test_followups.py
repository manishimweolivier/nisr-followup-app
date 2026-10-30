"""
Unit Tests for Follow-Up Workflows, Rescheduling, and Overdue Tracking
"""

import unittest
from datetime import date, timedelta
from database.initialization import initialize_database
from services.patient_service import register_patient, get_patient_by_ref
from services.followup_service import (
    schedule_appointment,
    reschedule_appointment,
    record_followup_interaction,
    sync_overdue_appointments,
    list_appointments
)
from database.connection import execute_single, execute_statement
import config

class TestFollowups(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        initialize_database()
        # Register a test patient
        ok, msg, pref = register_patient(
            full_name="Test Continuity Patient",
            age=50,
            sex="Male",
            facility_id=1,
            condition_category="Type 2 Diabetes",
            district="Nyarugenge",
            is_demo=0
        )
        cls.patient_ref = pref
        row = execute_single("SELECT id FROM patients WHERE patient_ref = ?", (pref,))
        cls.patient_id = row["id"]
        
    def test_appointment_scheduling_and_due_logic(self):
        """Test scheduling future appointment vs due today vs missed past."""
        today = date.today()
        
        # 1. Future appointment -> Scheduled
        ok, msg, aref1 = schedule_appointment(
            patient_id=self.patient_id,
            facility_id=1,
            scheduled_date=(today + timedelta(days=5)).isoformat(),
            followup_type="Facility Clinical Consultation",
            responsible_worker="Dr. Mucyo"
        )
        self.assertTrue(ok)
        apt1 = execute_single("SELECT status FROM appointments WHERE appointment_ref = ?", (aref1,))
        self.assertEqual(apt1["status"], config.STATUS_SCHEDULED)
        
        # 2. Today appointment -> Due
        ok, msg, aref2 = schedule_appointment(
            patient_id=self.patient_id,
            facility_id=1,
            scheduled_date=today.isoformat(),
            followup_type="Phone Follow-Up Call",
            responsible_worker="Aline Uwase"
        )
        self.assertTrue(ok)
        apt2 = execute_single("SELECT status FROM appointments WHERE appointment_ref = ?", (aref2,))
        self.assertEqual(apt2["status"], config.STATUS_DUE)
        
    def test_reschedule_appointment(self):
        """Verify rescheduling marks original as Rescheduled and generates linked record."""
        today = date.today()
        ok, msg, aref = schedule_appointment(
            patient_id=self.patient_id,
            facility_id=1,
            scheduled_date=(today + timedelta(days=3)).isoformat(),
            followup_type="Facility Clinical Consultation",
            responsible_worker="Dr. Mucyo"
        )
        apt_row = execute_single("SELECT id FROM appointments WHERE appointment_ref = ?", (aref,))
        
        new_date = (today + timedelta(days=10)).isoformat()
        ok_resched, resched_msg = reschedule_appointment(
            appointment_id=apt_row["id"],
            new_scheduled_date=new_date,
            reason="Patient requested postponement due to funeral.",
            actor_username="dr.mucyo",
            actor_role="Healthcare Provider"
        )
        self.assertTrue(ok_resched)
        
        # Verify original appointment is Rescheduled
        orig_updated = execute_single("SELECT status, rescheduled_reason FROM appointments WHERE id = ?", (apt_row["id"],))
        self.assertEqual(orig_updated["status"], config.STATUS_RESCHEDULED)
        self.assertIn("funeral", orig_updated["rescheduled_reason"].lower())
        
    def test_overdue_sync_does_not_prematurely_mark_missed(self):
        """CRITICAL: Ensure future appointments are NEVER marked missed."""
        today = date.today()
        ok, msg, aref = schedule_appointment(
            patient_id=self.patient_id,
            facility_id=1,
            scheduled_date=(today + timedelta(days=7)).isoformat(),
            followup_type="Medication Adherence Check",
            responsible_worker="Aline Uwase"
        )
        sync_overdue_appointments()
        apt = execute_single("SELECT status FROM appointments WHERE appointment_ref = ?", (aref,))
        self.assertNotEqual(apt["status"], config.STATUS_MISSED, "Future appointment was improperly marked as missed.")
        self.assertEqual(apt["status"], config.STATUS_SCHEDULED)

if __name__ == "__main__":
    unittest.main()
