import requests
import json

def call_mcp_model(prompt: str) -> dict:
    """
    Calls the MCP model endpoint to get a prediction.

    Args:
        prompt: The input prompt for the model.

    Returns:
        A dictionary containing the model's response.
    """
    url = "http://192.168.1.228:8088/chat"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    data = {
        "message": prompt,
        "chat_type": "ollama"
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling MCP model: {e}")
        return {"error": str(e)}

if __name__ == '__main__':
    # Example usage
    test_prompt = "Based on the following data, predict the likelihood of cardiovascular disease: age: 55, gender: 2, height: 170, weight: 85, ap_hi: 140, ap_lo: 90, cholesterol: 2, gluc: 1, smoke: 0, alco: 1, active: 1"
    prediction = call_mcp_model(test_prompt)
    print(json.dumps(prediction, indent=2))
