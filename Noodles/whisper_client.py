"""
Test client for Whisper API
Demonstrates how to use the speech-to-text endpoints
"""

import requests
import json
import os
from typing import Optional

class WhisperClient:
    def __init__(self, base_url: str = "http://localhost:8006"):
        self.base_url = base_url
        
    def health_check(self):
        """Check if the API is healthy"""
        try:
            response = requests.get(f"{self.base_url}/health")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_models(self):
        """Get available Whisper models"""
        try:
            response = requests.get(f"{self.base_url}/models")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def transcribe_file(
        self, 
        file_path: str, 
        model: str = "base",
        include_segments: bool = False,
        temperature: float = 0.0
    ):
        """Transcribe an audio file"""
        try:
            if not os.path.exists(file_path):
                return {"error": f"File not found: {file_path}"}
            
            with open(file_path, "rb") as audio_file:
                files = {"file": audio_file}
                params = {
                    "model": model,
                    "include_segments": include_segments,
                    "temperature": temperature
                }
                
                response = requests.post(
                    f"{self.base_url}/transcribe",
                    files=files,
                    params=params
                )
                
                return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def transcribe_url(
        self,
        url: str,
        model: str = "base", 
        include_segments: bool = False,
        temperature: float = 0.0
    ):
        """Transcribe audio from URL"""
        try:
            params = {
                "url": url,
                "model": model,
                "include_segments": include_segments,
                "temperature": temperature
            }
            
            response = requests.post(
                f"{self.base_url}/transcribe-url",
                params=params
            )
            
            return response.json()
        except Exception as e:
            return {"error": str(e)}

def main():
    """Test the Whisper API"""
    client = WhisperClient()
    
    print("🎤 Testing Whisper API")
    print("=" * 50)
    
    # Health check
    print("1. Health Check:")
    health = client.health_check()
    print(json.dumps(health, indent=2))
    print()
    
    # Get models
    print("2. Available Models:")
    models = client.get_models()
    if "error" not in models:
        print("   🚀 English-Only Models (Recommended for English):")
        for model in models:
            if model['name'].endswith('.en'):
                print(f"      - {model['name']}: {model['description']} ({model['size']}, {model['speed']}, VRAM: {model['vram']})")
        
        print("   🌍 Multilingual Models:")
        for model in models:
            if not model['name'].endswith('.en'):
                print(f"      - {model['name']}: {model['description']} ({model['size']}, {model['speed']}, VRAM: {model['vram']})")
    else:
        print(f"   Error: {models['error']}")
    print()
    
    # Test file transcription (if you have an audio file)
    test_file = "test_audio.wav"  # Replace with your audio file
    if os.path.exists(test_file):
        print("3. File Transcription Test:")
        result = client.transcribe_file(test_file, model="base.en")  # Using English-only model
        if "error" not in result:
            print(f"   Text: {result['text']}")
            print(f"   Model: {result['model_used']}")
            print(f"   Duration: {result.get('duration', 'N/A')} seconds")
        else:
            print(f"   Error: {result['error']}")
    else:
        print("3. File Transcription Test: Skipped (no test file)")
    print()
    
    # Test URL transcription (example with a public audio URL)
    print("4. URL Transcription Test:")
    print("   Note: This requires a valid audio URL")
    # Uncomment and replace with a valid audio URL to test
    # result = client.transcribe_url("https://example.com/audio.mp3", model="tiny")
    # print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()