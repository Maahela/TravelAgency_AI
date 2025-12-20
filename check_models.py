import google.generativeai as genai
from config import GOOGLE_API_KEYS
import os

if GOOGLE_API_KEYS:
    genai.configure(api_key=GOOGLE_API_KEYS[0])
    print("Listing available models...")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
else:
    print("No GOOGLE_API_KEYS found in config.")
