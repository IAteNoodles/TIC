import streamlit as st
import requests
import pandas as pd
from typing import Optional, Dict, Any

# Page Configuration
st.set_page_config(
    page_title="Patient Health Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #ff7f0e;
        border-bottom: 2px solid #ff7f0e;
        padding-bottom: 0.5rem;
        margin: 1rem 0;
    }
    .prediction-results {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #007bff;
    }
    .risk-high {
        border-left-color: #dc3545 !important;
        background-color: #fff5f5;
    }
    .risk-low {
        border-left-color: #28a745 !important;
        background-color: #f0fff4;
    }
    .factor-item {
        background-color: white;
        border-radius: 5px;
        padding: 0.5rem;
        margin: 0.25rem 0;
        border-left: 3px solid #17a2b8;
    }
</style>
""", unsafe_allow_html=True)

import json
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime
import time

# Configure page
st.set_page_config(
    page_title="Patient Health Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
BACKEND_API = "http://192.168.1.228:8001"
LLM_API = "http://192.168.1.65:1234/v1/chat/completions"
CARDIO_API = "http://localhost:5002/predict"
DIABETES_API = "http://localhost:5003/predict"

# Custom CSS for basic styling
st.markdown("""
<style>
            st.error("🔴 Diabetes API")   .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #ff7f0e;
        border-bottom: 2px solid #ff7f0e;
        padding-bottom: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    if 'patient_id' not in st.session_state:
        st.session_state.patient_id = ""
    if 'patient_data' not in st.session_state:
        st.session_state.patient_data = None
    if 'diagnostic_reports' not in st.session_state:
        st.session_state.diagnostic_reports = []
    if 'selected_report' not in st.session_state:
        st.session_state.selected_report = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'predictions' not in st.session_state:
        st.session_state.predictions = {}
    if 'report_loaded' not in st.session_state:
        st.session_state.report_loaded = False
    if 'report_error' not in st.session_state:
        st.session_state.report_error = None
    if 'current_loading_report' not in st.session_state:
        st.session_state.current_loading_report = None

# API Helper Functions
def make_api_request(url: str, method: str = "GET", data: Dict = None, timeout: int = 30) -> Dict[str, Any]:
    """Make API request with error handling"""
    try:
        if method == "GET":
            response = requests.get(url, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=timeout)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timed out"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.exceptions.HTTPError as e:
        return {"success": False, "error": f"HTTP Error: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def fetch_patient_data(patient_id: str) -> Optional[Dict]:
    """Fetch complete patient data"""
    url = f"{BACKEND_API}/get_patient_complete_details"
    if patient_id:
        url += f"?patient_id={patient_id}"
    
    result = make_api_request(url)
    if result["success"]:
        patients = result["data"].get("patients", [])
        if patients:
            # Find the specific patient or return the first one
            for patient in patients:
                personal = patient.get("personal_details", {})
                if str(personal.get("patient_id")) == str(patient_id):
                    return patient
            # If specific patient not found but we have patients, return first one
            return patients[0] if patients else None
    return None

def fetch_diagnostic_reports(patient_id: str) -> List[Dict]:
    """Fetch all diagnostic reports for a patient"""
    url = f"{BACKEND_API}/get_all_diagnostic_reports?patient_id={patient_id}"
    result = make_api_request(url)
    if result["success"]:
        return result["data"].get("report_ids", [])
    return []

def fetch_report_content(report_id: str) -> Optional[Dict]:
    """Fetch specific report content"""
    url = f"{BACKEND_API}/get_diagnostic_report?report_id={report_id}"
    result = make_api_request(url)
    
    # Debug logging
    if not result["success"]:
        print(f"ERROR fetching report {report_id}: {result.get('error', 'Unknown error')}")
        return None
    
    if result["success"] and result.get("data"):
        print(f"SUCCESS: Loaded report {report_id}")
        return result["data"]
    else:
        print(f"ERROR: No data returned for report {report_id}")
        return None

def chat_with_llm(message: str, context: str = "") -> str:
    """Chat with the LLM about reports"""
    system_prompt = f"""You are a helpful medical assistant. You help patients understand their diagnostic reports and health data. 
    Always provide clear, compassionate explanations while emphasizing that you cannot replace professional medical advice.
    
    Current report context: {context}"""
    
    payload = {
        "model": "medgemma-4b-it",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        "temperature": 0.7,
        "max_tokens": -1,
        "stream": False
    }
    
    result = make_api_request(LLM_API, method="POST", data=payload)
    if result["success"]:
        choices = result["data"].get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "Sorry, I couldn't process your request.")
    return "Sorry, I'm having trouble connecting to the chat service."

