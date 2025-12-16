"""
Migration script to add the 'contract_data' table to the existing database.
"""
from database.db_init import get_db_connection
from config import DB_PATH
import sqlite3

def migrate():
    print(f"🔄 Migrating database at {DB_PATH}...")
    
    try:
        conn = get_db_connection(DB_PATH)
        cursor = conn.cursor()
        
        # Create extended contract data table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contract_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hotel_name TEXT,
                source_file TEXT,
                raw_json TEXT,
                extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        print("✅ Migration successful: 'contract_data' table created.")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    migrate()
