"""
Workflow for automating rate refresh campaigns.
Identifies hotels with stale rates and generates draft email requests.
"""
from typing import List, Dict
from database.hotel_management import HotelManager
from email_handler.outlook_sender import OutlookSender
from utils.logger import get_logger

logger = get_logger(__name__)

class RateRefreshWorkflow:
    def __init__(self, outlook_sender: OutlookSender):
        self.hotel_manager = HotelManager()
        self.sender = outlook_sender

    def run(self, days_threshold: int = 30, dry_run: bool = False):
        """
        Execute the rate refresh campaign.
        
        Args:
            days_threshold: Days since last contact to consider "stale"
            dry_run: If True, does not create actual drafts, just logs.
        """
        logger.info(f"Starting Rate Refresh Campaign (Threshold: {days_threshold} days)")
        
        stale_hotels = self.hotel_manager.get_stale_hotels(days_threshold)
        
        if not stale_hotels:
            logger.info("No stale hotels found. Campaign complete.")
            return

        logger.info(f"Found {len(stale_hotels)} hotels needing rate refresh.")
        
        for hotel in stale_hotels:
            self._process_hotel(hotel, dry_run)

    def _process_hotel(self, hotel: Dict, dry_run: bool):
        """Generate and stage a request for a single hotel."""
        name = hotel['name']
        email = hotel['email_address']
        hotel_id = hotel['id']
        
        if not email:
            logger.warning(f"Skipping {name}: No email address listed.")
            return

        logger.info(f"Processing {name} ({email})...")
        
        # 1. Generate Email Content
        request_details = "Updated contract rates for upcoming seasons."
        # Using the sender's helper which calls the LLM
        email_content = self.sender.generate_rate_request_email(name, email, request_details)
        
        if dry_run:
            logger.info(f"[DRY RUN] Would create draft to {email}: {email_content['subject']}")
            return

        # 2. Create Draft
        draft_id = self.sender.create_draft_email(
            to_recipients=[email],
            subject=email_content['subject'],
            body=email_content['body']
        )
        
        if draft_id:
            logger.info(f"Draft created for {name} (ID: {draft_id})")
            # 3. Update Last Contact Date
            self.hotel_manager.update_last_contact(hotel_id)
        else:
            logger.error(f"Failed to create draft for {name}")
