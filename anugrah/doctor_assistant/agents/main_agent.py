from state import GraphState
from logging_config import get_logger

logger = get_logger("agents.main")

def main_agent_node(state: GraphState):
    """
    The main agent node that orchestrates the workflow.
    This is a placeholder and will be expanded.
    """
    logger.info("Main agent received query for patient_id=%s", state.get('patient_id'))
    
    # For now, just pass the state through
    return state

if __name__ == '__main__':
    # Example usage
    initial_state: GraphState = {
        "query": "Get me patient 123's data.",
        "patient_id": "123",
        "intent": "",
        "db_response": {},
        "final_report": "",
        "error_message": ""
    }
    result_state = main_agent_node(initial_state)
    print(result_state)
