import sys
import os
import sqlite3
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from config import DB_PATH
from database.hotel_management import HotelManager

print(f"DB_PATH: {DB_PATH}")
print(f"DB exists: {DB_PATH.exists()}")

try:
    manager = HotelManager()
    conn = manager._get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = """
        SELECT h.*, e.email as detail_email, e.purpose
        FROM hotels h
        LEFT JOIN hotel_emails e ON h.id = e.hotel_id
    """
    
    print("\nExecuting query...")
    cursor.execute(query)
    rows = cursor.fetchall()
    
    print(f"Found {len(rows)} rows")
    
    sqlite_data = {}
    for row in rows:
        hid = row['id']
        if hid not in sqlite_data:
            sqlite_data[hid] = {
                "id": hid,
                "name": row['name'],
                "email_address": row['email_address'],
                "website": row['website'],
                "contact_person": row['contact_person'],
                "last_rate_request_date": row['last_rate_request_date'],
                "emails": [],
                "source": "Local DB"
            }
        
        if row['detail_email']:
            sqlite_data[hid]["emails"].append({
                "email": row['detail_email'],
                "purpose": row['purpose']
            })
            if not sqlite_data[hid]["email_address"]:
                sqlite_data[hid]["email_address"] = row['detail_email']
    
    print(f"\nProcessed into {len(sqlite_data)} unique hotels:")
    for hid, data in sqlite_data.items():
        print(f"  {data['name']}: {data['email_address']}")
    
    conn.close()
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
