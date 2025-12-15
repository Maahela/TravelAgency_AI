"""
Script to list all valid users in the Azure Tenant.
This helps identify which email addresses the bot allows access to.
"""
import requests
import json
from msal import ConfidentialClientApplication
from config import AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID, GRAPH_SCOPES

def debug_tenant_users():
    print("Debug: Listing Tenant Users...")
    
    # 1. Authenticate
    authority = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}"
    app = ConfidentialClientApplication(
        AZURE_CLIENT_ID,
        authority=authority,
        client_credential=AZURE_CLIENT_SECRET,
    )
    result = app.acquire_token_for_client(scopes=GRAPH_SCOPES)
    
    if "access_token" not in result:
        print("❌ Auth Failed. Check Client Secret.")
        return

    token = result['access_token']
    
    # 2. List Users
    endpoint = "https://graph.microsoft.com/v1.0/users"
    headers = {'Authorization': f'Bearer {token}'}
    params = {'$select': 'displayName,userPrincipalName,mail'}
    
    try:
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()
        
        users = response.json().get('value', [])
        
        print(f"\n✅ Success! Found {len(users)} users in this Tenant:")
        print("-" * 60)
        print(f"{'Name':<30} | {'Email (UPN)':<40}")
        print("-" * 60)
        
        for user in users:
            name = user.get('displayName', 'N/A')
            email = user.get('userPrincipalName', 'N/A')
            print(f"{name:<30} | {email:<40}")
            
        print("-" * 60)
        print("\nℹ️  The bot can ONLY read emails for the accounts listed above.")
        print("   Personal emails (@outlook.com) will NOT work unless listed here as a member.")
        
    except Exception as e:
        print(f"\n❌ API Call Failed: {e}")
        if response.status_code == 401:
            print("   Reason: 401 Unauthorized. Admin Consent might not be fully active yet.")

if __name__ == "__main__":
    debug_tenant_users()
