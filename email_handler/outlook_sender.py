"""
Outlook email sender using Microsoft Graph API.
Handles creating and sending draft emails.
"""

from typing import List, Optional, Dict
from utils.logger import get_logger

logger = get_logger(__name__)


class OutlookSender:
    """
    Handles sending emails via Microsoft Outlook using Graph API.
    """
    
    def __init__(self, access_token: Optional[str] = None):
        """
        Initialize Outlook sender with Graph API access token.
        
        Args:
            access_token: Microsoft Graph API access token
        
        TODO:
            - Share authentication with OutlookReader
            - Implement token validation
        """
        self.access_token = access_token
        logger.info("OutlookSender initialized")
    
    def create_draft_email(
        self,
        to_recipients: List[str],
        subject: str,
        body: str,
        cc_recipients: Optional[List[str]] = None,
        attachments: Optional[List[Dict]] = None
    ) -> Optional[str]:
        """
        Create a draft email (does NOT send automatically).
        
        Args:
            to_recipients: List of recipient email addresses
            subject: Email subject
            body: Email body (HTML or plain text)
            cc_recipients: List of CC recipient email addresses
            attachments: List of attachment dicts with 'name' and 'content_bytes'
        
        Returns:
            Draft email ID if successful, None otherwise
        
        TODO:
            - Implement Graph API call to create draft
            - Support HTML email body formatting
            - Handle multiple recipients
            - Add attachment support
            - Support inline images
            - Add template support for common email types
        """
        import requests
        
        if not self.access_token:
            logger.error("Cannot create draft: No access token provided")
            return None
            
        endpoint = "https://graph.microsoft.com/v1.0/me/messages"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Construct recipients list
        to_list = [{'emailAddress': {'address': addr}} for addr in to_recipients]
        cc_list = [{'emailAddress': {'address': addr}} for addr in (cc_recipients or [])]
        
        email_msg = {
            'subject': subject,
            'body': {
                'contentType': 'HTML',
                'content': body
            },
            'toRecipients': to_list,
            'ccRecipients': cc_list
        }
        
        # Add attachments if any
        if attachments:
            # Graph API requires attachments to be base64 encoded strings
            # Assuming 'attachments' is list of {name: str, content_bytes: bytes}
            import base64
            atts_payload = []
            for att in attachments:
                b64_content = base64.b64encode(att['content_bytes']).decode('utf-8')
                atts_payload.append({
                    '@odata.type': '#microsoft.graph.fileAttachment',
                    'name': att['name'],
                    'contentBytes': b64_content
                })
            email_msg['attachments'] = atts_payload
            
        try:
            logger.info(f"Creating draft email to {to_recipients}...")
            response = requests.post(endpoint, headers=headers, json=email_msg)
            response.raise_for_status()
            
            result = response.json()
            draft_id = result.get('id')
            logger.info(f"Draft created successfully. ID: {draft_id}")
            return draft_id
            
        except Exception as e:
            logger.error(f"Failed to create draft email: {e}")
            if 'response' in locals():
                logger.error(f"Response: {response.text}")
            return None
    
    def send_email(
        self,
        to_recipients: List[str],
        subject: str,
        body: str,
        cc_recipients: Optional[List[str]] = None,
        attachments: Optional[List[Dict]] = None
    ) -> bool:
        """
        Send an email directly (bypassing draft).
        
        Args:
            to_recipients: List of recipient email addresses
            subject: Email subject
            body: Email body (HTML or plain text)
            cc_recipients: List of CC recipient email addresses
            attachments: List of attachment dicts
        
        Returns:
            True if sent successfully, False otherwise
        
        NOTE: This is for future use. Current requirement is draft-only.
        
        TODO:
            - Implement Graph API call to send email
            - Add delivery confirmation tracking
            - Implement retry logic for failures
        """
        logger.warning("Direct email sending is not recommended. Use create_draft_email instead.")
        logger.info(f"TODO: Send email to {to_recipients} with subject '{subject}'")
        return False
    
    def generate_rate_request_email(
        self,
        hotel_name: str,
        hotel_email: str,
        requested_details: Dict
    ) -> Dict[str, str]:
        """
        Generate draft email content for hotel rate requests.
        
        Args:
            hotel_name: Name of the hotel
            hotel_email: Hotel contact email
            requested_details: Dictionary with request specifics (dates, room types, etc.)
        
        Returns:
            Dictionary with 'subject' and 'body' keys
        
        TODO:
            - Implement email template with professional formatting
            - Add personalization based on hotel details
            - Support multiple languages
            - Include agency branding/signature
        """
        from llm.llm_client import generate_email_with_llm
        
        logger.info(f"Generating rate request content for {hotel_name}...")
        
        context = {
            'hotel_name': hotel_name,
            'target_email': hotel_email,
            'request_details': requested_details
        }
        
        return generate_email_with_llm('rate_request', context)
    
    def generate_client_quote_email(
        self,
        client_name: str,
        client_email: str,
        rate_data: Dict
    ) -> Dict[str, str]:
        """
        Generate draft email content for client quotes.
        
        Args:
            client_name: Name of the client
            client_email: Client email address
            rate_data: Parsed rate information from database
        
        Returns:
            Dictionary with 'subject' and 'body' keys
        
        TODO:
            - Implement professional quote template
            - Format rate data in readable table/list
            - Add terms and conditions
            - Include booking instructions
            - Add agency contact information
        """
        logger.info(f"TODO: Generate client quote email for {client_name}")
        
        subject = f"Hotel Quote - {rate_data.get('hotel_name', 'Your Request')}"
        body = """
        Dear {client_name},
        
        [TODO: Add professional quote template with rate details]
        
        Best regards,
        [Your Agency Name]
        """
        
        return {
            'subject': subject,
            'body': body
        }
