import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from unittest.mock import patch, MagicMock
from database.insert_rates import insert_rate
from pathlib import Path
import os
import logging

# Configure logging to capture output
logging.basicConfig(level=logging.INFO)

# Setup temp DB
DB_PATH = Path("test_sync.db").resolve()

@patch('database.airtable_client.AirtableClient')
def test_sync(MockClient):
    print("--- Testing Airtable Sync Logic ---")
    
    # Setup Mock
    instance = MockClient.return_value
    instance.is_connected.return_value = True
    
    # Test Data
    data = {
        "hotel_name": "Sync Hotel",
        "room_type": "Sync Room",
        "rate_per_night": 100,
        "season_start_date": "2025-01-01",
        "season_end_date": "2025-01-02",
        "meal_plan": "BB" # Ensure we provide a meal plan to test 3NF lookup resilience
    }
    
    # Run Insert
    from database.db_init import initialize_database
    initialize_database(DB_PATH)
    
    # We need to mock HotelManager inside insert_rate or ensure DB is prepped
    # insert_rate calls HotelManager. To avoid complex mocking of HM, let's just let it run against real SQLite
    # Since we initialized the DB, it should work fine.
    
    print("Inserting rate...")
    insert_rate(data, DB_PATH)
    
    # Verify Sync Call
    # Expect insert_rate to be called on the mock instance
    instance.insert_rate.assert_called_once_with(data)
    print("✅ Airtable Sync Call Verified: insert_rate() was called on AirtableClient")

if __name__ == "__main__":
    try:
        test_sync()
    except Exception as e:
        print(f"❌ Test Failed: {e}")
    finally:
        if DB_PATH.exists():
            try:
                os.remove(DB_PATH)
            except:
                pass
