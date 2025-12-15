"""
Test script to verify Microsoft Graph authentication.
"""
import sys
import logging
from email_handler.outlook_reader import OutlookReader

# Configure logging to show output in console
logging.basicConfig(level=logging.INFO)

def test_auth():
    print("Testing Microsoft Graph Authentication...")
    reader = OutlookReader()
    
    if reader.authenticate():
        print("\n✅ SUCCESS: Authenticated successfully!")
        print(f"Access Token (truncated): {reader.access_token[:20]}...")
    else:
        print("\n❌ FAILURE: Could not authenticate.")
        print("Please check your .env file credentials.")

if __name__ == "__main__":
    test_auth()
