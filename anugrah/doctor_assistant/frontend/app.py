import os
import sys
import streamlit as st
import time
from typing import Dict, Any

# Ensure repository root (parent of package dir) is on sys.path so absolute imports work
_here = os.path.dirname(os.path.abspath(__file__))
_pkg_dir = os.path.abspath(os.path.join(_here, os.pardir))  # .../doctor_assistant
_repo_root = os.path.dirname(_pkg_dir)  # parent of package dir
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

# Absolute imports from the package with fallback to relative
try:
    from doctor_assistant.graph import app, stream_diagnosis_workflow  # compiled LangGraph
    from doctor_assistant.logging_config import get_logger
    from doctor_assistant.state import GraphState
except ModuleNotFoundError:
    from ..graph import app, stream_diagnosis_workflow  # type: ignore
    from ..logging_config import get_logger  # type: ignore
    from ..state import GraphState  # type: ignore

logger = get_logger("frontend")

def _generate_status_display(node_name: str, state: Dict[str, Any], step: int) -> str:
    """Generate HTML for real-time status display."""
    node_descriptions = {
        "main_agent": "🧠 Main Agent - Orchestrating the workflow",
        "intent_agent": "🎯 Intent Agent - Understanding your request",
        "information_retrieval": "📊 Information Retrieval - Fetching patient data",
        "diagnosis": "🩺 Diagnosis Agent - Analyzing medical data"
    }
    
    description = node_descriptions.get(node_name, f"⚙️ {node_name.replace('_', ' ').title()}")
    
    # Create progress indicator
    progress_html = f"""
    <div style="
        background-color: #f0f2f6; 
        padding: 10px; 
        border-radius: 10px; 
        border-left: 4px solid #1f77b4;
        margin: 5px 0;
    ">
        <div style="display: flex; align-items: center;">
            <div style="margin-right: 10px;">
                <span style="
                    background-color: #1f77b4; 
                    color: white; 
                    padding: 2px 8px; 
                    border-radius: 50%; 
                    font-size: 12px;
                ">{step}</span>
            </div>
            <div>
                <strong>{description}</strong>
                <div style="color: #28a745; font-size: 12px;">✅ Completed</div>
            </div>
        </div>
    </div>
    """
    
    return progress_html

def _get_info_retrieval_insight(state: Dict[str, Any]) -> str:
    """Generate insights for information retrieval node."""
    db_response = state.get('db_response', {})
    
    if db_response.get('success'):
        patient_info = db_response.get('personal_info', {})
        medical_data = db_response.get('medical_data', {})
        return f"Successfully retrieved data for **{patient_info.get('name', 'Unknown')}** (Age: {patient_info.get('age', 'Unknown')}). Found medical data including BMI: {medical_data.get('bmi', 'N/A')}, BP: {medical_data.get('ap_hi', 'N/A')}/{medical_data.get('ap_lo', 'N/A')}."
    elif 'error' in db_response:
        return f"Encountered an issue: {db_response.get('error', 'Unknown error')}"
    else:
        return "Fetching patient data from the database..."

def _get_diagnosis_insight(state: Dict[str, Any]) -> str:
    """Generate insights for diagnosis node."""
    if state.get('error_message'):
        return f"Diagnosis process encountered an issue: {state.get('error_message')}"
    elif state.get('final_report'):
        report_preview = state.get('final_report', '')[:100]
        return f"Generated diagnostic analysis. Report preview: '{report_preview}...'"
    else:
        return "Analyzing patient data and generating diagnostic insights..."

def _generate_insights(node_name: str, state: Dict[str, Any]) -> str:
    """Generate insights based on the current node and state."""
    insights = {
        "main_agent": "Starting the workflow and preparing to analyze your request.",
        "intent_agent": f"Determined intent: **{state.get('intent', 'unknown')}** - Routing to appropriate handler.",
        "information_retrieval": _get_info_retrieval_insight(state),
        "diagnosis": _get_diagnosis_insight(state)
    }
    
    return insights.get(node_name, "")

def _stream_response_real_time(query: str, patient_id: str) -> None:
    """
    Stream the response in real-time as the AI model generates it.
    """
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # Use the streaming diagnosis function
            for chunk in stream_diagnosis_workflow(query, patient_id):
                if chunk.startswith('[STATUS]'):
                    # Display status updates
                    status_msg = chunk.replace('[STATUS]', '').strip()
                    temp_response = full_response + f"\n\n*{status_msg}*"
                    message_placeholder.markdown(temp_response)
                    time.sleep(0.5)  # Brief pause for status updates
                elif chunk.startswith('[ERROR]'):
                    # Display error messages
                    error_msg = chunk.replace('[ERROR]', '').strip()
                    full_response += f"\n\n❌ **Error**: {error_msg}"
                    message_placeholder.markdown(full_response)
                    break
                else:
                    # Regular content - stream character by character for dramatic effect
                    for char in chunk:
                        full_response += char
                        message_placeholder.markdown(full_response + "▋")  # Add cursor
                        time.sleep(0.01)  # Small delay for typing effect
            
            # Remove cursor from final display
            message_placeholder.markdown(full_response)
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            error_response = f"❌ **Error**: An error occurred during streaming: {str(e)}"
            message_placeholder.markdown(error_response)
            full_response = error_response
        
        # Add to chat history
        st.session_state.messages.append({"role": "assistant", "content": full_response})

