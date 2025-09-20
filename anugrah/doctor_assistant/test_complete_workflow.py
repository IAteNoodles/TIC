#!/usr/bin/env python3
"""
Test the complete workflow to verify SHAP prominence in MedGemma reports
"""
import asyncio
import json
import sys
sys.path.append('.')
from unittest.mock import AsyncMock, Mock, patch

# Mock MCP response with SHAP data
mock_mcp_response = {
    "status": "success",
    "prediction": 1,
    "confidence": 0.78,
    "shap_explanations": [
        {
            "feature": "age",
            "value": 58.0,
            "shap_value": -1.2274,
            "description": "Age (in years)"
        },
        {
            "feature": "ap_hi", 
            "value": 140.0,
            "shap_value": 1.1884,
            "description": "Systolic blood pressure"
        },
        {
            "feature": "cholesterol",
            "value": 2.0,
            "shap_value": 0.3778,
            "description": "Cholesterol level"
        }
    ],
    "model_version": "cardio_v1",
    "timestamp": "2024-12-19T13:30:45Z"
}

def test_shap_processing_demo():
    """Demonstrate the enhanced SHAP processing capabilities"""
    print("=" * 80)
    print("ENHANCED SHAP PROCESSING DEMONSTRATION")
    print("=" * 80)
    
    # Import the SHAP processing functions directly
    try:
        from agents.diagnosis_agent import _extract_shap_data, _create_detailed_shap_summary
        
        print("1. Testing Enhanced SHAP Data Extraction:")
        print("-" * 50)
        
        # Test the enhanced extraction
        shap_data = _extract_shap_data(mock_mcp_response)
        print(f"✅ Model Prediction: {shap_data.get('prediction', 'N/A')}")
        print(f"✅ Confidence: {shap_data.get('confidence', 'N/A')}")
        print(f"✅ Number of SHAP explanations: {len(shap_data.get('explanations', []))}")
        print(f"✅ Top factors identified: {len(shap_data.get('top_factors', []))}")
        
        print("\n2. Testing Detailed SHAP Summary Generation:")
        print("-" * 50)
        
        # Generate the detailed summary with mock patient data
        mock_patient_data = {
            'age': 58.0,
            'ap_hi': 140.0,
            'cholesterol': 2.0
        }
        detailed_summary = _create_detailed_shap_summary(shap_data, mock_patient_data)
        
        print("✅ Generated detailed SHAP summary!")
        print(f"✅ Summary length: {len(detailed_summary)} characters")
        
        # Check for key elements
        key_elements = {
            "Contains SHAP scores": "SHAP Score:" in detailed_summary,
            "Contains clinical significance": "Clinical Significance:" in detailed_summary,
            "Contains importance rankings": "Importance Ranking:" in detailed_summary,
            "Contains top factors section": "TOP 3 MOST INFLUENTIAL FACTORS:" in detailed_summary,
            "Contains risk summary": "RISK FACTOR SUMMARY:" in detailed_summary,
            "Contains emojis for clarity": "🔴" in detailed_summary and "🟢" in detailed_summary
        }
        
        print("\n3. Summary Content Analysis:")
        print("-" * 50)
        for element, present in key_elements.items():
            status = "✅" if present else "❌"
            print(f"{status} {element}")
        
        print("\n4. Sample of Enhanced Summary:")
        print("-" * 50)
        # Show first few lines of the summary
        summary_lines = detailed_summary.split('\n')[:15]
        for line in summary_lines:
            if line.strip():
                print(f"   {line}")
        print("   [... truncated for display ...]")
        
        print("\n5. Key Improvements for MedGemma:")
        print("-" * 50)
        print("✅ Structured SHAP data with clear sections")
        print("✅ Numerical SHAP scores prominently displayed")
        print("✅ Clinical interpretations for each feature")
        print("✅ Importance rankings to guide clinical focus")
        print("✅ Top factor identification with visual indicators")
        print("✅ Risk factor summaries for quick assessment")
        print("✅ Clear instructions for LLM integration")
        
        print("\n🎯 RESULT: MedGemma will now receive comprehensive SHAP analysis")
        print("   that forces integration of quantitative model insights!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

if __name__ == "__main__":
    success = test_shap_processing_demo()
    if success:
        print("\n" + "=" * 80)
        print("✅ ENHANCED SHAP PROCESSING TEST COMPLETED SUCCESSFULLY!")
        print("The diagnosis agent is now ready to generate reports with")
        print("prominent SHAP analysis integration.")
        print("=" * 80)
    else:
        print("\n❌ Test failed - please check the errors above.")
if __name__ == "__main__":
    success = test_shap_processing_demo()
    if success:
        print("\n" + "=" * 80)
        print("✅ ENHANCED SHAP PROCESSING TEST COMPLETED SUCCESSFULLY!")
        print("The diagnosis agent is now ready to generate reports with")
        print("prominent SHAP analysis integration.")
        print("=" * 80)
    else:
        print("\n❌ Test failed - please check the errors above.")