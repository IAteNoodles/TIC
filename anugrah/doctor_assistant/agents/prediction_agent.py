from state import GraphState
from tools.mcp_tool import get_mcp_prediction_tool
from tools.backend_tool import get_patient_data_tool
import json

def prediction_agent_node(state: GraphState):
    """
    Agent node to call the MCP model for a prediction.
    """
    print("---PREDICTION AGENT---")
    patient_id = state.get('patient_id')

    if not patient_id:
        state['error_message'] = "No patient ID provided for prediction."
        return state

    # 1. Fetch patient data
    patient_data = get_patient_data_tool(patient_id)
    if "error" in patient_data:
        state['error_message'] = patient_data['error']
        return state

    # 2. Construct the prompt for the MCP model
    # This is a simple example; a real implementation might involve
    # more sophisticated logic to select the right model and format the data.
    prompt = f"Based on the following patient data, provide a prediction. Data: {json.dumps(patient_data)}"

    # 3. Call the MCP model tool
    prediction_result = get_mcp_prediction_tool(prompt)

    # 4. Update the state
    if "error" in prediction_result:
        state['error_message'] = prediction_result['error']
    else:
        # We'll just put the raw answer into the final report for now
        state['final_report'] = prediction_result.get('answer', 'No answer received from model.')

    return state
