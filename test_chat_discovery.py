"""
Test chat interface with discovery integration
"""
from chat.chat_interface import ChatInterface

def test_chat_discovery():
    chat = ChatInterface()
    
    print("=" * 60)
    print("Testing Chat Discovery Integration")
    print("=" * 60)
    
    # Test 1: Find email for Taj Samudra
    print("\n\n1. Query: Find email for Taj Samudra")
    print("-" * 60)
    response = chat.query("Find email for Taj Samudra")
    print(response)
    
    # Test 2: Granbell
    print("\n\n2. Query: Get contact for Granbell Hotel Colombo")
    print("-" * 60)
    response = chat.query("Get contact for Granbell Hotel Colombo")
    print(response)
    
    # Test 3: Regular query (non-discovery)
    print("\n\n3. Query: What are the rates for Hilton?")
    print("-" * 60)
    response = chat.query("What are the rates for Hilton?")
    print(response)

if __name__ == "__main__":
    test_chat_discovery()