def call_cardio_prediction(data: Dict) -> Dict:
    """Call cardiovascular prediction API directly"""
    result = make_api_request(CARDIO_API, method="POST", data=data)
    return result

def call_diabetes_prediction(data: Dict) -> Dict:
    """Call diabetes prediction API directly"""
    result = make_api_request(DIABETES_API, method="POST", data=data)
    return result

# UI Functions
def render_patient_input():
    """Render patient ID input section"""
    st.markdown('<div class="section-header">🔍 Patient Information</div>', unsafe_allow_html=True)
    
    st.info("💡 Enter your Patient ID below to access your health dashboard, diagnostic reports, and AI-powered health insights.")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        patient_id = st.text_input(
            "Patient ID", 
            value=st.session_state.patient_id, 
            key="patient_id_input",
            placeholder="Enter your Patient ID (e.g., 1, 2, 3...)",
            help="This is the unique identifier assigned to you by your healthcare provider"
        )
    
    with col2:
        st.write("")  # Add spacing
        if st.button("🔄 Load Data", type="primary"):
            if patient_id:
                with st.spinner("🔍 Loading patient data..."):
                    st.session_state.patient_id = patient_id
                    st.session_state.patient_data = fetch_patient_data(patient_id)
                    st.session_state.diagnostic_reports = fetch_diagnostic_reports(patient_id)
                    if st.session_state.patient_data:
                        st.success(f"✅ Patient data loaded successfully!")
                    else:
                        st.error("❌ Patient not found or no data available.")
            else:
                st.error("⚠️ Please enter a patient ID.")

def render_patient_summary():
    """Render patient summary if data is loaded"""
    if st.session_state.patient_data:
        st.markdown('<div class="section-header">👤 Patient Summary</div>', unsafe_allow_html=True)
        
        personal = st.session_state.patient_data.get("personal_details", {})
        lab_details = st.session_state.patient_data.get("lab_details", [])
        
        # Patient Info
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Patient ID", personal.get("patient_id", "N/A"))
        
        with col2:
            st.metric("Patient Name", personal.get("full_name", personal.get("name", "N/A")))
        
        with col3:
            st.metric("Gender", personal.get("gender", "N/A"))
        
        with col4:
            st.metric("Date of Birth", personal.get("dob", "N/A"))
        
        # Health Metrics
        if lab_details:
            st.subheader("📊 Health Metrics")
            latest_lab = lab_details[0]  # Get the first (most recent) lab result
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                age = latest_lab.get("age", "N/A")
                st.metric("Age", f"{age} years" if age != "N/A" else "N/A")
            
            with col2:
                height = latest_lab.get("height", "N/A")
                st.metric("Height", f"{height} cm" if height != "N/A" else "N/A")
            
            with col3:
                weight = latest_lab.get("weight", "N/A")
                st.metric("Weight", f"{weight} kg" if weight != "N/A" else "N/A")
            
            with col4:
                # Calculate BMI
                try:
                    height_m = float(height) / 100
                    weight_kg = float(weight)
                    bmi = round(weight_kg / (height_m ** 2), 1)
                    st.metric("BMI", bmi)
                except:
                    st.metric("BMI", "N/A")
            
            # Key Health Indicators
            st.subheader("🩺 Key Health Indicators")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                bp = f"{latest_lab.get('ap_hi', 'N/A')}/{latest_lab.get('ap_lo', 'N/A')}"
                st.metric("Blood Pressure", bp)
            
            with col2:
                glucose = latest_lab.get("blood_glucose_level", "N/A")
                st.metric("Blood Glucose", f"{glucose} mg/dL" if glucose != "N/A" else "N/A")
            
            with col3:
                hba1c = latest_lab.get("HbA1c_level", "N/A")
                st.metric("HbA1c Level", f"{hba1c}%" if hba1c != "N/A" else "N/A")
            
            with col4:
                chol = latest_lab.get('cholesterol', 'N/A')
                st.metric("Cholesterol", f"Level {chol}" if chol != "N/A" else "N/A")

