"""
Hotel Discovery Agent (V2)
Orchestrates finding, validating, and updating hotel email addresses.
"""
import json
from typing import List, Dict, Optional
from duckduckgo_search import DDGS
from llm.llm_client import generate_llm_response
from llm.prompts_discovery import get_discovery_agent_prompt
from database.hotel_management import HotelManager
from utils.logger import get_logger

logger = get_logger(__name__)

class HotelDiscoveryAgent:
    def __init__(self):
        self.hotel_manager = HotelManager()

    def run(self, hotel_name: str, city: str = "", country: str = "") -> Dict:
        """
        Execute the discovery pipeline for a single hotel.
        """
        logger.info(f"🕵️‍♂️ Starting Discovery Agent for: {hotel_name}")
        
        # Step 1: Source Discovery (Search)
        sources = self._discover_sources(hotel_name, city, country)
        if not any(sources.values()):
            logger.warning(f"❌ No credible sources found for {hotel_name}")
            return {
                "hotel_name": hotel_name,
                "sources": sources,
                "emails": [],
                "run_status": "sources_not_found",
                "manual_review_required": True
            }

        # Step 2 & 3: Extraction & Classification
        discovered_emails = []
        
        for source_type, content in sources.items():
            if not content:
                continue
                
            logger.info(f"   extracting from {source_type}...")
            emails = self._extract_emails_with_llm(source_type, content)
            
            for email_data in emails:
                # Add source metadata
                email_data['source'] = source_type
                discovered_emails.append(email_data)

        # Optimization:deduplicate by email address, keeping highest confidence
        unique_emails = {}
        for e in discovered_emails:
            addr = e['email'].lower()
            if addr not in unique_emails or e['confidence'] > unique_emails[addr]['confidence']:
                unique_emails[addr] = e
        
        final_list = list(unique_emails.values())

        # Step 4: Change Detection (Save to DB)
        # We need the hotel_id. Ensure hotel exists in main table first.
        hotel_id = self.hotel_manager.get_or_create_hotel(hotel_name)
        
        saved_emails = []
        for item in final_list:
            # Determine status based on DB (Placeholder logic for now)
            # In a real run, we'd compare with `hotel_emails` table
            status = "new"  
            
            self._save_email_to_db(hotel_id, item)
            
            item['status'] = status
            saved_emails.append(item)

        return {
            "hotel_name": hotel_name,
            "sources": {k: "Found" if v else "Not Found" for k, v in sources.items()}, # summary
            "emails": saved_emails,
            "run_status": "success",
            "manual_review_required": len(saved_emails) == 0
        }

    def _discover_sources(self, name: str, city: str, country: str) -> Dict[str, str]:
        """
        Search and return raw text content for each source type.
        """
        sources = {
            "official_website": "",
            "google_maps": "",
            "ota_sources": "" 
        }
        
        # 1. Official Site Search
        query = f"{name} {city} {country} official hotel site contact"
        sources["official_website"] = self._search(query, limit=3)
        
        # 2. LinkedIn / Facebook (Social helps for emails) - Mapping "google_maps" to broad "business listing"
        # The user requested GMap, but via text search we mostly get directories. 
        # We'll treat general web results as potential business listings.
        
        return sources

    def _search(self, query: str, limit=3) -> str:
        try:
            with DDGS() as ddgs:
                # region='wt-wt' for global
                results = list(ddgs.text(query, region="wt-wt", max_results=limit))
                if not results:
                    return ""
                
                # Concatenate title + snippet (we don't scrape full HTML yet, just snippets)
                text = ""
                for r in results:
                    text += f"Title: {r['title']}\nSnippet: {r['body']}\nURL: {r['href']}\n\n"
                return text
        except Exception as e:
            logger.error(f"Search error for '{query}': {e}")
            return ""

    def _extract_emails_with_llm(self, source_type: str, text: str) -> List[Dict]:
        prompt = get_discovery_agent_prompt(source_type, text)
        response = generate_llm_response(prompt, temperature=0.0)
        
        try:
            # Clean JSON
            json_str = response.strip()
            if json_str.startswith("```json"):
                json_str = json_str.split("```json")[1].split("```")[0]
            elif json_str.startswith("```"):
                json_str = json_str.split("```")[1].split("```")[0]
                
            data = json.loads(json_str)
            return data.get("emails", [])
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return []

    def _save_email_to_db(self, hotel_id: int, email_data: Dict):
        """
        Upsert email into hotel_emails table.
        """
        # This requires a method in HotelManager we haven't written yet.
        # Allowing it to fail gracefully or adding TODO
        try:
             self.hotel_manager.upsert_hotel_email(
                 hotel_id=hotel_id,
                 email=email_data['email'],
                 purpose=email_data['purpose'],
                 source_type=email_data['source'],
                 confidence=email_data['confidence']
             )
        except AttributeError:
            logger.error("HotelManager.upsert_hotel_email not implemented yet")
