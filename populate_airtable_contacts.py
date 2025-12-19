
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "../../")))

from database.airtable_client import AirtableClient

def populate_dummy_contacts():
    print("🚀 Starting dummy contact population in Airtable...")
    load_dotenv()
    
    airtable = AirtableClient()
    if not airtable.is_connected():
        print("❌ Airtable not connected. Check environment variables.")
        return

    # Try a few variations of the table name
    table_variations = ["HotelContacts", "Hotel Contacts", "Contacts", "EmailContacts"]
    
    success = False
    for table_name in table_variations:
        try:
            print(f"\n🔍 Probing table: '{table_name}'...")
            table = airtable.api.table(airtable.base_id, table_name)
            
            # Try to add one dummy record
            dummy = {
                "Hotel Name": f"Test Hotel ({table_name})",
                "Email": "test@example.com",
                "Discovery Source": "Script Probe"
            }
            table.create(dummy)
            print(f"✅ Success! Table '{table_name}' exists and is writable.")
            
            # Now add the rest
            print("Adding more dummy data...")
            dummy_contacts = [
                {"Hotel Name": "The Blue Water Hotel Wadduwa", "Email": "info@bluewatersrilanka.com", "Discovery Source": "Manual Dummy"},
                {"Hotel Name": "Shangri-La Colombo", "Email": "reservations.slcb@shangri-la.com", "Discovery Source": "Manual Dummy"},
                {"Hotel Name": "Taj Samudra", "Email": "samudra.colombo@tajhotels.com", "Discovery Source": "Manual Dummy"}
            ]
            for contact in dummy_contacts:
                table.create(contact)
                print(f"  Added {contact['Hotel Name']}")
            
            success = True
            # Update AirtableClient map if needed in memory (but here we just want to verify)
            break
        except Exception as e:
            if "INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND" in str(e):
                print(f"❌ Table '{table_name}' not found.")
            else:
                print(f"❌ Table '{table_name}' error: {e}")

    if not success:
        print("\n❌ Could not find a valid Contacts table in Airtable.")
    else:
        print("\n✨ Done! Dummy data populated.")

if __name__ == "__main__":
    populate_dummy_contacts()
