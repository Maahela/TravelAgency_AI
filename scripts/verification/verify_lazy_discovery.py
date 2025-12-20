import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))


import sys
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from chat.chat_interface import ChatInterface
from utils.logger import get_logger

logger = get_logger("verify_automation")

def verify_lazy_discovery():
    chat = ChatInterface()
    
    print("\n--- TESTING LAZY DISCOVERY ---")
    # Hotel name that definitely doesn't exist in local DB or Airtable
    test_hotel = "The Blue Water Hotel Wadduwa"
    query = f"Send a rate request to {test_hotel}"
    
    print(f"User: {query}")
    print("Wait: This should trigger a live web search (10-20 seconds)...")
    
    response = chat.query(query)
    
    print(f"Assistant: {response}")
    
    if "Rate request draft created" in response:
        print("\n✅ SUCCESS: Lazy discovery found an email and created a draft!")
    elif "reservations@" in response and "placeholder" in response.lower():
        print("\n⚠️ PARTIAL: Failed to find email, fell back to placeholder (expected if no SEO find).")
    elif "Authentication failed" in response:
        print("\n❌ AUTH FAIL: Outlook token expired or invalid.")
    else:
        print("\n❓ OTHER: " + response[:100])

if __name__ == "__main__":
    verify_lazy_discovery()
