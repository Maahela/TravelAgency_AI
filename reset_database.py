import os
import sqlite3
from database.airtable_client import AirtableClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_database():
    print("WARNING: This will delete ALL data found in Airtable and local DB.")
    # confirm = input("Type 'DELETE' to confirm: ")
    # if confirm != "DELETE":
    #     print("Aborted.")
    #     return
    
    # 1. Clear Airtable
    client = AirtableClient()
    if client.is_connected():
        tables = [
            client.rates_table,
            client.price_items_table,
            client.contract_data_table, # ContractData
            client.processing_log_table, # Processing_Logs
            client.contacts_table, # HotelContacts
            client.room_types_table, 
            client.meal_plans_table,
            client.hotels_table
        ]
        
        table_names = [
            "Rates", "Price_Items", "ContractData", "Processing_Logs", 
            "HotelContacts", "Room Types", "Meal Plans", "Hotels"
        ]

        # Delete in order? 
        # Actually, iterating and deleting all records is fine. 
        # If we delete parents (Hotels) before children (Rates), links just disappear.
        
        for table, name in zip(tables, table_names):
            print(f"Clearing table: {name}...")
            try:
                records = table.all()
                ids = [r['id'] for r in records]
                if ids:
                    # Batch delete (max 10 at a time usually, pyairtable handles batching?)
                    # table.batch_delete(ids) 
                    # pyairtable's batch_delete handles chunks of 10 automatically.
                    table.batch_delete(ids)
                    print(f"  Deleted {len(ids)} records from {name}.")
                else:
                    print(f"  {name} is already empty.")
            except Exception as e:
                print(f"  Failed to clear {name}: {e}")

    # 2. Clear Local SQLite
    db_path = os.path.join("admin_dashboard", "backend", "data", "rates.db")
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"Deleted local database: {db_path}")
        except Exception as e:
            print(f"Failed to delete {db_path}: {e}")
    else:
        print("Local database not found.")

if __name__ == "__main__":
    reset_database()
