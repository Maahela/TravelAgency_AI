"""
Migration script to add 'hotel_emails' table and update 'hotels' schema.
"""
import sys
import os
from pathlib import Path
import sqlite3

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from config import DB_PATH
from database.db_init import initialize_database
from utils.logger import get_logger

logger = get_logger(__name__)

def migrate():
    print(f"Migrating database at {DB_PATH}...")
    
    # 1. Run standard init (creates new tables)
    if initialize_database(DB_PATH):
        print("✅ Standard initialization ran (tables created if missing).")
    
    # 2. Manual column addition for existing 'hotels' table (sqlite doesn't support IF NOT EXISTS for columns)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(hotels)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'last_discovery_run_at' not in columns:
            print("   Adding 'last_discovery_run_at' to 'hotels' table...")
            cursor.execute("ALTER TABLE hotels ADD COLUMN last_discovery_run_at TEXT")
            conn.commit()
            print("   ✅ Column added.")
        else:
            print("   ℹ️ 'last_discovery_run_at' already exists.")
            
    except Exception as e:
        print(f"❌ Migration error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
