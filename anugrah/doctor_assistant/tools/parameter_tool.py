import os
import json
try:
    from doctor_assistant.logging_config import get_logger
except ImportError:
    from logging_config import get_logger

logger = get_logger("tools.parameters")

def get_model_parameters_tool() -> dict:
    """
    A tool for reading and parsing model parameters from the parameters.txt file.
    """
    logger.info("Reading model parameters")
    
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config', 'parameters.txt'))
    
    if not os.path.exists(config_path):
        logger.warning("Parameter file not found at %s", config_path)
        return {"error": "Parameter file not found."}
    
    try:
        with open(config_path, 'r') as f:
            params = json.load(f)
        return params
    except json.JSONDecodeError:
        logger.error("Could not decode JSON from %s", config_path)
        return {"error": "Parameter file is not valid JSON."}
    except Exception as e:
        logger.exception("Unexpected error reading parameter file")
        return {"error": "An unexpected error occurred while reading the parameter file."}

if __name__ == '__main__':
    # Example usage
    print("Fetching model parameters:")
    print(get_model_parameters_tool())
