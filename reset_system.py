import os
import sys
import shutil
from pathlib import Path
from dotenv import load_dotenv
from pyairtable import Api

# Load environment variables
load_dotenv()

# Configuration
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "rates")

# Paths (using absolute paths as fixed earlier)
BASE_DIR = Path(os.path.realpath(__file__)).parent
DATA_DIR = BASE_DIR / "data"

def clear_airtable():
    print(f"🗑️ Clearing Airtable table '{AIRTABLE_TABLE_NAME}'...")
    if not AIRTABLE_API_KEY or not AIRTABLE_BASE_ID:
        print("❌ Missing Airtable credentials in .env")
        return

    try:
        api = Api(AIRTABLE_API_KEY)
        table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)
        records = table.all()
        
        if not records:
            print("   Table is already empty.")
            return

        print(f"   Found {len(records)} records. Deleting...")
        # Delete in batches (pyairtable handles batching, but we pass IDs)
        record_ids = [r['id'] for r in records]
        table.batch_delete(record_ids)
        print("✅ Airtable cleared successfully.")
    except Exception as e:
        print(f"❌ Error clearing Airtable: {e}")

def clear_local_db():
    print("🗑️ Clearing local SQLite databases...")
    
    # List of possible DB locations to clean
    db_files = [
        DATA_DIR / "rates.db",
        BASE_DIR / "admin_dashboard/backend/data/rates.db" # The accidental one
    ]

    for db_path in db_files:
        if db_path.exists():
            try:
                os.remove(db_path)
                print(f"✅ Deleted {db_path}")
            except Exception as e:
                print(f"❌ Failed to delete {db_path}: {e}")
        else:
            print(f"   {db_path} not found (already clean).")

    # Re-create empty rates.db by initializing the DB
    # We do this so the backend doesn't crash on startup
    try:
        from database.db_init import initialize_database
        # Ensure data dir exists
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        main_db_path = DATA_DIR / "rates.db"
        print(f"🔄 Re-initializing clean database at {main_db_path}...")
        initialize_database(main_db_path)
        print("✅ Database re-initialized.")
    except Exception as e:
        print(f"❌ Error re-initializing DB: {e}")

if __name__ == "__main__":
    confirm = input("⚠️ WARNING: This will DELETE ALL DATA in Airtable and local DBs. Type 'yes' to proceed: ")
    if confirm.lower() == "yes":
        print("\n🚀 Starting System Reset...\n")
        clear_airtable()
        clear_local_db()
        print("\n✨ System Reset Complete. Ready for new test.")
    else:
        print("Operation cancelled.")
