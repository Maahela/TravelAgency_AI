from database.airtable_client import AirtableClient
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_normalization_phase2():
    client = AirtableClient()

    if not client.is_connected():
        print("Airtable not connected. Skipping test.")
        return

    hotel_name = "Test Hotel 3NF"
    print(f"\n--- Testing 3NF for hotel: {hotel_name} ---")

    # 1. Test Meal Plan Standardization
    print("\n[Test 1] Meal Plan Standardization")
    variants = ["Bed & Breakfast", "bread and brakfast", "BB"]
    for v in variants:
        ids = client.get_or_create_meal_plan(v)
        print(f"  Variant '{v}' -> ID: {ids}")
    
    # 2. Test Room Type Creation (Linked to Hotel)
    print("\n[Test 2] Room Type Creation")
    # First ensure hotel exists
    hotel_ids = client.get_or_create_hotel(hotel_name)
    print(f"  Hotel ID: {hotel_ids}")
    
    if not hotel_ids:
        print("  Failed to create hotel!")
        return

    room_type_name = "Ocean View Suite"
    rt_ids = client.get_or_create_room_type(room_type_name, hotel_ids[0])
    print(f"  Room Type '{room_type_name}' -> ID: {rt_ids}")

    # 3. Test Full Insert Rate
    print("\n[Test 3] Full Insert Rate")
    rate_data = {
        "hotel_name": hotel_name,
        "room_type": room_type_name,
        "meal_plan": "bread and brakfast", # Should be standardized to BB
        "price": 250,
        "currency": "USD",
        "season_start_date": "2025-06-01",
        "season_end_date": "2025-06-30",
        "source_file": "test_script_3nf"
    }

    print("  Attempting to insert rate...")
    # Temporarily modify logging propagation or just catch it here if client allows
    # But client inserts and catches internally.
    # We should look at the log output which is being truncated.
    # Let's use the private method if necessary or modify client?
    # No, let's just inspect the return. If false, we can't see why easily unless we look at logs.
    
    # Actually, let's try to call the table.create directly to see the error!
    try:
        # Re-construct payload here to test
        # Note: we need the IDs first
        
        # ... Or better, let's read the log file I'm creating? 
        # No, let's just make the client throw the error so we can see it?
        # Creating a temporary client that doesn't swallow errors?
        pass 
    except:
        pass

    # Let's rely on the fact that I can't modify the client easily to throw.
    # I will modify client to PRINT the error to stdout using print() instead of logger.error 
    # so I can see it.
    
    success = client.insert_rate(rate_data)
    if success:
        print("  Successfully inserted rate with 3NF links.")
    else:
        print("  Failed to insert rate.")
        # We can't see the error.
        
    # Hack: Access the internal table and try manual insert to debug
    print("  Debugging manual insert to see error:")
    try:
         # Same logic as client
         rec = {
               "Hotel Name": hotel_name, 
               "Hotel": hotel_ids, 
               # "Room Type (Text)": room_type_name, # Ignoring legacy text field for now
               "Room Type": rt_ids, 
               # "Meal Plan (Text)": "bread and brakfast", 
               "Meal Plan": client.get_or_create_meal_plan("bread and brakfast"), 
               "Price": "250",
               "Currency": "USD"
         }
         client.rates_table.create(rec)
         print("  Manual insert SUCCESS")
    except Exception as e:
         print(f"  Manual insert FAILED: {e}")
         if hasattr(e, 'response'):
             print(f"  Response: {e.response.text}")

if __name__ == "__main__":
    test_normalization_phase2()
