import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import os
from dotenv import load_dotenv
from pyairtable import Api

load_dotenv()

api_key = os.getenv("AIRTABLE_API_KEY")
base_id = os.getenv("AIRTABLE_BASE_ID")

if not api_key or not base_id:
    print("❌ Missing Airtable credentials")
    exit(1)

api = Api(api_key)

# Try common table names for hotel contacts
table_names = ["Hotels", "Hotel", "Contacts", "HotelContacts", "Hotel Contacts", "Properties"]

print(f"Testing tables in base {base_id}...\n")

for table_name in table_names:
    try:
        table = api.table(base_id, table_name)
        records = table.all(max_records=3)
        print(f"✅ '{table_name}' - Found {len(records)} records (showing first 3)")
        if records:
            print(f"   Fields: {list(records[0]['fields'].keys())}")
    except Exception as e:
        if "INVALID_PERMISSIONS" in str(e) or "NOT_FOUND" in str(e):
            print(f"❌ '{table_name}' - Not found or no access")
        else:
            print(f"❌ '{table_name}' - Error: {e}")
    print()
