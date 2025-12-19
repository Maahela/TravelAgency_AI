import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "../../")))

from config import DB_PATH, BASE_DIR, DATA_DIR

print(f"BASE_DIR: {BASE_DIR}")
print(f"DATA_DIR: {DATA_DIR}")
print(f"DB_PATH: {DB_PATH}")
print(f"DB exists: {DB_PATH.exists()}")

if DB_PATH.exists():
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"\nTables in database: {[t[0] for t in tables]}")
    conn.close()
