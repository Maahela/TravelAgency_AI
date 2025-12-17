"""
Test script for Email Generation and Outlook Draft Creation.
"""
from email_handler.outlook_sender import OutlookSender
from email_handler.outlook_reader import OutlookReader
import json
import os

def test_email_generation():
    print("📧 Testing AI Email Generation...")
    
    sender = OutlookSender() # No token needed for generation mock
    
    request_details = "Rates for Winter 2025/2026 Season, specifically looking for Deluxe Rooms and Suites on HB basis."
    hotel_name = "Hotel Topaz Kandy"
    hotel_email = "reservations@hoteltopaz.com"
    
    # 1. Generate Content
    print(f"\n   Generating request for {hotel_name}...")
    email_content = sender.generate_rate_request_email(hotel_name, hotel_email, request_details)
    
    print("\n   ✅ Generated Content:")
    print(f"   Subject: {email_content.get('subject')}")
    print(f"   Body Preview: {email_content.get('body')[:200]}...")
    
    # 2. Test Draft Creation (Requires Auth)
    # We will try to auth using the Reader's auth flow which saves token
    print("\n📬 Testing Draft Creation (Live)...")
    
    reader = OutlookReader()
    if reader.authenticate():
        print("   ✅ Authenticated with Graph API.")
        # Pass the token to the sender
        sender = OutlookSender(access_token=reader.access_token)
        
        draft_id = sender.create_draft_email(
            to_recipients=[hotel_email],
            subject=email_content['subject'],
            body=email_content['body']
        )
        
        if draft_id:
            print(f"   ✅ Draft created successfully! ID: {draft_id}")
            print("   Please check your Outlook 'Drafts' folder.")
        else:
            print("   ❌ Failed to create draft.")
    else:
        print("   ⚠️  Skipping live draft test (Authentication failed or skipped).")

if __name__ == "__main__":
    test_email_generation()
