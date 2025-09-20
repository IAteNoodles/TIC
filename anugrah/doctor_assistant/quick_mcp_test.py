#!/usr/bin/env python3
"""
Quick MCP connectivity and response test
"""

import json
import requests
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_mcp_connectivity():
    """Test MCP endpoint connectivity and response format."""
    
    print("=" * 60)
    print("MCP CONNECTIVITY AND RESPONSE TEST")
    print("=" * 60)
    
    # MCP endpoint from your connector
    url = "http://192.168.1.228:8088/chat"
    headers = {
        "accept": "application/json", 
        "Content-Type": "application/json"
    }
    
    print(f"MCP Endpoint: {url}")
    print(f"Headers: {headers}")
    print()
    
    # Simple test payload
    test_data = {
        "message": "Test cardiovascular risk prediction",
        "chat_type": "ollama"
    }
    
    print("Test payload:")
    print(json.dumps(test_data, indent=2))
    print()
    
    try:
        print("Attempting connection (timeout: 10 seconds)...")
        response = requests.post(url, headers=headers, json=test_data, timeout=10)
        
        print(f"✓ Connection successful!")
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print()
        
        if response.status_code == 200:
            try:
                json_response = response.json()
                print("✓ Valid JSON response received!")
                print("Response structure:")
                print(json.dumps(json_response, indent=2))
                print()
                
                # Analyze what the diagnosis agent expects vs what we got
                print("DIAGNOSIS AGENT EXPECTATIONS:")
                print("-" * 30)
                print("Expected: dict with 'answer' key or 'error' key")
                print("Received keys:", list(json_response.keys()) if isinstance(json_response, dict) else "Not a dict")
                
                if isinstance(json_response, dict):
                    if 'answer' in json_response:
                        print("✓ 'answer' key found - diagnosis agent will use this")
                    elif 'error' in json_response:
                        print("❌ 'error' key found - diagnosis agent will report error")
                    else:
                        print("❌ Neither 'answer' nor 'error' key found")
                        print("   Diagnosis agent will report: 'No answer from prediction model.'")
                
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON response: {e}")
                print("Raw response:")
                print(response.text[:500] + "..." if len(response.text) > 500 else response.text)
        else:
            print(f"❌ HTTP Error {response.status_code}")
            print("Response:", response.text[:200])
            
    except requests.exceptions.Timeout:
        print("❌ Connection timed out after 10 seconds")
        print("   The MCP endpoint may be slow or unreachable")
        
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        print("   The MCP endpoint may be down or unreachable")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mcp_connectivity()