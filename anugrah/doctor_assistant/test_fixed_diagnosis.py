#!/usr/bin/env python3
"""
Test the fixed diagnosis agent with the actual MCP response format
"""

import json
import sys
import os

# Add the project root to Python path  
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.diagnosis_agent import diagnosis_agent_node
from state import GraphState

def test_diagnosis_agent_with_real_mcp_response():
    """Test diagnosis agent with the actual MCP response format you're getting."""
    
    print("=" * 60)
    print("TESTING FIXED DIAGNOSIS AGENT WITH REAL MCP RESPONSE")
    print("=" * 60)
    
    # Simulate the state that would come into diagnosis_agent_node
    test_state = {
        "query": "What is the cardiovascular risk for this patient?",
        "patient_id": "test-123", 
        "intent": "diagnosis",
        "db_response": {},
        "final_report": "",
        "error_message": ""
    }
    
    print("INPUT STATE:")
    print(json.dumps(test_state, indent=2))
    print()
    
    try:
        print("CALLING DIAGNOSIS AGENT...")
        result_state = diagnosis_agent_node(test_state)
        
        print("RESULT STATE:")
        print(json.dumps(result_state, indent=2))
        print()
        
        # Analyze the result
        if result_state.get('error_message'):
            print("❌ AGENT REPORTED ERROR:")
            print(f"   {result_state['error_message']}")
        elif result_state.get('final_report'):
            print("✓ AGENT GENERATED FINAL REPORT:")
            print(f"   Report length: {len(result_state['final_report'])} characters")
            print(f"   Report preview: {result_state['final_report'][:200]}...")
        else:
            print("❌ AGENT RETURNED NEITHER ERROR NOR REPORT")
            
    except Exception as e:
        print(f"❌ EXCEPTION OCCURRED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_diagnosis_agent_with_real_mcp_response()