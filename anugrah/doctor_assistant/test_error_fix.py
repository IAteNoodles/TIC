#!/usr/bin/env python3
"""
Simple test to validate the error checking fix
"""
import sys
sys.path.append('.')

def test_error_checking_fix():
    """Test the fixed error checking logic"""
    print("=" * 60)
    print("TESTING FIXED ERROR CHECKING LOGIC")
    print("=" * 60)
    
    # Simulate the MCP response format from the debug output
    mock_mcp_response = {
        "ok": True,
        "model": "ollama",
        "chat_type": "ollama",
        "answer": "Based on the provided data and the error message, I cannot provide a prediction for cardiovascular disease. The tool `get_predictions` is not callable.",
        "tool_calls": [
            {
                "name": "get_predictions",
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
                "result": "Error calling tool 'get_predictions': 'FunctionTool' object is not callable"
            }
        ],
        "retries": {
            "gemini": 0,
            "groq": 0,
            "ollama": 1
        },
        "error": None  # This was causing the issue
    }
    
    print("1. Testing OLD error checking logic:")
    print("-" * 40)
    
    # Old logic: if prediction_result.get('error') or not prediction_result.get('answer'):
    old_error_check = mock_mcp_response.get('error') or not mock_mcp_response.get('answer')
    print(f"   get('error'): {mock_mcp_response.get('error')}")
    print(f"   get('answer'): {mock_mcp_response.get('answer') is not None}")
    print(f"   OLD logic result: {old_error_check}")
    print(f"   Would trigger error: {'YES' if old_error_check else 'NO'}")
    
    print("\n2. Testing NEW error checking logic:")
    print("-" * 40)
    
    # New logic: if prediction_result.get('error') is not None or not prediction_result.get('answer'):
    new_error_check = mock_mcp_response.get('error') is not None or not mock_mcp_response.get('answer')
    print(f"   get('error') is not None: {mock_mcp_response.get('error') is not None}")
    print(f"   get('answer'): {mock_mcp_response.get('answer') is not None}")
    print(f"   NEW logic result: {new_error_check}")
    print(f"   Would trigger error: {'YES' if new_error_check else 'NO'}")
    
    print("\n3. Analysis:")
    print("-" * 40)
    if old_error_check and not new_error_check:
        print("✅ FIXED! The new logic correctly handles null errors.")
        print("   The diagnosis agent will now process the MCP response.")
    elif old_error_check == new_error_check:
        print("⚠️  Both logics give the same result.")
        if new_error_check:
            print("   This means there's still a real issue to investigate.")
        else:
            print("   Both correctly identify this as a valid response.")
    else:
        print("❌ Unexpected result in logic comparison.")
    
    print("\n4. What happens next:")
    print("-" * 40)
    if not new_error_check:
        print("✅ Diagnosis agent will:")
        print("   - Extract raw_prediction from the 'answer' field")
        print("   - Try to parse SHAP data from tool_calls")
        print("   - Generate an enhanced report")
        print("   - Call MedGemma for final report")
    else:
        print("❌ Diagnosis agent will:")
        print("   - Set error_message and return early")
        print("   - User will see the error instead of a report")
        
    print("\n5. SHAP Data Extraction Test:")
    print("-" * 40)
    # Test if SHAP data can be extracted from this response
    try:
        from agents.diagnosis_agent import _extract_shap_data
        shap_data = _extract_shap_data(mock_mcp_response)
        print(f"   SHAP data extracted: {len(shap_data)} keys")
        if shap_data:
            print(f"   Keys: {list(shap_data.keys())}")
        else:
            print("   No SHAP data found (expected for this error response)")
    except Exception as e:
        print(f"   Error extracting SHAP data: {e}")

if __name__ == "__main__":
    test_error_checking_fix()