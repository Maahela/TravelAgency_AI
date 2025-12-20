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
        self.room_types_table = self.api.table(self.base_id, "Room Types")
        self.meal_plans_table = self.api.table(self.base_id, "Meal Plans")
        
        self._initialized = True
        logger.info("AirtableClient initialized successfully")

    def is_connected(self) -> bool:
        """Check if Airtable connection is valid."""
        return self.api is not None

    def get_or_create_hotel(self, hotel_name: str) -> List[str]:
        """
        Check if hotel exists in Hotels table.
        If yes, return [Record ID].
        If no, create and return [Record ID].
        """
        if not self.is_connected() or not hotel_name:
            return []
            
        try:
            # Check if exists
            formula = f"{{Name}}='{hotel_name}'"
            existing = self.hotels_table.all(formula=formula)
            
            if existing:
                return [existing[0]['id']]
            else:
                # Create new
                new_record = self.hotels_table.create({"Name": hotel_name})
                return [new_record['id']]
        except Exception as e:
            logger.error(f"Error in get_or_create_hotel: {e}")
            return []

    def get_or_create_room_type(self, room_type_name: str, hotel_id: str) -> List[str]:
        """
        Get or create a Room Type linked to a specific Hotel.
        Args:
            room_type_name: Name of the room type
            hotel_id: Record ID of the Hotel
        """
        if not self.is_connected() or not room_type_name or not hotel_id:
            return []
            
        try:
            # Check if exists for this hotel
            safe_name = room_type_name.replace("'", "\\'")
            formula = f"AND({{Name}}='{safe_name}', {{Hotel}}='{hotel_id}')"
            
            existing = self.room_types_table.all(formula=formula)
            
            if existing:
                return [existing[0]['id']]
            else:
                # Create new
                record = {
                    "Name": room_type_name,
                    "Hotel": [hotel_id] # Link to hotel
                }
                new_record = self.room_types_table.create(record)
                return [new_record['id']]
        except Exception as e:
            logger.error(f"Error in get_or_create_room_type: {e}")
            return []

    def get_or_create_meal_plan(self, meal_plan_name: str) -> List[str]:
        """
        Get or create a Meal Plan.
        Standardizes names (e.g. 'bed & breakfast' -> 'BB').
        """
        if not self.is_connected() or not meal_plan_name:
            return []
            
        # Standardization Logic
        raw = meal_plan_name.lower().strip().replace('.', '').replace(',', '')
        
        # Mapping dict
        mapping = {
            'bb': 'BB',
            'bed & breakfast': 'BB',
            'bed and breakfast': 'BB',
            'bread and brakfast': 'BB',
            'bed and brakfast': 'BB',
            'hb': 'HB',
            'half board': 'HB',
            'fb': 'FB',
            'full board': 'FB',
            'ai': 'AI',
            'all inclusive': 'AI',
            'ro': 'RO',
            'room only': 'RO',
        }
        
        # Check explicit mapping first
        final_name = mapping.get(raw)
        
        # If not exact match, check fuzzy contains
        if not final_name:
            if 'breakfast' in raw or 'brakfast' in raw:
                final_name = 'BB'
            elif 'half' in raw and 'board' in raw:
                final_name = 'HB'
            elif 'full' in raw and 'board' in raw:
                final_name = 'FB'
            elif 'inclusive' in raw:
                final_name = 'AI'
            else:
                final_name = meal_plan_name # Fallback to original if unknown category. 
                # Or maybe standardized to Title Case?
                # Let's keep original if we don't know it.
        
        try:
            safe_name = final_name.replace("'", "\\'")
            formula = f"{{Name}}='{safe_name}'"
            existing = self.meal_plans_table.all(formula=formula)
            
            if existing:
                return [existing[0]['id']]
            else:
                record = {"Name": final_name}
                new_record = self.meal_plans_table.create(record)
                return [new_record['id']]
        except Exception as e:
            logger.error(f"Error in get_or_create_meal_plan: {e}")
            return []

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

            # Get Hotel ID (Linked Record)
            hotel_ids = self.get_or_create_hotel(rate_data.get('hotel_name'))
            
            # Safe access to singleton list
            hotel_id_str = hotel_ids[0] if hotel_ids else None

            # Get Room Type ID (Linked Record)
            room_type_ids = []
            if hotel_id_str and rate_data.get('room_type'):
                room_type_ids = self.get_or_create_room_type(rate_data.get('room_type'), hotel_id_str)

            # Get Meal Plan ID (Linked Record)
            meal_plan_ids = self.get_or_create_meal_plan(rate_data.get('meal_plan'))

            # Map Python dict keys to Airtable column names
            record = {
               "Hotel Name": rate_data.get('hotel_name'), # Text
               "Hotel": hotel_ids, # Linked to Hotels
               
               # "Room Type (Text)": rate_data.get('room_type'), # Legacy text field removed
               "Room Type": room_type_ids, # Linked field
               
               # "Meal Plan (Text)": rate_data.get('meal_plan'), # Legacy text field removed
               "Meal Plan": meal_plan_ids, # Linked to Meal Plans
               
               "Occupancy": self._map_occupancy(rate_data.get('occupancy')),
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
            # Check if contact already exists by Email
            formula = f"{{Email}}='{email}'"
            existing = self.contacts_table.all(formula=formula)
            
            record = {
                "Hotel Name": hotel_name,
                "Email": email,
                "Discovery Source": source,
                "Confidence": confidence
            }
            
            if existing:
                # Update existing record
                # Only update hotel name if the new one is not "Unknown" 
                if "Unknown" in hotel_name and "Unknown" not in existing[0]['fields'].get('Hotel Name', ''):
                     # Don't overwrite a good name with a bad one
                     del record['Hotel Name']
                
                self.contacts_table.update(existing[0]['id'], record)
                logger.info(f"Updated contact for {email}")
            else:
                # Create new
                self.contacts_table.create(record)
                logger.info(f"Created new contact for {email}")
                
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

            # Get Hotel ID (Linked Record)
            hotel_ids = self.get_or_create_hotel(item_data.get('hotel_name'))
            
            record = {
                "Hotel Name": item_data.get('hotel_name'),
                "Hotel": hotel_ids,
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
            # BUT exclude 'Hotel' which must remain a list
            vals = {}
            for k, v in record.items():
                if v is None:
                    continue
                if k == 'Hotel':
                    vals[k] = v
                else:
                    vals[k] = str(v)
            
            record = vals
            
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

    def _map_occupancy(self, val) -> str:
        """Map raw occupancy string to Airtable Single Select choices."""
        if not val:
            return None
        
        v = str(val).lower().strip()
        
        # Simple mapping
        if "1" in v or "single" in v: return "Single"
        if "2" in v or "double" in v: return "Double"
        if "3" in v or "triple" in v: return "Triple"
        if "4" in v or "quad" in v: return "Quad"
        
        # Default fallback
        return "Other"
