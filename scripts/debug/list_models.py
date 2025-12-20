import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

"""
Script to list available Google Gemini models.
"""
import os
import google.generativeai as genai
from config import GOOGLE_API_KEY

def list_available_models():
    print("Checking available models...")
    
    if not GOOGLE_API_KEY:
        print("❌ Error: GOOGLE_API_KEY not found in environment.")
        return

    genai.configure(api_key=GOOGLE_API_KEY)
    
    try:
        print("\n--- Available Models ---")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
        print("------------------------\n")
        
    except Exception as e:
        print(f"❌ Error listing models: {e}")

if __name__ == "__main__":
    list_available_models()
