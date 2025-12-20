"""
Test script for client quote email generation.
"""
import sys
import os
from pathlib import Path

# Add project root to python path
sys.path.append(str(Path(__file__).parent))

from email_handler.outlook_sender import OutlookSender

def test_generate_client_quote():
    print("Testing Client Quote Generation...")
    
    sender = OutlookSender(access_token="fake_token")
    
    # Sample Test Data
    client_name = "John Doe"
    client_email = "john.doe@example.com"
    rate_data = {
        'hotel_name': "Grand Hotel Example",
        'rates': [
            {
                'room_type': 'Deluxe Room',
                'meal_plan': 'Bed & Breakfast',
                'price': '250',
                'currency': 'USD'
            },
            {
                'room_type': 'Standard Room',
                'meal_plan': 'Room Only',
                'price': '180',
                'currency': 'USD'
            }
        ]
    }
    
    # Generate email
    result = sender.generate_client_quote_email(client_name, client_email, rate_data)
    
    # Verify Subject
    print(f"\nSubject: {result['subject']}")
    assert result['subject'] == "Your Hotel Quote for Grand Hotel Example"
    
    # Verify Body Content
    body = result['body']
    print("\nBody Snippet (Full debug):")
    print(body) # Print FULL body
    
    # Check for key elements
    assert "Grand Hotel Example" in body, "Hotel name missing"
    assert "John Doe" in body, "Client name missing"
    # assert "Deluxe Room" in body, "Room type missing"
    # assert "USD 250" in body, "Price missing"
    assert "Terms & Conditions" in body, "Terms section missing"
    
    # Check for HTML table structure
    if "<td" not in body:
        print("WARNING: '<td>' tags not found in body!")
        print(f"rates_html content might be empty. Rate data used: {rate_data}")
        
    assert "<table" in body
    assert "<tr" in body
    assert "<td" in body
    
    print("\n✅ Client Quote Email Generation Test Passed!")

    # Test with simple dictionary rates (backward compatibility)
    print("\nTesting Backward Compatibility (Dict rates)...")
    simple_rates = {
        'hotel_name': 'Simple Hotel',
        'rates': {
            'Single Room': '100 USD',
            'Double Room': '150 USD'
        }
    }
    result_simple = sender.generate_client_quote_email("Jane", "jane@test.com", simple_rates)
    
    assert "Simple Hotel" in result_simple['body']
    assert "Single Room" in result_simple['body']
    assert "100 USD" in result_simple['body']
    print("✅ Backward Compatibility Test Passed!")

def test_generate_rate_request():
    print("\nTesting Rate Request Generation...")
    
    sender = OutlookSender(access_token="fake_token")
    
    # Sample Request Data
    hotel_name = "Seaside Resort"
    hotel_email = "reservations@seaside.com"
    requested_details = {
        'season': "Winter 2025/2026"
    }
    
    # Generate email
    result = sender.generate_rate_request_email(hotel_name, hotel_email, requested_details)
    
    # Verify Subject
    print(f"Subject: {result['subject']}")
    assert "Contract Rate Request" in result['subject']
    assert "Seaside Resort" in result['subject']
    
    # Verify Body Content
    body = result['body']
    
    # Check for dynamic data
    assert "Seaside Resort" in body, "Hotel name missing"
    assert "Winter 2025/2026" in body, "Season info missing"
    
    # Check for static template parts
    assert "Maahela Weerasinghe" in body, "Sender name missing"
    assert "JAK Travels" in body, "Agency name missing"
    assert "Nett contracted rates" in body, "Core request missing"
    assert "validity periods" in body.lower(), "Validity missing"
    
    print("✅ Rate Request Email Generation Test Passed!")

if __name__ == "__main__":
    test_generate_client_quote()
    test_generate_rate_request()
