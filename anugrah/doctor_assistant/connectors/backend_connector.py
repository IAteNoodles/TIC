import json
import requests
from typing import Dict, Any, Optional
try:
    from doctor_assistant.logging_config import get_logger
except ImportError:
    from logging_config import get_logger

logger = get_logger("connectors.backend")

# Backend API configuration
BACKEND_BASE_URL = "http://192.168.1.228:8001"
PATIENT_ENDPOINT = "/get_patient_complete_details"

# Dummy data representing a database of patients
dummy_patients = {
    "123": {
        "name": "John Doe",
        "age": 45,
        "gender": "1", # For diabetes model
        "symptoms": ["fever", "cough", "headache"],
        "vitals": {
            "temperature": "38.5 C",
            "blood_pressure": "120/80 mmHg",
            "heart_rate": "85 bpm"
        },
        "medical_history": "Hypertension, diagnosed 5 years ago.",
        # Fields for Diabetes
        "hypertension": 1,
        "heart_disease": 0,
        "smoking_history": "former",
        "bmi": 28.5,
        "HbA1c_level": 6.0,
        "blood_glucose_level": 110,
        # Fields for Cardiovascular
        "height": 175,
        "weight": 82,
        "ap_hi": 120,
        "ap_lo": 80,
        "cholesterol": 1,
        "gluc": 1,
        "smoke": 1,
        "alco": 0,
        "active": 1
    },
    "456": {
        "name": "Jane Smith",
        "age": 32,
        "gender": "Female", # For diabetes model
        "symptoms": ["sore throat", "fatigue"],
        "vitals": {
            "temperature": "37.2 C",
            "blood_pressure": "110/70 mmHg",
            "heart_rate": "72 bpm"
        },
        "medical_history": "None.",
        # Fields for Diabetes
        "hypertension": 0,
        "heart_disease": 0,
        "smoking_history": "never",
        "bmi": 22.1,
        "HbA1c_level": 5.5,
        "blood_glucose_level": 95,
        # Fields for Cardiovascular
        "height": 165,
        "weight": 60,
        "ap_hi": 110,
        "ap_lo": 70,
        "cholesterol": 1,
        "gluc": 1,
        "smoke": 0,
        "alco": 0,
        "active": 1
    }
}

