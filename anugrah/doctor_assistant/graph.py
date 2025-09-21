from typing import TypedDict, Iterator
from langgraph.graph import StateGraph, END
from agents.main_agent import main_agent_node
from agents.intent_agent import intent_agent_node
from agents.diagnosis_agent import diagnosis_agent_node, diagnosis_agent_streaming_node
from tools.backend_tool import get_patient_data_tool, get_patient_summary_tool
from state import GraphState
from logging_config import get_logger

logger = get_logger("graph")

# Updated Information Retrieval Node
def information_retrieval_node(state: GraphState):
    """
    Fetches patient data using the backend tool and summarizes it.
    """
    logger.info("Information retrieval node")
    patient_id = state.get('patient_id')

    if not patient_id:
        state['error_message'] = "No patient ID was provided in the state."
        return state
    
    # Call the tool to get patient data
    db_response = get_patient_data_tool(patient_id)
    state['db_response'] = db_response

    if not db_response.get("success"):
        state['error_message'] = db_response.get('error', 'Failed to fetch patient data')
        return state
    
    # Generate a human-readable summary using the new tool
    try:
        summary = get_patient_summary_tool(patient_id)
        state['final_report'] = summary
    except Exception as e:
        logger.error(f"Error generating patient summary: {str(e)}")
        # Fallback to basic summary
        personal_info = db_response.get('personal_info', {})
        medical_data = db_response.get('medical_data', {})
        basic_summary = f"""Patient Information Retrieved:
        
Name: {personal_info.get('name', 'Unknown')}
Age: {personal_info.get('age', 'Unknown')} years
Gender: {personal_info.get('gender', 'Unknown')}
BMI: {medical_data.get('bmi', 'N/A')}
Blood Pressure: {medical_data.get('ap_hi', 'N/A')}/{medical_data.get('ap_lo', 'N/A')} mmHg
Blood Glucose: {medical_data.get('blood_glucose_level', 'N/A')} mg/dL
HbA1c: {medical_data.get('HbA1c_level', 'N/A')}%
"""
        state['final_report'] = basic_summary

    return state

# Define the workflow
workflow = StateGraph(GraphState)

# Add the nodes
workflow.add_node("main_agent", main_agent_node)
workflow.add_node("intent_agent", intent_agent_node)
workflow.add_node("information_retrieval", information_retrieval_node)
workflow.add_node("diagnosis", diagnosis_agent_node) # Use the imported agent

# Set the entry point
workflow.set_entry_point("main_agent")

# Add edges
workflow.add_edge("main_agent", "intent_agent")

# Add conditional routing
def route_based_on_intent(state: GraphState):
    """
    Routes the workflow based on the classified intent.
    """
    intent = state.get('intent')
    if intent == "information_retrieval":
        return "information_retrieval"
    else:
        return "diagnosis"

workflow.add_conditional_edges(
    "intent_agent",
    route_based_on_intent,
    {
        "information_retrieval": "information_retrieval",
        "diagnosis": "diagnosis",
    }
)

# End the workflow after the branches
workflow.add_edge("information_retrieval", END)
workflow.add_edge("diagnosis", END)

app = workflow.compile()

if __name__ == '__main__':
    # Simple smoke test
    inputs: GraphState = {
        "query": "Get me patient data.", 
        "patient_id": "123",
        "intent": "",
        "db_response": {},
        "final_report": "",
        "error_message": ""
    }
    for _ in app.stream(inputs):
        pass


def run_streaming_diagnosis(query: str, patient_id: str) -> Iterator[str]:
    """
    Run a streaming diagnosis workflow that yields real-time results.
    
    Args:
        query: User's medical query
        patient_id: ID of the patient to analyze
        
    Yields:
        str: Real-time chunks of the diagnosis report
    """
    logger.info(f"Starting streaming diagnosis for patient {patient_id}")
    
    # Create initial state
    state: GraphState = {
        "query": query,
        "patient_id": patient_id,
        "intent": "",
        "db_response": {},
        "final_report": "",
        "error_message": ""
    }
    
    # Step 1: Determine intent
    yield "[STATUS] Analyzing your request..."
    try:
        state = intent_agent_node(state)
        intent = state.get('intent', 'diagnosis')
        logger.info(f"Intent classified as: {intent}")
        
        if intent == "information_retrieval":
            yield "[STATUS] Retrieving patient information..."
            state = information_retrieval_node(state)
            
            if state.get('error_message'):
                yield f"[ERROR] {state['error_message']}"
                return
            
            # Stream the information retrieval result
            final_report = state.get('final_report', '')
            for line in final_report.split('\n'):
                if line.strip():
                    yield line + '\n'
        else:
            # Stream diagnosis results
            yield "[STATUS] Starting medical analysis..."
            for chunk in diagnosis_agent_streaming_node(state):
                yield chunk
                
    except Exception as e:
        logger.error(f"Error in streaming workflow: {e}")
        yield f"[ERROR] An unexpected error occurred: {str(e)}"


def stream_diagnosis_workflow(query: str, patient_id: str) -> Iterator[str]:
    """
    Alias for run_streaming_diagnosis for compatibility.
    """
    return run_streaming_diagnosis(query, patient_id)

