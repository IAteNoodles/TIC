# Backend Integration Documentation

## Overview

The Doctor Assistant system now includes full integration with the backend database API to fetch real patient data. This document describes the implemented functionality and how to use it.

## Backend API Details

- **Base URL**: `http://192.168.1.228:8001`
- **Endpoint**: `/get_patient_complete_details`
- **Method**: GET
- **Parameter**: `patient_id` (query parameter)

### Example Request
```bash
curl -X 'GET' \
  'http://192.168.1.228:8001/get_patient_complete_details?patient_id=1' \
  -H 'accept: application/json'
```

### Example Response
```json
{
  "status": "success",
  "patients": [
    {
      "personal_details": {
        "patient_id": "1",
        "full_name": "John Doe",
        "gender": "Male",
        "dob": "1985-03-15",
        "entity_type": "person",
        "node_type": "Patient"
      },
      "lab_details": [
        {
          "age": "59",
          "bmi": "28.4",
          "blood_glucose_level": "295",
          "HbA1c_level": "8.4",
          "hypertension": "0",
          "heart_disease": "0",
          "smoking_history": "former"
        }
      ]
    }
  ],
  "count": 1
}
```

## Implementation Components

### 1. Backend Connector (`connectors/backend_connector.py`)

#### Functions:
- `get_patient_data_from_api(patient_id, timeout=30)` - Calls the real API
- `get_patient_data_mock(patient_id)` - Uses mock data for testing
- `get_patient_data(patient_id, use_mock=False, timeout=30)` - Main function that can use either real or mock data
- `extract_patient_info(api_response)` - Extracts and formats patient data for easier processing

#### Configuration:
```python
BACKEND_BASE_URL = "http://192.168.1.228:8001"
PATIENT_ENDPOINT = "/get_patient_complete_details"
```

### 2. Backend Tool (`tools/backend_tool.py`)

#### Functions:
- `get_patient_data_tool(patient_id, use_mock=False, include_raw=False)` - Main tool for agents to fetch patient data
- `get_patient_summary_tool(patient_id, use_mock=False)` - Generates formatted text summary for display or LLM consumption

### 3. Updated Agents

#### Diagnosis Agent (`agents/diagnosis_agent.py`)
- Updated to use `get_patient_data_tool()` with new response format
- Handles both `personal_info` and `medical_data` sections
- Improved error handling for API failures

#### Prediction Agent (`agents/prediction_agent.py`)
- Updated to use the new backend tool functions
- Uses `get_patient_summary_tool()` for better formatted data input to MCP models

## Usage Examples

### Basic Usage
```python
from tools.backend_tool import get_patient_data_tool, get_patient_summary_tool

# Fetch patient data (uses real API by default)
patient_data = get_patient_data_tool("1")
if patient_data.get("success"):
    print(f"Patient: {patient_data['personal_info']['name']}")
    print(f"BMI: {patient_data['medical_data']['bmi']}")

# Get formatted summary
summary = get_patient_summary_tool("1")
print(summary)
```

### Using Mock Data
```python
# For testing purposes, use mock data
mock_data = get_patient_data_tool("123", use_mock=True)
mock_summary = get_patient_summary_tool("123", use_mock=True)
```

### In Agents
```python
from tools.backend_tool import get_patient_data_tool

def some_agent_node(state):
    patient_id = state.get('patient_id')
    
    # Fetch patient data
    patient_data = get_patient_data_tool(patient_id)
    if not patient_data.get("success"):
        state['error_message'] = f"Failed to fetch patient data: {patient_data.get('error')}"
        return state
    
    # Use the structured data
    personal_info = patient_data["personal_info"]
    medical_data = patient_data["medical_data"]
    
    # Process the data...
    return state
```

## Data Structure

The `get_patient_data_tool()` returns a structured dictionary:

```python
{
    "success": True,
    "patient_id": "1",
    "personal_info": {
        "name": "John Doe",
        "gender": "Male",
        "age": "59",
        "date_of_birth": "1985-03-15",
        "entity_type": "person",
        "node_type": "Patient"
    },
    "medical_data": {
        # Diabetes-related fields
        "hypertension": 0,
        "heart_disease": 0,
        "smoking_history": "former",
        "bmi": 28.4,
        "HbA1c_level": 8.4,
        "blood_glucose_level": 295.0,
        
        # Cardiovascular-related fields
        "height": 172.0,
        "weight": 49.0,
        "ap_hi": 143,  # Systolic BP
        "ap_lo": 83,   # Diastolic BP
        "cholesterol": 1,
        "glucose": 1,
        "smoking": 0,
        "alcohol": 1,
        "physical_activity": 0
    },
    "raw_data": {...}  # Original API response
}
```

## Error Handling

The system handles various error scenarios:

1. **Connection Errors**: Network issues, server unavailable
2. **HTTP Errors**: 404, 500, etc.
3. **Validation Errors**: Invalid patient ID format (422)
4. **Patient Not Found**: Valid format but non-existent patient
5. **JSON Parse Errors**: Malformed responses
6. **Timeout Errors**: Requests taking too long

All errors are logged and return a structured error response:

```python
{
    "success": False,
    "error": "Error type",
    "details": "Detailed error message"
}
```

## Testing

### Run Backend Tests
```bash
python3 test_backend_connector.py
python3 test_integration.py
python3 tools/backend_tool.py
```

### Available Test Patients
- **Real API**: Patient ID `1` (John Doe, age 59)
- **Mock Data**: Patient ID `123` (John Doe, age 45)

## Configuration

### Environment Variables (Optional)
You can override the backend URL by setting environment variables:

```python
import os
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://192.168.1.228:8001")
```

### Timeout Configuration
Default timeout is 30 seconds, but can be adjusted:

```python
patient_data = get_patient_data_tool("1", timeout=60)  # 60 second timeout
```

## Logging

All backend operations are logged with appropriate levels:
- **INFO**: Successful operations, normal flow
- **WARNING**: Patient not found, validation issues
- **ERROR**: Connection errors, HTTP errors, unexpected failures

Log entries include:
- Timestamp
- Logger name (e.g., `connectors.backend`, `tools.backend`)
- Log level
- Detailed message with patient ID and operation context

## Future Enhancements

1. **Caching**: Add response caching to reduce API calls
2. **Authentication**: Add API key or token-based authentication
3. **Batch Operations**: Support fetching multiple patients
4. **Data Validation**: Add schema validation for API responses
5. **Retry Logic**: Implement automatic retry for transient failures