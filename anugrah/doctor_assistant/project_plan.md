# Project Plan: AI Doctor's Assistant (Agent-Focused)

## Project Vision

To develop a multi-agent, LLM-powered chatbot system using LangGraph and Streamlit that assists doctors by interfacing with existing backend services and ML models to provide patient information and generate preliminary diagnostic reports.

## Core Technologies

- **Language:** Python
- **Agent Framework:** LangGraph
- **Frontend:** Streamlit
- **LLMs:**
  - **Gemma 3 (or similar general-purpose model):** Used by the Main, Intent, and Diagnosis agents for internal reasoning, routing, and data formatting.
  - **MedGemma (specialized medical model):** Called by the Diagnosis agent exclusively for generating the final medical report.
- **External Systems:** Pre-existing Backend API and MCP Client for ML model inference.

## Phase 0: Foundation & Setup (Estimated Time: 2 Days)

This phase is about creating a solid foundation for the project to ensure a clean and scalable architecture.

### Task 0.1: Project Scaffolding

- Initialize a Git repository for version control.
- Create the main project directory structure:

  ```
  /doctor_assistant
  |-- /agents           # All agent definitions
  |-- /connectors       # Adapters for external services (Backend, MCP)
  |-- /frontend         # Streamlit application
  |-- /tools            # Reusable internal tools for agents
  |-- /logs             # Directory for log files
  |-- /config           # Configuration files
  |   |-- parameters.txt # ML model parameters
  |-- main.py           # Main entry point to run the system
  |-- requirements.txt  # Python dependencies
  |-- README.md         # Project documentation
  ```

### Task 0.2: Environment Setup

- Set up a Python virtual environment.
- Install core dependencies: `langchain`, `langgraph`, `streamlit`, `requests`, etc.

### Task 0.3: Centralized Logging Configuration

- Implement a logging module that can be imported by all agents.
- Configure it to log the agent name, timestamp, log level, and message.
- Set up file rotation to manage log file sizes.

## Phase 1: Interfaces and Frontend Shell (Estimated Time: 3 Days)

Define the contracts with external systems and build the user-facing layer. This allows for independent development and testing of the agentic workflow.

### Task 1.1: Define and Mock the Backend API Interface

- Document the exact endpoints, request methods (GET/POST), and expected JSON request/response structures for the existing Backend API.
- Create a "mock" backend function or class within `/connectors` that returns realistic dummy patient data. This allows the agentic system to be developed and tested without a live connection to the actual backend.

### Task 1.2: Develop the Streamlit Frontend

- Create a standard chatbot interface using `st.chat_input` and `st.chat_message`.
- Implement session state to maintain conversation history.
- Connect the frontend to a placeholder function that will eventually trigger the agentic workflow.

## Phase 2: Agentic Core & Intent Analysis (Estimated Time: 5 Days)

This is where we build the brain of the operation using LangGraph.

### Task 2.1: Define Agent States and Graph

- Define the main `GraphState`. It should include fields like `query`, `patient_id`, `intent`, `db_response`, `final_report`, `error_message`, etc.
- Set up the main `StatefulGraph` workflow in LangGraph.

### Task 2.2: Implement the Main Agent (Orchestrator)

- Create the primary node in the graph for routing and orchestration.

### Task 2.3: Implement the Intent Analysis Agent

- Create a dedicated agent node to classify the user's intent as either `information_retrieval` or `diagnosis`.
- The agent's output will update the `intent` field in the `GraphState`.

### Task 2.4: Implement Conditional Routing

- Add a conditional edge to the LangGraph that routes the workflow based on the `intent`.

## Phase 3: "Information Retrieval" Workflow (Estimated Time: 3 Days)

Flesh out the simpler of the two main workflows.

### Task 3.1: Develop the Backend Connector Tool

- Create a tool within `/connectors/backend_connector.py`.
- This tool will be a Python function responsible for making the live API call to the backend. It will initially use the mock function from Phase 1.
- Wrap the tool's logic in a `try...except` block to catch API errors, network issues, or invalid patient IDs. Log errors using the central logger.

### Task 3.2: Implement the Information Retrieval Node

- Create a node that calls the Backend Connector Tool to get patient data.
- It then uses an LLM to transform the returned JSON data into a clear, human-readable summary.

### Task 3.3: End-to-End Integration

- Connect this workflow fully from the Streamlit UI to the agentic system and back.

## Phase 4: "Diagnosis" Workflow (Estimated Time: 8 Days)

This is the most complex phase, involving multiple external calls and state management.

### Task 4.1: Develop Model Parameter Tool

- Create a tool to read and parse the `parameters.txt` file.

### Task 4.2: Implement Data Sufficiency Check & Doctor Interaction Loop

- Implement logic for the Main Agent to fetch data via the Backend Connector and check if it meets the requirements from the `parameters.txt` file.
- If data is missing, create the interactive loop to ask the doctor for clarification.

### Task 4.3: Implement the Diagnosis Agent

- Create the stateful Diagnosis Agent node to receive validated patient data.

### Task 4.4: Develop a Modular MCP Client Adapter

- In `/connectors/mcp_connector.py`, create a wrapper function (the adapter) that handles all communication with the MCP Client.
- This function will take structured data from the Diagnosis Agent, format it exactly as the MCP Client expects, and make the call.
- This adapter will handle the response and any potential errors, isolating the rest of the system from the MCP Client's specific implementation.

### Task 4.5: Integrate with MedGemma for Report Generation

- The Diagnosis Agent will call the MedGemma LLM to generate the final report after getting a successful response via the MCP Client Adapter.

### Task 4.6: Complete the Diagnosis Loop

- The generated report is passed back to the Main Agent and displayed in the Streamlit UI.

## Phase 5: Testing, Refinement, & Deployment (Estimated Time: 5 Days)

### Task 5.1: Comprehensive Testing

- Write unit tests for individual tools and connectors.
- Perform end-to-end testing for all workflows.
- Switch from mock connectors to live connectors and perform integration testing.

### Task 5.2: Prompt Engineering & Refinement

- Review and refine all LLM prompts.

### Task 5.3: Documentation

- Update the `README.md` with setup instructions and an architecture overview.

### Task 5.4: Containerization (Optional but Recommended)

- Create a `Dockerfile` for easy deployment.

## Modular Design Principles

- **Agents as Nodes:** Each agent is a self-contained node in the LangGraph, communicating purely through the shared `GraphState`.
- **Connectors for External Services:** All communication with external systems (Backend API, MCP Client) is handled through dedicated connector modules. This isolates the core agent logic from the specific implementation details of external APIs, allowing them to be easily updated or replaced.
- **Tools as Functions:** Internal logic, like reading a config file, is abstracted into a reusable tool.
- **Configuration-Driven:** Details like model parameters (`parameters.txt`) are kept in external config files.
- **State Management:** LangGraph's state management is the single source of truth for the data flowing through the workflow.

## Error Handling & Logging Strategy

- **Centralized Logging:** A single, configured Python logging instance will be used across all modules.
- **Try-Except Blocks:** Every external call within the connectors will be wrapped in a `try...except` block.
- **Graceful Failure:** When an error is caught, it will be logged with a full traceback, and the `GraphState` will be updated with a user-friendly error message to be displayed on the UI.
