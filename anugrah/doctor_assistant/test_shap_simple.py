#!/usr/bin/env python3
"""
Test if SHAP scores are highlighted in the final report
"""
import sys
sys.path.append('.')

def test_shap_highlighting():
    """Check if SHAP scores are prominently featured in diagnosis reports"""
    print("=" * 80)
    print("TESTING SHAP SCORE HIGHLIGHTING IN FINAL REPORT")
    print("=" * 80)
    
    try:
        from agents.diagnosis_agent import _extract_shap_data, _create_detailed_shap_summary
        
        # Simulate real MCP response with SHAP data
        mock_mcp_response = {
            "ok": True,
            "answer": "High cardiovascular risk predicted",
            "tool_calls": [{
                "result": """{
                    "prediction": 1,
                    "explanations": {
                        "explanations": [
                            {"feature": "age", "value": 58.0, "shap_value": -1.2274, "impact": "decreases"},
                            {"feature": "ap_hi", "value": 140.0, "shap_value": 1.1884, "impact": "increases"},
                            {"feature": "cholesterol", "value": 2.0, "shap_value": 0.3778, "impact": "increases"}
                        ]
                    }
                }"""
            }]
        }
        
        mock_patient_data = {"name": "John Doe", "age": 58}
        
        print("1. TESTING SHAP DATA EXTRACTION:")
        print("-" * 40)
        
        shap_data = _extract_shap_data(mock_mcp_response)
        print(f"✅ Extracted {len(shap_data.get('explanations', []))} SHAP explanations")
        
        print("\n2. TESTING DETAILED SHAP SUMMARY:")
        print("-" * 40)
        
        detailed_summary = _create_detailed_shap_summary(shap_data, mock_patient_data)
        print(f"✅ Generated summary: {len(detailed_summary)} characters")
        
        # Check if SHAP scores are prominently featured
        shap_checks = [
            ("Contains 'SHAP Score:'", "SHAP Score:" in detailed_summary),
            ("Contains numerical values", "-1.2274" in detailed_summary),
            ("Contains impact analysis", "increases" in detailed_summary and "decreases" in detailed_summary),
            ("Contains visual indicators", "🔴" in detailed_summary or "🟢" in detailed_summary)
        ]
        
        print("\n   SHAP prominence in summary:")
        all_passed = True
        for check, passed in shap_checks:
            status = "✅" if passed else "❌"
            print(f"   {status} {check}")
            if not passed:
                all_passed = False
        
        print("\n3. SAMPLE SHAP CONTENT:")
        print("-" * 25)
        
        # Show actual SHAP content
        lines = detailed_summary.split('\n')
        shap_lines = [line for line in lines if 'SHAP' in line or any(score in line for score in ['-1.2274', '1.1884', '0.3778'])]
        
        for i, line in enumerate(shap_lines[:5]):
            print(f"   {i+1}. {line.strip()}")
        
        if all_passed:
            print("\n✅ SHAP scores are prominently highlighted!")
            return True
        else:
            print("\n❌ SHAP scores need better highlighting")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_shap_highlighting()
    print("\n" + "=" * 80)
    if success:
        print("🎯 RESULT: SHAP scores ARE prominently featured in reports!")
    else:
        print("⚠️  RESULT: SHAP scores need better highlighting")
    print("=" * 80)