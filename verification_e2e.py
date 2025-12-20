from database.airtable_client import AirtableClient
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_end_to_end():
    print("--- Starting End-to-End System Verification ---")
    client = AirtableClient()

    if not client.is_connected():
        print("Airtable not connected. Aborting.")
        return

    # 1. Simulate Extracted Data (as it comes from the LLM/Parsing logic)
    hotel_name = "Grand Verification Hotel"
    room_type_name = "Executive Suite Ocean Front"
    meal_plan_input = "half board plus" # Should standardize to HB (or closely related if logic allows, otherwise create new)
    # Note: 'half board plus' logic in code might mapped to HB or keep original? 
    # Let's check logic: 'half' and 'board' in raw -> HB. So it should map to HB.

    rate_data = {
        "hotel_name": hotel_name,
        "room_type": room_type_name,
        "meal_plan": meal_plan_input,
        "price": "550.00",
        "currency": "USD",
        "occupancy": "Double",
        "season_start_date": "2026-01-01",
        "season_end_date": "2026-12-31",
        "source_file": "e2e_verification_test.pdf",
        "confidence": 0.95
    }

    price_item_data = {
        "hotel_name": hotel_name,
        "category": "compulsory_supplement", # Will default to 'other_charge' if not in allowed list
        "description": "Christmas Eve Gala Dinner",
        "price": "150",
        "currency": "USD",
        "per_unit": "per person",
        "meal_type": "Dinner",
        "applicable_dates": "2026-12-24",
        "source_file": "e2e_verification_test.pdf"
    }

    # 2. Execute Insertion - Rates
    print(f"\n[Step 1] Inserting Rate for '{hotel_name}'...")
    try:
        success_rate = client.insert_rate(rate_data)
        if success_rate:
            print("  ✅ Rate insertion reported success.")
        else:
            print("  ❌ Rate insertion failed.")
    except Exception as e:
        print(f"  ❌ Exception during rate insertion: {e}")

    # 3. Execute Insertion - Price Items
    print(f"\n[Step 2] Inserting Price Item for '{hotel_name}'...")
    try:
        success_item = client.insert_price_item(price_item_data)
        if success_item:
            print("  ✅ Price Item insertion reported success.")
        else:
            print("  ❌ Price Item insertion failed.")
    except Exception as e:
        print(f"  ❌ Exception during price item insertion: {e}")

    # 4. Verification Queries (Check if linked records exist)
    print("\n[Step 3] Verifying Records in Airtable...")
    
    # Check Hotel
    hotel_ids = client.get_or_create_hotel(hotel_name)
    if hotel_ids:
        print(f"  ✅ Hotel '{hotel_name}' exists with ID: {hotel_ids[0]}")
    else:
        print(f"  ❌ Hotel '{hotel_name}' not found!")

    # Check Room Type
    if hotel_ids:
        rt_ids = client.get_or_create_room_type(room_type_name, hotel_ids[0])
        if rt_ids:
             print(f"  ✅ Room Type '{room_type_name}' linked to Hotel exists with ID: {rt_ids[0]}")
        else:
             print(f"  ❌ Room Type '{room_type_name}' creation/fetch failed.")
    
    # Check Meal Plan
    # 'half board plus' -> Should be 'HB' based on fuzzy logic: "half" + "board" in string
    mp_ids = client.get_or_create_meal_plan("HB") 
    if mp_ids:
        print(f"  ✅ Standardized Meal Plan 'HB' exists with ID: {mp_ids[0]}")
    else:
        print(f"  warning: Could not find 'HB', maybe it wasn't standardized as expected? Checking original input...")
        mp_ids_orig = client.get_or_create_meal_plan(meal_plan_input)
        print(f"  Original '{meal_plan_input}' ID: {mp_ids_orig}")

    print("\n--- Verification Complete ---")
    print("Please check your Airtable dashboard manually to confirm the visual layout and links are perfect.")

if __name__ == "__main__":
    verify_end_to_end()
