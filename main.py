"""
Main entry point for the Email Automation System.
Orchestrates the complete workflow from email reading to data storage.
"""

import sys
from pathlib import Path
from utils.logger import get_logger
from utils.file_storage import save_attachment, get_file_type
from email_handler.outlook_reader import OutlookReader
from email_handler.notifications import NotificationService
from extractor.pdf_text_extractor import PDFTextExtractor
from extractor.image_ocr_extractor import ImageOCRExtractor
from extractor.rate_parser import RateParser
from database.db_init import initialize_database
from database.insert_rates import insert_rate, log_processing_status
from config import DB_PATH
from datetime import datetime

logger = get_logger(__name__)


def process_email_workflow():
    """
    Main workflow for processing incoming emails.
    
    Workflow Steps:
    1. Authenticate with Microsoft Graph
    2. Check for new emails
    3. Download attachments
    4. Detect file type (PDF / image)
    5. Extract text
    6. Send text to LLM for parsing
    7. Validate parsed data
    8. Save valid data to database
    9. Flag errors for manual review
    10. Log all steps
    
    TODO:
        - Implement complete workflow
        - Add error recovery mechanisms
        - Implement scheduling (run every N minutes)
        - Add dry-run mode for testing
        - Implement parallel processing for multiple emails
    """
    logger.info("=" * 60)
    logger.info("Starting Email Automation Workflow")
    logger.info("=" * 60)
    
    # Initialize components
    notification_service = NotificationService()
    outlook_reader = OutlookReader()
    pdf_extractor = PDFTextExtractor()
    ocr_extractor = ImageOCRExtractor()
    rate_parser = RateParser()
    
    # Step 1: Initialize database
    logger.info("Step 1: Initializing database")
    if not initialize_database(DB_PATH):
        logger.error("Failed to initialize database. Exiting.")
        return
    
    # Step 2: Authenticate with Microsoft Graph
    logger.info("Step 2: Authenticating with Microsoft Graph API")
    if not outlook_reader.authenticate():
        logger.error("Authentication failed. Please check credentials.")
        notification_service.notify_manual_review_needed(
            'authentication',
            'Failed to authenticate with Microsoft Graph',
            {}
        )
        return
    
    # Step 3: Fetch new emails
    logger.info("Step 3: Fetching unread emails")
    emails = outlook_reader.get_unread_emails(limit=10)
    
    if not emails:
        logger.info("No new emails to process")
        return
    
    logger.info(f"Found {len(emails)} new email(s)")
    
    # Step 4-10: Process each email
    for email in emails:
        process_single_email(
            email,
            outlook_reader,
            pdf_extractor,
            ocr_extractor,
            rate_parser,
            notification_service
        )
    
    logger.info("=" * 60)
    logger.info("Workflow completed")
    logger.info("=" * 60)


def process_single_email(
    email: dict,
    outlook_reader: OutlookReader,
    pdf_extractor: PDFTextExtractor,
    ocr_extractor: ImageOCRExtractor,
    rate_parser: RateParser,
    notification_service: NotificationService
):
    """
    Process a single email and its attachments.
    
    Args:
        email: Email metadata dictionary
        outlook_reader: OutlookReader instance
        pdf_extractor: PDFTextExtractor instance
        ocr_extractor: ImageOCRExtractor instance
        rate_parser: RateParser instance
        notification_service: NotificationService instance
    
    TODO:
        - Implement complete processing logic
        - Add transaction support (rollback on failure)
        - Implement retry logic
    """
    email_id = email.get('id')
    subject = email.get('subject', 'No Subject')
    sender = email.get('from', 'Unknown')
    
    logger.info(f"Processing email: '{subject}' from {sender}")
    
    # Notify about new email
    notification_service.notify_new_email(
        subject,
        sender,
        email.get('attachment_count', 0)
    )

    # --- Feature: Auto-Capture Contact ---
    try:
        from database.airtable_client import AirtableClient
        airtable = AirtableClient()
        if airtable.is_connected():
             # We use the sender's name if we can infer it, or just use the email as name initially
             # Ideally we'd extract the name from "From: Name <email>", but 'sender' here is likely just the address
             # based on outlook_reader implementation. 
             # Let's check outlook_reader again if 'sender' is address or full string.
             # Actually, logged as 'sender' is email address.
             # We can try to guess a hotel name from subject or just leave it as "Unknown (Auto-Captured)"
             airtable.log_hotel_contact(
                 hotel_name="Unknown (Auto-Captured)", 
                 email=sender,
                 source="Email Manifest",
                 confidence=1.0
             )
             logger.info(f"Auto-captured contact: {sender}")
    except Exception as e:
        logger.warning(f"Failed to auto-capture contact: {e}")
    # -------------------------------------
    
    # Get attachments
    attachments = outlook_reader.get_email_attachments(email_id)
    
    # Process attachments if they exist
    if attachments:
        logger.info(f"Processing {len(attachments)} attachment(s)")
        for attachment in attachments:
            process_attachment(
                attachment,
                email_id,
                pdf_extractor,
                ocr_extractor,
                rate_parser,
                notification_service
            )
    else:
        logger.info("No attachments found")
    
    # ALSO process email body if it has substantial text
    body = email.get('body', '').strip()
    if body and len(body) > 50:  # Minimum threshold
        logger.info(f"Processing email body text ({len(body)} chars)")
        try:
            # Parse rates from body text directly
            rates = rate_parser.parse_rate_data(body, f"EmailBody_{subject[:30]}")
            
            if rates:
                from database.insert_rates import insert_rate
                from config import DB_PATH
                
                success_count = 0
                for rate in rates:
                    # Add metadata
                    rate['extracted_at'] = datetime.now().isoformat()
                    rate['confidence'] = 0.85  # Slightly lower than attachment-based
                    
                    # Validate
                    validation = rate_parser.validate_rate_data(rate)
                    if validation['valid']:
                        if insert_rate(rate, DB_PATH):
                            success_count += 1
                    else:
                        logger.warning(f"Invalid rate from body: {validation['errors']}")
                
                logger.info(f"Inserted {success_count}/{len(rates)} rates from email body")
                
                # ALSO extract price items and contract data from body
                hotel_name = rates[0].get('hotel_name', 'Unknown') if rates else 'Unknown'
                
                try:
                    rate_parser.extract_and_store_price_items(
                        body, 
                        f"EmailBody_{subject[:30]}", 
                        hotel_name
                    )
                except Exception as e:
                    logger.warning(f"Failed to extract price items from body: {e}")
                
                try:
                    rate_parser.extract_and_store_contract_data(
                        body,
                        f"EmailBody_{subject[:30]}"
                    )
                except Exception as e:
                    logger.warning(f"Failed to extract contract data from body: {e}")
                    
            else:
                logger.info("No rates found in email body")
        except Exception as e:
            logger.error(f"Failed to process email body: {e}")
    
    # Mark email as processed
    outlook_reader.mark_as_read(email_id)
    logger.info(f"Email '{subject}' processed successfully")


