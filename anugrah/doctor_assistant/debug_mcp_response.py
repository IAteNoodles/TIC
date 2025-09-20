#!/usr/bin/env python3
"""
Script to test the actual MCP connector and show the response format.
This will help debug response processing issues.
"""

import json
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from connectors.mcp_connector import call_mcp_model
from tools.mcp_tool import get_mcp_prediction_tool

def test_mcp_response():
    """Test the MCP connector with real data and show the response format."""
    
    print("=" * 60)
    print("TESTING MCP CONNECTOR - REAL RESPONSE ANALYSIS")
    print("=" * 60)
    
    # Sample patient data similar to what diagnosis_agent would send
    test_prompt = """Based on the following patient data, provide a prediction for cardiovascular disease. Data: {"name": "John Doe", "age": 58, "symptoms": ["chest pain", "shortness of breath"], "vitals": {"bp": "140/90", "hr": "85"}, "gender": 1, "height": 170, "weight": 85, "ap_hi": 140, "ap_lo": 90, "cholesterol": 2, "gluc": 1, "smoke": 0, "alco": 0, "active": 1}"""
    
    print("SENDING PROMPT TO MCP:")
    print("-" * 40)
    print(test_prompt)
    print("-" * 40)
    print()
    
    try:
        # Test the direct connector with timeout info
        print("1. TESTING DIRECT MCP CONNECTOR (call_mcp_model):")
        print("-" * 50)
        print("Attempting to connect to MCP endpoint...")
        print("(This may take up to 60 seconds or timeout)")
        direct_response = call_mcp_model(test_prompt)
        print("✓ MCP connector returned successfully!")
        print("Response type:", type(direct_response))
        print("Response content:")
        print(json.dumps(direct_response, indent=2))
        print()
        
        # Test the tool wrapper
        print("2. TESTING MCP TOOL WRAPPER (get_mcp_prediction_tool):")
        print("-" * 55)
        tool_response = get_mcp_prediction_tool(test_prompt)
        print("Response type:", type(tool_response))
        print("Response content:")
        print(json.dumps(tool_response, indent=2))
        print()
        
        # Analyze the response structure
        print("3. RESPONSE ANALYSIS:")
        print("-" * 25)
        
        if isinstance(tool_response, dict):
            print("✓ Response is a dictionary")
            print("Keys in response:", list(tool_response.keys()))
            
            if "error" in tool_response:
                print("❌ Error found in response:")
                print("   Error:", tool_response["error"])
            else:
                print("✓ No error key found")
            
            if "answer" in tool_response:
                print("✓ 'answer' key found")
                print("   Answer type:", type(tool_response["answer"]))
                print("   Answer content preview:", str(tool_response["answer"])[:100] + "..." if len(str(tool_response["answer"])) > 100 else str(tool_response["answer"]))
            else:
                print("❌ No 'answer' key found")
                print("   Available keys:", list(tool_response.keys()))
        else:
            print("❌ Response is not a dictionary, got:", type(tool_response))
        
        print()
        print("4. DIAGNOSIS AGENT EXPECTATION:")
        print("-" * 35)
        print("The diagnosis_agent expects:")
        print("- Response to be a dict")
        print("- If error: key 'error' should exist")
        print("- If success: key 'answer' should exist with the prediction")
        print()
        
        # Show what the diagnosis agent would do
        if "error" in tool_response:
            print("❌ Diagnosis agent would set error_message and return")
        elif tool_response.get('answer'):
            print("✓ Diagnosis agent would use this answer:")
            print("   Raw prediction:", tool_response.get('answer'))
        else:
            print("❌ Diagnosis agent would set error: 'No answer from prediction model.'")
            
    except Exception as e:
        print(f"❌ ERROR CALLING MCP: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mcp_response()