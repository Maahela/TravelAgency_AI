"""
Airtable Client forJAKEmailBot.
Handles connection and CRUD operations for the Airtable backend.
"""
import os
from typing import Dict, List, Optional
from pyairtable import Api
from dotenv import load_dotenv
from utils.logger import get_logger

logger = get_logger(__name__)

# Load env in case it's not loaded
load_dotenv()

class AirtableClient:
    """
    Wrapper for Airtable API operations.
    Singleton pattern to reuse connection.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AirtableClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.api_key = os.getenv("AIRTABLE_API_KEY")
        self.base_id = os.getenv("AIRTABLE_BASE_ID")
        
        if not self.api_key or not self.base_id:
            logger.warning("Airtable credentials missing. Airtable functionality will be disabled.")
            self.api = None
            return
            
        self.api = Api(self.api_key)
        self.rates_table = self.api.table(self.base_id, "Rates")
        self.hotels_table = self.api.table(self.base_id, "Hotels")
        self.processing_log_table = self.api.table(self.base_id, "ProcessingLog")
        
        self._initialized = True
        logger.info("AirtableClient initialized successfully")

    def is_connected(self) -> bool:
        """Check if Airtable connection is valid."""
        return self.api is not None

    def insert_rate(self, rate_data: Dict) -> bool:
        """
        Insert a single rate record into Airtable.
        """
        if not self.is_connected():
            return False
            
        try:
            # Helper to sanitize price
            def clean_price(val):
                if not val: return None
                try:
                    # Remove currency symbols and commas
                    s = str(val).replace('$', '').replace(',', '').strip()
                    return float(s)
                except:
                    return None

            # Helper to sanitize date (basic check)
            def clean_date(val):
                if not val or str(val).strip() == "":
                    return None
                # Airtable strictly needs YYYY-MM-DD. 
                # If our DB has other formats, we might need parsing.
                # For now, just pass non-empty, assuming ISO from scraper.
                return val

            # Map Python dict keys to Airtable column names
            record = {
               "Hotel Name": rate_data.get('hotel_name'),
               "Room Type": rate_data.get('room_type'),
               "Meal Plan": rate_data.get('meal_plan'),
               "Price": clean_price(rate_data.get('price', rate_data.get('rate_per_night'))),
               "Currency": rate_data.get('currency'),
               "Season Start": clean_date(rate_data.get('season_start_date')),
               "Season End": clean_date(rate_data.get('season_end_date')),
               "Source File": rate_data.get('source_file'),
               "Confidence": rate_data.get('confidence', 1.0)
            }
            
            # Remove None values to avoid API errors (or let Airtable handle empty)
            record = {k: v for k, v in record.items() if v is not None}
            
            self.rates_table.create(record)
            logger.info(f"Inserted rate for {rate_data.get('hotel_name')} to Airtable")
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert rate to Airtable: {e}")
            logger.error(f"Payload was: {record}")
            return False

    def log_processing(self, email_id: str, filename: str, status: str, error: str = None):
        """Log file processing status."""
        if not self.is_connected():
            return
        
        try:
            self.processing_log_table.create({
                "Email ID": email_id,
                "Filename": filename,
                "Status": status,
                "Error Message": error or ""
            })
        except Exception as e:
            logger.error(f"Failed to log to Airtable: {e}")
