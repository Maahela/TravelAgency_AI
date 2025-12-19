"""
Test script for verifying chat interface integration with new features.
Simulates sending rate requests and checking emails via the chat bot.
"""
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from chat.chat_interface import ChatInterface

def test_rate_request_command():
    print("\n1. Testing 'Send rate request' command...")
    
    # Mock OutlookSender and DiscoveryAgent to avoid real API calls
    with patch('email_handler.outlook_sender.OutlookSender') as MockSender, \
         patch('email_handler.outlook_reader.OutlookReader') as MockReader, \
         patch('workflow.hotel_discovery_agent.HotelDiscoveryAgent') as MockAgent:
        
        # Setup mocks
        mock_sender_instance = MockSender.return_value
        mock_sender_instance.generate_rate_request_email.return_value = {
            'subject': 'Test Subject', 'body': 'Test Body'
        }
        mock_sender_instance.create_draft_email.return_value = "fake_draft_id_123"
        
        mock_reader_instance = MockReader.return_value
        mock_reader_instance.authenticate.return_value = True
        mock_reader_instance.access_token = "fake_token"
        
        chat = ChatInterface()
        
        # Test Query
        response = chat.query("Send rate request to Seaside Resort")
        
        print(f"Response: {response}")
        
        # Verify
        if "✅ Rate request draft created" in response and "Seaside Resort" in response:
            print("✓ Success: Chat handled rate request command correctly")
        else:
            print("✗ Failure: Response did not indicate success")
            print(f"Actual response: {response}")

def test_workflow_trigger_command():
    print("\n2. Testing 'Check emails' command...")
    
    # Mock the workflow function to avoid running real processing
    with patch('main.process_email_workflow') as mock_workflow:
        chat = ChatInterface()
        
        # Test Queries
        commands = ["Check for new emails", "Process inbox", "Run workflow"]
        
        for cmd in commands:
            print(f"Testing command: '{cmd}'")
            response = chat.query(cmd)
            
            if "✅ Workflow cycle completed" in response:
                print(f"✓ Success for '{cmd}'")
            else:
                print(f"✗ Failure for '{cmd}': {response}")
        
        # Verify mock was called 3 times
        assert mock_workflow.call_count == 3
        print("✓ Verified workflow function was triggered 3 times")

if __name__ == "__main__":
    print("=== Chat Interface Integration Test ===")
    try:
        test_rate_request_command()
        test_workflow_trigger_command()
        print("\n=== All Tests Passed! ===")
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
