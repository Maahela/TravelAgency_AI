import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))


import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from chat.chat_interface import ChatInterface

def verify_budget_context_debug():
    chat = ChatInterface()
    
    print(f"Initial flow state: {chat.current_flow}")

    print("\n--- TURN 1: Initial Budget Request ---")
    q1 = "Calculate the total budget for a stay at Elephant Stables from January 1st to January 10th, 2026, for 2 adults in a Double room."
    print(f"User: {q1}")
    r1 = chat.query(q1)
    print(f"Assistant: {r1}")
    print(f"Flow state after Turn 1: {chat.current_flow}")
    
    if chat.current_flow != 'budget':
        print("❌ FAILED: flow state should be 'budget'")
        return

    print("\n--- TURN 2: Providing Missing Info (Mirror User) ---")
    q2 = "BB and USD"
    print(f"User: {q2}")
    r2 = chat.query(q2)
    print(f"Assistant: {r2}")
    print(f"Flow state after Turn 2: {chat.current_flow}")

    if "TOTAL TRIP COST" in r2:
        print("\n✅ SUCCESS: Budget calculated successfully!")
    elif "Based on the provided data" in r2:
         print("\n❌ FAILED: Routed to default branch (Rate Search) instead of Budget.")
    else:
        print("\n❓ UNKNOWN: Turn 2 returned: " + r2[:50] + "...")

if __name__ == "__main__":
    verify_budget_context_debug()
