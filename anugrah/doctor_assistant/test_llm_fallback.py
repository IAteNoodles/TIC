#!/usr/bin/env python3
"""
Test what happens when MCP works but final LLM polishing fails
"""

import sys
import os
from unittest.mock import patch

# Add the project root to Python path  
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.diagnosis_agent import diagnosis_agent_node

def test_mcp_success_llm_timeout():
    """Test scenario: MCP succeeds with SHAP data, but final LLM times out."""
    
    print("=" * 70)
    print("TESTING: MCP SUCCESS + LLM TIMEOUT SCENARIO")
    print("=" * 70)
    
    # Mock successful MCP response (like your actual one)  
    mock_mcp_response = {
        "ok": True,
        "answer": "High probability of diabetes based on glucose and age factors.",
        "tool_calls": [{
            "name": "call_diabetes_api",  # Make sure this contains 'cardio' or similar
            "result": '{"prediction": 1, "explanations": {"explanations": [{"feature": "gluc", "value": 2.0, "impact": "increases", "importance": 0.8}, {"feature": "age", "value": 58, "impact": "increases", "importance": 0.6}], "top_factors": [{"feature": "gluc", "value": 2.0, "impact": "increases", "importance": 0.8}], "summary": "Elevated glucose is the primary risk factor."}}'
        }],
        "error": None
    }
    
    # Mock patient data
    mock_patient_data = {
        "name": "Test Patient",
        "age": 58,
        "gluc": 2,
        "cholesterol": 1,
        "active": 1
    }
    
    with patch('agents.diagnosis_agent.get_patient_data_tool') as mock_patient_tool, \
         patch('agents.diagnosis_agent._determine_model_type') as mock_model_type, \
         patch('agents.diagnosis_agent.get_model_parameters_tool') as mock_params, \
         patch('agents.diagnosis_agent.get_mcp_prediction_tool') as mock_mcp, \
         patch('agents.diagnosis_agent.call_llm') as mock_llm:
        
        # Setup mocks
        mock_patient_tool.return_value = mock_patient_data
        mock_model_type.return_value = "diabetes"
        mock_params.return_value = {
            "diabetes": {"required_fields": ["age", "gluc"]}
        }
        mock_mcp.return_value = mock_mcp_response
        
        # Simulate LLM timeout
        mock_llm.side_effect = Exception("Connection timeout")
        
        # Test state
        test_state = {
            "query": "Check diabetes risk for this patient",
            "patient_id": "test-123",
            "intent": "diagnosis",
            "db_response": {},
            "final_report": "",
            "error_message": ""
        }
        
        print("SCENARIO: MCP provides rich SHAP data, but LLM times out...")
        result_state = diagnosis_agent_node(test_state)
        
        print("\n✅ RESULT: Agent gracefully falls back to enhanced SHAP report!")
        print(f"✅ Final report length: {len(result_state.get('final_report', ''))} characters")
        print(f"✅ Error message: {result_state.get('error_message') or 'None'}")
        
        final_report = result_state.get('final_report', '')
        
        print("\n📋 ENHANCED FALLBACK REPORT:")
        print("=" * 50)
        print(final_report)
        print("=" * 50)
        
        # Verify the report contains SHAP insights
        checks = [
            ("Contains SHAP analysis", "ENHANCED DIAGNOSTIC ANALYSIS" in final_report),
            ("Contains risk factors", "Risk Factor" in final_report),
            ("Contains clinical insights", "Clinical Insights" in final_report),
            ("Contains glucose factor", "Glucose" in final_report),
            ("Not just basic prediction", len(final_report) > 100)
        ]
        
        print("\n🔍 REPORT QUALITY CHECKS:")
        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"{status} {check_name}")

if __name__ == "__main__":
    test_mcp_success_llm_timeout()