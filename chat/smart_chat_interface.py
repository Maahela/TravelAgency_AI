import google.generativeai as genai
from database.query_rates import search_rates
from database.query_price_items import search_price_items
from database.hotel_management import HotelManager
from workflow.hotel_discovery_agent import HotelDiscoveryAgent
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class SmartChatInterface:
    def __init__(self, db_path=None):
        self.db_path = db_path
        self.conversation_history = []
        
        # Define tools that Gemini can call
        self.tools = [
            {
                "function_declarations": [
                    {
                        "name": "search_hotel_rates",
                        "description": "Search for hotel room rates and availability in the database. Use this when user asks about prices, room types, or availability.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "hotel_name": {"type": "string", "description": "Name of the hotel to search for (optional if searching by budget)"},
                                "occupancy": {"type": "string", "description": "Occupancy type: 'Single', 'Double', 'Triple', 'Quad'"},
                                "max_rate": {"type": "number", "description": "Maximum price limit per night (Budget)"},
                                "room_type": {"type": "string", "description": "Specific room type if mentioned"},
                                "meal_plan": {"type": "string", "description": "Meal plan filter: 'BB', 'HB', 'FB', 'AI'"}
                            },
                            "required": []
                        }
                    },
                    {
                        "name": "search_price_supplements",
                        "description": "Search for extra charges, meal plans, child rates, and other supplements.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "hotel_name": {"type": "string", "description": "Name of the hotel"}
                            },
                            "required": ["hotel_name"]
                        }
                    },
                    {
                        "name": "find_hotel_email",
                        "description": "Find contact email for a hotel. Checks database first, then performs web search if needed.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "hotel_name": {"type": "string", "description": "Name of the hotel"}
                            },
                            "required": ["hotel_name"]
                        }
                    }
                ]
            }
        ]
        
    def query(self, user_message: str) -> str:
        """
        Send query and let Gemini decide what functions to call.
        Implements automatic API key rotation on quota errors.
        """
        from config import GOOGLE_API_KEYS
        
        if not GOOGLE_API_KEYS:
             return "Error: No Google API Keys configured in .env"

        last_error = None

        # Try each API key in order
        for key_index, api_key in enumerate(GOOGLE_API_KEYS):
            try:
                genai.configure(api_key=api_key)
                
                # Initialize model with tools
                model = genai.GenerativeModel(
                    "gemini-2.5-flash",
                    tools=self.tools,
                    system_instruction="""You are an expert hotel booking assistant for a travel agency. 
                    Your goal is to provide accurate, helpful info about hotel rates and details.
                    
                    Capabilities:
                    - ALWAYS use the provided tools to fetch real data. Do not make up rates.
                    - If you search for rates and find none, tell the user clearly.
                    - When showing rates, organize them clearly (e.g. by room type or meal plan).
                    - Be concise but professional."""
                )
                
                # Start Chat with existing history
                # We create a new chat session for each attempt to ensure clean state
                chat = model.start_chat(history=self.conversation_history)
                
                logger.info(f"Using Google API Key #{key_index + 1}")
                
                # Send user message
                response = chat.send_message(user_message)
                
                # Handle Function Calls
                def safe_search_rates(**kwargs):
                    try:
                        return search_rates(**kwargs)
                    except Exception as e:
                        return f"Error searching rates: {e}"

                def safe_search_supplements(**kwargs):
                    try:
                        return search_price_items(**kwargs)
                    except Exception as e:
                        return f"Error searching supplements: {e}"
                
                def safe_find_email(hotel_name):
                    try:
                        manager = HotelManager()
                        emails = manager.get_hotel_emails(hotel_name)
                        if emails:
                            return {"source": "database", "emails": emails}
                        
                        agent = HotelDiscoveryAgent()
                        res = agent.run(hotel_name)
                        return res
                    except Exception as e:
                        return f"Error finding email: {e}"

                function_map = {
                    "search_hotel_rates": safe_search_rates,
                    "search_price_supplements": safe_search_supplements,
                    "find_hotel_email": safe_find_email
                }
                
                # Loop for function calling (max 5 turns)
                for _ in range(5):
                    if not response.candidates:
                        break
                        
                    part = response.candidates[0].content.parts[0]
                    
                    if part.function_call:
                        fn_name = part.function_call.name
                        fn_args = dict(part.function_call.args)
                        
                        logger.info(f"🤖 Gemini calling function: {fn_name} with {fn_args}")
                        
                        if fn_name in function_map:
                            api_res = function_map[fn_name](**fn_args)
                            
                            response = chat.send_message(
                                genai.protos.Content(
                                    parts=[genai.protos.Part(
                                        function_response=genai.protos.FunctionResponse(
                                            name=fn_name,
                                            response={"result": api_res}
                                        )
                                    )]
                                )
                            )
                        else:
                            response = chat.send_message(f"Error: Unknown function {fn_name}")
                    else:
                        break
                
                # If we got here, success! Update history and return
                self.conversation_history = chat.history
                return response.text

            except Exception as e:
                error_str = str(e)
                # Check for quota limits or server errors
                is_retryable = (
                    "429" in error_str or 
                    "quota" in error_str.lower() or 
                    "ResourceExhausted" in error_str or
                    "503" in error_str or
                    "500" in error_str
                )
                
                if is_retryable:
                    logger.warning(f"Key #{key_index+1} failed ({error_str}). Trying next key...")
                    last_error = e
                    continue # Try next key
                else:
                    # Non-retryable error (e.g. invalid request), raise or return
                    logger.error(f"Non-retryable error with Key #{key_index+1}: {e}")
                    return f"Error processing request: {e}"

        logger.error("All API keys exhausted or failed.")
        return f"Service unavailable: All API keys exhausted. Last error: {last_error}"
