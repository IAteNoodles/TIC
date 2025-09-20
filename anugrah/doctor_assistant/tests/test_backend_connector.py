import unittest
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from connectors.backend_connector import get_patient_data_mock

class TestBackendConnector(unittest.TestCase):

    def test_get_patient_data_success(self):
        """
        Test fetching data for a valid patient ID.
        """
        patient_id = "123"
        data = get_patient_data_mock(patient_id)
        self.assertIn("name", data)
        self.assertEqual(data["name"], "John Doe")
        self.assertNotIn("error", data)

    def test_get_patient_data_not_found(self):
        """
        Test fetching data for an invalid patient ID.
        """
        patient_id = "999"
        data = get_patient_data_mock(patient_id)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Patient not found")

    def test_patient_data_has_required_fields(self):
        """
        Test that a valid patient record contains all expected fields for diagnosis.
        """
        patient_id = "123"
        data = get_patient_data_mock(patient_id)
        
        # Example fields from both models
        required_for_diabetes = ["hypertension", "bmi", "blood_glucose_level"]
        required_for_cardio = ["ap_hi", "ap_lo", "cholesterol"]
        
        for field in required_for_diabetes:
            self.assertIn(field, data)
            self.assertIsNotNone(data[field])
            
        for field in required_for_cardio:
            self.assertIn(field, data)
            self.assertIsNotNone(data[field])

if __name__ == '__main__':
    unittest.main()
