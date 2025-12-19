
"""
Rate Refresh Service for JAKEmailBot.
Identifies expiring rates in Airtable and auto-drafts extension requests.
"""
import os
import datetime
from typing import List, Dict
from database.airtable_client import AirtableClient
from database.hotel_management import HotelManager
from email_handler.outlook_sender import OutlookSender
from email_handler.outlook_reader import OutlookReader
from utils.logger import get_logger

logger = get_logger(__name__)

class RateRefreshService:
    def __init__(self, expiry_days: int = 60):
        self.airtable = AirtableClient()
        self.manager = HotelManager()
        self.expiry_days = expiry_days
        
    def get_expiring_hotels(self) -> List[Dict]:
        """
        Identify hotels with at least one rate expiring within 'expiry_days'.
        Returns list of dicts: {'hotel_name': str, 'expiry_date': str}
        """
        if not self.airtable.is_connected():
            logger.error("Airtable not connected")
            return []
            
        today = datetime.date.today()
        threshold = today + datetime.timedelta(days=self.expiry_days)
        
        # Fetch all rates
        # Formula: IS_BEFORE({Season End}, 'YYYY-MM-DD')
        # Note: IS_BEFORE is strict, filter manually for safety or refine formula
        records = self.airtable.rates_table.all()
        
        expiring_hotels = {}
        
        for rec in records:
            fields = rec.get('fields', {})
            hotel = fields.get('Hotel Name')
            end_date_str = fields.get('Season End')
            
            if hotel and end_date_str:
                try:
                    end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()
                    if today <= end_date <= threshold:
                        if hotel not in expiring_hotels or end_date < expiring_hotels[hotel]:
                            expiring_hotels[hotel] = end_date
                except Exception as e:
                    continue
                    
        return [{"hotel_name": name, "expiry_date": date.strftime("%Y-%m-%d")} 
                for name, date in expiring_hotels.items()]

    def run_refresh_cycle(self, limit: int = 5) -> int:
        """
        Run a cycle to draft emails for expiring contracts.
        """
        hotels = self.get_expiring_hotels()
        if not hotels:
            logger.info("No expiring rates found.")
            return 0
            
        logger.info(f"Found {len(hotels)} hotels with expiring rates. Processing top {limit}...")
        
        # Auth for Outlook
        reader = OutlookReader()
        if not reader.authenticate():
            logger.error("Auth failed for Outlook")
            return 0
            
        sender = OutlookSender(access_token=reader.access_token)
        count = 0
        
        for h in hotels[:limit]:
            hotel_name = h['hotel_name']
            emails = self.manager.get_hotel_emails(hotel_name)
            
            # Prioritize reservations/sales
            target_email = None
            for p in ['reservations', 'sales', 'general']:
                if p in emails:
                    target_email = emails[p]
                    break
            
            if not target_email and emails:
                target_email = list(emails.values())[0]
                
            if not target_email:
                logger.warning(f"No contact found for {hotel_name}. Skipping refresh draft.")
                continue
                
            # Generate content
            details = {'season': 'the upcoming seasons (Winter 2025/2026)'}
            draft_content = sender.generate_rate_request_email(hotel_name, target_email, details)
            
            # Add a specific note about the expiry
            draft_content['body'] = draft_content['body'].replace(
                "Dear Reservations / Sales Team,",
                f"Dear Reservations / Sales Team,<br><br>We noticed our current contracted rates for <strong>{hotel_name}</strong> are set to expire on {h['expiry_date']}."
            )
            
            result = sender.create_draft_email(
                to_recipients=[target_email],
                subject=f"Rate Extension Request: {hotel_name} (Expiring {h['expiry_date']})",
                body=draft_content['body']
            )
            
            if result:
                logger.info(f"Draft created for {hotel_name} at {target_email}")
                count += 1
            else:
                logger.error(f"Failed to create draft for {hotel_name}")
                
        return count

if __name__ == "__main__":
    service = RateRefreshService()
    service.run_refresh_cycle()
