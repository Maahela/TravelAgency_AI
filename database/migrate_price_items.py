"""
Migration script to add the 'price_items' table.
"""
from database.db_init import get_db_connection
from config import DB_PATH

def migrate():
    print(f"🔄 Adding price_items table to {DB_PATH}...")
    
    try:
        conn = get_db_connection(DB_PATH)
        cursor = conn.cursor()
        
        # Create price items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hotel_name TEXT,
                source_file TEXT,
                category TEXT,
                description TEXT,
                price REAL,
                currency TEXT,
                per_unit TEXT,
                adult_or_child TEXT,
                age_range TEXT,
                applicable_room_types TEXT,
                applicable_dates TEXT,
                meal_type TEXT,
                conditions TEXT,
                source_text_snippet TEXT,
                extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        print("✅ Migration successful: 'price_items' table created.")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    migrate()
