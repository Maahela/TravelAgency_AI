"""
Test script for Database module.
Verifies initialization, insertion, and querying of rates.
"""
import logging
from pathlib import Path
from database.db_init import initialize_database
from database.insert_rates import insert_rate
from database.query_rates import search_rates
from config import DB_PATH

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database():
    print("Testing Database Module...")
    
    # 1. Initialize
    print("\n--- Initializing Database ---")
    if initialize_database(DB_PATH):
        print("✅ Database initialized successfully.")
    else:
        print("❌ Database initialization failed.")
        return

    # 2. Insert Test Rate
    print("\n--- Testing Insert ---")
    test_rate = {
        'hotel_name': 'Test Hotel Resort',
        'room_type': 'Ocean View Suite',
        'rate_per_night': 250.00,
        'currency': 'USD',
        'meal_plan': 'All Inclusive',
        'season_start_date': '2024-06-01',
        'season_end_date': '2024-08-31',
        'conditions': 'Non-refundable',
        'validity_date': '2024-05-31',
        'source_file': 'test_script.py',
        'extracted_at': '2024-01-01',
        'confidence': 0.99
    }
    
    if insert_rate(test_rate, DB_PATH):
        print("✅ Rate inserted successfully.")
    else:
        print("❌ Rate insertion failed.")
        return

    # 3. Query Test Rate
    print("\n--- Testing Query ---")
    results = search_rates(hotel_name='Test Hotel', db_path=DB_PATH)
    if results:
        print(f"✅ Found {len(results)} rate(s).")
        print(f"Sample: {results[0]['hotel_name']} - {results[0]['room_type']} (${results[0]['rate_per_night']})")
    else:
        print("❌ No rates found (Query failed).")

if __name__ == "__main__":
    test_database()
