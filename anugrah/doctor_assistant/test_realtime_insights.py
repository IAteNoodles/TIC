#!/usr/bin/env python3
"""
Test script to verify the real-time insights functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph import app
from state import GraphState
import time

def test_real_time_insights():
    """Test the real-time insights by streaming the graph execution."""
    print("=" * 60)
    print("TESTING REAL-TIME INSIGHTS FUNCTIONALITY")
    print("=" * 60)
    
    # Create test input
    inputs: GraphState = {
        "query": "Please get patient information for medical review", 
        "patient_id": "1",  # Use real patient ID
        "intent": "",
        "db_response": {},
        "final_report": "",
        "error_message": ""
    }
    
    print(f"\n🔄 Starting workflow for patient ID: {inputs['patient_id']}")
    print(f"📝 Query: {inputs['query']}")
    print("\n" + "─" * 50)
    
    step_counter = 0
    final_state = None
    
    try:
        for output in app.stream(inputs):
            # output is a dict of node_name -> state
            for node_name, state_value in output.items():
                step_counter += 1
                final_state = state_value
                
                # Simulate real-time status display
                print(f"\n{step_counter}. 🎯 Executing: {node_name.replace('_', ' ').title()}")
                
                # Show relevant state information
                if node_name == "intent_agent":
                    intent = state_value.get('intent', 'unknown')
                    print(f"   ➤ Detected intent: {intent}")
                
                elif node_name == "information_retrieval":
                    db_response = state_value.get('db_response', {})
                    if db_response.get('success'):
                        personal_info = db_response.get('personal_info', {})
                        print(f"   ➤ Retrieved data for: {personal_info.get('name', 'Unknown')}")
                        print(f"   ➤ Age: {personal_info.get('age', 'Unknown')}")
                    elif db_response.get('error'):
                        print(f"   ➤ Error: {db_response.get('error')}")
                
                elif node_name == "diagnosis":
                    if state_value.get('error_message'):
                        print(f"   ➤ Diagnosis error: {state_value.get('error_message')}")
                    elif state_value.get('final_report'):
                        report_preview = state_value.get('final_report', '')[:100]
                        print(f"   ➤ Generated report preview: {report_preview}...")
                
                print(f"   ✅ {node_name} completed")
                
                # Simulate processing time
                time.sleep(0.8)
    
    except Exception as e:
        print(f"\n❌ Error during execution: {str(e)}")
        final_state = {"error_message": f"Internal error: {e}"}
    
    print("\n" + "─" * 50)
    print("📋 FINAL RESULTS:")
    
    if final_state:
        if final_state.get("error_message"):
            print(f"❌ Error: {final_state['error_message']}")
        elif final_state.get("final_report"):
            print("✅ Generated Report:")
            print(final_state['final_report'])
        else:
            print("⚠️  No report generated")
    else:
        print("❌ No final state received")
    
    print("\n" + "=" * 60)
    print("REAL-TIME INSIGHTS TEST COMPLETED")
    print("=" * 60)

def test_diagnosis_workflow():
    """Test the diagnosis workflow specifically."""
    print("\n" + "=" * 60)
    print("TESTING DIAGNOSIS WORKFLOW")
    print("=" * 60)
    
    inputs: GraphState = {
        "query": "Please analyze this patient for diabetes risk", 
        "patient_id": "1",
        "intent": "",
        "db_response": {},
        "final_report": "",
        "error_message": ""
    }
    
    print(f"\n🩺 Starting diagnosis workflow for patient ID: {inputs['patient_id']}")
    print(f"📝 Query: {inputs['query']}")
    
    step_counter = 0
    
    try:
        for output in app.stream(inputs):
            for node_name, state_value in output.items():
                step_counter += 1
                print(f"\n{step_counter}. 🔄 {node_name}")
                
                if node_name == "diagnosis":
                    print("   🧠 Analyzing medical data...")
                    print("   📊 Checking data sufficiency...")
                    print("   🔬 Generating diagnostic insights...")
                
                time.sleep(0.5)
    
    except Exception as e:
        print(f"\n❌ Diagnosis workflow error: {str(e)}")

if __name__ == "__main__":
    print("Real-Time Insights Test Suite")
    print("This tests the streaming functionality and real-time status updates")
    
    # Test information retrieval workflow
    test_real_time_insights()
    
    # Test diagnosis workflow
    test_diagnosis_workflow()
    
    print("\n✅ All tests completed!")