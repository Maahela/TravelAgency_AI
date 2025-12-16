"""
Script to inspect the contents of the rates database.
Prints all rates found in a readable format.
"""
from database.query_rates import search_rates
from database.db_init import get_db_connection
from config import DB_PATH


def inspect_rates():
    print(f"\n🔍 Inspecting Database at: {DB_PATH}")
    
    # Check if DB exists
    if not DB_PATH.exists():
        print("❌ Database file not found!")
        return

    # Check connection
    try:
        conn = get_db_connection(DB_PATH)
        conn.close()
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return

    # Fetch all rates
    rates = search_rates()
    
    if not rates:
        print("⚠️  No rates found in the database. (Tables exist but are empty)")
        return

    print(f"✅ Found {len(rates)} rates:\n")
    
    # Print as a nice list
    print("-" * 100)
    print(f"{'ID':<4} | {'Hotel':<30} | {'Room Type':<25} | {'Rate':<10} | {'Dates'}")
    print("-" * 100)
    
    for rate in rates:
        price = f"{rate['currency']} {rate['rate_per_night']}"
        dates = f"{rate['season_start_date']} to {rate['season_end_date']}"
        print(f"{rate['id']:<4} | {rate['hotel_name'][:30]:<30} | {rate['room_type'][:25]:<25} | {price:<10} | {dates}")
    
    print("-" * 100)
    print("\n")

if __name__ == "__main__":
    inspect_rates()
