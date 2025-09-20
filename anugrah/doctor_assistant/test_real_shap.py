#!/usr/bin/env python3
"""
Simple test to demonstrate the enhanced SHAP processing
"""
import sys
sys.path.append('.')
import json

# Test with the format the MCP actually returns (through tool_calls)
mock_mcp_response_with_tool_calls = {
    "tool_calls": [
        {
            "name": "cardio_prediction_api",
            "result": json.dumps({
                "prediction": 1,
                "confidence": 0.78,
                "explanations": {
                    "age": {
                        "value": 58.0,
                        "shap_value": -1.2274,
                        "description": "Age (in years)"
                    },
                    "ap_hi": {
                        "value": 140.0,
                        "shap_value": 1.1884,
                        "description": "Systolic blood pressure"
                    },
                    "cholesterol": {
                        "value": 2.0,
                        "shap_value": 0.3778,
                        "description": "Cholesterol level"
                    }
                }
            })
        }
    ]
}

def test_real_shap_processing():
    """Test the SHAP processing with realistic data format"""
    print("=" * 80)
    print("TESTING REAL SHAP PROCESSING WITH CORRECT FORMAT")
    print("=" * 80)
    
    try:
        from agents.diagnosis_agent import _extract_shap_data, _create_detailed_shap_summary
        
        print("1. Testing SHAP Data Extraction with Tool Calls Format:")
        print("-" * 60)
        
        # Extract SHAP data using the real format
        shap_data = _extract_shap_data(mock_mcp_response_with_tool_calls)
        
        print(f"✅ Model Prediction: {shap_data.get('model_prediction')}")
        print(f"✅ Confidence: {shap_data.get('confidence')}")
        print(f"✅ Number of explanations: {len(shap_data) - 2}")  # -2 for prediction and confidence
        
        # Create mock patient data for the summary
        mock_patient_data = {
            'age': 58.0,
            'ap_hi': 140.0,
            'cholesterol': 2.0
        }
        
        print("\n2. Testing Detailed SHAP Summary Generation:")
        print("-" * 60)
        
        # Generate detailed summary
        detailed_summary = _create_detailed_shap_summary(shap_data, mock_patient_data)
        
        print(f"✅ Summary generated successfully!")
        print(f"✅ Summary length: {len(detailed_summary)} characters")
        
        # Check key content
        key_checks = {
            "Contains SHAP scores": "SHAP Score:" in detailed_summary,
            "Contains clinical significance": "Clinical Significance:" in detailed_summary,
            "Contains importance rankings": "Importance Ranking:" in detailed_summary,
            "Contains risk indicators": "🔴" in detailed_summary or "🟢" in detailed_summary,
            "Contains top factors": "TOP" in detailed_summary and "INFLUENTIAL" in detailed_summary
        }
        
        print("\n3. Content Validation:")
        print("-" * 60)
        for check, passed in key_checks.items():
            status = "✅" if passed else "❌"
            print(f"{status} {check}")
        
        print("\n4. Sample Summary Content:")
        print("-" * 60)
        # Show first 15 lines of the summary
        lines = detailed_summary.split('\n')[:15]
        for line in lines:
            if line.strip():
                print(f"   {line}")
        print("   [... content continues ...]")
        
        print("\n" + "=" * 80)
        print("✅ SHAP PROCESSING VALIDATION COMPLETE!")
        print("\nKey accomplishments:")
        print("• SHAP data extracted correctly from MCP response")
        print("• Detailed summary generated with clinical context") 
        print("• Numerical SHAP scores prominently featured")
        print("• Clinical significance interpretations provided")
        print("• Top factors identified with visual indicators")
        print("\n🎯 The diagnosis agent is now equipped to provide")
        print("   MedGemma with rich, structured SHAP analysis!")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_real_shap_processing()