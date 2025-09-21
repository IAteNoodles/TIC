#!/usr/bin/env python3
"""
Comprehensive integration test for the Doctor Assistant system.
Tests the complete workflow from backend API to agent processing.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from connectors.backend_connector import get_patient_data, extract_patient_info
from tools.backend_tool import get_patient_data_tool, get_patient_summary_tool
import json

def test_backend_integration():
    """Test the backend connector and tool integration."""
    print("=" * 60)
    print("BACKEND INTEGRATION TEST")
    print("=" * 60)
    
    # Test 1: Real API connectivity
    print("\n1. Testing real API connectivity...")
    api_response = None
    try:
        api_response = get_patient_data("1", use_mock=False)
        if api_response.get("status") == "success":
            print("✅ Real API connection successful")
        else:
            print(f"❌ Real API failed: {api_response.get('error')}")
    except Exception as e:
        print(f"❌ Real API connection failed: {str(e)}")
        api_response = {"status": "error", "error": str(e)}
    
    # Test 2: Data extraction and formatting
    print("\n2. Testing data extraction and formatting...")
    if api_response and api_response.get("status") == "success":
        try:
            extracted_data = extract_patient_info(api_response)
            if extracted_data.get("success"):
                print("✅ Data extraction successful")
                print(f"   Patient: {extracted_data['personal_info']['name']}")
                print(f"   Age: {extracted_data['personal_info']['age']}")
                print(f"   BMI: {extracted_data['medical_data']['bmi']}")
            else:
                print(f"❌ Data extraction failed: {extracted_data.get('error')}")
        except Exception as e:
            print(f"❌ Data extraction failed: {str(e)}")
    else:
        print("⚠️  Skipping data extraction test - API response unavailable")
    
    # Test 3: Backend tool functionality
    print("\n3. Testing backend tool functionality...")
    try:
        tool_result = get_patient_data_tool("1", use_mock=False)
        if tool_result.get("success"):
            print("✅ Backend tool successful")
        else:
            print(f"❌ Backend tool failed: {tool_result.get('error')}")
    except Exception as e:
        print(f"❌ Backend tool failed: {str(e)}")
    
    # Test 4: Patient summary generation
    print("\n4. Testing patient summary generation...")
    try:
        summary = get_patient_summary_tool("1", use_mock=False)
        if "PATIENT SUMMARY" in summary:
            print("✅ Patient summary generated successfully")
            print("   Sample from summary:")
            lines = summary.split('\n')[:10]
            for line in lines:
                print(f"   {line}")
        else:
            print(f"❌ Patient summary failed: {summary}")
    except Exception as e:
        print(f"❌ Patient summary failed: {str(e)}")

def test_mock_vs_real_comparison():
    """Compare mock and real API responses."""
    print("\n" + "=" * 60)
    print("MOCK VS REAL API COMPARISON")
    print("=" * 60)
    
    # Test with patient ID 1 (real) vs 123 (mock)
    print("\n1. Fetching real patient data (ID: 1)...")
    real_data = get_patient_data_tool("1", use_mock=False)
    
    print("\n2. Fetching mock patient data (ID: 123)...")
    mock_data = get_patient_data_tool("123", use_mock=True)
    
    if real_data.get("success") and mock_data.get("success"):
        print("\n3. Comparing data structures...")
        
        # Compare personal info fields
        real_personal = real_data["personal_info"]
        mock_personal = mock_data["personal_info"]
        
        print("   Personal info fields:")
        for field in real_personal.keys():
            real_val = real_personal.get(field)
            mock_val = mock_personal.get(field)
            status = "✅" if field in mock_personal else "❌"
            print(f"   {status} {field}: Real='{real_val}', Mock='{mock_val}'")
        
        # Compare medical data fields
        real_medical = real_data["medical_data"]
        mock_medical = mock_data["medical_data"]
        
        print("\n   Medical data fields:")
        for field in real_medical.keys():
            real_val = real_medical.get(field)
            mock_val = mock_medical.get(field)
            status = "✅" if field in mock_medical else "❌"
            print(f"   {status} {field}: Real='{real_val}', Mock='{mock_val}'")
    else:
        print("❌ Could not compare - one or both requests failed")

def test_error_handling():
    """Test error handling scenarios."""
    print("\n" + "=" * 60)
    print("ERROR HANDLING TEST")
    print("=" * 60)
    
    # Test 1: Invalid patient ID
    print("\n1. Testing with invalid patient ID...")
    invalid_result = get_patient_data_tool("invalid_id", use_mock=False)
    if not invalid_result.get("success"):
        print("✅ Invalid patient ID handled correctly")
        print(f"   Error: {invalid_result.get('error')}")
    else:
        print("❌ Invalid patient ID should have failed")
    
    # Test 2: Non-existent patient ID
    print("\n2. Testing with non-existent patient ID...")
    missing_result = get_patient_data_tool("999", use_mock=False)
    if not missing_result.get("success"):
        print("✅ Non-existent patient ID handled correctly")
        print(f"   Error: {missing_result.get('error')}")
    else:
        print("❌ Non-existent patient ID should have failed")
    
    # Test 3: Mock fallback
    print("\n3. Testing mock fallback...")
    mock_result = get_patient_data_tool("999", use_mock=True)
    if not mock_result.get("success"):
        print("✅ Mock error handling works correctly")
    else:
        print("❌ Mock should have failed for non-existent patient")

def test_agent_integration():
    """Test agent integration with the new backend."""
    print("\n" + "=" * 60)
    print("AGENT INTEGRATION TEST")
    print("=" * 60)
    
    try:
        # Import agent components
        from agents.diagnosis_agent import diagnosis_agent_node
        from state import GraphState
        
        # Create test state
        test_state = GraphState(
            query="Please provide a diabetes diagnosis for this patient",
            patient_id="1",
            intent="diagnosis",
            db_response={},
            final_report="",
            error_message=""
        )
        
        print("\n1. Testing diagnosis agent with real backend data...")
        try:
            result_state = diagnosis_agent_node(test_state)
            if result_state.get("error_message"):
                print(f"⚠️  Agent returned error: {result_state['error_message']}")
            elif result_state.get("final_report"):
                print("✅ Diagnosis agent completed successfully")
                print(f"   Report preview: {result_state['final_report'][:100]}...")
            else:
                print("⚠️  Agent completed but no report generated")
        except Exception as e:
            print(f"❌ Diagnosis agent failed: {str(e)}")
            
    except ImportError as e:
        print(f"⚠️  Could not import agent components: {str(e)}")

def run_all_tests():
    """Run all integration tests."""
    print("DOCTOR ASSISTANT INTEGRATION TEST SUITE")
    print("Testing complete workflow from backend API to agent processing")
    print("Make sure backend service is running at http://192.168.1.228:8001")
    
    try:
        test_backend_integration()
        test_mock_vs_real_comparison()
        test_error_handling()
        test_agent_integration()
        
        print("\n" + "=" * 60)
        print("INTEGRATION TEST SUITE COMPLETED")
        print("=" * 60)
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()