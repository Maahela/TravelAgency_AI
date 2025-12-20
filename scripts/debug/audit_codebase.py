import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import os
import sys
import sqlite3
from pathlib import Path

# --- Configuration ---
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
# ---------------------

def check_file_exists(path, description):
    if os.path.exists(path):
        print(f"✅ FOUND {description}: {path}")
        return True
    else:
        print(f"❌ MISSING {description}: {path}")
        return False

def check_db_schema(db_path):
    print(f"\n--- Checking Database Schema: {db_path} ---")
    if not os.path.exists(db_path):
        print(f"❌ DATABASE FILE MISSING: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check hotels table
        try:
            cursor.execute("PRAGMA table_info(hotels)")
            cols = [row[1] for row in cursor.fetchall()]
            required = ['email_address', 'website', 'contact_person']
            missing = [c for c in required if c not in cols]
            
            if missing:
                print(f"❌ MISSING COLUMNS in 'hotels': {missing}")
            else:
                print(f"✅ schema 'hotels': OK (Has {required})")
                
            # Check row count
            cursor.execute("SELECT Count(*) FROM hotels")
            count = cursor.fetchone()[0]
            print(f"ℹ️  'hotels' row count: {count}")
            
        except Exception as e:
            print(f"❌ Error checking 'hotels' table: {e}")

        conn.close()
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

def check_config_resolution():
    print("\n--- Checking Config Resolution ---")
    try:
        import config
        print(f"ℹ️  Imported config from: {config.__file__}")
        print(f"ℹ️  config.BASE_DIR: {config.BASE_DIR}")
        print(f"ℹ️  config.DB_PATH: {config.DB_PATH}")
        
        expected_db = os.path.join(ROOT_DIR, "data", "rates.db")
        resolved_db = str(config.DB_PATH)
        
        if os.path.normpath(resolved_db) == os.path.normpath(expected_db):
            print(f"✅ DB_PATH matches expected ROOT path")
        else:
            print(f"⚠️  DB_PATH Mismatch!")
            print(f"   Expected: {expected_db}")
            print(f"   Actual:   {resolved_db}")
            
        return str(config.DB_PATH)
        
    except ImportError:
        print("❌ FAILED to import config.py")
        return None

def main():
    print(f"Audit Script Running from: {ROOT_DIR}")
    
    # 1. Check Vital Files
    check_file_exists(os.path.join(ROOT_DIR, ".env"), ".env file")
    check_file_exists(os.path.join(ROOT_DIR, "config.py"), "config.py")
    
    # 2. Check Config Resolution
    db_path = check_config_resolution()
    
    # 3. Check DB Schema (using resolved path)
    if db_path:
        check_db_schema(db_path)
        
    # 4. Check Backend Main Existence
    backend_main = os.path.join(ROOT_DIR, "admin_dashboard", "backend", "main.py")
    check_file_exists(backend_main, "Backend main.py")

if __name__ == "__main__":
    main()
