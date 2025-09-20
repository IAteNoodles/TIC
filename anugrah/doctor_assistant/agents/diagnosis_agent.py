from connectors.llm_connector import call_llm
from state import GraphState
from tools.parameter_tool import get_model_parameters_tool
from tools.mcp_tool import get_mcp_prediction_tool
from tools.backend_tool import get_patient_data_tool
from logging_config import get_logger
import json

logger = get_logger("agents.diagnosis")

def _determine_model_type(query: str) -> str:
    """
    Determines the type of model to use based on the query.
    """
    query_lower = query.lower()
    if any(keyword in query_lower for keyword in ["diabetes", "blood sugar", "insulin", "hba1c", "glucose"]):
        return "diabetes"
    elif any(keyword in query_lower for keyword in ["cardiovascular", "heart", "cardio", "blood pressure", "cholesterol"]):
        return "cardiovascular_disease"
    else:
        # Default to cardiovascular for now
        return "cardiovascular_disease"

def _transform_patient_data_for_mcp(patient_data: dict, model_type: str) -> dict:
    """
    Transform patient data to match the field names expected by the MCP model.
    
    Args:
        patient_data: Raw patient data from the database
        model_type: Type of model being used ('diabetes' or 'cardiovascular_disease')
    
    Returns:
        Transformed patient data with correct field names for MCP
    """
    transformed_data = patient_data.copy()
    
    # Field mappings for different models
    if model_type == "diabetes":
        # The diabetes model expects 'd_age' instead of 'age'
        if 'age' in transformed_data:
            transformed_data['d_age'] = transformed_data['age']
            # Keep the original 'age' field as well for backward compatibility
        
        # Map gender to string format for diabetes model
        if 'gender' in transformed_data:
            gender_val = transformed_data['gender']
            transformed_data['d_gender'] = "Male" if gender_val == 1 else "Female"
        
        # Map smoking status to string
        if 'smoke' in transformed_data:
            smoke_val = transformed_data['smoke']
            transformed_data['smoking_history'] = "current" if smoke_val == 1 else "never"
        
        # Calculate BMI if height and weight are available
        if 'height' in transformed_data and 'weight' in transformed_data:
            height_m = transformed_data['height'] / 100  # Convert cm to meters
            weight_kg = transformed_data['weight']
            if height_m > 0:
                transformed_data['bmi'] = round(weight_kg / (height_m ** 2), 2)
        
        # Set default diabetes-specific fields if not present
        if 'hypertension' not in transformed_data:
            # Infer from blood pressure if available
            ap_hi = transformed_data.get('ap_hi', 0)
            transformed_data['hypertension'] = 1 if ap_hi >= 140 else 0
        
        if 'heart_disease' not in transformed_data:
            transformed_data['heart_disease'] = 0  # Default to no known heart disease
        
        # Set default HbA1c and glucose if not available
        if 'HbA1c_level' not in transformed_data:
            transformed_data['HbA1c_level'] = 5.7  # Default normal value
        
        if 'blood_glucose_level' not in transformed_data:
            transformed_data['blood_glucose_level'] = 95  # Default fasting glucose
    
    # Add more model-specific transformations here as needed
    # elif model_type == "cardiovascular_disease":
    #     # Any cardiovascular-specific transformations
    #     pass
    
    return transformed_data


