import json

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

def get_patient_data_mock(patient_id: str) -> dict:
    """
    Mock function to simulate fetching patient data from a backend API.

    Args:
        patient_id: The ID of the patient.

    Returns:
        A dictionary containing dummy patient data, or an error message.
    """
    if patient_id in dummy_patients:
        return dummy_patients[patient_id]
    else:
        return {"error": "Patient not found"}

if __name__ == '__main__':
    # Example usage
    print(json.dumps(get_patient_data_mock("123"), indent=2))
    print(json.dumps(get_patient_data_mock("999"), indent=2))
