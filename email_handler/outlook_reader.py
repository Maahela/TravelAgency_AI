"""
Outlook email reader using Microsoft Graph API.
Handles authentication and reading emails from Outlook mailbox.
"""

from typing import List, Dict, Optional
from msal import ConfidentialClientApplication
from utils.logger import get_logger

logger = get_logger(__name__)


class OutlookReader:
    """
    Handles reading emails from Microsoft Outlook using Graph API.
    """
    
    def __init__(self):
        """
        Initialize Outlook reader with Graph API credentials.
        
        TODO:
            - Implement proper authentication flow
            - Add token caching
            - Support for different authentication methods (device code, interactive)
        """
        from config import AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID, GRAPH_SCOPES, OUTLOOK_EMAIL
        
        self.client_id = AZURE_CLIENT_ID
        self.client_secret = AZURE_CLIENT_SECRET
        self.tenant_id = AZURE_TENANT_ID
        self.scopes = GRAPH_SCOPES
        self.target_email = OUTLOOK_EMAIL
        self.access_token = None
        
        logger.info(f"OutlookReader initialized for target: {self.target_email}")
    
    def authenticate(self) -> bool:
        """
        Authenticate with Microsoft Graph API using Device Code Flow.
        Allows personal accounts to log in interactively.
        """
        try:
            # Token cache setup could be added here for persistence
            
            # Using 'common' authority is REQUIRED for personal Microsoft accounts
            # AND for multi-tenant apps. Since we enabled "AzureADandPersonalMicrosoftAccount",
            # we must use 'common' (or 'consumers').
            authority = "https://login.microsoftonline.com/common"
            
            # Note: For Device Code Flow, we treat it as a Public Client
            from msal import PublicClientApplication
            app_public = PublicClientApplication(
                self.client_id,
                authority=authority
            )
            
            result = None
            accounts = app_public.get_accounts()
            if accounts:
                result = app_public.acquire_token_silent(self.scopes, account=accounts[0])
            
            if not result:
                # 2. Initiate Device Flow
                flow = app_public.initiate_device_flow(scopes=self.scopes)
                if "user_code" not in flow:
                    logger.error(f"Failed to create device flow: {flow.get('error')}")
                    return False
                
                print("\n" + "="*60)
                print("ACTION REQUIRED: Authentication Needed")
                print("1. Open this URL: " + flow['verification_uri'])
                print("2. Enter this code: " + flow['user_code'])
                print("="*60 + "\n")
                
                result = app_public.acquire_token_by_device_flow(flow)
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                granted_scopes = result.get("scope", "unknown")
                logger.info(f"Successfully authenticated with Microsoft Graph")
                logger.info(f"Granted Scopes: {granted_scopes}")
                
                # Update target_email to match the signed-in user if possible
                if 'id_token_claims' in result:
                    user_email = result['id_token_claims'].get('preferred_username')
                    if user_email:
                         logger.info(f"Signed in as: {user_email}")
                         
                return True
            else:
                logger.error(f"Authentication failed. Error: {result.get('error')}")
                logger.error(f"Description: {result.get('error_description')}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication exception: {e}")
            return False
                
        except Exception as e:
            logger.error(f"Authentication exception: {e}")
            return False
    
    def get_unread_emails(self, folder_id: str = "inbox", limit: int = 10) -> List[Dict]:
        """
        Fetch unread emails from specified folder.
        """
        import requests
        import urllib.parse
        
        if not self.access_token:
            logger.error("Not authenticated. Cannot fetch emails.")
            return []
            
        logger.info(f"Fetching last {limit} unread emails from {folder_id}")
        
        endpoint = f"https://graph.microsoft.com/v1.0/me/mailFolders/{folder_id}/messages"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Prefer': 'outlook.body-content-type="text"'
        }
        
        params = {
            '$filter': 'isRead eq false',
            '$top': str(limit),
            '$select': 'id,subject,from,receivedDateTime,hasAttachments,body',
            '$orderby': 'receivedDateTime desc'
        }
        
        try:
            response = requests.get(endpoint, headers=headers, params=params)
            
            if response.status_code != 200:
                logger.error(f"API Error {response.status_code}: {response.text}")
                
            response.raise_for_status()
            
            data = response.json()
            emails = []
            
            for msg in data.get('value', []):
                emails.append({
                    'id': msg['id'],
                    'subject': msg.get('subject', 'No Subject'),
                    'from': msg.get('from', {}).get('emailAddress', {}).get('address', 'Unknown'),
                    'received_datetime': msg.get('receivedDateTime'),
                    'body': msg.get('body', {}).get('content', ''),
                    'has_attachments': msg.get('hasAttachments', False),
                    'attachment_count': 0 # Will be populated if attachments are fetched
                })
                
            return emails
            
        except Exception as e:
            logger.error(f"Failed to fetch emails: {e}")
            return []
    
    def get_email_attachments(self, email_id: str) -> List[Dict]:
        """
        Retrieve attachments from a specific email.
        """
        import requests
        import base64
        import urllib.parse
        
        if not self.access_token:
            return []
            
        endpoint = f"https://graph.microsoft.com/v1.0/me/messages/{email_id}/attachments"
        headers = {'Authorization': f'Bearer {self.access_token}'}
        
        try:
            response = requests.get(endpoint, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            attachments = []
            
            for item in data.get('value', []):
                # We only care about file attachments for now
                if item.get('@odata.type') == '#microsoft.graph.fileAttachment':
                    attachments.append({
                        'id': item['id'],
                        'name': item.get('name', 'unknown'),
                        'content_type': item.get('contentType', ''),
                        'size': item.get('size', 0),
                        'content_bytes': base64.b64decode(item.get('contentBytes', ''))
                    })
            
            return attachments
            
        except Exception as e:
            logger.error(f"Failed to fetch attachments for {email_id}: {e}")
            return []
    
    def mark_as_read(self, email_id: str) -> bool:
        """
        Mark an email as read.
        """
        import requests
        import urllib.parse
        
        if not self.access_token:
            return False
            
        endpoint = f"https://graph.microsoft.com/v1.0/me/messages/{email_id}"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {'isRead': True}
        
        try:
            response = requests.patch(endpoint, headers=headers, json=payload)
            response.raise_for_status()
            logger.info(f"Marked email {email_id} as read")
            return True
        except Exception as e:
            logger.error(f"Failed to mark email as read: {e}")
            return False
    
    def move_email(self, email_id: str, destination_folder: str) -> bool:
        """
        Move email to a different folder.
        
        Args:
            email_id: Unique identifier of the email
            destination_folder: Target folder ID or name
        
        Returns:
            True if successful, False otherwise
        
        TODO:
            - Implement Graph API call to move email
            - Add folder validation
            - Support for creating folders if they don't exist
        """
        logger.info(f"TODO: Move email {email_id} to {destination_folder}")
        return False
