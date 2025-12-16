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
        Initialize chat interface.
        
        Args:
            db_path: Path to database
        
        TODO:
            - Add conversation history tracking
            - Implement multi-turn dialogues
            - Add quick action buttons/shortcuts
        """
        if db_path is None:
            from config import DB_PATH
            db_path = DB_PATH
        
        self.db_path = db_path
        logger.info("ChatInterface initialized")
    
    def query(self, user_query: str) -> str:
        """
        Process a user query and return an answer.
        
        Args:
            user_query: Natural language question
        
        Returns:
            Answer from the system
        
        TODO:
            - Implement intent classification
            - Extract search parameters from natural language
            - Support follow-up questions with context
            - Add suggested queries/autocomplete
        """
        logger.info(f"Processing query: {user_query}")
        
        # Extract search criteria from query using LLM
        from llm.llm_client import extract_search_params_with_llm
        params = extract_search_params_with_llm(user_query)
        logger.info(f"Extracted params: {params}")
        
        # Search database
        rates = search_rates(
            hotel_name=params.get('hotel_name'),
            max_rate=params.get('max_rate'),
            db_path=self.db_path
        )
        
        if not rates:
            return "I couldn't find any rates matching your criteria in the database."
        
        # Format context for LLM
        context = format_rates_for_llm(rates)
        
        # Generate answer using LLM
        answer = answer_query_with_llm(user_query, context)
        
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