def render_diagnostic_reports():
    """Render diagnostic reports section"""
    if st.session_state.diagnostic_reports:
        st.markdown('<div class="section-header">📋 Diagnostic Reports</div>', unsafe_allow_html=True)
        
        st.write(f"Found **{len(st.session_state.diagnostic_reports)}** reports for this patient:")
        
        # Create buttons for each report
        for i, report_id in enumerate(st.session_state.diagnostic_reports):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**Report {i+1}:** {report_id}")
            with col2:
                if st.button(f"Load Report {i+1}", key=f"report_{i}"):
                    # Clear previous state
                    st.session_state.report_loaded = False
                    st.session_state.report_error = None
                    
                    with st.spinner(f"Loading report {report_id}..."):
                        # Debug: Show which report is being loaded
                        st.session_state.current_loading_report = report_id
                        
                        report_content = fetch_report_content(report_id)
                        if report_content:
                            st.session_state.selected_report = report_content
                            st.session_state.report_loaded = True
                            st.session_state.current_loading_report = None
                        else:
                            st.session_state.report_error = f"Failed to load report {report_id}"
                            st.session_state.current_loading_report = None
                    
                    st.rerun()
        
        # Show messages after rerun
        if hasattr(st.session_state, 'report_loaded') and st.session_state.report_loaded:
            st.success("✅ Report loaded successfully!")
            st.session_state.report_loaded = False
            
        if hasattr(st.session_state, 'report_error') and st.session_state.report_error:
            st.error(f"❌ {st.session_state.report_error}")
            st.session_state.report_error = None
            
        # Show debug info if loading
        if hasattr(st.session_state, 'current_loading_report') and st.session_state.current_loading_report:
            st.info(f"🔄 Currently loading: {st.session_state.current_loading_report}")
    else:
        st.info("No diagnostic reports found for this patient.")

def render_selected_report():
    """Render the selected report content"""
    if st.session_state.selected_report:
        st.markdown('<div class="section-header">📄 Selected Report</div>', unsafe_allow_html=True)
        
        report = st.session_state.selected_report
        
        # Debug info
        st.write(f"**Debug:** Report object type: {type(report)}")
        st.write(f"**Debug:** Report keys: {list(report.keys()) if isinstance(report, dict) else 'Not a dict'}")
        
        # Report metadata
        col1, col2, col3 = st.columns(3)
        
        with col1:
            report_id = report.get('report_id', 'N/A') if isinstance(report, dict) else 'N/A'
            st.metric("Report ID", report_id)
        
        with col2:
            patient_id = report.get('patient_id', 'N/A') if isinstance(report, dict) else 'N/A'
            st.metric("Patient ID", patient_id)
        
        with col3:
            created_at = report.get('created_at', 'N/A') if isinstance(report, dict) else 'N/A'
            if created_at != 'N/A':
                try:
                    # Try to format the date
                    from datetime import datetime
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    formatted_date = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    formatted_date = created_at
            else:
                formatted_date = 'N/A'
            st.metric("Created", formatted_date)
        
        # Report content
        st.subheader("📑 Report Content")
        if isinstance(report, dict):
            report_content = report.get('data', 'No content available')
        else:
            report_content = str(report)
        
        # Display in a text area for better readability
        st.text_area("Report Data", value=report_content, height=300, disabled=True, label_visibility="collapsed")