def diagnosis_agent_node(state: GraphState):
    """
    Orchestrates the diagnosis workflow:
    1. Determines which model to use.
    2. Checks for data sufficiency for that model.
    3. Calls the MCP model for a raw prediction.
    4. Calls MedGemma to generate a formatted report.
    """
    logger.info("Diagnosis agent started")
    
    patient_id = state.get('patient_id')
    query = state.get('query')

    # Fetch patient data
    patient_data = get_patient_data_tool(patient_id)
    if "error" in patient_data:
        state['error_message'] = patient_data['error']
        return state
    state['db_response'] = patient_data

    # --- 1. Determine which model to use ---
    model_type = _determine_model_type(query)

    # --- 2. Data Sufficiency Check ---
    model_params = get_model_parameters_tool() 
    required_fields = model_params.get(model_type, {}).get("required_fields", [])
    
    missing_fields = [field for field in required_fields if field not in patient_data or patient_data.get(field) is None]
    
    if missing_fields:
        clarification_request = f"Patient data is incomplete for a {model_type.replace('_', ' ')} diagnosis. Please provide: {', '.join(missing_fields)}."
        state['final_report'] = clarification_request
        return state

    # --- 3. Transform patient data for MCP model ---
    transformed_data = _transform_patient_data_for_mcp(patient_data, model_type)
    
    # --- 4. Call MCP model for prediction ---
    mcp_prompt = f"Based on the following patient data, provide a prediction for {model_type.replace('_', ' ')}. Data: {json.dumps(transformed_data)}"
    prediction_result = get_mcp_prediction_tool(mcp_prompt)

    # Check for actual errors (not null values)
    if prediction_result.get('error') is not None or not prediction_result.get('answer'):
        error_msg = prediction_result.get('error') or "No answer from prediction model."
        state['error_message'] = f"Error from prediction model: {error_msg}"
        return state
    
    raw_prediction = prediction_result.get('answer', '')
    
    # --- Enhanced: Parse SHAP explanations from MCP response ---
    shap_data = _extract_shap_data(prediction_result)
    
    # --- 4. Generate enhanced report with SHAP insights ---
    enhanced_report = _generate_enhanced_report(
        patient_data=patient_data,
        raw_prediction=raw_prediction,
        shap_data=shap_data,
        model_type=model_type
    )
    
    # --- 5. Call MedGemma for final polished report ---
    if shap_data:
        # Create a detailed SHAP summary for the LLM
        shap_summary = _create_detailed_shap_summary(shap_data, patient_data)
        
        report_prompt = f"""
        Generate a comprehensive diagnostic report for {model_type.replace('_', ' ')} based on SPECIFIC patient data and AI model analysis with SHAP explanations.
        
        CRITICAL: You MUST integrate the SHAP feature importance scores and explanations into your report. These are scientifically-derived importance values that explain WHY the AI made its prediction.
        
        Structure the report with these EXACT sections:
        1. Executive Summary
        2. AI Model Prediction & Confidence
        3. SHAP Feature Analysis (MANDATORY - Include all SHAP scores and explanations)
        4. Risk Factor Interpretation
        5. Clinical Correlation
        6. Evidence-Based Recommendations
        7. Next Steps & Monitoring
        
        PATIENT DATA:
        {json.dumps(patient_data, indent=2)}
        
        AI MODEL PREDICTION:
        {raw_prediction}
        
        SHAP FEATURE IMPORTANCE ANALYSIS (MUST BE PROMINENTLY FEATURED):
        {shap_summary}
        
        ENHANCED DIAGNOSTIC ANALYSIS:
        {enhanced_report}
        
        INSTRUCTIONS:
        - Start with the SHAP analysis findings in section 3
        - Explain what each SHAP score means clinically
        - Reference specific SHAP values when discussing risk factors
        - Use the SHAP importance rankings to prioritize your recommendations
        - Include numerical SHAP values in parentheses when mentioning features
        - Explain why high/low SHAP values matter for this patient
        
        Make this report evidence-based using the SHAP explanations as the scientific foundation.
        """
    else:
        # Fallback to original approach if no SHAP data
        report_prompt = f"""
        Generate a preliminary diagnostic report for {model_type.replace('_', ' ')} based on the patient data and model prediction.
        Structure the report with: Patient Summary, Key Findings, Raw Model Prediction, Potential Diagnosis, and Recommended Next Steps.

        Patient Data:
        {json.dumps(patient_data, indent=2)}

        Raw Prediction from ML Model:
        {raw_prediction}
        """

    medgemma_endpoint = "http://192.168.1.65:1234/v1/chat/completions"
    medgemma_model = "medgemma-4b-it"
    medgemma_system = "You are a medical expert generating a comprehensive diagnostic report. Focus on clinical accuracy and actionable insights."
    
    # Try to get LLM polishing, but fallback gracefully
    try:
        response = call_llm(
            model_name=medgemma_model,
            endpoint=medgemma_endpoint,
            system_prompt=medgemma_system,
            user_prompt=report_prompt,
            timeout=300  # 5 minutes for complex medical report generation
        )
        
        if "error" in response:
            logger.warning("LLM returned error, using enhanced report as fallback: %s", response.get('error'))
            final_report = enhanced_report
        elif "choices" in response and response["choices"]:
            final_report = response['choices'][0]['message']['content']
            logger.info("Successfully generated polished report via LLM")
        else:
            logger.warning("LLM returned unexpected format, using enhanced report as fallback")
            final_report = enhanced_report
            
    except Exception as e:
        logger.error("LLM call failed with exception: %s", e)
        logger.info("Falling back to enhanced report generated from SHAP data")
        final_report = enhanced_report

    state['final_report'] = final_report
    return state


