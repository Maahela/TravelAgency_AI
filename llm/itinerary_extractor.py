"""
LLM-based extractor for travel itinerary parameters.
"""
import json
import re
from typing import Dict, List, Optional
from llm.llm_client import generate_llm_response
from utils.logger import get_logger

logger = get_logger(__name__)

class ItineraryExtractor:
    def __init__(self):
        self.system_prompt = """
        You are a travel assistant extracting structured itinerary data from user text.
        
        GOAL: Extract a list of hotel stays with explicit details for generic budget calculation.
        
        OUTPUT FORMAT (JSON ONLY):
        {
            "trip_start_date": "YYYY-MM-DD" or "23 Jan", // Extract the FIRST date mentioned
            "guests": {
                "adults": 2,
                "children": 1,
                "child_ages": [5] // If mentioned
            },
            "stays": [
                {
                    "hotel_name": "Exact Hotel Name",
                    "nights": 3,
                    "rooms": 1,
                    "room_type": "Standard/Double/etc",
                    "occupancy": "Single/Double/Triple", // Map based on adults per room
                    "meal_plan": "BB/HB/FB",
                    "explicitly_stated": true/false 
                }
            ],
            "missing_info": ["list", "of", "missing", "params"], 
            "currency": "USD"
        }
        
        RULES:
        1. If user says "2 nights at Taj and 3 at Heritance", create two stay entries.
        2. "guests": Extract total party composition. if not mentioned, default to 2 adults, 0 children.
        3. "occupancy": If 1 adult -> Single, 2 adults -> Double, 3+ adults -> Triple / Extra Adult logic.
        4. "meal_plan": Only populate if explicitly mentioned (BB, HB, FB). If not mentioned, leave as null.
        5. "missing_info": If "nights", "hotel_name", "meal_plan", or "currency" is missing, list it in "missing_info".
        
        CONTEXT MERGING (VERY IMPORTANT):
        If a 'CONTEXT' is provided, it contains the conversation history.
        - Your result MUST combine 'CONTEXT' and 'NEW QUERY'.
        - If 'NEW QUERY' provides a meal plan (e.g. "BB"), and 'CONTEXT' has the hotel/dates, the final JSON must have the hotel/dates FROM CONTEXT and the meal plan FROM NEW QUERY.
        - Do not drop information from CONTEXT unless NEW QUERY explicitly changes it.
        """

    def extract(self, user_query: str, context: str = None) -> Dict:
        """
        Extract structured itinerary from text, optionally merging with context.
        """
        full_query = user_query
        if context:
            full_query = f"CONTEXT: {context}\nNEW QUERY: {user_query}"

        prompt = f"""
        Extract the itinerary details as JSON from the following input:
        "{full_query}"
        """
        
        try:
            response = generate_llm_response(prompt, system_message=self.system_prompt)
            # clean markdown code blocks
            clean_response = response.replace('```json', '').replace('```', '').strip()
            data = json.loads(clean_response)
            
            # Post-processing / Validation
            from dateutil import parser
            from datetime import timedelta
            import datetime

            # 1. Parse Trip Start Date
            start_date_str = data.get("trip_start_date")
            current_date = None
            
            if start_date_str:
                try:
                    # Parse generic date string (e.g., "23 January")
                    # Assuming current year if not specified, logic can be enhanced
                    current_date = parser.parse(start_date_str)
                    
                    # If date is in past (by a lot), maybe assume next year? 
                    # For now trusted as is, defaulting to 2025/2026 based on system time if vague
                    # But dateutil defaults to current year/month.
                    # Let's ensure year is valid if missing.
                    if current_date.year < 2024:
                        current_date = current_date.replace(year=datetime.datetime.now().year)

                except Exception as e:
                    logger.warning(f"Could not parse date '{start_date_str}': {e}")
            
            valid_stays = []
            for stay in data.get('stays', []):
                # Basic validation
                if stay.get('hotel_name') and stay.get('nights'):
                    
                    # 2. Assign Dates
                    nights = int(stay.get('nights', 1))
                    
                    if current_date:
                        stay['check_in'] = current_date.strftime("%Y-%m-%d")
                        stay['check_out'] = (current_date + timedelta(days=nights)).strftime("%Y-%m-%d")
                        # Advance current_date for next leg
                        current_date += timedelta(days=nights)
                    else:
                        stay['check_in'] = None
                        stay['check_out'] = None

                    valid_stays.append(stay)
            
            data['stays'] = valid_stays
            return data
            
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return {"stays": [], "missing_info": ["Failed to parse itinerary"]}
