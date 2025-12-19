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
    
    # 3. Upload to Airtable (Idempotent)
    print("Fetching existing records from Airtable to avoid duplicates...")
    existing_records = client.rates_table.all()
    # Create a set of (hotel, room_type) for quick lookup
    # Note: Use case-insensitive and stripped comparison
    existing_set = set()
    for r in existing_records:
        f = r['fields']
        hotel = str(f.get('Hotel Name', '')).strip().lower()
        room = str(f.get('Room Type', '')).strip().lower()
        price = str(f.get('Price', '')).strip()
        start = str(f.get('Season Start', '')).strip()
        end = str(f.get('Season End', '')).strip()
        
        # Unique tuple: (hotel, room, price, start, end)
        existing_set.add((hotel, room, price, start, end))
    
    print(f"Found {len(existing_set)} unique seasonal rates already in Airtable.")
    print("Uploading remaining rates (this may take a while)...")
    
    count = 0
    skipped = 0
    errors = 0
    
    for rate in rates_data:
        hotel = str(rate.get('hotel_name', '')).strip().lower()
        room = str(rate.get('room_type', '')).strip().lower()
        price = str(rate.get('rate_per_night', '')).strip()
        # Dates in SQLite might be season_start_date
        start = str(rate.get('season_start_date', '')).strip()
        end = str(rate.get('season_end_date', '')).strip()
        
        if (hotel, room, price, start, end) in existing_set:
            skipped += 1
            continue
            
        if client.insert_rate(rate):
            count += 1
            print(f"[OK] {count+skipped}/{len(rates_data)} - Imported: {rate.get('hotel_name')} - {rate.get('room_type')}")
            # Add to set to avoid duplicates within the same run if they exist in source
            existing_set.add((hotel, room, price, start, end))
        else:
            errors += 1
            print(f"[FAIL] {count+skipped+errors}/{len(rates_data)} - Failed: {rate.get('hotel_name')} - {rate.get('room_type')}")
        
        # Increased delay for Airtable limits (5 requests/sec)
        time.sleep(0.3) 
        
    print("\n" + "="*50)
    print(f"Sync Complete!")
    print(f"New Imports: {count}")
    print(f"Already Existed: {skipped}")
    print(f"Failed: {errors}")
    print("="*50)

if __name__ == "__main__":
    migrate_to_airtable()
