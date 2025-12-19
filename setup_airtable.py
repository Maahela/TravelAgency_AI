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
            {"name": "Occupancy", "type": "singleSelect", "options": {"choices": [{"name": "Single"}, {"name": "Double"}, {"name": "Triple"}, {"name": "Quad"}, {"name": "Other"}]}},
            {"name": "Meal Plan", "type": "singleLineText"},
            {"name": "Price", "type": "currency", "options": {"precision": 2, "symbol": ""}}, # Storing as number
            {"name": "Currency", "type": "singleSelect", "options": {"choices": [{"name": "USD"}, {"name": "LKR"}, {"name": "EUR"}]}},
            {"name": "Season Start", "type": "date", "options": {"dateFormat": {"name": "iso"}}},
            {"name": "Season End", "type": "date", "options": {"dateFormat": {"name": "iso"}}},
            {"name": "Source File", "type": "singleLineText"},
            {"name": "Confidence", "type": "number", "options": {"precision": 2}}
        ]
    }
    
    # ... existing table creation code ...

    print("Creating 'Rates' table...")
    resp = requests.post(url, json=rates_schema, headers=headers)
    
    if resp.status_code == 200:
        print("✅ 'Rates' table created successfully!")
    elif "already exists" in resp.text:
        print("⚠️ 'Rates' table already exists. Checking for 'Occupancy' field...")
        # To add a field to an existing table, we need the Table ID or name.
        # We can fetch the base schema to find the table ID.
        schema_url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
        schema_resp = requests.get(schema_url, headers=headers)
        if schema_resp.status_code == 200:
            tables = schema_resp.json().get("tables", [])
            rates_table = next((t for t in tables if t["name"] == "Rates"), None)
            if rates_table:
                table_id = rates_table["id"]
                existing_fields = [f["name"] for f in rates_table["fields"]]
                if "Occupancy" not in existing_fields:
                    print("   Adding 'Occupancy' field...")
                    add_field_url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables/{table_id}/fields"
                    occupancy_field = {"name": "Occupancy", "type": "singleSelect", "options": {"choices": [{"name": "Single"}, {"name": "Double"}, {"name": "Triple"}, {"name": "Quad"}, {"name": "Other"}]}}
                    f_resp = requests.post(add_field_url, json=occupancy_field, headers=headers)
                    if f_resp.status_code == 200:
                        print("   ✅ 'Occupancy' field added!")
                    else:
                        print(f"   ❌ Failed to add 'Occupancy': {f_resp.text}")
                else:
                    print("   ✅ 'Occupancy' field already exists.")
    else:
        print(f"⚠️ Result: {resp.status_code} - {resp.text}")

    # 2. Create HotelContacts Table
    contacts_schema = {
        "name": "HotelContacts",
        "fields": [
            {"name": "Hotel Name", "type": "singleLineText"},
            {"name": "Email", "type": "singleLineText"},
            {"name": "Discovery Source", "type": "singleSelect", "options": {"choices": [{"name": "Web Scraping"}, {"name": "Email Parsing"}, {"name": "Manual"}]}},
            {"name": "Confidence", "type": "number", "options": {"precision": 2}},
            {"name": "Last Updated", "type": "lastModifiedTime", "options": {}}
        ]
    }
    print("Creating 'HotelContacts' table...")
    resp = requests.post(url, json=contacts_schema, headers=headers)
    if resp.status_code == 200:
        print("✅ 'HotelContacts' table created successfully!")
    
    # 3. Create ProcessingLog Table
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
