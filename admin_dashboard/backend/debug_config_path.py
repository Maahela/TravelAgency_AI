import sys
import os
import shutil

# Add project root to path EXACTLY like main.py does
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

print(f"DEBUG: CWD is {os.getcwd()}")
print(f"DEBUG: sys.path[0] is {sys.path[0]}")
# Also print the appended path
print(f"DEBUG: sys.path[-1] is {sys.path[-1]}")

try:
    import config
    print(f"DEBUG: config imported from {config.__file__}")
    from config import DB_PATH, BASE_DIR
    print(f"DEBUG: config.BASE_DIR = {BASE_DIR}")
    print(f"DEBUG: config.DB_PATH = {DB_PATH}")
    
    if hasattr(config, "raw_db_path"):
        print(f"DEBUG: config.raw_db_path = {config.raw_db_path}")

except ImportError as e:
    print(f"DEBUG: ImportError: {e}")
    # Try to find where config.py might be
    print("DEBUG: Searching for config.py in sys.path...")
    for p in sys.path:
        target = os.path.join(p, "config.py")
        if os.path.exists(target):
            print(f"Found config.py at {target}")
