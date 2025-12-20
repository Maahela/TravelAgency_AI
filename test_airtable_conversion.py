from database.airtable_client import AirtableClient
import logging

# Configure logging to see output
logging.basicConfig(level=logging.INFO)

def test_conversion():
    client = AirtableClient()

    if not client.is_connected():
        print("Airtable not connected. Skipping test.")
        return

    hotel_name = "Test Hotel Conversion"
    print(f"Testing for hotel: {hotel_name}")

    # 1. Test get_or_create
    ids = client.get_or_create_hotel(hotel_name)
    print(f"Hotel IDs: {ids}")

    if not ids:
        print("Failed to get or create hotel.")
        return

    # 2. Test insert_rate
    rate_data = {
        "hotel_name": hotel_name,
        "room_type": "Standard Room",
        "price": 100,
        "currency": "USD",
        "season_start_date": "2025-01-01",
        "season_end_date": "2025-12-31",
        "source_file": "test_script"
    }

    print("Attempting to insert rate...")
    success = client.insert_rate(rate_data)
    if success:
        print("Successfully inserted rate with linked hotel.")
    else:
        print("Failed to insert rate.")

    # 3. Test insert_price_item
    price_item_data = {
        "hotel_name": hotel_name,
        "category": "meal_rate",
        "description": "Breakfast",
        "price": 20,
        "currency": "USD",
        "source_file": "test_script"
    }
    
    print("Attempting to insert price item...")
    success_item = client.insert_price_item(price_item_data)
    if success_item:
        print("Successfully inserted price item with linked hotel.")
    else:
        print("Failed to insert price item.")

if __name__ == "__main__":
    test_conversion()
