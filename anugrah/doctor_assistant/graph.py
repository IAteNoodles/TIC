from typing import TypedDict
from langgraph.graph import StateGraph, END
from agents.main_agent import main_agent_node
from agents.intent_agent import intent_agent_node
from agents.diagnosis_agent import diagnosis_agent_node
from tools.backend_tool import get_patient_data_tool
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

    if "error" in db_response:
        state['error_message'] = db_response['error']
    else:
        # Simple summary (LLM would be used here in a real scenario)
        summary = f"Patient: {db_response.get('name')}, Age: {db_response.get('age')}. " \
                  f"Symptoms: {', '.join(db_response.get('symptoms', []))}. " \
                  f"Vitals: {db_response.get('vitals')}."
        state['final_report'] = summary # Using final_report to pass back the summary

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
    inputs = {"query": "Get me patient data.", "patient_id": "123"}
    for _ in app.stream(inputs):
        pass

