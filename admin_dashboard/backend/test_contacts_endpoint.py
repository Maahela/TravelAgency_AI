import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import sqlite3
from database.hotel_management import HotelManager
from config import DB_PATH

print(f"Testing /contacts endpoint logic...")
print(f"DB_PATH: {DB_PATH}")

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
    cursor.execute(query)
    rows = cursor.fetchall()
    
    print(f"Query returned {len(rows)} rows")
    
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

    conn.close()
    
    results = list(sqlite_data.values())
    print(f"✅ SUCCESS: Converted to {len(results)} contacts")
    print(f"\nFirst 3:")
    for i, contact in enumerate(results[:3]):
        print(f"  {i+1}. {contact['name']}: {contact.get('email_address', 'No email')}")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
