from typing import TypedDict

class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        query: The user's query.
        patient_id: The ID of the patient.
        intent: The classified intent of the user's query.
        db_response: The response from the backend database/API.
        final_report: The final generated diagnostic report.
        error_message: Any error message that occurred during the workflow.
    """
    query: str
    patient_id: str
    intent: str
    db_response: dict
    final_report: str
    error_message: str
