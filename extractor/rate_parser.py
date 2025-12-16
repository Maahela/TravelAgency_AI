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
            # Clean response if it contains markdown code blocks
            clean_response = response.replace("```json", "").replace("```", "").strip()
            parsed_data = json.loads(clean_response)
            
            # Ensure we have a list of rates
            if isinstance(parsed_data, dict):
                rates = [parsed_data]
            elif isinstance(parsed_data, list):
                rates = parsed_data
            else:
                logger.error(f"Unexpected JSON format from LLM: {type(parsed_data)}")
                return []
                
            # Enrich with metadata
            for rate in rates:
                rate['source_file'] = source_file
                rate['extracted_at'] = datetime.now().isoformat()
                rate['confidence'] = 0.90  # Placeholder confidence
                
            logger.info(f"Successfully passed {len(rates)} rates from {source_file}")
            return rates
            
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON from LLM response. Response: {response[:100]}...")
            return []
        except Exception as e:
            logger.error(f"Error parsing rate data: {e}")
            return []
    
    def validate_rate_data(self, rate_data: Dict) -> Dict[str, any]:
        """
        Validate parsed rate data for completeness and correctness.
        
        Args:
            rate_data: Parsed rate dictionary
        
        Returns:
            Validation result:
            {
                'valid': bool,
                'errors': List[str],
                'warnings': List[str]
            }
        
        TODO:
            - Check required fields are present
            - Validate date formats and ranges
            - Validate numeric fields (rate > 0)
            - Check currency codes against ISO 4217
            - Validate date logic (start < end, validity >= end)
            - Flag suspicious values for review
        """
        logger.info("TODO: Validate rate data")
        
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        required_fields = [
            'hotel_name', 'room_type', 'rate_per_night', 'currency',
            'season_start_date', 'season_end_date'
        ]
        
        # Check required fields
        for field in required_fields:
            if field not in rate_data or not rate_data[field]:
                validation_result['valid'] = False
                validation_result['errors'].append(f"Missing required field: {field}")
        
        # TODO: Add more validation logic
        
        return validation_result
    
    def standardize_currency(self, currency: str) -> str:
        """
        Standardize currency code to ISO 4217.
        
        Args:
            currency: Raw currency string from extraction
        
        Returns:
            Standardized 3-letter currency code
        
        TODO:
            - Map common variations (USD, $, dollars -> USD)
            - Handle multi-currency rates
            - Add currency conversion support
        """
        logger.info(f"TODO: Standardize currency: {currency}")
        return currency.upper()
    
    def parse_date(self, date_string: str) -> Optional[str]:
        """
        Parse various date formats into ISO format (YYYY-MM-DD).
        
        Args:
            date_string: Raw date string from extraction
        
        Returns:
            ISO formatted date string or None if parsing fails
        
        TODO:
            - Handle multiple date formats (DD/MM/YYYY, MM-DD-YYYY, etc.)
            - Parse relative dates (e.g., "valid until end of year")
            - Handle date ranges
            - Add timezone awareness if needed
        """
        logger.info(f"TODO: Parse date: {date_string}")
        
        # Placeholder:
        # from dateutil import parser
        # try:
        #     parsed_date = parser.parse(date_string)
        #     return parsed_date.strftime('%Y-%m-%d')
        # except:
        #     return None
        
        return None

    def extract_and_store_contract_data(self, extracted_text: str, source_file: str) -> bool:
        """
        Extract extended contract data and store in 'contract_data' table.
        """
        from llm.llm_client import parse_extended_contract_data
        from database.db_init import get_db_connection
        from config import DB_PATH
        import json
        
        logger.info(f"Extracting extended contract data from {source_file}...")
        
        # 1. Parse with LLM
        contract_json = parse_extended_contract_data(extracted_text)
        
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
