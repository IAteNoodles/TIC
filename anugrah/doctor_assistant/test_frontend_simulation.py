#!/usr/bin/env python3
"""
Quick test to verify the diagnosis functionality works end-to-end.
This simulates what happens when the frontend calls the graph.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_frontend_simulation():
    """Simulate the exact process the frontend goes through."""
    print("=" * 60)
    print("FRONTEND SIMULATION TEST")
    print("=" * 60)
    
    # Import exactly like the frontend does
    try:
        from graph import app
        from state import GraphState
        print("✅ Successfully imported graph and state")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return
    
    # Create inputs exactly like frontend does
    inputs = GraphState({
        "query": "what is the diabetes risk?",
        "patient_id": "1",
        "intent": "",
        "db_response": {},
        "final_report": "",
        "error_message": ""
    })
    
    print(f"\n🔄 Starting workflow...")
    print(f"Query: {inputs['query']}")
    print(f"Patient ID: {inputs['patient_id']}")
    
    final_state = None
    step_counter = 0
    
    try:
        for output in app.stream(inputs):
            for node_name, state_value in output.items():
                step_counter += 1
                final_state = state_value
                
                print(f"\n{step_counter}. 🎯 Node: {node_name}")
                
                # Check for errors at each step
                if state_value.get("error_message"):
                    print(f"   ❌ Error: {state_value['error_message']}")
                
                # Check for intent classification
                if node_name == "intent_agent" and state_value.get("intent"):
                    print(f"   ➤ Intent: {state_value['intent']}")
                
                # Check for final report
                if state_value.get("final_report"):
                    report_preview = state_value['final_report'][:150]
                    print(f"   ➤ Report preview: {report_preview}...")
                
                # Break early if we get to diagnosis to avoid MCP timeout
                if node_name == "diagnosis" and state_value.get("final_report"):
                    print("   ✅ Diagnosis completed successfully!")
                    break
    
    except Exception as e:
        print(f"\n❌ Graph execution failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    
    if final_state:
        if final_state.get("error_message"):
            print(f"❌ Final Error: {final_state['error_message']}")
        elif final_state.get("final_report"):
            print("✅ SUCCESS: Diagnosis report generated!")
            print(f"Report length: {len(final_state['final_report'])} characters")
        else:
            print("⚠️  No final report generated")
    else:
        print("❌ No final state received")

if __name__ == "__main__":
    print("Frontend Simulation Test")
    print("This simulates exactly what the Streamlit frontend does")
    test_frontend_simulation()