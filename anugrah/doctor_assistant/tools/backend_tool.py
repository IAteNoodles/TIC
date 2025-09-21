try:
    from doctor_assistant.connectors.backend_connector import get_patient_data, extract_patient_info
    from doctor_assistant.logging_config import get_logger
except ImportError:
    from connectors.backend_connector import get_patient_data, extract_patient_info
    from logging_config import get_logger

logger = get_logger("tools.backend")

def get_patient_data_tool(patient_id: str, use_mock: bool = False, include_raw: bool = False) -> dict:
    """
    A tool for fetching patient data from the backend API.
    
    Args:
        patient_id: The ID of the patient to fetch.
        use_mock: Whether to use mock data instead of real API (default: False).
        include_raw: Whether to include raw API response data (default: False).
    
    Returns:
        A dictionary containing formatted patient data or error information.
    """
    logger.info(f"Fetching data for patient_id={patient_id}, use_mock={use_mock}")
    
    try:
        # Get data from the backend connector
        api_response = get_patient_data(patient_id, use_mock=use_mock)
        
        # Extract and format the patient information
        formatted_data = extract_patient_info(api_response)
        
        # Add raw data if requested
        if include_raw and formatted_data.get("success"):
            formatted_data["raw_api_response"] = api_response
        
        # Log results
        if formatted_data.get("success"):
            logger.info(f"Successfully retrieved data for patient {patient_id}")
        else:
            logger.warning(f"Failed to retrieve data for patient {patient_id}: {formatted_data.get('error')}")
        
        return formatted_data
        
    except Exception as e:
        error_msg = f"Unexpected error fetching patient data for patient_id={patient_id}: {str(e)}"
        logger.exception(error_msg)
        return {
            "success": False,
            "error": "Unexpected error",
            "details": error_msg
        }

def get_patient_summary_tool(patient_id: str, use_mock: bool = False) -> str:
    """
    Get a formatted text summary of patient data for display or LLM consumption.
    
    Args:
        patient_id: The ID of the patient to fetch.
        use_mock: Whether to use mock data instead of real API (default: False).
    
    Returns:
        A formatted string summary of the patient data or error message.
    """
    logger.info(f"Generating summary for patient_id={patient_id}")
    
    patient_data = get_patient_data_tool(patient_id, use_mock=use_mock)
    
    if not patient_data.get("success"):
        return f"Error retrieving patient data: {patient_data.get('error', 'Unknown error')} - {patient_data.get('details', 'No additional details')}"
    
    try:
        personal = patient_data["personal_info"]
        medical = patient_data["medical_data"]
        
        summary = f"""
PATIENT SUMMARY
================
Patient ID: {patient_data['patient_id']}
Name: {personal['name']}
Age: {personal['age']} years old
Gender: {personal['gender']}
Date of Birth: {personal.get('date_of_birth', 'Not specified')}

MEDICAL DATA
============
Physical Measurements:
- Height: {medical['height']} cm
- Weight: {medical['weight']} kg
- BMI: {medical['bmi']}

Cardiovascular:
- Blood Pressure: {medical['ap_hi']}/{medical['ap_lo']} mmHg
- Cholesterol Level: {'Normal' if medical['cholesterol'] == 1 else 'Above Normal' if medical['cholesterol'] == 2 else 'Well Above Normal'}
- Heart Disease: {'Yes' if medical['heart_disease'] else 'No'}
- Hypertension: {'Yes' if medical['hypertension'] else 'No'}

Diabetes-Related:
- Blood Glucose Level: {medical['blood_glucose_level']} mg/dL
- HbA1c Level: {medical['HbA1c_level']}%
- Glucose Level: {'Normal' if medical['glucose'] == 1 else 'Above Normal' if medical['glucose'] == 2 else 'Well Above Normal'}

Lifestyle Factors:
- Smoking History: {medical['smoking_history']}
- Current Smoker: {'Yes' if medical['smoking'] else 'No'}
- Alcohol Consumption: {'Yes' if medical['alcohol'] else 'No'}
- Physical Activity: {'Active' if medical['physical_activity'] else 'Inactive'}
"""
        
        logger.info(f"Generated summary for patient {patient_id}")
        return summary.strip()
        
    except Exception as e:
        error_msg = f"Error formatting patient summary: {str(e)}"
        logger.error(error_msg)
        return f"Error formatting patient data: {error_msg}"

if __name__ == '__main__':
    # Test both mock and real API functionality
    print("=== Testing Backend Tool ===")
    
    print("\n1. Testing with mock data (patient ID 123):")
    result = get_patient_data_tool("123", use_mock=True)
    print(f"Success: {result.get('success')}")
    if result.get('success'):
        print(f"Patient: {result['personal_info']['name']}")
        print(f"Age: {result['personal_info']['age']}")
        print(f"BMI: {result['medical_data']['bmi']}")
    else:
        print(f"Error: {result.get('error')}")
    
    print("\n2. Testing patient summary (mock data):")
    summary = get_patient_summary_tool("123", use_mock=True)
    print(summary)
    
    print("\n3. Testing with real API (patient ID 1):")
    result = get_patient_data_tool("1", use_mock=False)
    print(f"Success: {result.get('success')}")
    if result.get('success'):
        print(f"Patient: {result['personal_info']['name']}")
        print(f"Age: {result['personal_info']['age']}")
        print(f"BMI: {result['medical_data']['bmi']}")
    else:
        print(f"Error: {result.get('error')}")
    
    print("\n4. Testing real API patient summary:")
    summary = get_patient_summary_tool("1", use_mock=False)
    print(summary)
