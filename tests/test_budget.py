"""
Test script for Budget Calculator feature.
Verifies LLM extraction and math transparency.
"""
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.append(str(Path(__file__).parent.parent))

from chat.chat_interface import ChatInterface
import logging
logging.basicConfig(level=logging.WARNING)

def test_budget_flow():
    print("\n--- Testing Budget Calculator ---")
    
    # Mocking extraction to avoid real LLM calls for this test (deterministic)
    # BUT we want to test the full flow ideally. 
    # Let's mock the 'search_rates' so we know the math numbers.
    
    # Scenario: 2 Nights at Hotel A ($100), 3 Nights at Hotel B ($200)
    mock_rates = [
        {'hotel_name': 'Hotel A', 'rate_per_night': 100, 'currency': 'USD', 'room_type': 'Standard'},
        {'hotel_name': 'Hotel B', 'rate_per_night': 200, 'currency': 'USD', 'room_type': 'Suite'}
    ]
    
    # We patch search_rates to return specific rates based on input
    def side_effect_search(hotel_name, **kwargs):
        return [r for r in mock_rates if r['hotel_name'] == hotel_name]

    # We also patch ItineraryExtractor to return a fixed JSON
    mock_extract_data = {
        "stays": [
            {"hotel_name": "Hotel A", "nights": 2, "rooms": 1, "room_type": "Standard"},
            {"hotel_name": "Hotel B", "nights": 3, "rooms": 1, "room_type": "Suite"}
        ],
        "currency": "USD"
    }
    
    # Import classes to patch directly
    from llm.itinerary_extractor import ItineraryExtractor
    
    # Patch object instead of string path to avoid resolution errors
    with patch('database.query_rates.search_rates', side_effect=side_effect_search), \
         patch.object(ItineraryExtractor, 'extract', return_value=mock_extract_data):
        
        chat = ChatInterface()
        response = chat.query("Calculate budget for 2 nights at Hotel A and 3 nights at Hotel B")
        
        # safe write to file
        with open("test_output.txt", "w", encoding="utf-8") as f:
            f.write(response)
            
        print(f"Response written to test_output.txt")
        
        # Assertions
        if "TOTAL TRIP COST: USD 800.00" not in response:
             print("❌ Total Cost mismatch!")
        else:
             print("✅ Total Cost match!")

        assert "Hotel A" in response
        assert "100.0" in response
        assert "200.0" in response
        assert "USD 200.00" in response  # 100*2
        assert "USD 600.00" in response  # 200*3
        assert "**TOTAL TRIP COST**: USD 800.00" in response
        
        print("✅ Verification Successful: Math is correct and format is transparent.")

if __name__ == "__main__":
    test_budget_flow()
