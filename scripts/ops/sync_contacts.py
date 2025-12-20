import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from database.airtable_client import AirtableClient
from database.hotel_management import HotelManager
import sys

def sync_contacts():
    print("--- DEBUG SYNC START ---", flush=True)
    try:
        airtable = AirtableClient()
        manager = HotelManager()
        print(f"DB Path: {manager.db_path}", flush=True)
        
        print("Fetching from Airtable...", flush=True)
        contacts = airtable.contacts_table.all()
        print(f"Found {len(contacts)} contacts", flush=True)
        
        for i, c in enumerate(contacts):
            print(f"Processing contact {i+1}...", flush=True)
            fields = c['fields']
            name = fields.get('Hotel Name')
            email = fields.get('Email')
            print(f"  Name: {name}, Email: {email}", flush=True)
            
            if name:
                print("  Adding hotel logic...", flush=True)
                hotel_id = manager.add_hotel(
                    name=name, 
                    email=email,
                    website=fields.get('Website'), 
                    contact_person=fields.get('Contact Person')
                )
                print(f"  Hotel ID: {hotel_id}", flush=True)
                
                if email:
                    print(f"  Upserting email for ID {hotel_id}...", flush=True)
                    manager.upsert_hotel_email(
                        hotel_id=hotel_id,
                        email=email,
                        purpose='reservations',
                        source_type='airtable_sync',
                        confidence=1.0
                    )
                    print("  Upsert done.", flush=True)
        
        print("--- SYNC COMPLETE ---", flush=True)
        
    except Exception as e:
        print(f"!!! CRASH !!! {e}", flush=True)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    sync_contacts()
