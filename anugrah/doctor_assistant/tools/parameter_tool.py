import os
import json

def get_model_parameters_tool() -> dict:
    """
    A tool for reading and parsing model parameters from the parameters.txt file.
    """
    print("---PARAMETER TOOL: Reading model parameters---")
    
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'parameters.txt')
    
    if not os.path.exists(config_path):
        print(f"Warning: {config_path} not found.")
        return {"error": "Parameter file not found."}
    
    try:
        with open(config_path, 'r') as f:
            params = json.load(f)
        return params
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {config_path}")
        return {"error": "Parameter file is not valid JSON."}
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {"error": "An unexpected error occurred while reading the parameter file."}

if __name__ == '__main__':
    # Example usage
    print("Fetching model parameters:")
    print(get_model_parameters_tool())
