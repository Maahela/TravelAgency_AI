
import requests
import sys

try:
    print("Testing /chat endpoint...")
    response = requests.post(
        "http://localhost:4005/chat", 
        json={"message": "Hello, are you online?"},
        timeout=10
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("SUCCESS: Chat endpoint is working!")
    else:
        print("FAILED: Chat endpoint returned error error.")
except Exception as e:
    print(f"FAILED: Connection error: {e}")
