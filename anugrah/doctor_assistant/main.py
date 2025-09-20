import streamlit as st
from graph import app # Import the compiled graph

# Set the title for the Streamlit app
st.title("AI Doctor's Assistant")

# Get patient_id from URL query parameters
patient_id = st.query_params.get("patient_id")

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
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call the LangGraph agent with the user's prompt and the patient_id
    inputs = {"query": prompt, "patient_id": patient_id}
    final_state = None
    # The `stream` method returns an iterator of all states the graph has passed through
    with st.spinner("Thinking..."):
        for output in app.stream(inputs):
            for key, value in output.items():
                # The last state in the stream is the final state
                final_state = value

    # Determine the response from the final state
    if final_state:
        if final_state.get("error_message"):
            assistant_response = final_state["error_message"]
        elif final_state.get("final_report"):
            assistant_response = final_state["final_report"]
        else:
            assistant_response = "I'm not sure how to help with that."
    else:
        assistant_response = "Something went wrong. Please try again."


    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(assistant_response)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
