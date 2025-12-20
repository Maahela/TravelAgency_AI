import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from database.airtable_client import AirtableClient
import os

def list_fields():
    client = AirtableClient()
    if not client.is_connected():
        print("Not connected")
        return

    # To get fields, we interpret a record or use schema API (metadata API requires different token usually).
    # Easier way: Get one record and print its keys.
    # Note: This only shows fields that have values. 
    # If new fields are empty, they won't show up.
    
    # We will try to fetch a record.
    records = client.rates_table.all(max_records=1)
    if records:
        print("Existing Fields in a record:")
        print(list(records[0]['fields'].keys()))
    else:
        print("No records found to inspect fields.")

    # There isn't a simple way to get ALL field names via standard pyairtable table object without metadata API.
    # But checking an existing record helps. 
    # The error message in logs is critical.
    
    # We can also TRY to insert with just "Hotel Name" and see if it works, then add fields one by one.
    
if __name__ == "__main__":
    list_fields()
