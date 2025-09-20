AI Doctor's Assistant
=====================

Project overview
----------------

Multi-agent, LLM-powered assistant for doctors built with LangGraph and Streamlit. It connects to backend services and an MCP client to fetch patient data and generate preliminary diagnostic reports.

Tech stack
---------

- Python
- LangGraph for orchestration
- Streamlit frontend
- Requests for HTTP connectors

Project structure
-----------------

- agents: Orchestrator, Intent, Diagnosis agents
- connectors: Backend API, LLM, MCP adapters
- tools: Reusable utilities (parameters reader, backend tool, MCP tool)
- config/parameters.txt: Model requirements
- frontend/app.py: Streamlit UI
- graph.py: LangGraph workflow
- state.py: GraphState definition

Setup
-----

1. Create a virtual environment and install dependencies:
   - pip install -r requirements.txt
2. Optional: set DA_LOG_LEVEL=DEBUG for verbose logs.

Run
---

1. Start the UI:
   - streamlit run doctor_assistant/frontend/app.py
2. Open the provided URL and pass a patient id in the query string, e.g.:
   - [http://localhost:8501/?patient_id=123](http://localhost:8501/?patient_id=123)

Notes
-----

- Intent and diagnosis currently call local HTTP LLM endpoints; update endpoints/models in agents as needed.
- Logs are written to doctor_assistant/logs/app.log with rotation.
