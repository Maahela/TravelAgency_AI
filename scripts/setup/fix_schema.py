import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import sqlite3
from config import DB_PATH

def fix_schema():
    print(f"Fixing schema at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check 'hotels' columns
    cursor.execute("PRAGMA table_info(hotels)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"Current columns: {columns}")
    
    if 'email_address' not in columns:
        print("Adding email_address...")
        cursor.execute("ALTER TABLE hotels ADD COLUMN email_address TEXT")
        
    if 'website' not in columns:
        print("Adding website...")
        cursor.execute("ALTER TABLE hotels ADD COLUMN website TEXT")
        
    if 'contact_person' not in columns:
        print("Adding contact_person...")
        cursor.execute("ALTER TABLE hotels ADD COLUMN contact_person TEXT")
        
    conn.commit()
    conn.close()
    print("Schema fixed.")

if __name__ == "__main__":
    fix_schema()
