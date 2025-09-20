import requests
import json

def call_llm(model_name: str, endpoint: str, system_prompt: str, user_prompt: str) -> dict:
    """
    Calls a large language model endpoint.

    Args:
        model_name: The name of the model to use (e.g., "google/gemma-3-4b").
        endpoint: The URL of the model's API endpoint.
        system_prompt: The system message to set the context for the model.
        user_prompt: The user's message to the model.

    Returns:
        A dictionary containing the model's response or an error.
    """
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": -1,
        "stream": False
    }

    try:
        response = requests.post(endpoint, headers=headers, data=json.dumps(data))
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling LLM at {endpoint}: {e}")
        return {"error": f"Failed to connect to the language model at {endpoint}."}

if __name__ == '__main__':
    # Example usage for Gemma 3
    gemma_endpoint = "http://192.168.1.54:1234/v1/chat/completions"
    gemma_model = "google/gemma-3-4b"
    gemma_system = "You are a helpful assistant."
    gemma_user = "What is the capital of France?"
    
    print("--- Calling Gemma 3 ---")
    response = call_llm(gemma_model, gemma_endpoint, gemma_system, gemma_user)
    if "choices" in response:
        print(response['choices'][0]['message']['content'])
    else:
        print(response)

    # Example usage for MedGemma
    medgemma_endpoint = "http://192.168.1.228:1234/v1/chat/completions"
    medgemma_model = "medgemma-4b-it"
    medgemma_system = "You are a medical expert."
    medgemma_user = "What are the common symptoms of a cold?"

    print("\n--- Calling MedGemma ---")
    response = call_llm(medgemma_model, medgemma_endpoint, medgemma_system, medgemma_user)
    if "choices" in response:
        print(response['choices'][0]['message']['content'])
    else:
        print(response)
