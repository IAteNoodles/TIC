import unittest
import sys
import os
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.parameter_tool import get_model_parameters_tool

class TestParameterTool(unittest.TestCase):

    def test_read_parameters_file(self):
        """
        Test that the parameters file is read correctly and is a dictionary.
        """
        params = get_model_parameters_tool()
        self.assertIsInstance(params, dict)
        self.assertIn("cardiovascular_disease", params)
        self.assertIn("diabetes", params)

    def test_cardiovascular_parameters_structure(self):
        """
        Test the structure and content of the cardiovascular_disease parameters.
        """
        params = get_model_parameters_tool()
        cardio_params = params.get("cardiovascular_disease", {})
        self.assertIn("required_fields", cardio_params)
        self.assertIsInstance(cardio_params["required_fields"], list)
        self.assertIn("ap_hi", cardio_params["required_fields"])
        self.assertEqual(len(cardio_params["required_fields"]), 11)

    def test_diabetes_parameters_structure(self):
        """
        Test the structure and content of the diabetes parameters.
        """
        params = get_model_parameters_tool()
        diabetes_params = params.get("diabetes", {})
        self.assertIn("required_fields", diabetes_params)
        self.assertIsInstance(diabetes_params["required_fields"], list)
        self.assertIn("bmi", diabetes_params["required_fields"])
        self.assertEqual(len(diabetes_params["required_fields"]), 8)

if __name__ == '__main__':
    unittest.main()
