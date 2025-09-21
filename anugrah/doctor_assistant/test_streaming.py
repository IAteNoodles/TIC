#!/usr/bin/env python3
"""
Test the streaming diagnosis functionality
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph import run_streaming_diagnosis
import time

def test_streaming():
    """Test the streaming diagnosis with a real patient query"""
    print("Testing streaming diagnosis...")
    print("=" * 50)
    
    query = "What is the diabetes risk?"
    patient_id = "123"
    
    print(f"Query: {query}")
    print(f"Patient ID: {patient_id}")
    print("-" * 50)
    
    try:
        for chunk in run_streaming_diagnosis(query, patient_id):
            if chunk.startswith('[STATUS]'):
                print(f"\n🔄 {chunk}")
            elif chunk.startswith('[ERROR]'):
                print(f"\n❌ {chunk}")
            else:
                print(chunk, end='', flush=True)
    
    except Exception as e:
        print(f"\nError during streaming test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_streaming()