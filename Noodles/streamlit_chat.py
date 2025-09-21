import os
import json
import time
from typing import List, Dict, Any

import streamlit as st
import requests

API_URL = os.getenv("CHAT_API_URL", "http://127.0.0.1:8088/chat")

st.set_page_config(page_title="CDSX Chatbot", page_icon="💬", layout="centered")

# Sidebar configuration
with st.sidebar:
    st.title("CDSX Chatbot")
    st.caption("FastAPI + MCP tools")
    api_url = st.text_input("API URL", value=API_URL)
    chat_type = st.selectbox("Preferred provider", ["gemini", "groq", "ollama"], index=0)
    clear = st.button("Clear Conversation")

# Initialize session state
if "messages" not in st.session_state or clear:
    st.session_state.messages: List[Dict[str, Any]] = []

# Chat history display
for m in st.session_state.messages:
    with st.chat_message(m.get("role", "assistant")):
        st.markdown(m.get("content", ""))

# Input box
if prompt := st.chat_input("Type your message..."):
    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call API
    with st.chat_message("assistant"):
        placeholder = st.empty()
        status = st.status("Contacting API…", expanded=False)
        try:
            payload = {"message": prompt, "chat_type": chat_type}
            resp = requests.post(api_url, json=payload, timeout=120)
            if resp.status_code != 200:
                status.update(label=f"API error: {resp.status_code}", state="error")
                st.error(resp.text)
            else:
                data = resp.json()
                if not data.get("ok"):
                    status.update(label="All providers failed", state="error")
                    st.error(data.get("error") or "Unknown error")
                else:
                    # Show retries and provider
                    retries = data.get("retries", {})
                    tool_calls = data.get("tool_calls", [])
                    provider = data.get("model")

                    status.update(label=f"Provider: {provider} | Retries: {json.dumps(retries)}", state="complete")

                    # Render tool calls if any
                    if tool_calls:
                        with st.expander("Tool calls", expanded=False):
                            for i, t in enumerate(tool_calls, start=1):
                                st.write(f"{i}. {t.get('name')}({json.dumps(t.get('arguments'))})")
                                if t.get("result"):
                                    st.code(t["result"], language="json")

                    answer = data.get("answer", "")
                    placeholder.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
        except requests.RequestException as e:
            status.update(label="Network error", state="error")
            st.error(str(e))