def render_chat_interface():
    """Render chat interface for discussing reports"""
    st.markdown('<div class="section-header">💬 Discuss Your Report with AI Assistant</div>', unsafe_allow_html=True)
    
    if not st.session_state.selected_report:
        st.info("🤖 Please select a diagnostic report first to start chatting with the AI assistant.")
        return
    
    # Chat history
    if st.session_state.chat_history:
        st.subheader("💭 Conversation History")
        for i, message in enumerate(st.session_state.chat_history):
            if message["role"] == "user":
                st.markdown(f"**👤 You:** {message['content']}")
            else:
                st.markdown(f"**🤖 AI Assistant:** {message['content']}")
            st.markdown("---")
    else:
        st.info("🤖 AI Assistant Ready! Ask me anything about your diagnostic report.")
    
    # Chat input
    st.subheader("✍️ Ask a Question")
    
    col1, col2 = st.columns([4, 1])
    with col1:
        # Use a unique key that changes to clear the input
        input_key = f"chat_input_{len(st.session_state.chat_history)}"
        user_message = st.text_input(
            "Type your question here...", 
            key=input_key, 
            placeholder="e.g., What do these test results mean?",
            label_visibility="collapsed"
        )
    with col2:
        send_button = st.button("Send 📤", type="primary")
    
    # Handle message sending
    if send_button and user_message:
        # Add user message to history
        st.session_state.chat_history.append({"role": "user", "content": user_message})
        
        # Get context from selected report
        context = st.session_state.selected_report.get('data', '')
        
        # Get response from LLM
        with st.spinner("🤔 AI is thinking..."):
            response = chat_with_llm(user_message, context)
        
        # Add assistant response to history
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        
        # Rerun to show new messages and clear input
        st.rerun()
    
    # Quick question buttons
    st.subheader("🔍 Quick Questions")
    col1, col2, col3 = st.columns(3)
    
    quick_questions = [
        "What are the key findings?",
        "Are there any concerning values?", 
        "What should I discuss with my doctor?"
    ]
    
    for i, question in enumerate(quick_questions):
        col = [col1, col2, col3][i]
        with col:
            if st.button(question, key=f"quick_{i}"):
                # Add question to chat
                st.session_state.chat_history.append({"role": "user", "content": question})
                
                # Get response
                context = st.session_state.selected_report.get('data', '')
                with st.spinner("🤔 AI is thinking..."):
                    response = chat_with_llm(question, context)
                
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.rerun()

def render_predictions():
    """Render health predictions section"""
    if st.session_state.patient_data:
        st.markdown('<div class="section-header">🔮 Health Predictions</div>', unsafe_allow_html=True)
        
        personal = st.session_state.patient_data.get("personal_details", {})
        lab_details = st.session_state.patient_data.get("lab_details", [])
        
        # Create tabs for different predictions
        cardio_tab, diabetes_tab = st.tabs(["Cardiovascular Risk", "Diabetes Risk"])
        
        with cardio_tab:
            render_cardio_prediction(personal, lab_details)
        
        with diabetes_tab:
            render_diabetes_prediction(personal, lab_details)

def render_cardio_prediction(personal: Dict, lab_details: List[Dict]):
    """Render cardiovascular prediction form"""
    st.subheader("Cardiovascular Risk Assessment")
    
    # Get the latest lab data for auto-filling
    latest_lab = lab_details[0] if lab_details else {}
    
    col1, col2 = st.columns(2)
    
    with col1:
        age = st.number_input("Age", value=int(latest_lab.get("age", 30)), min_value=1, max_value=120)
        gender_value = latest_lab.get("gender", personal.get("gender", "Male"))
        gender_index = 0 if gender_value in ["Male", "M", "1"] else 1
        gender = st.selectbox("Gender", ["Male", "Female"], index=gender_index)
        height = st.number_input("Height (cm)", value=int(latest_lab.get("height", 170)), min_value=100, max_value=250)
        weight = st.number_input("Weight (kg)", value=int(latest_lab.get("weight", 70)), min_value=30, max_value=300)
        
    with col2:
        ap_hi = st.number_input("Systolic BP (mmHg)", value=int(latest_lab.get("ap_hi", 120)), min_value=80, max_value=200)
        ap_lo = st.number_input("Diastolic BP (mmHg)", value=int(latest_lab.get("ap_lo", 80)), min_value=50, max_value=120)
        cholesterol = st.selectbox("Cholesterol Level", [1, 2, 3], index=int(latest_lab.get("cholesterol", 1))-1, format_func=lambda x: f"Level {x}")
        gluc = st.selectbox("Glucose Level", [1, 2, 3], index=int(latest_lab.get("gluc", 1))-1, format_func=lambda x: f"Level {x}")
        smoke = st.selectbox("Smoking", [0, 1], index=int(latest_lab.get("smoke", 0)), format_func=lambda x: "No" if x == 0 else "Yes")
        alco = st.selectbox("Alcohol", [0, 1], index=int(latest_lab.get("alco", 0)), format_func=lambda x: "No" if x == 0 else "Yes")
        active = st.selectbox("Physical Activity", [0, 1], index=int(latest_lab.get("active", 0)), format_func=lambda x: "No" if x == 0 else "Yes")
    
    if st.button("Predict Cardiovascular Risk", type="primary"):
        with st.spinner("Calculating risk..."):
            payload = {
                "age": int(age),
                "gender": 1 if gender == "Male" else 0,
                "height": int(height),
                "weight": int(weight),
                "ap_hi": int(ap_hi),
                "ap_lo": int(ap_lo),
                "cholesterol": int(cholesterol),
                "gluc": int(gluc),
                "smoke": int(smoke),
                "alco": int(alco),
                "active": int(active)
            }
            
            result = call_cardio_prediction(payload)
            if result["success"]:
                prediction_data = result["data"]
                st.session_state.predictions["cardio"] = prediction_data
                display_prediction_result("Cardiovascular Risk", prediction_data)
            else:
                st.error(f"Prediction failed: {result.get('error', 'Unknown error')}")

