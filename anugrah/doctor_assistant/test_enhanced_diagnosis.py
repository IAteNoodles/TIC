#!/usr/bin/env python3
"""
Test the enhanced diagnosis agent with rich SHAP data parsing
"""

import json
import sys
import os
from unittest.mock import patch, MagicMock

# Add the project root to Python path  
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.diagnosis_agent import diagnosis_agent_node, _extract_shap_data, _generate_enhanced_report
from state import GraphState

def test_enhanced_diagnosis_agent():
    """Test the enhanced diagnosis agent with mock MCP response containing SHAP data."""
    
    print("=" * 70)
    print("TESTING ENHANCED DIAGNOSIS AGENT WITH SHAP DATA")
    print("=" * 70)
    
    # Mock the MCP response with your actual response structure
    mock_mcp_response = {
        "ok": True,
        "model": "ollama",
        "chat_type": "ollama",
        "answer": "Based on the provided data, there is a high probability of cardiovascular disease for John Doe. The prediction is influenced by his age, ap_hi, and cholesterol levels. It's recommended to consult with a healthcare professional for further evaluation and advice.",
        "tool_calls": [
            {
                "name": "call_cardio_api",
                "arguments": {
                    "age": 58,
                    "gender": 1,
                    "height": 170,
                    "weight": 85,
                    "ap_hi": 140,
                    "ap_lo": 90,
                    "cholesterol": 2,
                    "gluc": 1,
                    "smoke": 0,
                    "alco": 0,
                    "active": 1
                },
                "result": json.dumps({
                    "prediction": 1,
                    "explanations": {
                        "explanations": [
                            {"feature": "age", "value": 58.0, "shap_value": -1.2273634672164917, "impact": "decreases", "importance": 1.2273634672164917},
                            {"feature": "ap_hi", "value": 140.0, "shap_value": 1.188364863395691, "impact": "increases", "importance": 1.188364863395691},
                            {"feature": "cholesterol", "value": 2.0, "shap_value": 0.3777754008769989, "impact": "increases", "importance": 0.3777754008769989},
                            {"feature": "height", "value": 170.0, "shap_value": -0.16889558732509613, "impact": "decreases", "importance": 0.16889558732509613},
                            {"feature": "ap_lo", "value": 90.0, "shap_value": -0.1517324596643448, "impact": "decreases", "importance": 0.1517324596643448}
                        ],
                        "top_factors": [
                            {"feature": "age", "value": 58.0, "shap_value": -1.2273634672164917, "impact": "decreases", "importance": 1.2273634672164917},
                            {"feature": "ap_hi", "value": 140.0, "shap_value": 1.188364863395691, "impact": "increases", "importance": 1.188364863395691},
                            {"feature": "cholesterol", "value": 2.0, "shap_value": 0.3777754008769989, "impact": "increases", "importance": 0.3777754008769989}
                        ],
                        "summary": "The prediction is primarily influenced by: Age (value: 58.00) decreases the risk, Ap Hi (value: 140.00) increases the risk, Cholesterol (value: 2.00) increases the risk."
                    }
                })
            }
        ],
        "retries": {"gemini": 0, "groq": 0, "ollama": 1},
        "error": None
    }
    
    # Mock patient data
    mock_patient_data = {
        "name": "John Doe",
        "age": 58,
        "symptoms": ["chest pain", "shortness of breath"],
        "vitals": {"bp": "140/90", "hr": "85"},
        "gender": 1, "height": 170, "weight": 85, "ap_hi": 140, "ap_lo": 90,
        "cholesterol": 2, "gluc": 1, "smoke": 0, "alco": 0, "active": 1
    }
    
    print("1. TESTING SHAP DATA EXTRACTION:")
    print("-" * 40)
    shap_data = _extract_shap_data(mock_mcp_response)
    print("✓ Extracted SHAP data:")
    print(json.dumps(shap_data, indent=2))
    print()
    
    print("2. TESTING ENHANCED REPORT GENERATION:")
    print("-" * 45)
    enhanced_report = _generate_enhanced_report(
        patient_data=mock_patient_data,
        raw_prediction=mock_mcp_response["answer"],
        shap_data=shap_data,
        model_type="cardiovascular_disease"
    )
    print("✓ Generated enhanced report:")
    print(enhanced_report)
    print()
    
    print("3. TESTING FULL DIAGNOSIS AGENT WITH MOCKS:")
    print("-" * 45)
    
    # Mock all dependencies
    with patch('agents.diagnosis_agent.get_patient_data_tool') as mock_patient_tool, \
         patch('agents.diagnosis_agent._determine_model_type') as mock_model_type, \
         patch('agents.diagnosis_agent.get_model_parameters_tool') as mock_params, \
         patch('agents.diagnosis_agent.get_mcp_prediction_tool') as mock_mcp, \
         patch('agents.diagnosis_agent.call_llm') as mock_llm:
        
        # Setup mocks
        mock_patient_tool.return_value = mock_patient_data
        mock_model_type.return_value = "cardiovascular_disease"
        mock_params.return_value = {
            "cardiovascular_disease": {
                "required_fields": ["age", "gender", "height", "weight", "ap_hi", "ap_lo", "cholesterol", "gluc", "smoke", "alco", "active"]
            }
        }
        mock_mcp.return_value = mock_mcp_response
        mock_llm.return_value = {
            "choices": [{"message": {"content": "Final polished medical report based on AI analysis."}}]
        }
        
        # Test state
        test_state = {
            "query": "What is the cardiovascular risk for this patient?",
            "patient_id": "john-doe-123",
            "intent": "diagnosis",
            "db_response": {},
            "final_report": "",
            "error_message": ""
        }
        
        # Run the agent
        result_state = diagnosis_agent_node(test_state)
        
        print("✓ Diagnosis agent completed successfully!")
        print(f"✓ Final report length: {len(result_state.get('final_report', ''))} characters")
        print(f"✓ Error message: {result_state.get('error_message', 'None')}")
        
        # Check that MCP tool was called
        mock_mcp.assert_called_once()
        
        # Check that LLM was called with enhanced prompt
        mock_llm.assert_called_once()
        llm_call_args = mock_llm.call_args
        user_prompt = llm_call_args[1]['user_prompt']
        
        print("\n4. VERIFYING ENHANCED PROMPT TO LLM:")
        print("-" * 40)
        print("✓ LLM prompt contains SHAP analysis:", "Risk Factor Analysis" in user_prompt)
        print("✓ LLM prompt contains clinical insights:", "Clinical Insights" in user_prompt)
        print("✓ LLM prompt length:", len(user_prompt), "characters")
        
        if len(user_prompt) > 1000:  # Enhanced prompt should be much longer
            print("✓ Enhanced prompt is significantly more detailed than basic version")
        
        print("\nSample of enhanced prompt sent to LLM:")
        print(user_prompt[:500] + "...\n")