def _stream_response(response_text: str) -> None:
    """
    Stream the response text character by character to create a typing effect.
    (Legacy function for non-streaming workflows)
    """
    with st.chat_message("assistant"):
        # Create a placeholder for the streaming text
        message_placeholder = st.empty()
        full_response = ""
        
        # Add a thinking indicator first
        message_placeholder.markdown("🤔 Generating response...")
        time.sleep(0.5)
        
        # Stream the response
        for i, char in enumerate(response_text):
            full_response += char
            
            # Update every few characters for better performance
            if i % 3 == 0 or char in ['.', '!', '?', '\n', ':']:
                # Add a cursor effect
                cursor_response = full_response + "▋"
                message_placeholder.markdown(cursor_response)
                
                # Variable delay based on character type
                if char in ['.', '!', '?']:
                    time.sleep(0.3)  # Longer pause for sentence endings
                elif char in [',', ';', ':']:
                    time.sleep(0.15)  # Medium pause for punctuation
                elif char == '\n':
                    time.sleep(0.2)  # Pause for line breaks
                else:
                    time.sleep(0.02)  # Normal typing speed
        
        # Final update without cursor
        message_placeholder.markdown(full_response)
        
        # Add to chat history
        st.session_state.messages.append({"role": "assistant", "content": full_response})

def _stream_response_with_sections(response_text: str) -> None:
    """
    Enhanced streaming that highlights different sections as they appear.
    """
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # Split response into logical sections
        sections = _parse_response_sections(response_text)
        full_response = ""
        
        for section_title, section_content in sections:
            # Show section header with highlight
            if section_title:
                section_header = f"\n\n**🔍 {section_title}**\n"
                full_response += section_header
                message_placeholder.markdown(full_response + "▋")
                time.sleep(0.5)
            
            # Stream section content
            for i, char in enumerate(section_content):
                full_response += char
                
                # Update display periodically
                if i % 5 == 0 or char in ['.', '!', '?', '\n']:
                    cursor_response = full_response + "▋"
                    message_placeholder.markdown(cursor_response)
                    
                    # Dynamic timing
                    if char in ['.', '!', '?']:
                        time.sleep(0.4)
                    elif char == '\n':
                        time.sleep(0.1)
                    else:
                        time.sleep(0.03)
        
        # Final display without cursor
        message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})

def _parse_response_sections(response_text: str) -> list:
    """
    Parse response into logical sections for enhanced streaming.
    """
    sections = []
    lines = response_text.split('\n')
    current_section = ""
    current_title = None
    
    for line in lines:
        line = line.strip()
        
        # Detect section headers (lines with specific patterns)
        if any(keyword in line.upper() for keyword in ['SUMMARY', 'FINDINGS', 'RECOMMENDATIONS', 'DIAGNOSIS', 'ASSESSMENT', 'ANALYSIS']):
            # Save previous section
            if current_section.strip():
                sections.append((current_title, current_section))
            
            # Start new section
            current_title = line.replace('*', '').replace('#', '').strip()
            current_section = ""
        else:
            current_section += line + "\n"
    
    # Add the last section
    if current_section.strip():
        sections.append((current_title, current_section))
    
    return sections

st.set_page_config(page_title="AI Doctor's Assistant", page_icon="🩺")
st.title("AI Doctor's Assistant")

# Get patient_id from URL query parameters (support both new and legacy APIs)
patient_id = None
try:
    # Streamlit >= 1.37 provides st.query_params (dict-like)
    qp = getattr(st, "query_params", None)
    if qp is not None:
        patient_id = qp.get("patient_id")
    else:
        raise AttributeError
except AttributeError:
    # Older versions
    try:
        q_old = st.experimental_get_query_params()
        patient_id = q_old.get("patient_id", [None])
    except Exception:
        patient_id = None

# Normalize patient_id to a simple string
if isinstance(patient_id, list):
    patient_id = patient_id[0] if patient_id else None

if not patient_id:
    st.warning("Please provide a patient_id in the URL, e.g., `?patient_id=123`")
    st.stop()

st.info(f"Viewing assistant for Patient ID: {patient_id}")

# Initialize chat history in session state if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("How can I help you today?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Use real-time streaming for all requests
    _stream_response_real_time(prompt, patient_id)