def render_diabetes_prediction(personal: Dict, lab_details: List[Dict]):
    """Render diabetes prediction form"""
    st.subheader("Diabetes Risk Assessment")
    
    # Get the latest lab data for auto-filling
    latest_lab = lab_details[0] if lab_details else {}
    
    col1, col2 = st.columns(2)
    
    with col1:
        age = st.number_input("Age", value=int(latest_lab.get("age", 30)), min_value=1, max_value=120, key="diabetes_age")
        gender_value = latest_lab.get("gender", personal.get("gender", "Male"))
        gender_options = ["Male", "Female", "Other"]
        gender_index = 0 if gender_value in ["Male", "M"] else (1 if gender_value in ["Female", "F"] else 2)
        gender = st.selectbox("Gender", gender_options, index=gender_index, key="diabetes_gender")
        hypertension = st.selectbox("Hypertension", [0, 1], index=int(latest_lab.get("hypertension", 0)), format_func=lambda x: "No" if x == 0 else "Yes", key="diabetes_hypertension")
        heart_disease = st.selectbox("Heart Disease", [0, 1], index=int(latest_lab.get("heart_disease", 0)), format_func=lambda x: "No" if x == 0 else "Yes", key="diabetes_heart")
        
    with col2:
        smoking_options = ["never", "current", "former", "ever", "not current"]
        smoking_default = latest_lab.get("smoking_history", "never")
        smoking_index = smoking_options.index(smoking_default) if smoking_default in smoking_options else 0
        smoking_history = st.selectbox("Smoking History", smoking_options, index=smoking_index, key="diabetes_smoking")
        
        # Calculate BMI if height and weight available, otherwise use stored BMI
        try:
            if latest_lab.get("bmi"):
                default_bmi = float(latest_lab.get("bmi"))
            elif latest_lab.get("height") and latest_lab.get("weight"):
                height_val = float(latest_lab.get("height"))
                weight_val = float(latest_lab.get("weight"))
                default_bmi = round(weight_val / (height_val/100)**2, 1)
            else:
                default_bmi = 25.0
        except:
            default_bmi = 25.0
            
        bmi = st.number_input("BMI", value=default_bmi, min_value=10.0, max_value=50.0, key="diabetes_bmi")
        hba1c = st.number_input("HbA1c Level (%)", value=float(latest_lab.get("HbA1c_level", 5.5)), min_value=3.0, max_value=15.0, key="diabetes_hba1c")
        glucose = st.number_input("Blood Glucose (mg/dL)", value=float(latest_lab.get("blood_glucose_level", 100)), min_value=50.0, max_value=400.0, key="diabetes_glucose")
    
    if st.button("Predict Diabetes Risk", type="primary"):
        with st.spinner("Calculating risk..."):
            payload = {
                "age": float(age),
                "gender": gender,
                "hypertension": int(hypertension),
                "heart_disease": int(heart_disease),
                "smoking_history": smoking_history,
                "bmi": float(bmi),
                "HbA1c_level": float(hba1c),
                "blood_glucose_level": float(glucose)
            }
            
            result = call_diabetes_prediction(payload)
            if result["success"]:
                prediction_data = result["data"]
                st.session_state.predictions["diabetes"] = prediction_data
                display_prediction_result("Diabetes Risk", prediction_data)
            else:
                st.error(f"Prediction failed: {result.get('error', 'Unknown error')}")

