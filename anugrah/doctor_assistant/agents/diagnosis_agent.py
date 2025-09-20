from connectors.llm_connector import call_llm
from state import GraphState
from tools.parameter_tool import get_model_parameters_tool
from tools.mcp_tool import get_mcp_prediction_tool
from tools.backend_tool import get_patient_data_tool
import json

def _determine_model_type(query: str) -> str:
    """
    Uses an LLM to determine which model to use based on the query.
    """
    print("---DETERMINING MODEL TYPE---")
    system_prompt = """
    You are an expert at classifying a medical query. Based on the user's query, determine which of the following models is most relevant:
    - `cardiovascular_disease`
    - `diabetes`

    Respond with ONLY the name of the model and nothing else. For example: `diabetes`
    If the query is unclear, default to `diabetes`.
    """
    gemma_endpoint = "http://192.168.1.54:1234/v1/chat/completions"
    gemma_model = "google/gemma-3-4b"

    response = call_llm(
        model_name=gemma_model,
        endpoint=gemma_endpoint,
        system_prompt=system_prompt,
        user_prompt=query
    )

    model_type = "diabetes" # Default
    if "error" in response:
        print(f"LLM call for model type failed, defaulting to: {model_type}")
    elif "choices" in response and response["choices"]:
        llm_response = response['choices'][0]['message']['content'].strip().lower()
        if llm_response in ["cardiovascular_disease", "diabetes"]:
            model_type = llm_response
    
    print(f"Determined Model Type: {model_type}")
    return model_type


def diagnosis_agent_node(state: GraphState):
    """
    Orchestrates the diagnosis workflow:
    1. Determines which model to use.
    2. Checks for data sufficiency for that model.
    3. Calls the MCP model for a raw prediction.
    4. Calls MedGemma to generate a formatted report.
    """
    print("---DIAGNOSIS AGENT---")
    
    patient_id = state.get('patient_id')
    query = state.get('query')

    # Fetch patient data
    patient_data = get_patient_data_tool(patient_id)
    if "error" in patient_data:
        state['error_message'] = patient_data['error']
        return state
    state['db_response'] = patient_data

    # --- 1. Determine which model to use ---
    model_type = _determine_model_type(query)

    # --- 2. Data Sufficiency Check ---
    model_params = get_model_parameters_tool() 
    required_fields = model_params.get(model_type, {}).get("required_fields", [])
    
    missing_fields = [field for field in required_fields if field not in patient_data or patient_data.get(field) is None]
    
    if missing_fields:
        clarification_request = f"Patient data is incomplete for a {model_type.replace('_', ' ')} diagnosis. Please provide: {', '.join(missing_fields)}."
        state['final_report'] = clarification_request
        return state

    # --- 3. Call MCP model for prediction ---
    mcp_prompt = f"Based on the following patient data, provide a prediction for {model_type.replace('_', ' ')}. Data: {json.dumps(patient_data)}"
    prediction_result = get_mcp_prediction_tool(mcp_prompt)

    if "error" in prediction_result or not prediction_result.get('answer'):
        error_msg = prediction_result.get('error') or "No answer from prediction model."
        state['error_message'] = f"Error from prediction model: {error_msg}"
        return state
    
    raw_prediction = prediction_result.get('answer')

    # --- 4. Call MedGemma for final report ---
    report_prompt = f"""
    Generate a preliminary diagnostic report for {model_type.replace('_', ' ')} based on the patient data and model prediction.
    Structure the report with: Patient Summary, Key Findings, Raw Model Prediction, Potential Diagnosis, and Recommended Next Steps.

    Patient Data:
    {json.dumps(patient_data, indent=2)}

    Raw Prediction from ML Model:
    {raw_prediction}
    """

    medgemma_endpoint = "http://192.168.1.228:1234/v1/chat/completions"
    medgemma_model = "medgemma-4b-it"
    medgemma_system = "You are a medical expert generating a preliminary diagnostic report."
    
    response = call_llm(
        model_name=medgemma_model,
        endpoint=medgemma_endpoint,
        system_prompt=medgemma_system,
        user_prompt=report_prompt
    )
    
    if "error" in response:
        final_report = response["error"]
    elif "choices" in response and response["choices"]:
        final_report = response['choices'][0]['message']['content']
    else:
        final_report = "Failed to generate report from MedGemma."

    state['final_report'] = final_report
    return state
