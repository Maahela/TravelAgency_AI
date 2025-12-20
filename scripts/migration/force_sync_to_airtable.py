import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

"""
Force Sync Script
Syncs data from local SQLite database to Airtable.
Useful for recovering data when Airtable API fails or rate limits occur.
"""
import sqlite3
import time
from config import DB_PATH
from database.airtable_client import AirtableClient
from utils.logger import get_logger

logger = get_logger(__name__)

def force_sync():
    logger.info("Starting Force Sync: SQLite -> Airtable")
    
    airtable = AirtableClient()
    if not airtable.is_connected():
        logger.error("Airtable not connected. Check credentials.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Sync Rates
    logger.info("Syncing Rates...")
    cursor.execute("SELECT * FROM rates")
    rates = [dict(row) for row in cursor.fetchall()]
    
    success_count = 0
    for rate in rates:
        # Check uniqueness in Airtable via separate check or just try insert
        # For this script, we'll blindly insert, assuming Airtable automation or user will dedup,
        # or we can check if it exists (expensive).
        # Better strategy: Try to insert.
        if airtable.insert_rate(rate):
            success_count += 1
            print(f"Synced rate: {rate.get('hotel_name')} - {rate.get('room_type')}")
        else:
            print(f"Failed to sync rate: {rate.get('hotel_name')}")
        time.sleep(0.25) # Throttle to avoid rate limits (5 req/sec limit)

    logger.info(f"Synced {success_count}/{len(rates)} rates.")

    # 2. Sync Price Items
    logger.info("Syncing Price Items...")
    cursor.execute("SELECT * FROM price_items")
    items = [dict(row) for row in cursor.fetchall()]
    
    item_success = 0
    for item in items:
        if airtable.insert_price_item(item):
            item_success += 1
            print(f"Synced price item: {item.get('category')} - {item.get('price')}")
        else:
             print(f"Failed to sync item: {item.get('id')}")
        time.sleep(0.25)

    logger.info(f"Synced {item_success}/{len(items)} price items.")
    
    conn.close()
    logger.info("Force sync completed.")

if __name__ == "__main__":
    force_sync()
