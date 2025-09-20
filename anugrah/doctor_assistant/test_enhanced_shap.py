#!/usr/bin/env python3
"""
Test the enhanced SHAP processing and detailed summary generation
"""

import json
import sys
import os

# Add the project root to Python path  
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.diagnosis_agent import _extract_shap_data, _create_detailed_shap_summary

def test_enhanced_shap_processing():
    """Test the enhanced SHAP data extraction and detailed summary creation."""
    
    print("=" * 80)
    print("TESTING ENHANCED SHAP PROCESSING & DETAILED SUMMARY GENERATION")
    print("=" * 80)
    
    # Mock your actual MCP response structure
    mock_mcp_response = {
        "ok": True,
        "answer": "Based on the provided data, there is a high probability of cardiovascular disease for John Doe. The prediction is influenced by his age, ap_hi, and cholesterol levels.",
        "tool_calls": [
            {
                "name": "call_cardio_api",
                "arguments": {
                    "age": 58,
                    "gender": 1,
                    "height": 170,
                    "weight": 85,
                    "ap_hi": 140,
                    "ap_lo": 90,
                    "cholesterol": 2,
                    "gluc": 1,
                    "smoke": 0,
                    "alco": 0,
                    "active": 1
                },
                "result": json.dumps({
                    "prediction": 1,
                    "confidence": 0.78,
                    "explanations": {
                        "explanations": [
                            {"feature": "age", "value": 58.0, "shap_value": -1.2273634672164917, "impact": "decreases", "importance": 1.2273634672164917},
                            {"feature": "ap_hi", "value": 140.0, "shap_value": 1.188364863395691, "impact": "increases", "importance": 1.188364863395691},
                            {"feature": "cholesterol", "value": 2.0, "shap_value": 0.3777754008769989, "impact": "increases", "importance": 0.3777754008769989},
                            {"feature": "height", "value": 170.0, "shap_value": -0.16889558732509613, "impact": "decreases", "importance": 0.16889558732509613},
                            {"feature": "ap_lo", "value": 90.0, "shap_value": -0.1517324596643448, "impact": "decreases", "importance": 0.1517324596643448},
                            {"feature": "weight", "value": 85.0, "shap_value": 0.1268458217382431, "impact": "increases", "importance": 0.1268458217382431},
                            {"feature": "gluc", "value": 1.0, "shap_value": 0.05598160997033119, "impact": "increases", "importance": 0.05598160997033119},
                            {"feature": "gender", "value": 1.0, "shap_value": 0.04984044283628464, "impact": "increases", "importance": 0.04984044283628464},
                            {"feature": "active", "value": 1.0, "shap_value": -0.026526223868131638, "impact": "decreases", "importance": 0.026526223868131638},
                            {"feature": "alco", "value": 0.0, "shap_value": 0.023148661479353905, "impact": "increases", "importance": 0.023148661479353905},
                            {"feature": "smoke", "value": 0.0, "shap_value": 0.020166756585240364, "impact": "increases", "importance": 0.020166756585240364}
                        ],
                        "top_factors": [
                            {"feature": "age", "value": 58.0, "shap_value": -1.2273634672164917, "impact": "decreases", "importance": 1.2273634672164917},
                            {"feature": "ap_hi", "value": 140.0, "shap_value": 1.188364863395691, "impact": "increases", "importance": 1.188364863395691},
                            {"feature": "cholesterol", "value": 2.0, "shap_value": 0.3777754008769989, "impact": "increases", "importance": 0.3777754008769989}
                        ],
                        "summary": "The prediction is primarily influenced by: Age (value: 58.00) decreases the risk, Ap Hi (value: 140.00) increases the risk, Cholesterol (value: 2.00) increases the risk."
                    }
                })
            }
        ],
        "error": None
    }
    
    mock_patient_data = {
        "name": "John Doe",
        "age": 58,
        "gender": 1,
        "height": 170,
        "weight": 85,
        "ap_hi": 140,
        "ap_lo": 90,
        "cholesterol": 2,
        "gluc": 1,
        "smoke": 0,
        "alco": 0,
        "active": 1
    }
    
    print("1. TESTING ENHANCED SHAP DATA EXTRACTION:")
    print("-" * 50)
    
    shap_data = _extract_shap_data(mock_mcp_response)
    print("✅ Enhanced SHAP data extracted:")
    print(f"   - Model Prediction: {shap_data.get('model_prediction')}")
    print(f"   - Confidence: {shap_data.get('confidence')}")
    print(f"   - Number of explanations: {len(shap_data.get('explanations', []))}")
    print(f"   - Number of top factors: {len(shap_data.get('top_factors', []))}")
    print(f"   - Has summary: {'Yes' if shap_data.get('summary') else 'No'}")
    print()
    
    print("2. TESTING DETAILED SHAP SUMMARY GENERATION:")
    print("-" * 50)
    
    detailed_summary = _create_detailed_shap_summary(shap_data, mock_patient_data)
    print("✅ Generated detailed SHAP summary:")
    print()
    print(detailed_summary)
    print()
    
    print("3. SUMMARY ANALYSIS:")
    print("-" * 20)
    print(f"✅ Summary length: {len(detailed_summary)} characters")
    print(f"✅ Contains SHAP scores: {'SHAP Score:' in detailed_summary}")
    print(f"✅ Contains clinical significance: {'Clinical Significance:' in detailed_summary}")
    print(f"✅ Contains importance rankings: {'Importance Ranking:' in detailed_summary}")
    print(f"✅ Contains top factors: {'TOP 3 MOST INFLUENTIAL' in detailed_summary}")
    print(f"✅ Contains risk summary: {'RISK FACTOR SUMMARY' in detailed_summary}")
    print()
    
    print("4. WHAT THE LLM WILL NOW RECEIVE:")
    print("-" * 35)
    print("The MedGemma LLM will now receive:")
    print("• Structured SHAP data with clear sections")
    print("• Numerical SHAP scores for each feature")
    print("• Clinical significance interpretations")
    print("• Top factor rankings with emojis")
    print("• Risk factor summaries")
    print("• Clear instructions to integrate SHAP values")
    print()
    print("This should result in reports that prominently feature")
    print("SHAP analysis instead of generic clinical assessments!")

if __name__ == "__main__":
    test_enhanced_shap_processing()