def get_patient_data_from_api(patient_id: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Fetch patient data from the actual backend API.
    
    Args:
        patient_id: The ID of the patient to fetch.
        timeout: Request timeout in seconds (default: 30).
        
    Returns:
        A dictionary containing patient data or error information.
    """
    try:
        # Construct the full URL
        url = f"{BACKEND_BASE_URL}{PATIENT_ENDPOINT}"
        params = {"patient_id": patient_id}
        
        logger.info(f"Fetching patient data for ID: {patient_id} from {url}")
        
        # Make the API request
        response = requests.get(url, params=params, timeout=timeout)
        
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            
            # Check if the API returned success status
            if data.get("status") == "success" and data.get("count", 0) > 0:
                # Extract the first patient's data
                patient_data = data["patients"][0]
                logger.info(f"Successfully fetched data for patient {patient_id}")
                return {
                    "status": "success",
                    "patient_data": patient_data
                }
            else:
                logger.warning(f"Patient {patient_id} not found in database")
                return {
                    "status": "error",
                    "error": "Patient not found",
                    "details": "No patient data returned from database"
                }
                
        elif response.status_code == 422:
            # Validation error
            error_data = response.json()
            logger.error(f"Validation error for patient {patient_id}: {error_data}")
            return {
                "status": "error",
                "error": "Validation error",
                "details": error_data.get("detail", "Invalid patient ID format")
            }
        else:
            # Other HTTP errors
            logger.error(f"HTTP {response.status_code} error fetching patient {patient_id}: {response.text}")
            return {
                "status": "error",
                "error": f"HTTP {response.status_code} error",
                "details": response.text
            }
            
    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching data for patient {patient_id}")
        return {
            "status": "error",
            "error": "Request timeout",
            "details": f"Request timed out after {timeout} seconds"
        }
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error fetching data for patient {patient_id}")
        return {
            "status": "error",
            "error": "Connection error",
            "details": "Could not connect to backend service"
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error fetching data for patient {patient_id}: {str(e)}")
        return {
            "status": "error",
            "error": "Request error",
            "details": str(e)
        }
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error for patient {patient_id}: {str(e)}")
        return {
            "status": "error",
            "error": "Invalid JSON response",
            "details": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error fetching data for patient {patient_id}: {str(e)}")
        return {
            "status": "error",
            "error": "Unexpected error",
            "details": str(e)
        }

def get_patient_data(patient_id: str, use_mock: bool = False, timeout: int = 30) -> Dict[str, Any]:
    """
    Main function to fetch patient data. Can use either real API or mock data.
    
    Args:
        patient_id: The ID of the patient to fetch.
        use_mock: If True, use mock data instead of real API (default: False).
        timeout: Request timeout in seconds for API calls (default: 30).
        
    Returns:
        A dictionary containing patient data or error information.
    """
    if use_mock:
        logger.info(f"Using mock data for patient {patient_id}")
        return get_patient_data_mock(patient_id)
    else:
        logger.info(f"Using real API for patient {patient_id}")
        return get_patient_data_from_api(patient_id, timeout)

def get_patient_data_mock(patient_id: str) -> dict:
    """
    Mock function to simulate fetching patient data from a backend API.

    Args:
        patient_id: The ID of the patient.

    Returns:
        A dictionary containing dummy patient data in the same format as the real API, or an error message.
    """
    if patient_id in dummy_patients:
        patient_data = dummy_patients[patient_id]
        # Format the mock data to match the real API response structure
        mock_response = {
            "status": "success",
            "patient_data": {
                "personal_details": {
                    "patient_id": patient_id,
                    "full_name": patient_data["name"],
                    "name": patient_data["name"],
                    "gender": patient_data["gender"],
                    "age": str(patient_data["age"]),
                    "entity_type": "person",
                    "node_type": "Patient"
                },
                "lab_details": [{
                    "age": str(patient_data["age"]),
                    "gender": patient_data["gender"],
                    "hypertension": str(patient_data["hypertension"]),
                    "heart_disease": str(patient_data["heart_disease"]),
                    "smoking_history": patient_data["smoking_history"],
                    "bmi": str(patient_data["bmi"]),
                    "HbA1c_level": str(patient_data["HbA1c_level"]),
                    "blood_glucose_level": str(patient_data["blood_glucose_level"]),
                    "height": str(patient_data["height"]),
                    "weight": str(patient_data["weight"]),
                    "ap_hi": str(patient_data["ap_hi"]),
                    "ap_lo": str(patient_data["ap_lo"]),
                    "cholesterol": str(patient_data["cholesterol"]),
                    "gluc": str(patient_data["gluc"]),
                    "smoke": str(patient_data["smoke"]),
                    "alco": str(patient_data["alco"]),
                    "active": str(patient_data["active"])
                }]
            }
        }
        logger.info(f"Returning mock data for patient {patient_id}")
        return mock_response
    else:
        logger.warning("Patient id %s not found in dummy backend", patient_id)
        return {
            "status": "error",
            "error": "Patient not found",
            "details": "Patient ID not found in mock database"
        }

def extract_patient_info(api_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and format patient information from API response for easier processing.
    
    Args:
        api_response: The response from get_patient_data function.
        
    Returns:
        A simplified dictionary with patient information or error details.
    """
    if api_response.get("status") != "success":
        return {
            "success": False,
            "error": api_response.get("error", "Unknown error"),
            "details": api_response.get("details", "No details available")
        }
    
    try:
        patient_data = api_response["patient_data"]
        personal = patient_data.get("personal_details", {})
        lab_data = patient_data.get("lab_details", [{}])[0]  # Take first lab record
        
        # Extract and organize the information
        extracted_info = {
            "success": True,
            "patient_id": personal.get("patient_id"),
            "personal_info": {
                "name": personal.get("full_name") or personal.get("name"),
                "gender": personal.get("gender"),
                "age": lab_data.get("age") or personal.get("age"),
                "date_of_birth": personal.get("dob"),
                "entity_type": personal.get("entity_type"),
                "node_type": personal.get("node_type")
            },
            "medical_data": {
                # Diabetes-related fields
                "hypertension": int(lab_data.get("hypertension", 0)),
                "heart_disease": int(lab_data.get("heart_disease", 0)),
                "smoking_history": lab_data.get("smoking_history"),
                "bmi": float(lab_data.get("bmi", 0)),
                "HbA1c_level": float(lab_data.get("HbA1c_level", 0)),
                "blood_glucose_level": float(lab_data.get("blood_glucose_level", 0)),
                
                # Cardiovascular-related fields
                "height": float(lab_data.get("height", 0)),
                "weight": float(lab_data.get("weight", 0)),
                "ap_hi": int(lab_data.get("ap_hi", 0)),  # Systolic BP
                "ap_lo": int(lab_data.get("ap_lo", 0)),  # Diastolic BP
                "cholesterol": int(lab_data.get("cholesterol", 0)),
                "glucose": int(lab_data.get("gluc", 0)),
                "smoking": int(lab_data.get("smoke", 0)),
                "alcohol": int(lab_data.get("alco", 0)),
                "physical_activity": int(lab_data.get("active", 0))
            },
            "raw_data": patient_data  # Keep original data for reference
        }
        
        return extracted_info
        
    except Exception as e:
        logger.error(f"Error extracting patient info: {str(e)}")
        return {
            "success": False,
            "error": "Data extraction error",
            "details": f"Failed to parse patient data: {str(e)}"
        }

if __name__ == '__main__':
    # Example usage
    print("Testing with mock data:")
    print(json.dumps(get_patient_data("123", use_mock=True), indent=2))
    print("\nTesting with non-existent patient (mock):")
    print(json.dumps(get_patient_data("999", use_mock=True), indent=2))
    
    print("\nTesting with real API:")
    print(json.dumps(get_patient_data("1", use_mock=False), indent=2))
    print("\nTesting with non-existent patient (real API):")
    print(json.dumps(get_patient_data("999", use_mock=False), indent=2))