def test_comparison_basic_vs_enhanced():
    """Compare basic vs enhanced report generation."""
    
    print("=" * 70)
    print("COMPARISON: BASIC vs ENHANCED REPORTS")
    print("=" * 70)
    
    # Sample data
    patient_data = {"age": 58, "ap_hi": 140, "cholesterol": 2}
    raw_prediction = "High risk of cardiovascular disease."
    
    # Basic report (empty SHAP data)
    basic_report = _generate_enhanced_report(patient_data, raw_prediction, {}, "cardiovascular_disease")
    
    # Enhanced report (with SHAP data)
    shap_data = {
        "explanations": [
            {"feature": "age", "value": 58.0, "impact": "decreases", "importance": 1.23},
            {"feature": "ap_hi", "value": 140.0, "impact": "increases", "importance": 1.19}
        ],
        "top_factors": [
            {"feature": "ap_hi", "value": 140.0, "impact": "increases", "importance": 1.19}
        ],
        "summary": "High blood pressure increases risk significantly."
    }
    enhanced_report = _generate_enhanced_report(patient_data, raw_prediction, shap_data, "cardiovascular_disease")
    
    print("BASIC REPORT:")
    print("-" * 20)
    print(basic_report)
    print(f"\nLength: {len(basic_report)} characters\n")
    
    print("ENHANCED REPORT:")
    print("-" * 20)
    print(enhanced_report)
    print(f"\nLength: {len(enhanced_report)} characters")
    
    print(f"\nEnhancement factor: {len(enhanced_report) / len(basic_report):.1f}x more detailed")

if __name__ == "__main__":
    test_enhanced_diagnosis_agent()
    print("\n")
    test_comparison_basic_vs_enhanced()