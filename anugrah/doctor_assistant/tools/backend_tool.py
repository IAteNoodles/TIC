try:
    from doctor_assistant.connectors.backend_connector import get_patient_data_mock
    from doctor_assistant.logging_config import get_logger
except ImportError:
    from connectors.backend_connector import get_patient_data_mock
    from logging_config import get_logger

logger = get_logger("tools.backend")

def get_patient_data_tool(patient_id: str) -> dict:
    """
    A tool for fetching patient data. It wraps the backend connector
    and includes error handling.
    """
    logger.info(f"Fetching data for patient_id=%s", patient_id)
    try:
        # In a real scenario, you might have more complex logic here,
        # like handling authentication, retries, etc.
        data = get_patient_data_mock(patient_id)
        if "error" in data:
            logger.warning("Backend returned error for patient_id=%s: %s", patient_id, data["error"])
        return data
    except Exception as e:
        logger.exception("Unexpected error fetching patient data for patient_id=%s", patient_id)
        return {"error": "An unexpected error occurred while fetching patient data."}

if __name__ == '__main__':
    # Simple smoke test
    print(get_patient_data_tool("123"))
    print(get_patient_data_tool("999"))
