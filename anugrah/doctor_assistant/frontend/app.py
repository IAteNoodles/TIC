import os
import sys
import streamlit as st

# Ensure repository root (parent of package dir) is on sys.path so absolute imports work
_here = os.path.dirname(os.path.abspath(__file__))
_pkg_dir = os.path.abspath(os.path.join(_here, os.pardir))  # .../doctor_assistant
_repo_root = os.path.dirname(_pkg_dir)  # parent of package dir
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

# Absolute imports from the package with fallback to relative
try:
    from doctor_assistant.graph import app  # compiled LangGraph
    from doctor_assistant.logging_config import get_logger
except ModuleNotFoundError:
    from ..graph import app  # type: ignore
    from ..logging_config import get_logger  # type: ignore

logger = get_logger("frontend")

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

    # Call the LangGraph agent with the user's prompt and the patient_id
    inputs = {"query": prompt, "patient_id": patient_id}
    final_state = None

    with st.spinner("Thinking..."):
        try:
            for output in app.stream(inputs):
                # output is a dict of node_name -> state
                for key, value in output.items():
                    final_state = value
        except Exception as e:
            logger.exception("Graph execution failed")
            final_state = {"error_message": f"Internal error: {e}"}

    if final_state:
        if final_state.get("error_message"):
            assistant_response = final_state["error_message"]
        elif final_state.get("final_report"):
            assistant_response = final_state["final_report"]
        else:
            assistant_response = "I'm not sure how to help with that."
    else:
        assistant_response = "Something went wrong. Please try again."

    with st.chat_message("assistant"):
        st.markdown(assistant_response)
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
