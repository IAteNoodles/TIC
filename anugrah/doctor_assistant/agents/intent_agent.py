from state import GraphState
from connectors.llm_connector import call_llm

def intent_agent_node(state: GraphState):
    """
    Classifies the user's intent using an LLM.
    """
    print("---INTENT AGENT (LLM)---")
    query = state['query']

    system_prompt = """
    You are an expert at classifying user intent. Based on the user's query, classify the intent as one of the following two options:
    1. `information_retrieval`: Use this for requests to get, fetch, or view patient data, summaries, or history.
    2. `diagnosis`: Use this for requests related to diagnosing, predicting, analyzing risk, or asking for a diagnosis.

    You must respond with ONLY the name of the intent and nothing else. For example: `diagnosis`
    """
    
    gemma_endpoint = "http://192.168.1.54:1234/v1/chat/completions"
    gemma_model = "google/gemma-3-4b"

    response = call_llm(
        model_name=gemma_model,
        endpoint=gemma_endpoint,
        system_prompt=system_prompt,
        user_prompt=query
    )

    intent = "information_retrieval" # Default value
    if "error" in response:
        print(f"LLM call failed, defaulting to: {intent}")
    elif "choices" in response and response["choices"]:
        llm_response = response['choices'][0]['message']['content'].strip().lower()
        # Basic validation to ensure the LLM gives a valid response
        if llm_response in ["information_retrieval", "diagnosis"]:
            intent = llm_response
    
    print(f"LLM Classified Intent: {intent}")
    state['intent'] = intent
    return state

if __name__ == '__main__':
    # Example usage
    example_state: GraphState = {
        "query": "what is the risk of cardiovascular disease for this patient?",
        "patient_id": "123",
        "intent": "",
        "db_response": {},
        "final_report": "",
        "error_message": ""
    }
    result_state = intent_agent_node(example_state)
    print(f"Final State: {result_state}")

    example_state_2: GraphState = {
        "query": "get me this patient's history",
        "patient_id": "456",
        "intent": "",
        "db_response": {},
        "final_report": "",
        "error_message": ""
    }
    result_state_2 = intent_agent_node(example_state_2)
    print(f"Final State 2: {result_state_2}")
