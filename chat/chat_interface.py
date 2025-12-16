"""
Chat interface for querying hotel rate data.
"""

from typing import Optional
from pathlib import Path
from database.query_rates import search_rates, format_rates_for_llm
from llm.llm_client import answer_query_with_llm
from utils.logger import get_logger

logger = get_logger(__name__)


class ChatInterface:
    """
    Internal chat interface for querying stored rate data.
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize chat interface with conversation memory.
        """
        if db_path is None:
            from config import DB_PATH
            db_path = DB_PATH
        
        self.db_path = db_path
        self.conversation_history = []  # Track conversation context
        self.last_hotel = None  # Remember last mentioned hotel
        logger.info("ChatInterface initialized with conversation memory")
    
    def query(self, user_query: str) -> str:
        """
        Process a user query with conversation context.
        """
        logger.info(f"Processing query: {user_query}")
        
        # Extract search criteria from query using LLM with conversation context
        from llm.llm_client import extract_search_params_with_llm
        from database.query_price_items import search_price_items, format_price_items_for_llm
        
        # Build context-aware query
        context_query = user_query
        if self.last_hotel and not any(word in user_query.lower() for word in ['hotel', 'property', 'resort']):
            # User didn't mention a hotel, but we remember one from before
            context_query = f"Regarding {self.last_hotel}: {user_query}"
            logger.info(f"Adding context - Last hotel: {self.last_hotel}")
        
        params = extract_search_params_with_llm(context_query)
        logger.info(f"Extracted params: {params}")
        
        # Update conversation memory
        if params.get('hotel_name'):
            self.last_hotel = params['hotel_name']
        
        # Search BOTH tables
        # 1. Base rates table
        rates = search_rates(
            hotel_name=params.get('hotel_name'),
            max_rate=params.get('max_rate'),
            db_path=self.db_path
        )
        
        # 2. Price items table (meal supplements, charges, etc.)
        price_items = search_price_items(
            hotel_name=params.get('hotel_name'),
            db_path=self.db_path
        )
        
        if not rates and not price_items:
            return "I couldn't find any rates or pricing information matching your criteria in the database."
        
        # Format context for LLM - combine both sources
        context_parts = []
        
        if rates:
            context_parts.append("BASE ROOM RATES:")
            context_parts.append(format_rates_for_llm(rates))
        
        if price_items:
            context_parts.append("\n" + format_price_items_for_llm(price_items))
        
        context = "\n".join(context_parts)
        
        # Generate answer using LLM
        answer = answer_query_with_llm(user_query, context)
        
        # Save to conversation history
        self.conversation_history.append({
            'query': user_query,
            'params': params,
            'answer': answer
        })
        
        return answer
    
    def run_cli(self):
        """
        Run an interactive command-line chat interface.
        
        TODO:
            - Implement proper CLI with rich formatting
            - Add command history
            - Support slash commands (/search, /help, etc.)
            - Add export functionality
        """
        logger.info("Starting interactive chat interface")
        print("Hotel Rate Chat Interface")
        print("Type 'exit' to quit\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                response = self.query(user_input)
                print(f"\nAssistant: {response}\n")
            
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                logger.error(f"Error in chat interface: {e}")
                print(f"Error: {e}\n")


if __name__ == "__main__":
    chat = ChatInterface()
    chat.run_cli()
