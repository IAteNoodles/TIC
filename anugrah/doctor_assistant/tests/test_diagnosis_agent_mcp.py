import json
import unittest
from unittest.mock import patch, MagicMock

from agents.diagnosis_agent import diagnosis_agent_node
from state import GraphState

class TestDiagnosisAgentMCPInteraction(unittest.TestCase):

    @patch('agents.diagnosis_agent.get_patient_data_tool')
    @patch('agents.diagnosis_agent._determine_model_type')
    @patch('agents.diagnosis_agent.get_model_parameters_tool')
    @patch('agents.diagnosis_agent.get_mcp_prediction_tool')
    @patch('agents.diagnosis_agent.call_llm')
    def test_mcp_prompt_and_response_handling(
        self,
        mock_call_llm,
        mock_get_mcp_prediction_tool,
        mock_get_model_parameters_tool,
        mock_determine_model_type,
        mock_get_patient_data_tool
    ):
        """
        Tests that the diagnosis agent calls the MCP tool with a correctly formatted prompt
        and handles the response to generate a final report.
        """
        # --- 1. Setup Mocks ---

        # Mock patient data
        patient_id = "test-patient-123"
        mock_patient_data = {
            "name": "John Doe",
            "age": 58,
            "symptoms": ["chest pain", "shortness of breath"],
            "vitals": {"bp": "140/90", "hr": "85"},
            "gender": 1, "height": 170, "weight": 85, "ap_hi": 140, "ap_lo": 90,
            "cholesterol": 2, "gluc": 1, "smoke": 0, "alco": 0, "active": 1
        }
        mock_get_patient_data_tool.return_value = mock_patient_data

        # Mock model determination
        model_type = "cardiovascular_disease"
        mock_determine_model_type.return_value = model_type

        # Mock model parameters to prevent data sufficiency failure
        mock_get_model_parameters_tool.return_value = {
            "cardiovascular_disease": {
                "required_fields": ["age", "gender", "height", "weight", "ap_hi", "ap_lo", "cholesterol", "gluc", "smoke", "alco", "active"]
            }
        }

        # Mock the response from the MCP prediction tool
        mcp_raw_prediction = "Prediction: High risk of cardiovascular event."
        mock_get_mcp_prediction_tool.return_value = {"answer": mcp_raw_prediction}

        # Mock the final report generation LLM call
        final_report_text = "Final synthesized report about high risk."
        mock_call_llm.return_value = {"choices": [{"message": {"content": final_report_text}}]}

        # --- 2. Execute the Agent Node ---
        initial_state: GraphState = {
            "query": "What is the cardiovascular risk for this patient?",
            "patient_id": patient_id,
            "intent": "diagnosis",
            "db_response": {},
            "final_report": "",
            "error_message": ""
        }
        
        final_state = diagnosis_agent_node(initial_state)

        # --- 3. Assertions ---

        # Assert that the patient data tool was called
        mock_get_patient_data_tool.assert_called_once_with(patient_id)

        # Assert that the MCP prediction tool was called
        mock_get_mcp_prediction_tool.assert_called_once()
        
        # Spy on the arguments passed to the MCP tool
        mcp_call_args = mock_get_mcp_prediction_tool.call_args
        mcp_prompt = mcp_call_args[0][0]
        
        print("\n--- Captured MCP Prompt ---")
        print(mcp_prompt)
        print("---------------------------\n")

        # Verify the prompt sent to the MCP tool
        expected_mcp_prompt_data = json.dumps(mock_patient_data)
        self.assertIn(f"provide a prediction for {model_type.replace('_', ' ')}", mcp_prompt)
        self.assertIn(expected_mcp_prompt_data, mcp_prompt)

        # Assert that the final LLM for report generation was called with the MCP prediction
        mock_call_llm.assert_called_once()
        report_generation_prompt = mock_call_llm.call_args[1]['user_prompt']

        print("--- Captured Report Generation Prompt ---")
        print(report_generation_prompt)
        print("---------------------------------------\n")
        
        self.assertIn(mcp_raw_prediction, report_generation_prompt)
        self.assertIn(json.dumps(mock_patient_data, indent=2), report_generation_prompt)

        # Assert that the final report is in the state
        self.assertEqual(final_state.get('final_report'), final_report_text)
        self.assertIsNone(final_state.get('error_message'))

if __name__ == '__main__':
    unittest.main()
