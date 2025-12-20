import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))


"""
Script to automatically create the required Tables and Columns in Airtable.
Robust version with flexible field types.
"""
import os
import requests
import time
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
    
    url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
    
    # 1. Rates Schema
    rates_schema = {
        "name": "Rates",
        "fields": [
            {"name": "Hotel Name", "type": "singleLineText"},
            {"name": "Room Type", "type": "singleLineText"},
            {"name": "Occupancy", "type": "singleSelect", "options": {"choices": [{"name": "Single"}, {"name": "Double"}, {"name": "Triple"}, {"name": "Quad"}, {"name": "Other"}]}},
            {"name": "Meal Plan", "type": "singleLineText"},
            {"name": "Price", "type": "singleLineText"}, # Using text for flexibility with symbols/commas
            {"name": "Currency", "type": "singleLineText"}, # Using text to avoid select option errors
            {"name": "Season Start", "type": "date", "options": {"dateFormat": {"name": "iso"}}},
            {"name": "Season End", "type": "date", "options": {"dateFormat": {"name": "iso"}}},
            {"name": "Source File", "type": "singleLineText"},
            {"name": "Confidence", "type": "number", "options": {"precision": 2}}
        ]
    }

    # 2. HotelContacts Schema
    contacts_schema = {
        "name": "HotelContacts",
        "fields": [
            {"name": "Hotel Name", "type": "singleLineText"},
            {"name": "Email", "type": "singleLineText"},
            {"name": "Discovery Source", "type": "singleLineText"},
            {"name": "Confidence", "type": "number", "options": {"precision": 2}},
        ]
    }

    # 3. ProcessingLog Schema
    log_schema = {
        "name": "Processing_Logs",
        "fields": [
            {"name": "Email ID", "type": "singleLineText"},
            {"name": "Filename", "type": "singleLineText"},
            {"name": "Status", "type": "singleLineText"},
            {"name": "Error Message", "type": "multilineText"},
        ]
    }

    # 4. PriceItems Schema
    price_items_schema = {
        "name": "Price_Items",
        "fields": [
            {"name": "Hotel Name", "type": "singleLineText"},
            {"name": "Category", "type": "singleLineText"},
            {"name": "Description", "type": "multilineText"},
            {"name": "Price", "type": "singleLineText"},
            {"name": "Currency", "type": "singleLineText"},
            {"name": "Per Unit", "type": "singleLineText"},
            {"name": "Adult or Child", "type": "singleLineText"},
            {"name": "Age Range", "type": "singleLineText"},
            {"name": "Applicable Room Types", "type": "singleLineText"},
            {"name": "Applicable Dates", "type": "singleLineText"},
            {"name": "Meal Type", "type": "singleLineText"},
            {"name": "Conditions", "type": "multilineText"},
            {"name": "Source Text", "type": "multilineText"},
            {"name": "Source File", "type": "singleLineText"}
        ]
    }

    # 5. ContractData Schema
    contract_data_schema = {
        "name": "ContractData",
        "fields": [
            {"name": "Hotel Name", "type": "singleLineText"},
            {"name": "Source File", "type": "singleLineText"},
            {"name": "Raw JSON", "type": "multilineText"},
            {"name": "Extracted At", "type": "date", "options": {"dateFormat": {"name": "iso"}}}
        ]
    }

    schemas = [rates_schema, contacts_schema, log_schema, price_items_schema, contract_data_schema]

    for schema in schemas:
        print(f"Creating table '{schema['name']}'...")
        resp = requests.post(url, json=schema, headers=headers)
        if resp.status_code == 200:
            print(f"✅ '{schema['name']}' created.")
        else:
            print(f"⚠️ Result for '{schema['name']}': {resp.status_code} - {resp.text}")
        time.sleep(1) # Extra safety for Meta API sequential calls

if __name__ == "__main__":
    create_schema()
