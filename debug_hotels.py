from database.airtable_client import AirtableClient
import sys

try:
    client = AirtableClient()
    print(f"Connected: {client.is_connected()}")
    
    if hasattr(client, 'hotels_table'):
        records = client.hotels_table.all()
        print(f"Hotels Table Count: {len(records)}")
        if len(records) > 0:
            print("Sample Record:", records[0])
    else:
        print("hotels_table attribute missing from client")
        
    if hasattr(client, 'rates_table'):
        rates = client.rates_table.all()
        unique_hotels_in_rates = set()
        for r in rates:
            if 'Hotel Name' in r['fields']:
                unique_hotels_in_rates.add(r['fields']['Hotel Name'])
        print(f"Unique Hotels in Rates Table: {len(unique_hotels_in_rates)}")
        print(f"Hotels: {unique_hotels_in_rates}")

except Exception as e:
    print(f"Error: {e}")
