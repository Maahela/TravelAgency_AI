"""
Test script for Hotel Discovery Workflow.
"""
from workflow.hotel_discovery import HotelDiscoveryWorkflow
from database.hotel_management import HotelManager

def test_discovery():
    print("Testing Hotel Discovery Workflow...")
    
    # Famous hotels (high chance of finding info)
    test_hotels = [
        "Cinnamon Grand Colombo",
        "Shangri-La Colombo",
        "Araliya Green City"
    ]
    
    workflow = HotelDiscoveryWorkflow()
    results = workflow.discover_hotels(test_hotels)
    
    print("\nDiscovery Results:")
    for res in results:
        status_icon = "[OK]" if res['status'] == 'success' else "[FAIL]"
        print(f"   {status_icon} {res['name']}: {res.get('email', 'Not found')}")
        
    # Verify in DB
    print("\nChecking Database...")
    manager = HotelManager()
    all_hotels = manager.get_all_hotels()
    
    for h in all_hotels:
        # Check if it matches one of our test cases
        if h['name'] in test_hotels:
            print(f"   Stored: {h['name']} -> {h['email_address']} (ID: {h['id']})")

if __name__ == "__main__":
    test_discovery()