def _extract_shap_data(prediction_result: dict) -> dict:
    """
    Extract SHAP explanation data from MCP prediction result.
    
    Returns:
        dict: Parsed SHAP data with explanations, top factors, and summary
    """
    try:
        # Look for tool calls in the MCP response
        tool_calls = prediction_result.get('tool_calls', [])
        if not tool_calls:
            return {}
        
        # Find any prediction tool call (cardio, diabetes, etc.)
        for tool_call in tool_calls:
            tool_name = tool_call.get('name', '').lower()
            if any(keyword in tool_name for keyword in ['cardio', 'diabetes', 'api', 'prediction']):
                result_str = tool_call.get('result', '{}')
                if isinstance(result_str, str):
                    result_data = json.loads(result_str)
                else:
                    result_data = result_str
                
                # Handle nested explanations structure
                explanations_data = result_data.get('explanations', {})
                
                # Check if explanations is nested (explanations.explanations)
                if 'explanations' in explanations_data:
                    raw_explanations_list = explanations_data['explanations']
                    top_factors_list = explanations_data.get('top_factors', [])
                    summary = explanations_data.get('summary', '')
                else:
                    # Fallback to old format (explanations as dictionary)
                    raw_explanations_list = []
                    for feature, data in explanations_data.items():
                        if isinstance(data, dict):
                            raw_explanations_list.append({
                                'feature': feature,
                                'value': data.get('value', 'N/A'),
                                'shap_value': data.get('shap_value', 0),
                                'description': data.get('description', feature),
                                'importance': abs(data.get('shap_value', 0)),
                                'impact': 'increases' if data.get('shap_value', 0) > 0 else 'decreases'
                            })
                    top_factors_list = []
                    summary = ''
                
                # Process the explanations list
                explanations_list = []
                for explanation in raw_explanations_list:
                    if isinstance(explanation, dict):
                        shap_value = explanation.get('shap_value', 0)
                        processed_explanation = {
                            'feature': explanation.get('feature', 'Unknown'),
                            'value': explanation.get('value', 'N/A'),
                            'shap_value': shap_value,
                            'description': explanation.get('description', explanation.get('feature', 'Unknown')),
                            'importance': abs(shap_value),  # Importance is absolute value
                            'impact': explanation.get('impact', 'increases' if shap_value > 0 else 'decreases')
                        }
                        explanations_list.append(processed_explanation)
                
                # Sort by importance if not already sorted
                explanations_list.sort(key=lambda x: x['importance'], reverse=True)
                
                # Use provided top factors or create from sorted explanations
                if top_factors_list:
                    top_factors = []
                    for factor in top_factors_list:
                        if isinstance(factor, dict):
                            shap_value = factor.get('shap_value', 0)
                            top_factors.append({
                                'feature': factor.get('feature', 'Unknown'),
                                'value': factor.get('value', 'N/A'),
                                'shap_value': shap_value,
                                'description': factor.get('description', factor.get('feature', 'Unknown')),
                                'importance': abs(shap_value),
                                'impact': factor.get('impact', 'increases' if shap_value > 0 else 'decreases')
                            })
                else:
                    top_factors = explanations_list[:3]  # Top 3 most important
                
                # Create summary if not provided
                if not summary and explanations_list:
                    top_factor = explanations_list[0]
                    summary = f"The prediction is primarily influenced by: {top_factor['feature']} (value: {top_factor['value']:.2f}) {top_factor['impact']} the risk"
                    if len(explanations_list) > 1:
                        second_factor = explanations_list[1]
                        summary += f", {second_factor['feature']} (value: {second_factor['value']:.2f}) {second_factor['impact']} the risk"
                    if len(explanations_list) > 2:
                        third_factor = explanations_list[2]
                        summary += f", {third_factor['feature']} (value: {third_factor['value']:.2f}) {third_factor['impact']} the risk"
                    summary += "."
                
                return {
                    'model_prediction': result_data.get('prediction'),
                    'confidence': result_data.get('confidence'),
                    'explanations': explanations_list,
                    'top_factors': top_factors,
                    'summary': summary
                }
        
        return {}
    except (json.JSONDecodeError, KeyError, AttributeError) as e:
        logger.warning("Failed to parse SHAP data: %s", e)
        return {}


