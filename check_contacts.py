from database.airtable_client import AirtableClient
import json

airtable = AirtableClient()
contacts = airtable.contacts_table.all()

print("=== CHECKING ALL CONTACTS ===\n")
for idx, c in enumerate(contacts):
    print(f"Contact {idx+1}: {c['fields'].get('Hotel Name', 'Unknown')}")
    print(f"All fields: {list(c['fields'].keys())}")
    print(f"Full data:\n{json.dumps(c['fields'], indent=2)}\n")