def parse_json_string(json_string: str) -> Optional[Any]:
    """Safely parse a JSON string that might be nested or malformed."""
    if not isinstance(json_string, str):
        return json_string
    
    try:
        # First, try standard JSON parsing
        return json.loads(json_string)
    except json.JSONDecodeError:
        try:
            # If that fails, try ast.literal_eval for Python literal structures
            import ast
            return ast.literal_eval(json_string)
        except (ValueError, SyntaxError, MemoryError, TypeError):
            # Return None if all parsing fails
            return None

def display_prediction_result(title: str, data: Dict):
    """Display prediction results in a nice format"""
    
    # Debug section - can be removed in production
    with st.expander("🔧 Debug: Raw Prediction Data"):
        st.write("**Data structure:**")
        st.json(data)
    
    # Determine risk level and styling
    prediction = data.get("prediction")
    risk_class = "risk-high" if isinstance(prediction, (int, float)) and prediction > 0.5 else "risk-low"
    
    # Create styled container
    st.markdown(f'<div class="prediction-results {risk_class}">', unsafe_allow_html=True)
    st.markdown(f"## 🔬 {title} Results")
    
    # Display prediction
    if prediction is not None:
        if isinstance(prediction, (int, float)):
            risk_level = "High Risk" if prediction > 0.5 else "Low Risk"
            risk_color = "🔴" if prediction > 0.5 else "🟢"
            st.markdown(f"### {risk_color} **Prediction:** {risk_level} (Score: {prediction:.3f})")
        else:
            st.markdown(f"### **Prediction:** {prediction}")
    
    # Styling function for dataframes
    def highlight_impact(row):
        if row['Impact on Risk'] == 'increases':
            return ['background-color: #660000'] * len(row)
        elif row['Impact on Risk'] == 'decreases':
            return ['background-color: #004d00'] * len(row)
        return [''] * len(row)

    # Parse and display explanations
    explanations_data = data.get("explanations")
    if explanations_data:
        # Handle nested structure
        if isinstance(explanations_data, dict):
            explanations_list = explanations_data.get("explanations")
            top_factors_list = explanations_data.get("top_factors")
            summary_text = explanations_data.get("summary")
        else:
            # Fallback for older format
            explanations_list = explanations_data
            top_factors_list = data.get("top_factors")
            summary_text = data.get("summary")

        # Display explanations in a table
        if explanations_list:
            st.markdown("### 📊 **Key Contributing Factors:**")
            explanations = parse_json_string(explanations_list)
            
            if isinstance(explanations, list) and explanations:
                df_explanations = pd.DataFrame(explanations)
                df_explanations['feature'] = df_explanations['feature'].apply(format_feature_name)
                
                # Select and rename columns for display
                display_cols = {
                    'feature': 'Factor',
                    'value': 'Value',
                    'impact': 'Impact on Risk',
                    'importance': 'Importance'
                }
                df_display = df_explanations[display_cols.keys()].rename(columns=display_cols)
                
                st.dataframe(df_display.style.apply(highlight_impact, axis=1), use_container_width=True)
            elif explanations:
                st.text(str(explanations))

        # Display top factors in a table
        if top_factors_list:
            st.markdown("### 🎯 **Top Risk Factors:**")
            top_factors = parse_json_string(top_factors_list)
            
            if isinstance(top_factors, list) and top_factors:
                df_top_factors = pd.DataFrame(top_factors)
                df_top_factors['feature'] = df_top_factors['feature'].apply(format_feature_name)
                
                # Select and rename columns for display
                display_cols = {
                    'feature': 'Factor',
                    'value': 'Value',
                    'impact': 'Impact on Risk'
                }
                df_display = df_top_factors[display_cols.keys()].rename(columns=display_cols)
                
                st.dataframe(df_display.style.apply(highlight_impact, axis=1), use_container_width=True)
            elif top_factors:
                st.text(str(top_factors))
    
        # Display summary
        if summary_text:
            st.markdown("### 📝 **Summary:**")
            st.info(summary_text)
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("---")

