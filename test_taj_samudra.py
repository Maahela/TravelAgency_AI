"""
Test Taj Samudra hotel discovery
"""
from workflow.hotel_discovery_agent import HotelDiscoveryAgent
import json

def test_taj_samudra():
    print("Testing Taj Samudra Hotel Discovery...")
    
    agent = HotelDiscoveryAgent()
    result = agent.run("Taj Samudra", "Colombo", "Sri Lanka")
    
    print("\nResults:")
    print(json.dumps(result, indent=2))
    
    if result["emails"]:
        print(f"\n✅ SUCCESS! Found {len(result['emails'])} email(s)")
        for email_data in result["emails"]:
            print(f"  - {email_data['email']} ({email_data['purpose']}, confidence: {email_data['confidence']})")
    else:
        print("\n❌ No emails found")

if __name__ == "__main__":
    test_taj_samudra()
