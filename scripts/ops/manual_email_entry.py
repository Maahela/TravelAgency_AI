import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

"""
Manual Email Entry Tool

Use this to add emails you found manually (e.g., from blocked websites).

Usage:
    python manual_email_entry.py
"""

from database.hotel_management import HotelManager

def add_email_interactive():
    """
    Interactive CLI for adding emails to the database.
    """
    manager = HotelManager()
    
    print("\n" + "="*60)
    print("MANUAL EMAIL ENTRY")
    print("="*60 + "\n")
    
    hotel_name = input("Hotel Name: ").strip()
    if not hotel_name:
        print("❌ Hotel name required")
        return
    
    # Get or create hotel
    hotel_id = manager.get_or_create_hotel(hotel_name)
    print(f"✅ Hotel ID: {hotel_id}")
    
    # Get email details
    email = input("Email Address: ").strip()
    if not email:
        print("❌ Email required")
        return
    
    purpose = input("Purpose (reservations/sales/contracts/general) [default: general]: ").strip() or "general"
    
    confidence_input = input("Confidence (0.0-1.0) [default: 1.0]: ").strip()
    try:
        confidence = float(confidence_input) if confidence_input else 1.0
    except ValueError:
        confidence = 1.0
    
    source = input("Source (official_website/google_maps/manual) [default: manual]: ").strip() or "manual"
    reasoning = input("Reasoning/Notes [optional]: ").strip() or "Manually verified"
    
    # Save to DB
    email_data = {
        "email": email,
        "purpose": purpose,
        "confidence": confidence,
        "reasoning": reasoning
    }
    
    manager.upsert_hotel_email(hotel_id, email_data, source)
    
    print("\n✅ Email added successfully!")
    print(f"   Hotel: {hotel_name}")
    print(f"   Email: {email}")
    print(f"   Purpose: {purpose}")
    print(f"   Confidence: {confidence}")
    
    # Ask if want to add more
    another = input("\nAdd another email for this hotel? (y/n): ").strip().lower()
    if another == 'y':
        add_email_interactive()
    else:
        print("\n👋 Done!\n")

if __name__ == "__main__":
    try:
        add_email_interactive()
    except KeyboardInterrupt:
        print("\n\n👋 Cancelled\n")