def format_feature_name(feature: str) -> str:
    """Format feature names to be more user-friendly"""
    feature_display = feature.replace('_', ' ').title()
    
    # Special cases for better readability
    if feature == 'HbA1c_level':
        return 'HbA1c Level'
    elif feature == 'blood_glucose_level':
        return 'Blood Glucose Level'
    elif feature == 'gender_encoded':
        return 'Gender'
    elif feature == 'smoking_encoded':
        return 'Smoking History'
    elif feature == 'bmi':
        return 'BMI'
    
    return feature_display

# Main App
def main():
    init_session_state()
    
    st.markdown('<div class="main-header">🏥 Patient Health Dashboard</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Debug section (remove in production)
    with st.expander("🔧 Debug Info"):
        st.write("**Session State Debug:**")
        st.write(f"Patient ID: {st.session_state.patient_id}")
        st.write(f"Reports count: {len(st.session_state.diagnostic_reports)}")
        st.write(f"Selected report: {st.session_state.selected_report is not None}")
        st.write(f"Report loaded flag: {getattr(st.session_state, 'report_loaded', 'N/A')}")
        st.write(f"Report error: {getattr(st.session_state, 'report_error', 'N/A')}")
        st.write(f"Current loading: {getattr(st.session_state, 'current_loading_report', 'N/A')}")
        
        if st.session_state.diagnostic_reports:
            st.write("**Available Reports:**")
            for i, rep_id in enumerate(st.session_state.diagnostic_reports):
                st.write(f"  {i+1}: {rep_id}")
    
    # Sidebar for navigation
    with st.sidebar:
        st.header("Navigation")
        page = st.selectbox("Select Section:", [
            "Patient Info", 
            "Diagnostic Reports", 
            "Chat Assistant", 
            "Health Predictions"
        ])
    
    # Main content based on selected page
    if page == "Patient Info":
        render_patient_input()
        render_patient_summary()
    
    elif page == "Diagnostic Reports":
        if st.session_state.patient_data:
            render_diagnostic_reports()
            render_selected_report()
        else:
            st.info("Please load patient data first from the 'Patient Info' section.")
    
    elif page == "Chat Assistant":
        if st.session_state.selected_report:
            render_chat_interface()
        else:
            st.info("Please select a diagnostic report first to start chatting.")
    
    elif page == "Health Predictions":
        if st.session_state.patient_data:
            render_predictions()
        else:
            st.info("Please load patient data first from the 'Patient Info' section.")
    
    # Display API status in sidebar
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🔌 System Status")
        
        # Check backend API
        backend_status = make_api_request(f"{BACKEND_API}/health")
        if backend_status["success"]:
            st.success("🟢 Backend API")
        else:
            st.error("🔴 Backend API")
        
        # Check Cardio API
        cardio_status = make_api_request(CARDIO_API.replace("/predict", "/health"))
        if cardio_status["success"]:
            st.success("🟢 Cardio API")
        else:
            st.error("🔴 Cardio API")
            
        # Check Diabetes API
        diabetes_status = make_api_request(DIABETES_API.replace("/predict", "/health"))
        if diabetes_status["success"]:
            st.success("🟢 Diabetes API")
        else:
            st.markdown('� **Diabetes API** - Unavailable')
        
        # LLM API status (manual check)
        st.info("🟡 LLM API")
        
        st.markdown("---")
        st.markdown("### ℹ️ Quick Help")
        st.markdown("""
        **Getting Started:**
        1. Enter your Patient ID
        2. Load patient data
        3. View diagnostic reports
        4. Chat with AI assistant
        5. Get health predictions
        
        **Need Help?**
        Contact your healthcare provider for medical questions.
        """)

if __name__ == "__main__":
    main()