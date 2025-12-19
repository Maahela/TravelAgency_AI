
import sys
import os
from pathlib import Path
import sqlite3

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "../../")))

from database.airtable_client import AirtableClient
from database.hotel_management import HotelManager

def test_get_contacts_logic():
    print("Testing Contacts Retrieval Logic...")
    results = []
    
    # 1. Try Airtable
    try:
        print("Connecting to Airtable...")
        airtable = AirtableClient()
        if airtable.is_connected():
            try:
                records = airtable.contacts_table.all()
                print(f"Found {len(records)} records in Airtable.")
            except Exception as e:
                print(f"Airtable table error: {e}")
    except Exception as e:
        print(f"Airtable connection error: {e}")

    # 2. Try SQLite
    try:
        print("Connecting to SQLite...")
        manager = HotelManager()
        # Mocking the row factory logic
        conn = manager._get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
            SELECT h.*, e.email as detail_email, e.purpose
            FROM hotels h
            LEFT JOIN hotel_emails e ON h.id = e.hotel_id
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        print(f"Found {len(rows)} rows in SQLite (joined).")
        
        sqlite_data = {}
        for row in rows:
            hid = row['id']
            if hid not in sqlite_data:
                sqlite_data[hid] = {
                    "id": hid,
                    "name": row['name'],
                    "email_address": row['email_address'],
                    "website": row['website'],
                    "source": "Local DB"
                }
        print("Successfully processed SQLite rows.")
        conn.close()
    except Exception as e:
        print(f"SQLite error: {e}")

if __name__ == "__main__":
    test_get_contacts_logic()
