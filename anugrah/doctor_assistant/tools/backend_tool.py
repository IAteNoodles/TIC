from connectors.backend_connector import get_patient_data_mock

def get_patient_data_tool(patient_id: str) -> dict:
    """
    A tool for fetching patient data. It wraps the backend connector
    and includes error handling.
    """
    print(f"---BACKEND TOOL: Fetching data for patient {patient_id}---")
    try:
        # In a real scenario, you might have more complex logic here,
        # like handling authentication, retries, etc.
        data = get_patient_data_mock(patient_id)
        if "error" in data:
            # Log the error
            print(f"Error from backend: {data['error']}")
        return data
    except Exception as e:
        # Log the exception
        print(f"An unexpected error occurred: {e}")
        return {"error": "An unexpected error occurred while fetching patient data."}

if __name__ == '__main__':
    # Example usage
    print("Fetching data for a valid patient:")
    print(get_patient_data_tool("123"))
    
    print("\nFetching data for an invalid patient:")
    print(get_patient_data_tool("999"))
