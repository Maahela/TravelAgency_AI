"""
Verification script for Airtable Integration.
1. Checks if data exists in Airtable (Web Interface check).
2. Tests if ChatInterface can retrieve it (Bot check).
"""
import sys
import os
from pathlib import Path

# Add project root
sys.path.append(str(Path(__file__).parent))

from database.airtable_client import AirtableClient
from chat.chat_interface import ChatInterface
from utils.logger import get_logger

# Configure logger to show output
import logging
logging.basicConfig(level=logging.WARNING)

def verify_airtable_content():
    print("\n--- 1. Checking Airtable Content (Web Interface Verification) ---")
    client = AirtableClient()
    if not client.is_connected():
        print("❌ Airtable not connected.")
        return None
        
    try:
        # Fetch 1 record
        records = client.rates_table.all(max_records=1)
        if records:
            r = records[0]['fields']
            print("✅ Successfully connected to Airtable!")
            print(f"   Found record: {r.get('Hotel Name')} - {r.get('Room Type')} (${r.get('Price')})")
            return r.get('Hotel Name')
        else:
            print("⚠️ Connected, but table is empty. Migration might have failed or is still running.")
            return None
    except Exception as e:
        print(f"❌ Failed to read from Airtable: {e}")
        return None

def verify_chat_integration(hotel_name):
    print("\n--- 2. Checking Chat Integration (Bot Verification) ---")
    if not hotel_name:
        print("⏭️ Skipping chat test because no hotel was found in step 1.")
        return

    chat = ChatInterface()
    query = f"What are the rates for {hotel_name}?"
    print(f"🤖 User Query: '{query}'")
    
    # We expect the bot to find this.
    # Note: Search params extraction usually uses LLM. 
    # For this test to work without dependent LLM calls effectively, 
    # we hope the simple keyword match or mocks work, 
    # OR we rely on the actual LLM if configured.
    # Given the previous context, we'll try running it for real.
    
    response = chat.query(query)
    print(f"🤖 Bot Response:\n{response}")
    
    if "I couldn't find" in response:
        print("❌ Bot failed to find the info in Airtable.")
    else:
        print("✅ Bot successfully retrieved information!")

if __name__ == "__main__":
    hotel = verify_airtable_content()
    if hotel:
        verify_chat_integration(hotel)
