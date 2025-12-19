"""
Verification script for User Scenario (Typos + Logic).
Input: "2 night double room from the 23 of january on elephnats stables and after that 3 nights at 98 acres dooube room .all this is for 4 adults"
Goal: Verify typo correction and guest/room logic distribution.
"""
import sys
import os
from pathlib import Path
import json

sys.path.append(str(Path(__file__).parent))

from chat.chat_interface import ChatInterface
from llm.itinerary_extractor import ItineraryExtractor
import logging

# Suppress debug logs to see print output clearly
logging.basicConfig(level=logging.WARNING)

def test_scenario():
    print("\n--- Testing User Scenario (Strict Seasonality) ---")
    # Using year 2028 to force "No Seasonal Rate" error
    user_query = "2 night  double room from the 23 of january 2028 on elephnats stables .all this is for 4 adults on HB basis"
    print(f"Query: {user_query}\n")
    
    # 1. Test Extraction separately to see the JSON
    print("--- 1. Extraction Result ---")
    extractor = ItineraryExtractor()
    data = extractor.extract(user_query)
    print(json.dumps(data, indent=2))
    
    # 2. Test Full Flow
    print("\n--- 2. Bot Response ---")
    chat = ChatInterface()
    response = chat.query("Calculate budget for " + user_query)
    
    # Safe print
    try:
        print(response)
    except Exception:
        print(repr(response))

if __name__ == "__main__":
    test_scenario()
