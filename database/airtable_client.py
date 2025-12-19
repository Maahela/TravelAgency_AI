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
        self.processing_log_table = self.api.table(self.base_id, "Processing_Logs")
        self.contacts_table = self.api.table(self.base_id, "HotelContacts")
        self.price_items_table = self.api.table(self.base_id, "Price_Items")
        self.contract_data_table = self.api.table(self.base_id, "ContractData")
        
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
                    # Return as string since Airtable numeric field is rejecting floats currently
                    return s 
                except:
                    return None

            # Helper to sanitize date (basic check)
            def clean_date(val):
                if not val or str(val).strip() == "":
                    return None
                
                val_str = str(val).strip()
                # If it's already YYYY-MM-DD, return as is
                import re
                if re.match(r'^\d{4}-\d{2}-\d{2}$', val_str):
                    return val_str
                    
                # Handle DD.MM.YYYY (from our SQLite)
                if re.match(r'^\d{2}\.\d{2}\.\d{4}$', val_str):
                    parts = val_str.split('.')
                    return f"{parts[2]}-{parts[1]}-{parts[0]}"
                    
                # Handle DD/MM/YYYY
                if re.match(r'^\d{2}/\d{2}/\d{4}$', val_str):
                    parts = val_str.split('/')
                    return f"{parts[2]}-{parts[1]}-{parts[0]}"

                # Attempt generic parsing if dateutil is available
                try:
                    from dateutil import parser
                    dt = parser.parse(val_str)
                    return dt.strftime("%Y-%m-%d")
                except:
                    return None

            # Map currency symbols to codes for singleSelect
            currency = rate_data.get('currency', 'USD')
            if currency == '$': currency = 'USD'

            # Map Python dict keys to Airtable column names
            record = {
               "Hotel Name": rate_data.get('hotel_name'),
               "Room Type": rate_data.get('room_type'),
               "Occupancy": rate_data.get('occupancy'),  # New field
               "Meal Plan": rate_data.get('meal_plan'),
               "Price": clean_price(rate_data.get('price', rate_data.get('rate_per_night'))),
               "Currency": currency,
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
            import traceback
            error_details = getattr(e, 'response', None)
            if error_details:
                 logger.error(f"Airtable API Error Body: {error_details.text}")
            
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

    def log_hotel_contact(self, hotel_name: str, email: str, source: str = "Email Parsing", confidence: float = 1.0) -> bool:
        """
        Log or update a hotel contact email in Airtable.
        """
        if not self.is_connected():
            return False
            
        try:
            # Check if contact already exists
            formula = f"AND({{Hotel Name}}='{hotel_name}', {{Email}}='{email}')"
            existing = self.contacts_table.all(formula=formula)
            
            record = {
                "Hotel Name": hotel_name,
                "Email": email,
                "Discovery Source": source,
                "Confidence": confidence
            }
            
            if existing:
                # Update existing
                self.contacts_table.update(existing[0]['id'], record)
            else:
                # Create new
                self.contacts_table.create(record)
                
            return True
        except Exception as e:
            logger.error(f"Failed to log hotel contact: {e}")
            return False

    def insert_price_item(self, item_data: Dict) -> bool:
        """
        Insert a granular price item into Airtable.
        """
        if not self.is_connected():
            return False
            
        try:
            # Map currency symbols to codes for singleSelect
            currency = item_data.get('currency', 'USD')
            if currency == '$': currency = 'USD'
            
            # Map categories to allowed choices
            allowed_categories = [
                "meal_rate", "meal_plan_supplement", "extra_person_charge",
                "extra_bed_charge", "child_rate", "deduction",
                "package_price", "upgrade_price", "offer_discount",
                "cancellation_fee", "policy_fee", "other_charge"
            ]
            category = item_data.get('category', 'other_charge')
            if category not in allowed_categories:
                category = 'other_charge'

            record = {
                "Hotel Name": item_data.get('hotel_name'),
                "Category": category,
                "Description": item_data.get('description'),
                "Price": item_data.get('price'),
                "Currency": currency,
                "Per Unit": item_data.get('per_unit'),
                "Adult or Child": item_data.get('adult_or_child'),
                "Age Range": item_data.get('age_range'),
                "Applicable Room Types": item_data.get('applicable_room_types'),
                "Applicable Dates": item_data.get('applicable_dates'),
                "Meal Type": item_data.get('meal_type'),
                "Conditions": item_data.get('conditions'),
                "Source Text": item_data.get('source_text_snippet') or item_data.get('source_text'),
                "Source File": item_data.get('source_file')
            }
            # Stringify everything to avoid field type errors in singleLineText
            record = {k: str(v) if v is not None else None for k, v in record.items()}
            # Remove None
            record = {k: v for k, v in record.items() if v is not None}
            
            self.price_items_table.create(record)
            return True
        except Exception as e:
            logger.error(f"Failed to insert price item: {e}")
            return False

    def insert_contract_data(self, contract: Dict) -> bool:
        """
        Insert raw contract JSON data into Airtable.
        """
        if not self.is_connected():
            return False
            
        try:
            record = {
                "Hotel Name": contract.get('hotel_name'),
                "Source File": contract.get('source_file'),
                "Raw JSON": contract.get('raw_json'),
                "Extracted At": self._clean_date(contract.get('extracted_at'))
            }
            # Clean record
            record = {k: v for k, v in record.items() if v is not None}
            self.contract_data_table.create(record)
            return True
        except Exception as e:
            logger.error(f"Failed to insert contract data: {e}")
            return False

    def _clean_date(self, date_str):
        """Internal helper for date cleaning."""
        if not date_str: return None
        from datetime import datetime
        try:
            # Handle various formats
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    return datetime.strptime(str(date_str).split('.')[0], fmt).strftime("%Y-%m-%d")
                except:
                    continue
            return None
        except:
            return None