def _generate_enhanced_report(patient_data: dict, raw_prediction: str, shap_data: dict, model_type: str) -> str:
    """
    Generate an enhanced diagnostic report using SHAP explanations.
    """
    if not shap_data:
        return f"Basic Prediction: {raw_prediction}"
    
    # Extract key components
    explanations = shap_data.get('explanations', [])
    top_factors = shap_data.get('top_factors', [])
    summary = shap_data.get('summary', '')
    prediction = shap_data.get('prediction', 'Unknown')
    
    report_lines = [
        "=== ENHANCED DIAGNOSTIC ANALYSIS ===",
        "",
        f"**Model Prediction:** {'High Risk' if prediction == 1 else 'Low Risk'} for {model_type.replace('_', ' ').title()}",
        "",
        f"**Clinical Summary:** {raw_prediction}",
        "",
        "**Risk Factor Analysis (AI-Powered):**"
    ]
    
    if summary:
        report_lines.extend([
            f"• {summary}",
            ""
        ])
    
    # Top contributing factors
    if top_factors:
        report_lines.extend([
            "**Top Contributing Factors:**",
            ""
        ])
        
        for i, factor in enumerate(top_factors[:5], 1):
            feature = factor.get('feature', 'Unknown')
            value = factor.get('value', 'N/A')
            impact = factor.get('impact', 'unknown')
            importance = factor.get('importance', 0)
            
            # Map feature names to clinical terms
            clinical_name = _map_feature_to_clinical_term(feature)
            impact_emoji = "⬆️" if impact == "increases" else "⬇️"
            
            report_lines.append(
                f"{i}. **{clinical_name}** (Value: {value}) {impact_emoji} {impact} risk "
                f"(Importance: {importance:.3f})"
            )
        
        report_lines.append("")
    
    # Detailed breakdown of all factors
    if explanations:
        report_lines.extend([
            "**Complete Risk Factor Breakdown:**",
            ""
        ])
        
        # Group factors by impact direction
        increasing_factors = []
        decreasing_factors = []
        
        for explanation in explanations:
            factor_info = {
                'name': _map_feature_to_clinical_term(explanation.get('feature', '')),
                'value': explanation.get('value', 'N/A'),
                'importance': explanation.get('importance', 0)
            }
            
            if explanation.get('impact') == 'increases':
                increasing_factors.append(factor_info)
            else:
                decreasing_factors.append(factor_info)
        
        if increasing_factors:
            report_lines.append("*Factors Increasing Risk:*")
            for factor in sorted(increasing_factors, key=lambda x: x['importance'], reverse=True):
                report_lines.append(f"• {factor['name']}: {factor['value']} (Impact: {factor['importance']:.3f})")
            report_lines.append("")
        
        if decreasing_factors:
            report_lines.append("*Protective Factors:*")
            for factor in sorted(decreasing_factors, key=lambda x: x['importance'], reverse=True):
                report_lines.append(f"• {factor['name']}: {factor['value']} (Protection: {factor['importance']:.3f})")
            report_lines.append("")
    
    # Clinical recommendations based on top risk factors
    if top_factors:
        report_lines.extend([
            "**AI-Generated Clinical Insights:**",
            ""
        ])
        
        recommendations = _generate_clinical_recommendations(top_factors, model_type)
        for rec in recommendations:
            report_lines.append(f"• {rec}")
    
    return "\n".join(report_lines)


