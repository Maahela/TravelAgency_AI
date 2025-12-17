"""
Migration script to add 'hotels' table to the database.
"""
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from config import DB_PATH
from database.db_init import initialize_database
from utils.logger import get_logger

logger = get_logger(__name__)

def migrate():
    print(f"Migrating database at {DB_PATH}...")
    if initialize_database(DB_PATH):
        print("✅ Database migration successful (hotels table added if missing).")
    else:
        print("❌ Database migration failed.")

if __name__ == "__main__":
    migrate()
