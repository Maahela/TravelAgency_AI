"""
Test save email command in chat
"""
from chat.chat_interface import ChatInterface

chat = ChatInterface()

print("Testing save email command...\n")

# Test saving an email
response = chat.query("save email reservations@gallefacehotel.com for Galle Face Hotel")
print(f"Response: {response}\n")

# Test with purpose keyword
response2 = chat.query("save email sales@shangri-la.com for Shangri-La Colombo for sales")
print(f"Response: {response2}")
