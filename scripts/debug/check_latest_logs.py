import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from database.airtable_client import AirtableClient
from pyairtable.formulas import match
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def check_logs():
    client = AirtableClient()
    if not client.is_connected():
        print("Airtable not connected.")
        return

    print("--- Latest Processing Logs ---")
    # Fetch all logs (assuming volume isn't huge yet, otherwise sort param is needed)
    # pyairtable 'all' returns everything. For a quick check, this is fine.
    try:
        logs = client.processing_log_table.all(sort=["-Created"]) # Sort by Created descending (airtable default field is 'Created')
        # Note: 'Created' field might need to be explicitly enabled or referenced as 'createdTime' if using metadata, 
        # but in sort param we usually pass field names. 
        # If 'Created' field doesn't exist in the view, this might fail.
        # Let's try to just fetch all and take the last ones (as they are usually appended).
        
        # If sort fails, we accept unsorted.
        if not logs:
             print("No logs found.")
             return

        # Take top 5
        recent_logs = logs[:5] 
        
        for log in recent_logs:
            f = log['fields']
            print(f"File: {f.get('Filename', 'N/A')}")
            print(f"Status: {f.get('Status', 'N/A')}")
            error = f.get('Error Message')
            if error:
                print(f"Error: {error}")
            print("-" * 20)

    except Exception as e:
        print(f"Error fetching logs: {e}")
        # Fallback: just get all and print last 3
        try:
             logs = client.processing_log_table.all()
             print(f"Total Logs: {len(logs)}")
             for log in logs[-3:]:
                 print(log['fields'])
        except:
             pass

    print("\n--- Recent Rates Count ---")
    try:
        rates = client.rates_table.all()
        print(f"Total Rates currently in DB: {len(rates)}")
    except:
        print("Could not fetch rates.")

if __name__ == "__main__":
    check_logs()
