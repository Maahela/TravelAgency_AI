import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from database.airtable_client import AirtableClient

def inspect():
    client = AirtableClient()
    if not client.is_connected():
        print("Not connected.")
        return

    print("Fetching one record from 'Rates' table to check schema...")
    try:
        # Try to fetch 1 record
        records = client.rates_table.all(max_records=1)
        if records:
            print("Successfully fetched a record!")
            print("Fields found in Airtable:")
            for field in records[0]['fields'].keys():
                print(f" - {field}")
        else:
            print("Connected, but table is empty. Can't infer schema from records.")
            print("Please ensure your table has the following columns matching Python code:")
            print(" - Hotel Name")
            print(" - Room Type")
            print(" - Meal Plan")
            print(" - Price")
            print(" - Currency")
            print(" - Season Start")
            print(" - Season End")
            print(" - Source File")
            print(" - Confidence")
            
            # Try inserting a dummy record to provoke a detailed error
            print("\nAttempting dummy insert to see error details...")
            try:
                client.rates_table.create({"Hotel Name": "Test Hotel"})
            except Exception as e:
                print(f"\nERROR DETAIL: {e}")

    except Exception as e:
        print(f"Failed to fetch: {e}")

if __name__ == "__main__":
    inspect()
