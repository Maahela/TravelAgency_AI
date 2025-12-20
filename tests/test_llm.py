"""
Test script for LLM connection.
"""
import sys
import logging
from llm.llm_client import generate_llm_response

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_llm():
    print("Testing LLM Integration (OpenAI)...")
    
    prompt = "Hello! Are you working?"
    print(f"\nSending prompt: '{prompt}'")
    
    response = generate_llm_response(prompt, temperature=0.7)
    
    print("\n--- Response ---")
    print(response)
    
    if "Error" not in response:
        print("\n✅ SUCCESS: LLM connected and responded.")
    else:
        print("\n❌ FAILURE: LLM verification failed.")

if __name__ == "__main__":
    test_llm()
