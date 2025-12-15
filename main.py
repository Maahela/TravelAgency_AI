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
    
    # Get attachments
    attachments = outlook_reader.get_email_attachments(email_id)
    
    if not attachments:
        logger.info("No attachments to process")
        outlook_reader.mark_as_read(email_id)
        return
    
    # Process each attachment
    for attachment in attachments:
        process_attachment(
            attachment,
            email_id,
            pdf_extractor,
            ocr_extractor,
            rate_parser,
            notification_service
        )
    
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