def _map_feature_to_clinical_term(feature: str) -> str:
    """
    Map ML feature names to clinical terminology.
    """
    mapping = {
        'age': 'Age',
        'gender': 'Gender',
        'height': 'Height',
        'weight': 'Weight',
        'ap_hi': 'Systolic Blood Pressure',
        'ap_lo': 'Diastolic Blood Pressure',
        'cholesterol': 'Cholesterol Level',
        'gluc': 'Glucose Level',
        'smoke': 'Smoking Status',
        'alco': 'Alcohol Consumption',
        'active': 'Physical Activity Level'
    }
    return mapping.get(feature.lower(), feature.title())


def _generate_clinical_recommendations(top_factors: list, model_type: str) -> list:
    """
    Generate clinical recommendations based on top risk factors.
    """
    recommendations = []
    
    for factor in top_factors[:3]:  # Focus on top 3 factors
        feature = factor.get('feature', '').lower()
        impact = factor.get('impact', '')
        value = factor.get('value', 0)
        
        if feature == 'ap_hi' and impact == 'increases':
            recommendations.append("Monitor and manage hypertension - consider antihypertensive therapy")
        elif feature == 'cholesterol' and impact == 'increases':
            recommendations.append("Evaluate lipid profile and consider statin therapy if indicated")
        elif feature == 'age' and impact == 'increases':
            recommendations.append("Age-related risk requires enhanced monitoring and preventive measures")
        elif feature == 'smoke' and impact == 'increases':
            recommendations.append("Smoking cessation counseling and support is critical")
        elif feature == 'gluc' and impact == 'increases':
            recommendations.append("Assess diabetic status and optimize glucose control")
        elif feature == 'weight' and impact == 'increases':
            recommendations.append("Weight management and nutritional counseling recommended")
        elif feature == 'active' and impact == 'decreases':
            recommendations.append("Continue current physical activity levels - protective factor")
    
    if model_type == 'cardiovascular_disease':
        recommendations.append("Consider cardiology referral for comprehensive cardiovascular risk assessment")
    elif model_type == 'diabetes':
        recommendations.append("Consider endocrinology consultation for diabetes risk evaluation")
    
    return recommendations


