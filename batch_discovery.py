"""
Batch Hotel Discovery with Manual Review Workflow

Usage:
1. Edit the HOTELS_TO_DISCOVER list below
2. Run: python batch_discovery.py
3. Review the results (auto-discovered emails + blocked URLs for manual check)
4. Approve or reject each hotel's emails
5. Approved emails are saved to database
"""

from workflow.hotel_discovery_agent import HotelDiscoveryAgent
from database.hotel_management import HotelManager
import json

# ===== EDIT THIS LIST =====
HOTELS_TO_DISCOVER = [
    {"name": "Marino Beach Colombo", "city": "Colombo", "country": "Sri Lanka"},
    {"name": "Cinnamon Lakeside Colombo", "city": "Colombo", "country": "Sri Lanka"},
    {"name": "Granbell Hotel Colombo", "city": "Colombo", "country": "Sri Lanka"},
    {"name": "Courtyard by Marriott Colombo", "city": "Colombo", "country": "Sri Lanka"},
    {"name": "Mandarina Colombo", "city": "Colombo", "country": "Sri Lanka"},
]

def run_batch_discovery():
    """
    Run discovery for all hotels and present results for review.
    """
    agent = HotelDiscoveryAgent()
    results = []
    
    print("\n" + "="*80)
    print("BATCH HOTEL DISCOVERY - Starting...")
    print("="*80 + "\n")
    
    for hotel in HOTELS_TO_DISCOVER:
        print(f"\n🔍 Discovering: {hotel['name']}")
        print("-" * 60)
        
        result = agent.run(hotel['name'], hotel.get('city', ''), hotel.get('country', ''))
        results.append(result)
        
        # Display immediate results
        if result['emails']:
            print(f"✅ Found {len(result['emails'])} email(s):")
            for email in result['emails']:
                print(f"   • {email['email']} ({email['purpose']}, confidence: {email['confidence']})")
        else:
            print(f"❌ No emails found")
        
        if result.get('blocked_urls'):
            print(f"\n⚠️  {len(result['blocked_urls'])} site(s) blocked (403 Forbidden):")
            for url in result['blocked_urls']:
                print(f"   🔗 {url}")
            print(f"   → Please check these sites manually and use manual_email_entry.py")
    
    print("\n" + "="*80)
    print("DISCOVERY COMPLETE - Review Results")
    print("="*80 + "\n")
    
    # Save results to JSON for review
    with open('discovery_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("📄 Full results saved to: discovery_results.json")
    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("="*80)
    print("1. Review discovery_results.json")
    print("2. For blocked sites, visit URLs manually and extract emails")
    print("3. Use manual_email_entry.py to add emails you found manually")
    print("4. Emails from successful discoveries are already in the database!")
    print("\n")

if __name__ == "__main__":
    run_batch_discovery()
