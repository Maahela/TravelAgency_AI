"""
Script to automatically create the required Tables and Columns in Airtable.
Requires a token with 'schema.bases:write' permission.
"""
import os
import requests # pyairtable table creation is sometimes limited, standard API is safer for meta
from dotenv import load_dotenv

def create_schema():
    load_dotenv()
    api_key = os.getenv("AIRTABLE_API_KEY")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    
    if not api_key or not base_id:
        print("❌ Missing credentials in .env")
        return

    print("🚀 Setting up Airtable Schema...")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 1. Create Rates Table
    # Note: We can only create a table if we use the Meta API which interacts with the Base
    url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
    
    rates_schema = {
        "name": "Rates",
        "fields": [
            {"name": "Hotel Name", "type": "singleLineText"},
            {"name": "Room Type", "type": "singleLineText"},
            {"name": "Meal Plan", "type": "singleLineText"},
            {"name": "Price", "type": "currency", "options": {"precision": 2, "symbol": ""}}, # Storing as number
            {"name": "Currency", "type": "singleSelect", "options": {"choices": [{"name": "USD"}, {"name": "LKR"}, {"name": "EUR"}]}},
            {"name": "Season Start", "type": "date", "options": {"dateFormat": "Local"}},
            {"name": "Season End", "type": "date", "options": {"dateFormat": "Local"}},
            {"name": "Source File", "type": "singleLineText"},
            {"name": "Confidence", "type": "number", "options": {"precision": 2}}
        ]
    }
    
    print("Creating 'Rates' table...")
    resp = requests.post(url, json=rates_schema, headers=headers)
    
    if resp.status_code == 200:
        print("✅ 'Rates' table created successfully!")
    elif resp.status_code == 403:
        print("❌ Permission Denied (403). Your token needs 'schema.bases:write' scope.")
        return
    else:
        print(f"⚠️ Result: {resp.status_code} - {resp.text}")
        if "already exists" in resp.text:
            print("   (Table already exists, skipping)")

    # 2. Create ProcessingLog Table
    log_schema = {
        "name": "ProcessingLog",
        "fields": [
            {"name": "Email ID", "type": "singleLineText"},
            {"name": "Filename", "type": "singleLineText"},
            {"name": "Status", "type": "singleSelect", "options": {"choices": [{"name": "success"}, {"name": "failed"}, {"name": "partial"}]}},
            {"name": "Error Message", "type": "multilineText"},
            {"name": "Timestamp", "type": "createdTime", "options": {}}
        ]
    }
    
    print("Creating 'ProcessingLog' table...")
    resp = requests.post(url, json=log_schema, headers=headers)
    
    if resp.status_code == 200:
        print("✅ 'ProcessingLog' table created successfully!")
    else:
         # Ignore if exists
         pass
         
    print("\nSchema Setup Complete.")

if __name__ == "__main__":
    create_schema()