def _create_detailed_shap_summary(shap_data: dict, patient_data: dict) -> str:
    """
    Create a detailed, structured summary of SHAP explanations for LLM consumption.
    """
    if not shap_data:
        return "No SHAP explanations available."
    
    summary_lines = [
        "SHAP (SHapley Additive exPlanations) FEATURE IMPORTANCE ANALYSIS:",
        "=" * 60,
        ""
    ]
    
    # Model prediction info
    model_prediction = shap_data.get('model_prediction')
    if model_prediction is not None:
        prediction_text = "HIGH RISK" if model_prediction == 1 else "LOW RISK"
        summary_lines.append(f"🎯 MODEL PREDICTION: {prediction_text} (Value: {model_prediction})")
        summary_lines.append("")
    
    # Overall summary
    overall_summary = shap_data.get('summary', '')
    if overall_summary:
        summary_lines.extend([
            "📊 SHAP SUMMARY:",
            f"   {overall_summary}",
            ""
        ])
    
    # Detailed feature explanations
    explanations = shap_data.get('explanations', [])
    if explanations:
        summary_lines.extend([
            "🔍 DETAILED FEATURE ANALYSIS:",
            ""
        ])
        
        # Sort by importance (descending)
        sorted_explanations = sorted(explanations, key=lambda x: x.get('importance', 0), reverse=True)
        
        for i, explanation in enumerate(sorted_explanations, 1):
            feature = explanation.get('feature', 'Unknown')
            value = explanation.get('value', 'N/A')
            shap_value = explanation.get('shap_value', 0)
            impact = explanation.get('impact', 'unknown')
            importance = explanation.get('importance', 0)
            
            clinical_name = _map_feature_to_clinical_term(feature)
            impact_emoji = "🔴" if impact == "increases" else "🟢"
            direction = "INCREASES" if impact == "increases" else "DECREASES"
            
            summary_lines.extend([
                f"{i}. {clinical_name}:",
                f"   • Patient Value: {value}",
                f"   • SHAP Score: {shap_value:.4f}",
                f"   • Impact: {impact_emoji} {direction} risk",
                f"   • Importance Ranking: {importance:.4f}",
                f"   • Clinical Significance: {_get_clinical_significance(feature, value, impact, importance)}",
                ""
            ])
    
    # Top factors section
    top_factors = shap_data.get('top_factors', [])
    if top_factors:
        summary_lines.extend([
            "⭐ TOP 3 MOST INFLUENTIAL FACTORS:",
            ""
        ])
        
        for i, factor in enumerate(top_factors[:3], 1):
            feature = factor.get('feature', 'Unknown')
            value = factor.get('value', 'N/A')
            importance = factor.get('importance', 0)
            impact = factor.get('impact', 'unknown')
            
            clinical_name = _map_feature_to_clinical_term(feature)
            impact_emoji = "🔴" if impact == "increases" else "🟢"
            
            summary_lines.extend([
                f"{i}. {clinical_name} {impact_emoji}",
                f"   Value: {value} | Importance: {importance:.4f} | Impact: {impact.upper()}",
                ""
            ])
    
    # Risk interpretation
    increasing_factors = [e for e in explanations if e.get('impact') == 'increases']
    decreasing_factors = [e for e in explanations if e.get('impact') == 'decreases']
    
    summary_lines.extend([
        "📈 RISK FACTOR SUMMARY:",
        f"   • Factors INCREASING risk: {len(increasing_factors)}",
        f"   • Factors DECREASING risk: {len(decreasing_factors)}",
        ""
    ])
    
    if increasing_factors:
        top_risk = max(increasing_factors, key=lambda x: x.get('importance', 0))
        summary_lines.append(f"   🚨 Highest Risk Factor: {_map_feature_to_clinical_term(top_risk.get('feature', ''))} (Importance: {top_risk.get('importance', 0):.3f})")
    
    if decreasing_factors:
        top_protective = max(decreasing_factors, key=lambda x: x.get('importance', 0))
        summary_lines.append(f"   🛡️ Strongest Protective Factor: {_map_feature_to_clinical_term(top_protective.get('feature', ''))} (Importance: {top_protective.get('importance', 0):.3f})")
    
    summary_lines.extend([
        "",
        "=" * 60,
        "NOTE: SHAP values quantify each feature's contribution to the final prediction.",
        "Higher absolute values indicate greater influence on the model's decision."
    ])
    
    return "\n".join(summary_lines)


def _get_clinical_significance(feature: str, value, impact: str, importance: float) -> str:
    """
    Provide clinical significance interpretation for SHAP findings.
    """
    feature = feature.lower()
    
    significance_map = {
        'age': f"Age-related risk factor with {'high' if importance > 0.5 else 'moderate'} influence",
        'ap_hi': f"Systolic BP of {value} {'significantly' if importance > 1.0 else 'moderately'} affects cardiovascular risk",
        'ap_lo': f"Diastolic BP of {value} has {'major' if importance > 0.5 else 'minor'} impact on risk",
        'cholesterol': f"Cholesterol level {value} is {'critically important' if importance > 0.5 else 'notable'} for risk assessment",
        'gluc': f"Glucose level {value} {'strongly' if importance > 0.5 else 'moderately'} influences diabetes risk",
        'bmi': f"BMI of {value} is {'highly significant' if importance > 0.7 else 'relevant'} for metabolic risk",
        'smoke': f"Smoking status {'critically' if importance > 0.3 else 'moderately'} impacts cardiovascular health",
        'active': f"Activity level {'substantially' if importance > 0.2 else 'somewhat'} affects overall risk profile"
    }
    
    return significance_map.get(feature, f"Feature shows {'high' if importance > 0.5 else 'moderate'} predictive importance")