def process_attachment(
    attachment: dict,
    email_id: str,
    pdf_extractor: PDFTextExtractor,
    ocr_extractor: ImageOCRExtractor,
    rate_parser: RateParser,
    notification_service: NotificationService
):
    """
    Process a single attachment.
    
    Args:
        attachment: Attachment metadata dictionary
        email_id: Parent email ID
        pdf_extractor: PDFTextExtractor instance
        ocr_extractor: ImageOCRExtractor instance
        rate_parser: RateParser instance
        notification_service: NotificationService instance
    
    TODO:
        - Implement full processing pipeline
        - Add file validation
        - Handle processing errors gracefully
    """
    filename = attachment.get('name', 'unknown.file')
    logger.info(f"Processing attachment: {filename}")
    
    try:
        # Save attachment to disk
        file_path = save_attachment(
            attachment.get('content_bytes'),
            filename
        )
        
        # Determine file type and extract text
        file_type = get_file_type(file_path)
        extracted_text = ""
        
        if file_type == 'pdf':
            result = pdf_extractor.extract_text(file_path)
            if result['success']:
                extracted_text = result['text']
            else:
                raise Exception(result.get('error', 'PDF extraction failed'))
        
        elif file_type == 'image':
            result = ocr_extractor.extract_text(file_path)
            if result['success']:
                extracted_text = result['text']
            else:
                raise Exception(result.get('error', 'OCR extraction failed'))
        
        else:
            logger.warning(f"Unsupported file type: {file_type}")
            log_processing_status(email_id, filename, 'unsupported_type')
            return
        
        # Parse rate data
        rates = rate_parser.parse_rate_data(extracted_text, filename)
        
        # Validate and insert rates
        for rate in rates:
            validation = rate_parser.validate_rate_data(rate)
            
            if validation['valid']:
                insert_rate(rate, DB_PATH)
                logger.info(f"Inserted rate for {rate['hotel_name']}")
            else:
                logger.warning(f"Invalid rate data: {validation['errors']}")
                notification_service.notify_manual_review_needed(
                    'rate_data',
                    'Validation failed',
                    {'filename': filename, 'errors': validation['errors']}
                )
        
        # --- Deep Extraction (Contract Data & granular Price Items) ---
        if rates:
             # Use the hotel name from the first valid rate as the context
            primary_hotel_name = rates[0].get('hotel_name', 'Unknown')
            
            # 1. Extract Extended Contract Data (Policies, Rules)
            logger.info("Triggering deep contract data extraction...")
            rate_parser.extract_and_store_contract_data(extracted_text, filename)
            
            # 2. Extract Granular Price Items (Meal supplements, gala dinners, etc.)
            logger.info("Triggering granular price item extraction...")
            rate_parser.extract_and_store_price_items(extracted_text, filename, primary_hotel_name)
        # ----------------------------------------------------------------
        
        # Log success
        log_processing_status(email_id, filename, 'success')
        notification_service.notify_attachment_processed(filename, True)
    
    except Exception as e:
        logger.error(f"Failed to process {filename}: {e}")
        log_processing_status(email_id, filename, 'failed', str(e))
        notification_service.notify_extraction_failed(filename, str(e))


if __name__ == "__main__":
    try:
        process_email_workflow()
    except KeyboardInterrupt:
        logger.info("Workflow interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
