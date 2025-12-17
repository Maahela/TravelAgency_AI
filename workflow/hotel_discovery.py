"""
Workflow for discovering hotel contact information using Web Search + LLM.
"""
from typing import List, Dict
from duckduckgo_search import DDGS
from llm.llm_client import extract_contact_info_with_llm
from database.hotel_management import HotelManager
from utils.logger import get_logger

logger = get_logger(__name__)

class HotelDiscoveryWorkflow:
    def __init__(self):
        self.hotel_manager = HotelManager()

    def discover_hotels(self, hotel_names: List[str]) -> List[Dict]:
        """
        Search for contact info for a list of hotels and save valid ones to DB.
        """
        results = []
        
        for name in hotel_names:
            logger.info(f"Searching for contact info: {name}")
            
            # 1. Web Search
            # Simplified query for better results
            search_query = f"{name} hotel official contact email"
            snippets = self._search_web(search_query)
            if not snippets:
                logger.warning(f"No search results found for {name}")
                continue
                
            # 2. LLM Extraction
            info = extract_contact_info_with_llm(snippets)
            
            if info.get('email'):
                logger.info(f"Found email for {name}: {info['email']}")
                
                # 3. Save to DB
                hotel_id = self.hotel_manager.add_hotel(
                    name=name,
                    email=info['email'],
                    website=info.get('website'),
                    contact_person="Discovered via Web"
                )
                results.append({
                    'name': name,
                    'status': 'success',
                    'email': info['email'],
                    'id': hotel_id
                })
            else:
                logger.warning(f"Could not extract email for {name}")
                results.append({'name': name, 'status': 'failed'})
                
        return results

    def _search_web(self, query: str) -> str:
        """Perform web search and return concatenated snippets."""
        try:
            with DDGS() as ddgs:
                # Use region 'wt-wt' for global results, avoiding local noise
                # Get top 5 results
                results = list(ddgs.text(query, region="wt-wt", max_results=5))
                
                if not results:
                    logger.warning(f"DDGS returned no results for query: {query}")
                    return ""
                
                # Format for LLM
                snippet_text = ""
                for i, r in enumerate(results):
                    snippet_text += f"Result {i+1}:\nTitle: {r['title']}\nSnippet: {r['body']}\nURL: {r['href']}\n\n"
                    
                logger.info(f"DDGS found {len(results)} results")
                print(f"DEBUG SNIPPETS:\n{snippet_text}")
                return snippet_text
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return ""
