#!/usr/bin/env python3
"""
Test script for the backend connector functionality.
Tests both mock and real API functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from connectors.backend_connector import get_patient_data
import json

def test_mock_functionality():
    """Test the mock backend functionality."""
    print("=" * 50)
    print("TESTING MOCK FUNCTIONALITY")
    print("=" * 50)
    
    # Test existing patient
    print("\n1. Testing with existing patient ID '123' (mock):")
    result = get_patient_data("1", use_mock=True)
    print(json.dumps(result, indent=2))
    
    # Test non-existent patient
    print("\n2. Testing with non-existent patient ID '999' (mock):")
    result = get_patient_data("2", use_mock=True)
    print(json.dumps(result, indent=2))

def test_real_api_functionality():
    """Test the real API functionality."""
    print("\n" + "=" * 50)
    print("TESTING REAL API FUNCTIONALITY")
    print("=" * 50)
    
    # Test with patient ID 1 (from your example)
    print("\n1. Testing with patient ID '1' (real API):")
    result = get_patient_data("3", use_mock=False)
    print(json.dumps(result, indent=2))
    
    # Test with non-existent patient
    print("\n2. Testing with non-existent patient ID '999' (real API):")
    result = get_patient_data("4", use_mock=False)
    print(json.dumps(result, indent=2))

def test_error_handling():
    """Test error handling with invalid inputs."""
    print("\n" + "=" * 50)
    print("TESTING ERROR HANDLING")
    print("=" * 50)
    
    # Test with invalid patient ID format
    print("\n1. Testing with invalid patient ID 'abc' (real API):")
    result = get_patient_data("abc", use_mock=False)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    print("Backend Connector Test Suite")
    print("This script tests both mock and real API functionality.")
    print("Make sure the backend service is running at http://192.168.1.228:8001")
    
    # Test mock functionality first
    test_mock_functionality()
    
    # Test real API functionality
    test_real_api_functionality()
    
    # Test error handling
    test_error_handling()
    
    print("\n" + "=" * 50)
    print("TEST SUITE COMPLETED")
    print("=" * 50)