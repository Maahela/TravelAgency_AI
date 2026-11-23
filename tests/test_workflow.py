"""
Test script for Rate Refresh Workflow.
"""
from workflow.rate_refresh import RateRefreshWorkflow
from database.hotel_management import HotelManager
from email_handler.outlook_reader import OutlookReader
from email_handler.outlook_sender import OutlookSender
import sqlite3
from config import DB_PATH

def test_workflow():
    print("🔄 Testing Rate Refresh Workflow...")
    
    # 1. Setup Data - add a "Stale" hotel
    print("   Seeding database with test hotel...")
    manager = HotelManager()
    manager.add_hotel(
        name="Test Hotel Workflow",
        email="test-hotel@example.com",  # Reserved test domain: never a real inbox
        contact_person="Test Manager"
    )
    
    # Manually ensure it's stale (this is default for new entries with NULL last_contact)
    # But let's verify
    stale = manager.get_stale_hotels()
    found = any(h['name'] == "Test Hotel Workflow" for h in stale)
    print(f"   Hotel found in stale list: {found}")
    
    if not found:
        print("❌ Setup failed: Hotel not found in stale list.")
        return

    # 2. Setup Sender
    print("   Authenticating...")
    reader = OutlookReader()
    if not reader.authenticate():
        print("❌ Authentication failed. Cannot test live draft creation.")
        return
        
    sender = OutlookSender(reader.access_token)
    workflow = RateRefreshWorkflow(sender)
    
    # 3. Run Workflow
    print("   Running workflow (Live Draft Creation)...")
    workflow.run(days_threshold=30, dry_run=False)
    
    # 4. Verify Update
    print("   Verifying status update...")
    stale_after = manager.get_stale_hotels()
    found_after = any(h['name'] == "Test Hotel Workflow" for h in stale_after)
    
    if not found_after:
        print("✅ Success! Hotel removed from stale list (last_contact updated).")
        print("   Check Outlook drafts for: 'Rate Request - Test Hotel Workflow'")
    else:
        print("❌ Failure: Hotel still in stale list.")

if __name__ == "__main__":
    test_workflow()
