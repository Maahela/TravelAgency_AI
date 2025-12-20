import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import os
from dotenv import load_dotenv

def verify():
    load_dotenv()
    
    key = os.getenv("AIRTABLE_API_KEY")
    base = os.getenv("AIRTABLE_BASE_ID")
    
    print("--- Environment Check ---")
    
    if not key:
        print("❌ AIRTABLE_API_KEY is missing or empty.")
    else:
        if key.startswith("pat"):
            print(f"✅ API Key present (starts with '{key[:7]}...')")
        else:
            print(f"❌ API Key format warning (starts with '{key[:4]}...', expected 'pat...')")
            
    if not base:
        print("❌ AIRTABLE_BASE_ID is missing or empty.")
    else:
        if base.startswith("app"):
            print(f"✅ Base ID present ({base})")
        else:
            print(f"❌ Base ID format warning ('{base}', expected 'app...')")

    print("-------------------------")

if __name__ == "__main__":
    verify()
