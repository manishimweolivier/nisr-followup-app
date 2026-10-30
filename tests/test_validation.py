"""
Unit Tests for Validation and Clinical Safety Logic
"""

import unittest
from datetime import date, timedelta
from services.validation_service import (
    validate_patient_input,
    validate_discharge_input,
    validate_appointment_input,
    validate_task_input
)
from services.support_service import calculate_vulnerability_tier
import config

class TestValidation(unittest.TestCase):
    def test_patient_validation(self):
        """Test patient registration boundary validation."""
        # Valid input
        ok, err = validate_patient_input("Mukamwezi Marie", 45, "Female", "Gasabo", "Hypertension", "+250 788 123 456")
        self.assertTrue(ok, f"Valid patient was rejected: {err}")
        
        # Invalid: empty name
        ok, err = validate_patient_input("", 45, "Female", "Gasabo", "Hypertension")
        self.assertFalse(ok)
        self.assertIn("full name", err.lower())
        
        # Invalid: age out of range
        ok, err = validate_patient_input("Test Patient", 150, "Female", "Gasabo", "Hypertension")
        self.assertFalse(ok)
        
        # Invalid: invalid sex
        ok, err = validate_patient_input("Test Patient", 30, "Unknown", "Gasabo", "Hypertension")
        self.assertFalse(ok)
        
    def test_discharge_validation(self):
        """Test chronological consistency for discharge and recommended appointment dates."""
        today = date.today()
        # Valid dates
        ok, err = validate_discharge_input(
            admission_date_str=(today - timedelta(days=5)).isoformat(),
            discharge_date_str=today.isoformat(),
            recommended_apt_date_str=(today + timedelta(days=14)).isoformat(),
            diagnosis="Type 2 Diabetes Mellitus with Ketoacidosis",
            instructions="Maintain basal-bolus insulin regimen."
        )
        self.assertTrue(ok, f"Valid discharge was rejected: {err}")
        
        # Invalid: discharge before admission
        ok, err = validate_discharge_input(
            admission_date_str=today.isoformat(),
            discharge_date_str=(today - timedelta(days=2)).isoformat(),
            recommended_apt_date_str=(today + timedelta(days=7)).isoformat(),
            diagnosis="Sample diagnosis",
            instructions="Sample instructions"
        )
        self.assertFalse(ok)
        self.assertIn("cannot be earlier", err)
        
    def test_vulnerability_tier_calculation(self):
        """Verify transparent, rule-based tier assignment."""
        self.assertEqual(calculate_vulnerability_tier(0), config.VULNERABILITY_LOW)
        self.assertEqual(calculate_vulnerability_tier(1), config.VULNERABILITY_LOW)
        self.assertEqual(calculate_vulnerability_tier(2), config.VULNERABILITY_MODERATE)
        self.assertEqual(calculate_vulnerability_tier(3), config.VULNERABILITY_MODERATE)
        self.assertEqual(calculate_vulnerability_tier(4), config.VULNERABILITY_HIGH)
        self.assertEqual(calculate_vulnerability_tier(7), config.VULNERABILITY_HIGH)

if __name__ == "__main__":
    unittest.main()
