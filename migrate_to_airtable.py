"""
Migration script to move local SQLite data to Airtable.
Run this ONCE after configuring .env with Airtable keys.
"""
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from config import DB_PATH
from database.db_init import get_db_connection
from database.airtable_client import AirtableClient
from utils.logger import get_logger

logger = get_logger(__name__)

def migrate_to_airtable():
    print("Starting migration from SQLite to Airtable...")
    
    # 1. Check Airtable Connection
    client = AirtableClient()
    if not client.is_connected():
        print("❌ Airtable not connected. Check your .env file for AIRTABLE_API_KEY and AIRTABLE_BASE_ID.")
        return

    # 2. Fetch all local rates
    print(f"Reading from local DB: {DB_PATH}")
    conn = get_db_connection(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM rates")
    rows = cursor.fetchall()
    
    # Get column names
    col_names = [description[0] for description in cursor.description]
    
    rates_data = []
    for row in rows:
        # Create dict from row
        rate_dict = dict(zip(col_names, row))
        
        # Clean up keys to match what insert_rate expects roughly
        # Our SQLite col names: hotel_name, room_type, etc.
        # insert_rate maps these to "Hotel Name" etc.
        # We need to ensure date formats are strings if Airtable expects them
        
        # Adjust price to be string or float as needed
        rates_data.append(rate_dict)
        
    print(f"Found {len(rates_data)} rates locally.")
    
    # 3. Upload to Airtable
    print("Uploading to Airtable (this may take a while)...")
    
    count = 0
    errors = 0
    
    # Airtable API has rate limits (5 requests/sec). pyairtable handles specific retry logic usually,
    # but let's be safe and simple.
    for rate in rates_data:
        if client.insert_rate(rate):
            count += 1
            print(f"[OK] Imported: {rate.get('hotel_name')} - {rate.get('room_type')}")
        else:
            errors += 1
            print(f"[FAIL] Failed: {rate.get('hotel_name')}")
        
        # Slight delay to be nice to API limits if not using batch
        time.sleep(0.2) 
        
    print("\n" + "="*50)
    print(f"Migration Complete!")
    print(f"Successful: {count}")
    print(f"Failed: {errors}")
    print("="*50)

if __name__ == "__main__":
    migrate_to_airtable()
