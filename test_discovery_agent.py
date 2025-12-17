"""
Test script for Hotel Discovery Agent V2.
"""
from workflow.hotel_discovery_agent import HotelDiscoveryAgent
import json

def test_discovery_v2():
    print("🌍 Testing Hotel Discovery Agent V2...")
    
    agent = HotelDiscoveryAgent()
    
    # Test Case 1: Shangri-La Colombo (Expected Success)
    print("\n\n📍 Running for: Shangri-La Colombo")
    result = agent.run("Shangri-La Colombo", "Colombo", "Sri Lanka")
    print(json.dumps(result, indent=2))
    
    # Test Case 2: Granbell Hotel Colombo (Previously failed, let's see if agent logic helps or if it's just source data)
    print("\n\n📍 Running for: Granbell Hotel Colombo")
    result = agent.run("Granbell Hotel Colombo", "Colombo", "Sri Lanka")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    test_discovery_v2()
