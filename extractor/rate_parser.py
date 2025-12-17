"""
Rate data parser and validator.
Parses extracted text into structured hotel rate information.
"""

from typing import Dict, List, Optional
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)


class RateParser:
    """
    Parses and validates hotel rate data from extracted text.
    """
    
    def __init__(self):
        """
        Initialize rate parser.
        
        TODO:
            - Load parsing rules/patterns
            - Initialize validation schemas
        """
        logger.info("RateParser initialized")
    
    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """
        Helper to clean and parse JSON from LLM response.
        """
        import json
        try:
            # Clean response
            clean_json = response.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json.split("```json")[1].split("```")[0]
            elif clean_json.startswith("```"):
                clean_json = clean_json.split("```")[1].split("```")[0]
            
            return json.loads(clean_json)
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return None

    def parse_rate_data(self, extracted_text: str, source_file: str) -> List[Dict]:
        """
        Parse extracted text into structured rate records.
        """
        from llm.llm_client import generate_llm_response
        from llm.prompts import get_rate_parsing_prompt
        import json
        from datetime import datetime
        
        logger.info(f"Parsing rate data from {source_file}...")
        
        # Guard clause for empty text
        if not extracted_text or len(extracted_text.strip()) < 10:
            logger.warning(f"Text too short for parsing from {source_file}")
            return []

        # Generate prompt
        prompt = get_rate_parsing_prompt(extracted_text)
        
        # Call LLM
        response = generate_llm_response(prompt, temperature=0.0)
        
        # Parse JSON response
        try:
            parsed_data = self._parse_json_response(response)
            if not parsed_data:
                return []
            
            # Ensure we have a list of rates
            if isinstance(parsed_data, dict):
                rates = [parsed_data]
            elif isinstance(parsed_data, list):
                rates = parsed_data
            else:
                logger.error(f"Unexpected JSON format from LLM: {type(parsed_data)}")
                return []
                
                
            # Enrich with metadata AND Standardize
            for rate in rates:
                rate['source_file'] = source_file
                rate['extracted_at'] = datetime.now().isoformat()
                rate['confidence'] = 0.90  # Placeholder confidence
                
                # Standardization
                rate['currency'] = self.standardize_currency(rate.get('currency'))
                rate['season_start_date'] = self.parse_date(rate.get('season_start_date'))
                rate['season_end_date'] = self.parse_date(rate.get('season_end_date'))
                rate['validity_date'] = self.parse_date(rate.get('validity_date'))
                
            logger.info(f"Successfully passed {len(rates)} rates from {source_file}")
            return rates
            
        except Exception as e:
            logger.error(f"Error parsing rate data: {e}")
            return []
    
    def validate_rate_data(self, rate_data: Dict) -> Dict[str, any]:
        """
        Validate parsed rate data for completeness and correctness.
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        required_fields = [
            'hotel_name', 'room_type', 'rate_per_night', 'currency'
        ]
        
        # 1. Required Fields Check
        for field in required_fields:
            if field not in rate_data or not rate_data[field]:
                validation_result['valid'] = False
                validation_result['errors'].append(f"Missing required field: {field}")
        
        # 2. Date Validation
        if rate_data.get('season_start_date') and rate_data.get('season_end_date'):
            if rate_data['season_start_date'] > rate_data['season_end_date']:
                validation_result['valid'] = False
                validation_result['errors'].append("Start date is after end date")
        
        # 3. Numeric Validation
        try:
            rate = float(rate_data.get('rate_per_night', 0))
            if rate <= 0:
                validation_result['valid'] = False
                validation_result['errors'].append("Rate must be positive")
        except ValueError:
            validation_result['valid'] = False
            validation_result['errors'].append("Invalid rate value (not a number)")
            
        return validation_result
    
    def standardize_currency(self, currency: str) -> str:
        """
        Standardize currency code to ISO 4217.
        """
        if not currency:
            return "USD"
            
        currency = currency.strip().upper()
        
        # Common symbol mapping
        mapping = {
            "$": "USD",
            "€": "EUR",
            "£": "GBP",
            "USD": "USD",
            "EUR": "EUR",
            "GBP": "GBP",
            "RS": "LKR", # Assuming local context or INR/LKR based on user preference, default to LKR if Sri Lanka context implied, or just keep as is if unsure. Let's map Rs -> LKR for now as per likely context or just return standardized string.
            "RP": "IDR",
            "AUD": "AUD"
        }
        
        # Check if it's a known symbol
        for symbol, code in mapping.items():
            if currency == symbol or currency.startswith(symbol):
                return code
                
        # If it looks like a 3-letter code, return it
        if len(currency) == 3 and currency.isalpha():
            return currency
            
        # Default fallback
        return "USD"
    
    def parse_date(self, date_string: str) -> Optional[str]:
        """
        Parse various date formats into ISO format (YYYY-MM-DD).
        """
        from dateutil import parser
        
        if not date_string:
            return None
            
        try:
            # Parse using dateutil (handles most formats automatically)
            # dayfirst=True ensures DD/MM/YYYY is preferred over MM/DD/YYYY if ambiguous
            parsed_date = parser.parse(date_string, dayfirst=True)
            return parsed_date.strftime('%Y-%m-%d')
        except Exception:
            # logger.debug(f"Date parse failed for: {date_string}")
            return None

    def parse_extended_contract_data(self, extracted_text: str) -> Dict:
        """
        Parse complex contract data (policies, supplements) using LLM.
        """
        from llm.prompts import get_extended_contract_extraction_prompt
        from llm.llm_client import generate_llm_response
        
        prompt = get_extended_contract_extraction_prompt(extracted_text)
        # Use a creative temperature to allow for better interpretation of complex policy text
        # but strict enough for JSON structure.
        response = generate_llm_response(prompt, temperature=0.1)
        
        data = self._parse_json_response(response)
        if data is None:
             return {"error": "Failed to parse JSON", "raw_response": response}
        return data

    def extract_and_store_contract_data(self, extracted_text: str, source_file: str) -> bool:
        """
        Extract extended contract data and store in 'contract_data' table.
        """
        from database.db_init import get_db_connection
        from config import DB_PATH
        import json
        
        logger.info(f"Extracting extended contract data from {source_file}...")
        
        # 1. Parse with LLM
        contract_json = self.parse_extended_contract_data(extracted_text)
        
        if not contract_json or "error" in contract_json:
            logger.error(f"Failed to extract contract data: {contract_json.get('error', 'Unknown error')}")
            return False
            
        # 2. Store in Database
        try:
            conn = get_db_connection(DB_PATH)
            cursor = conn.cursor()
            
            # Serialize JSON for storage
            json_str = json.dumps(contract_json)
            hotel_name = "Unknown" 
            # Try to get hotel name from room metadata if available
            if "room_metadata" in contract_json and len(contract_json["room_metadata"]) > 0:
                 # Heuristic: Use filename or just denote 'Unknown' for now as the prompt doesn't explicitly ask for hotel name at top level
                 pass
            
            cursor.execute("""
                INSERT INTO contract_data (hotel_name, source_file, raw_json)
                VALUES (?, ?, ?)
            """, (hotel_name, source_file, json_str))
            
            conn.commit()
            conn.close()
            logger.info(f"Extended contract data stored for {source_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store contract data: {e}")
            return False

    def extract_all_price_items(self, extracted_text: str) -> Dict:
        """
        Extract every priced item from contract text (meal supplements, charges, etc.).
        """
        from llm.prompts import get_price_items_extraction_prompt
        from llm.llm_client import generate_llm_response
        
        prompt = get_price_items_extraction_prompt(extracted_text)
        response = generate_llm_response(prompt, temperature=0.0)
        
        data = self._parse_json_response(response)
        if data is None:
             return {"error": "Failed to parse JSON", "raw_response": response}
        return data

    def extract_and_store_price_items(self, extracted_text: str, source_file: str, hotel_name: str = "Unknown") -> bool:
        """
        Extract all priced items and store in 'price_items' table.
        """
        from database.db_init import get_db_connection
        from config import DB_PATH
        
        logger.info(f"Extracting price items from {source_file}...")
        
        # 1. Extract with LLM
        price_data = self.extract_all_price_items(extracted_text)
        
        if not price_data or "error" in price_data:
            logger.error(f"Failed to extract price items: {price_data.get('error', 'Unknown error')}")
            return False
        
        # 2. Store in Database
        try:
            conn = get_db_connection(DB_PATH)
            cursor = conn.cursor()
            
            items_inserted = 0
            for item in price_data.get('priced_items', []):
                cursor.execute("""
                    INSERT INTO price_items (
                        hotel_name, source_file, category, description, price, currency,
                        per_unit, adult_or_child, age_range, applicable_room_types,
                        applicable_dates, meal_type, conditions, source_text_snippet
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    hotel_name,
                    source_file,
                    item.get('category'),
                    item.get('description'),
                    item.get('price'),
                    item.get('currency', 'USD'),
                    item.get('per_unit'),
                    item.get('adult_or_child'),
                    item.get('age_range'),
                    item.get('applicable_room_types'),
                    item.get('applicable_dates'),
                    item.get('meal_type'),
                    item.get('conditions'),
                    item.get('source_text_snippet')
                ))
                items_inserted += 1
            
            conn.commit()
            conn.close()
            logger.info(f"Stored {items_inserted} price items for {source_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store price items: {e}")
            return False

