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
        """
        logger.info(f"Generating rate request content for {hotel_name}...")
        
        # Extract dynamic details from requested_details
        season_info = requested_details.get('season', 'the relevant season(s)')
        
        # =========================================================================
        # EMAIL TEMPLATE - EDIT HERE to customize the rate request email
        # =========================================================================
        
        email_subject = f"Contract Rate Request - {hotel_name} - JAK Travels"
        
        email_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <div>
                <p>Dear Reservations / Sales Team,</p>
                
                <p>I hope this email finds you well.</p>
                
                <p>My name is <strong>Maahela Weerasinghe</strong>, representing <strong>JAK Travels</strong>. We handle FIT and small group travel and are currently updating our hotel database in preparation for upcoming bookings.</p>
                
                <p>We would like to kindly request your <strong>contracted travel agent rates</strong> for <strong>{hotel_name}</strong> for {season_info}.</p>
                
                <p>If possible, could you please share:</p>
                
                <ul>
                    <li>Nett contracted rates (BB and other meal plans, if applicable)</li>
                    <li>Validity periods and seasonal breakdowns</li>
                    <li>Room categories and maximum occupancies</li>
                    <li>Supplements (HB / FB, extra person, extra bed, child policies)</li>
                    <li>Any special offers or promotions available to agents</li>
                    <li>Blackout dates, minimum stay requirements, and cancellation policies</li>
                </ul>
                
                <p>A <strong>rate sheet or contract document (PDF)</strong> would be ideal.</p>
                
                <p>Our details are below for your reference:</p>
                
                <p>
                    <strong>Agency Name:</strong> JAK Travels<br>
                    <strong>Contact Person:</strong> Maahela Weerasinghe<br>
                    <strong>Phone / WhatsApp:</strong> REDACTED_PHONE<br>
                    <strong>Email:</strong> <a href="mailto:MaahelaWeerasinghe@JAKTravels.onmicrosoft.com">MaahelaWeerasinghe@JAKTravels.onmicrosoft.com</a>
                </p>
                
                <p>We look forward to the possibility of working together and including your property in our itineraries.</p>
                
                <p>Thank you for your time and assistance.</p>
                
                <p>
                    Kind regards,<br>
                    <strong>Maahela Weerasinghe</strong><br>
                    JAK Travels<br>
                    📞 REDACTED_PHONE<br>
                    ✉️ <a href="mailto:MaahelaWeerasinghe@JAKTravels.onmicrosoft.com">MaahelaWeerasinghe@JAKTravels.onmicrosoft.com</a>
                </p>
            </div>
        </body>
        </html>
        """
        # =========================================================================
        
        return {
            'subject': email_subject,
            'body': email_body
        }
    
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
        """
        logger.info(f"Generating client quote email for {client_name}")
        
        hotel_name = rate_data.get('hotel_name', 'Requested Hotel')
        
        # Format rates into an HTML table rows
        # Expecting rate_data['rates'] to be a list of dicts or similar structure
        # If it's a simple dict of 'Room Type': 'Price', handle that too
        rates_html = ""
        rates = rate_data.get('rates', [])
        
        if isinstance(rates, list):
            for rate in rates:
                # Adjust keys based on your actual rate_data structure
                room_type = rate.get('room_type', 'Standard Room')
                meal_plan = rate.get('meal_plan', 'BB')
                price = rate.get('price', 'N/A')
                currency = rate.get('currency', 'USD')
                
                rates_html += f"""
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">{room_type}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">{meal_plan}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">{currency} {price}</td>
                </tr>
                """
        elif isinstance(rates, dict):
             for room_type, price in rates.items():
                rates_html += f"""
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">{room_type}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">-</td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">{price}</td>
                </tr>
                """

        # =========================================================================
        # EMAIL TEMPLATE - EDIT HERE to customize the email sent to clients
        # =========================================================================
        
        email_subject = f"Your Hotel Quote for {hotel_name}"
        
        email_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2c3e50;">Hotel Quote Proposal</h2>
                
                <p>Dear {client_name},</p>
                
                <p>Thank you for your inquiry. We are pleased to provide the following rates for your stay at <strong>{hotel_name}</strong>.</p>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <thead>
                        <tr style="background-color: #f8f9fa; text-align: left;">
                            <th style="padding: 10px; border-bottom: 2px solid #ddd;">Room Type</th>
                            <th style="padding: 10px; border-bottom: 2px solid #ddd;">Meal Plan</th>
                            <th style="padding: 10px; border-bottom: 2px solid #ddd;">Rate</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rates_html}
                    </tbody>
                </table>
                
                <div style="background-color: #f0f7ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h4 style="margin-top: 0; color: #0056b3;">Terms & Conditions:</h4>
                    <ul style="margin-bottom: 0; padding-left: 20px;">
                        <li>Rates are subject to availability at the time of booking.</li>
                        <li>Prices include all applicable taxes and service charges.</li>
                        <li>Cancellation policy needs to be confirmed upon booking.</li>
                    </ul>
                </div>
                
                <p>Please let us know if you would like to proceed with this booking or if you have any questions.</p>
                
                <p style="margin-top: 30px;">
                    Best regards,<br>
                    <strong>JAKEmailBot Reservations Team</strong><br>
                    <a href="mailto:reservations@example.com" style="color: #0056b3;">reservations@example.com</a>
                </p>
            </div>
        </body>
        </html>
        """
        # =========================================================================
        
        return {
            'subject': email_subject,
            'body': email_body
        }
