#!/usr/bin/env python3
"""
Test the data transformation for MCP
"""
import sys
sys.path.append('.')
import json

def test_data_transformation():
    """Test the updated data transformation function"""
    print("=" * 60)
    print("TESTING DATA TRANSFORMATION FOR MCP")
    print("=" * 60)
    
    from agents.diagnosis_agent import _transform_patient_data_for_mcp
    
    # Sample patient data
    sample_patient_data = {
        "name": "John Doe",
        "age": 58,
        "gender": 1,  # 1 = Male
        "height": 170,  # cm
        "weight": 85,   # kg
        "ap_hi": 140,   # systolic BP
        "ap_lo": 90,    # diastolic BP
        "cholesterol": 2,
        "gluc": 1,
        "smoke": 0,     # 0 = non-smoker
        "alco": 0,
        "active": 1
    }
    
    print("1. ORIGINAL PATIENT DATA:")
    print("-" * 30)
    print(json.dumps(sample_patient_data, indent=2))
    
    print("\n2. TESTING DIABETES MODEL TRANSFORMATION:")
    print("-" * 45)
    
    diabetes_data = _transform_patient_data_for_mcp(sample_patient_data, "diabetes")
    print("Transformed data for diabetes model:")
    print(json.dumps(diabetes_data, indent=2))
    
    print("\n3. CHECKING KEY TRANSFORMATIONS:")
    print("-" * 35)
    
    transformations = {
        "d_age": diabetes_data.get('d_age'),
        "d_gender": diabetes_data.get('d_gender'),
        "smoking_history": diabetes_data.get('smoking_history'),
        "bmi": diabetes_data.get('bmi'),
        "hypertension": diabetes_data.get('hypertension'),
        "heart_disease": diabetes_data.get('heart_disease'),
        "HbA1c_level": diabetes_data.get('HbA1c_level'),
        "blood_glucose_level": diabetes_data.get('blood_glucose_level')
    }
    
    for key, value in transformations.items():
        print(f"✓ {key}: {value} (type: {type(value).__name__})")
    
    print("\n4. VALIDATION CHECKS:")
    print("-" * 20)
    
    validation_checks = [
        ("d_age is numeric", isinstance(diabetes_data.get('d_age'), (int, float))),
        ("d_gender is string", isinstance(diabetes_data.get('d_gender'), str)),
        ("smoking_history is string", isinstance(diabetes_data.get('smoking_history'), str)),
        ("bmi is calculated", diabetes_data.get('bmi') is not None),
        ("hypertension inferred from BP", diabetes_data.get('hypertension') == 1),  # 140 >= 140
        ("BMI calculation correct", abs(diabetes_data.get('bmi', 0) - 29.41) < 0.1)  # 85/(1.7^2) ≈ 29.41
    ]
    
    for check, passed in validation_checks:
        status = "✅" if passed else "❌"
        print(f"{status} {check}")
    
    print("\n5. WHAT THIS SHOULD FIX:")
    print("-" * 25)
    print("✅ d_gender: '0' → 'Female' (string)")
    print("✅ smoking_history: '0' → 'never' (string)")
    print("✅ BMI: calculated from height/weight")
    print("✅ Hypertension: inferred from blood pressure")
    print("✅ Default values: provided for missing diabetes fields")
    
    print("\n6. EXPECTED MCP BEHAVIOR:")
    print("-" * 25)
    print("With these transformations, the MCP should:")
    print("• Accept the data without validation errors")
    print("• Process the prediction successfully")
    print("• Return SHAP explanations in tool_calls result")

if __name__ == "__main__":
    test_data_transformation()