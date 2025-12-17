"""
Hotel Discovery Agent (V2)
Orchestrates finding, validating, and updating hotel email addresses.
"""
import json
from typing import List, Dict, Optional
from googleapiclient.discovery import build
from llm.llm_client import generate_llm_response
from llm.prompts_discovery import get_discovery_agent_prompt
from database.hotel_management import HotelManager
from utils.logger import get_logger
from config import GOOGLE_SEARCH_API_KEY, GOOGLE_SEARCH_CX

logger = get_logger(__name__)

class HotelDiscoveryAgent:
    def __init__(self):
        self.hotel_manager = HotelManager()
        self.search_service = None
        if GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_CX:
            try:
                self.search_service = build("customsearch", "v1", developerKey=GOOGLE_SEARCH_API_KEY)
            except Exception as e:
                logger.error(f"Failed to init Google Search: {e}")

    def run(self, hotel_name: str, city: str = "", country: str = "") -> Dict:
        """
        Execute the discovery pipeline for a single hotel.
        """
        logger.info(f"Starting Discovery Agent for: {hotel_name}")
        
        # Step 1: Source Discovery (Search)
        sources = self._discover_sources(hotel_name, city, country)
        if not any(sources.values()):
            logger.warning(f"No credible sources found for {hotel_name}")
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
            "blocked_urls": self.blocked_urls if hasattr(self, 'blocked_urls') else [],
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
        # Detailed query with location to anchor results
        query = f"{name} {city} {country} official website contact email"
        # Increase limit since we have 100 queries/day and want high quality
        sources["official_website"] = self._search(query, limit=5)
        
        return sources

    def _search(self, query: str, limit=5) -> str:
        """
        Search and scrape actual contact pages for email addresses.
        """
        if not self.search_service:
            logger.error("Google Search Service not initialized")
            return ""
            
        try:
            # Step 1: Get search results from Google
            res = self.search_service.cse().list(
                q=query,
                cx=GOOGLE_SEARCH_CX,
                num=limit
            ).execute()
            
            items = res.get("items", [])
            if not items:
                return ""
            
            # Step 2: Scrape the actual pages
            scraped_content = ""
            
            for item in items:
                url = item.get("link", "")
                title = item.get("title", "")
                
                # Skip PDFs and other non-HTML content
                if url.lower().endswith('.pdf'):
                    logger.info(f"Skipping PDF: {url}")
                    continue
                
                logger.info(f"Scraping: {title}")
                page_text = self._scrape_page(url)
                
                if page_text:
                    scraped_content += f"Source: {title}\nURL: {url}\nContent:\n{page_text}\n\n---\n\n"
            
            return scraped_content if scraped_content else ""
            
        except Exception as e:
            logger.error(f"Google Search error for '{query}': {e}")
            return ""

    def _scrape_page(self, url: str, max_length: int = 5000) -> str:
        """
        Scrape a web page and extract text content, prioritizing contact sections.
        """
        try:
            import requests
            from bs4 import BeautifulSoup
            
            # Try multiple User-Agents if first one fails
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
                'Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0'
            ]
            
            response = None
            for ua in user_agents:
                try:
                    headers = {'User-Agent': ua}
                    response = requests.get(url, headers=headers, timeout=10)
                    response.raise_for_status()
                    break  # Success, exit loop
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 403 and ua != user_agents[-1]:
                        logger.info(f"403 with {ua[:30]}..., trying next")
                        continue
                    else:
                        raise
            
            if not response:
                return ""
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.decompose()
            
            # Try to find contact-specific sections first
            contact_keywords = ['contact', 'email', 'reservation', 'enquir', 'reach us', 'get in touch']
            contact_sections = []
            
            for keyword in contact_keywords:
                # Look for sections with contact-related IDs or classes
                sections = soup.find_all(['div', 'section', 'article'], 
                                        class_=lambda x: x and keyword in x.lower() if x else False)
                sections += soup.find_all(['div', 'section', 'article'],
                                         id=lambda x: x and keyword in x.lower() if x else False)
                contact_sections.extend(sections)
            
            # If we found contact sections, extract from those first
            if contact_sections:
                text = " ".join([section.get_text(separator=' ', strip=True) for section in contact_sections[:3]])
            else:
                # Fall back to general page text
                text = soup.get_text(separator=' ', strip=True)
            
            # Limit length to avoid overwhelming the LLM
            if len(text) > max_length:
                text = text[:max_length] + "..."
            
            return text
            
        except Exception as e:
            logger.warning(f"Failed to scrape {url}: {e}")
            return ""

    def _extract_emails_with_llm(self, source_type: str, text: str) -> List[Dict]:
        """
        Extract emails using regex first, then use LLM to classify them.
        """
        import re
        
        # Step 1: Find all email addresses with regex
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        found_emails = re.findall(email_pattern, text)
        
        if not found_emails:
            logger.info(f"No emails found via regex in {source_type}")
            return []
        
        # Remove duplicates
        unique_emails = list(set(found_emails))
        logger.info(f"Found {len(unique_emails)} unique email(s) via regex: {unique_emails}")
        
        # Step 2: Use LLM to classify each email
        results = []
        for email in unique_emails:
            # Create a focused prompt for classification
            classification_prompt = f"""
            Classify this hotel contact email address: {email}
            
            Determine:
            1. Purpose: reservations, sales, contracts, general, or unknown
            2. Confidence (0.0-1.0): How confident are you this is a legitimate business email?
            3. Reasoning: Brief explanation
            
            Rules:
            - Gmail/Yahoo emails get max 0.6 confidence
            - Role-based emails (reservations@, sales@) get 0.9+ confidence
            - Generic emails (info@, contact@) get 0.7-0.8 confidence
            
            Return ONLY valid JSON:
            {{
              "email": "{email}",
              "purpose": "...",
              "confidence": 0.0,
              "reasoning": "..."
            }}
            """
            
            response = generate_llm_response(classification_prompt, temperature=0.0)
            
            try:
                json_str = response.strip()
                if json_str.startswith("```json"):
                    json_str = json_str.split("```json")[1].split("```")[0]
                elif json_str.startswith("```"):
                    json_str = json_str.split("```")[1].split("```")[0]
                
                email_data = json.loads(json_str)
                results.append(email_data)
            except Exception as e:
                logger.error(f"Failed to classify email {email}: {e}")
                # Add with basic classification as fallback
                results.append({
                    "email": email,
                    "purpose": "unknown",
                    "confidence": 0.5,
                    "reasoning": "Found via regex but classification failed"
                })
        
        return results

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
