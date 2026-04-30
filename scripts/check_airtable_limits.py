import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.airtable_client import AirtableClient

def check_limits():
    print("Connecting to Airtable...")
    try:
        client = AirtableClient()
        if not client.is_connected():
            print("❌ Could not connect to Airtable. Check API Key and Base ID.")
            return

        tables = [
            ("Rates", client.rates_table),
            ("Price Items", client.price_items_table),
            ("Hotels", client.hotels_table),
            ("Processing Logs", client.processing_log_table),
            ("Hotel Contacts", client.contacts_table),
            ("Contract Data", client.contract_data_table),
            ("Room Types", client.room_types_table),
            ("Meal Plans", client.meal_plans_table)
        ]

        total_records = 0
        print("\n--- Airtable Usage ---")
        for name, table in tables:
            try:
                # Fetch minimal data (no fields) to count records
                records = table.all(fields=[]) 
                count = len(records)
                total_records += count
                print(f"{name}: {count} records")
            except Exception as e:
                print(f"{name}: Error fetching count ({e})")

        print("----------------------")
        print(f"TOTAL RECORDS: {total_records}")
        print("----------------------")
        
        limit = 1200
        if total_records >= limit:
            print(f"⚠️  CRITICAL: You have EXCEEDED the Free Tier limit ({limit})!")
        elif total_records > (limit * 0.8):
            print(f"⚠️  WARNING: You are approaching the limit ({total_records}/{limit})")
        else:
            print(f"✅ Status: Safe ({total_records}/{limit})")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    check_limits()
