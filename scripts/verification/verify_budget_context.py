import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))


import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from chat.chat_interface import ChatInterface

def verify_budget_context():
    chat = ChatInterface()
    
    print("\n--- TURN 1: Initial Budget Request (Missing Info) ---")
    q1 = "Calculate the total budget for a stay at Elephant Stables from January 1st to January 10th, 2026, for 2 adults in a Double room."
    print(f"User: {q1}")
    r1 = chat.query(q1)
    print(f"Assistant: {r1}")
    
    if "To calculate the budget, I need:" not in r1:
        print("❌ FAILED: Assistant should have asked for missing info.")
        return

    print("\n--- TURN 2: Providing Missing Info (Follow-up) ---")
    q2 = "BB, USD"
    print(f"User: {q2}")
    r2 = chat.query(q2)
    print(f"Assistant: {r2}")

    if "TOTAL TRIP COST" in r2:
        print("\n✅ SUCCESS: Budget calculated successfully using multi-turn context!")
    else:
        print("\n❌ FAILED: Budget calculation did not complete.")

if __name__ == "__main__":
    verify_budget_context()
