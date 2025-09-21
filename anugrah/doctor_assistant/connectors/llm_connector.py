import requests
import json
from logging_config import get_logger
from typing import Iterator, Dict, Any

logger = get_logger("connectors.llm")

def call_llm(model_name: str, endpoint: str, system_prompt: str, user_prompt: str, timeout: int = 30) -> dict:
    """
    Calls a large language model endpoint (non-streaming).

    Args:
        model_name: The name of the model to use (e.g., "google/gemma-3-4b").
        endpoint: The URL of the model's API endpoint.
        system_prompt: The system message to set the context for the model.
        user_prompt: The user's message to the model.
        timeout: Timeout in seconds for the request (default: 30).

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
        response = requests.post(endpoint, headers=headers, data=json.dumps(data), timeout=timeout)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error("Error calling LLM at %s: %s", endpoint, e)
        return {"error": f"Failed to connect to the language model at {endpoint}."}

def call_llm_streaming(model_name: str, endpoint: str, system_prompt: str, user_prompt: str, timeout: int = 120) -> Iterator[str]:
    """
    Calls a large language model endpoint with streaming support.

    Args:
        model_name: The name of the model to use (e.g., "google/gemma-3-4b").
        endpoint: The URL of the model's API endpoint.
        system_prompt: The system message to set the context for the model.
        user_prompt: The user's message to the model.
        timeout: Timeout in seconds for the request (default: 120).

    Yields:
        String chunks from the streaming response.
    """
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    data = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": -1,
        "stream": True
    }

    try:
        logger.info(f"Starting streaming request to {endpoint}")
        response = requests.post(
            endpoint, 
            headers=headers, 
            data=json.dumps(data), 
            timeout=timeout,
            stream=True
        )
        response.raise_for_status()
        
        # Process the streaming response
        for line in response.iter_lines(decode_unicode=True):
            if line:
                # Handle Server-Sent Events format
                if line.startswith('data: '):
                    data_str = line[6:]  # Remove 'data: ' prefix
                    
                    if data_str.strip() == '[DONE]':
                        logger.info("Streaming completed")
                        break
                    
                    try:
                        chunk_data = json.loads(data_str)
                        
                        # Extract content from the response
                        if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                            choice = chunk_data['choices'][0]
                            
                            if 'delta' in choice and 'content' in choice['delta']:
                                content = choice['delta']['content']
                                if content:
                                    yield content
                            elif 'message' in choice and 'content' in choice['message']:
                                content = choice['message']['content']
                                if content:
                                    yield content
                    except json.JSONDecodeError:
                        # Skip malformed JSON lines
                        continue
                        
    except requests.exceptions.RequestException as e:
        logger.error("Error in streaming LLM call to %s: %s", endpoint, e)
        yield f"[ERROR: Failed to connect to the language model]"
    except Exception as e:
        logger.error("Unexpected error in streaming LLM call: %s", e)
        yield f"[ERROR: Unexpected error occurred]"

if __name__ == '__main__':
    # Example usage for Gemma 3
    gemma_endpoint = "http://192.168.1.228:1234/v1/chat/completions"
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
    medgemma_endpoint = "http://192.168.1.65:1234/v1/chat/completions"
    medgemma_model = "medgemma-4b-it"
    medgemma_system = "You are a medical expert."
    medgemma_user = "What are the common symptoms of a cold?"

    print("\n--- Calling MedGemma ---")
    response = call_llm(medgemma_model, medgemma_endpoint, medgemma_system, medgemma_user)
    if "choices" in response:
        print(response['choices'][0]['message']['content'])
    else:
        print(response)
