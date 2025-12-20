import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))


import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from chat.chat_interface import ChatInterface

def run_unified_verification():
    chat = ChatInterface()
    
    print("\n--- TEST 1: Rate Request (DB Email Integration) ---")
    # This should use real DB lookup and prioritize reservations email
    q1 = "Draft a rate request for Elephant Stables"
    print(f"Query: {q1}")
    print(f"Result: {chat.query(q1)}")

    print("\n--- TEST 2: Hotel Discovery ---")
    # This should trigger the discovery agent
    q2 = "Find the email for Heritance Kandalama"
    print(f"Query: {q2}")
    print(f"Result: {chat.query(q2)}")

    print("\n--- TEST 3: Complex Budget (Supplements & Seasonality) ---")
    # Tests cross-seasonal splitting and guest-count awareness
    q3 = "What is the budget for 2 adults and 1 child (age 8) at Elephant Stables from January 1st to January 10th, 2026? We want a Triple room."
    print(f"Query: {q3}")
    print(f"Result: {chat.query(q3)}")

if __name__ == "__main__":
    run_unified_verification()
