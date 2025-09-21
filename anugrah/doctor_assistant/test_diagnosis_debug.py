#!/usr/bin/env python3
"""
Test the diagnosis agent specifically to debug the missing fields issue.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.diagnosis_agent import diagnosis_agent_node
from state import GraphState
from tools.backend_tool import get_patient_data_tool
import json

def test_diagnosis_agent():
    """Test the diagnosis agent with real patient data."""
    print("=" * 60)
    print("TESTING DIAGNOSIS AGENT")
    print("=" * 60)
    
    # First, let's see what data we actually get from the backend
    print("\n1. Fetching patient data to inspect structure...")
    patient_data_result = get_patient_data_tool("1", use_mock=False)
    
    if patient_data_result.get("success"):
        print("✅ Patient data retrieved successfully")
        print("\nPersonal Info:")
        for key, value in patient_data_result["personal_info"].items():
            print(f"  {key}: {value}")
        
        print("\nMedical Data:")
        for key, value in patient_data_result["medical_data"].items():
            print(f"  {key}: {value}")
    else:
        print(f"❌ Failed to get patient data: {patient_data_result.get('error')}")
        return
    
    # Now test the diagnosis agent
    print("\n" + "=" * 60)
    print("2. Testing Diagnosis Agent")
    print("=" * 60)
    
    test_state = GraphState({
        "query": "Please analyze this patient for diabetes risk",
        "patient_id": "1",
        "intent": "diagnosis",
        "db_response": {},
        "final_report": "",
        "error_message": ""
    })
    
    print(f"\nQuery: {test_state['query']}")
    print(f"Patient ID: {test_state['patient_id']}")
    
    try:
        result_state = diagnosis_agent_node(test_state)
        
        print("\n📋 DIAGNOSIS AGENT RESULTS:")
        
        if result_state.get("error_message"):
            print(f"❌ Error: {result_state['error_message']}")
        elif result_state.get("final_report"):
            print("✅ Diagnosis completed successfully:")
            print(result_state['final_report'])
        else:
            print("⚠️  No final report generated")
            
        # Show the db_response that was stored
        if result_state.get('db_response'):
            print(f"\n📊 DB Response stored: {type(result_state['db_response'])}")
            
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()

def test_with_mock_data():
    """Test with mock data to compare."""
    print("\n" + "=" * 60)
    print("TESTING WITH MOCK DATA")
    print("=" * 60)
    
    test_state = GraphState({
        "query": "Please analyze this patient for diabetes risk",
        "patient_id": "123",  # Mock patient
        "intent": "diagnosis",
        "db_response": {},
        "final_report": "",
        "error_message": ""
    })
    
    try:
        result_state = diagnosis_agent_node(test_state)
        
        print("\n📋 MOCK DATA RESULTS:")
        
        if result_state.get("error_message"):
            print(f"❌ Error: {result_state['error_message']}")
        elif result_state.get("final_report"):
            print("✅ Diagnosis completed successfully:")
            print(result_state['final_report'])
        else:
            print("⚠️  No final report generated")
            
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")

if __name__ == "__main__":
    print("Diagnosis Agent Debug Test")
    print("This will help us understand why the diagnosis agent reports missing fields")
    
    test_diagnosis_agent()
    test_with_mock_data()
    
    print("\n✅ Debug test completed!")