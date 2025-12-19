"""
Chat interface for querying hotel rate data.
"""
import sys
from pathlib import Path

# Add project root to path for direct execution
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

from typing import Optional
from pathlib import Path
from database.query_rates import search_rates, format_rates_for_llm
from llm.llm_client import answer_query_with_llm
from utils.logger import get_logger
from workflow.hotel_discovery_agent import HotelDiscoveryAgent
from database.hotel_management import HotelManager
import re

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
        self.last_hotel = None  # Remember last mentioned hotel
        self.current_flow = None  # Tracks active flow (e.g., 'budget')
        self.flow_context = {}    # Stores context for the active flow
        logger.info("ChatInterface initialized with conversation memory")
    
    
    def _handle_save_email(self, user_query: str) -> str:
        """
        Handle manual email save commands.
        Example: "save email reservations@hotel.com for Galle Face Hotel"
        """
        import re
        from database.hotel_management import HotelManager
        
        # Extract email and hotel name
        # Pattern: save/add email <email> for <hotel>
        pattern = r'(?:save|add)\s+email\s+([\w._%+-]+@[\w.-]+\.[a-zA-Z]{2,})\s+(?:for|to)\s+(.+?)(?:\?|$)'
        match = re.search(pattern, user_query, re.IGNORECASE)
        
        if not match:
            return "Please use format: 'save email address@hotel.com for Hotel Name'"
        
        email = match.group(1).strip()
        hotel_name = match.group(2).strip()
        
        # Ask for purpose (or extract from query if mentioned)
        purpose = "general"
        if 'reservation' in user_query.lower():
            purpose = "reservations"
        elif 'sales' in user_query.lower():
            purpose = "sales"
        
        # Save to database
        manager = HotelManager()
        hotel_id = manager.get_or_create_hotel(hotel_name)
        
        manager.upsert_hotel_email(
            hotel_id=hotel_id,
            email=email,
            purpose=purpose,
            source_type="manual",
            confidence=1.0
        )
        
        return f"✅ Saved {email} for {hotel_name} (purpose: {purpose})"

    def _handle_rate_request(self, user_query: str) -> str:
        """
        Handle rate request email generation.
        Example: "Send rate request to Seaside Resort"
        """
        from email_handler.outlook_sender import OutlookSender
        from database.hotel_management import HotelManager
        from utils.logger import get_logger
        
        logger = get_logger(__name__)
        
        # Extract hotel name
        pattern = r'(?:send|create|draft).*?rate request.*?(?:to|for)\s+(.+?)(?:\?|$)'
        match = re.search(pattern, user_query, re.IGNORECASE)
        
        if not match:
            # Fallback: try to see if just "rate request" and we have context
            if "rate request" in user_query.lower() and self.last_hotel:
                hotel_name = self.last_hotel
            else:
                return "Please specify the hotel. Example: 'Send rate request to Seaside Resort'"
        else:
            hotel_name = match.group(1).strip()
        
        # Try to find email in database
        manager = HotelManager()
        emails = manager.get_hotel_emails(hotel_name)
        
        # Prioritize 'reservations' then 'sales' then general
        hotel_email = None
        for purpose in ['reservations', 'sales', 'general']:
            if purpose in emails:
                hotel_email = emails[purpose]
                break
        
        if not hotel_email and emails:
            hotel_email = list(emails.values())[0]

        if not hotel_email:
             # TRY PROACTIVE DISCOVERY
             logger.info(f"No email found for {hotel_name}. Triggering proactive discovery...")
             agent = HotelDiscoveryAgent()
             discovery_result = agent.run(hotel_name)
             
             if discovery_result.get('run_status') == 'success' and discovery_result.get('emails'):
                 # Prioritize 'reservations' then 'sales' then general
                 new_emails = {e['purpose']: e['email'] for e in discovery_result['emails']}
                 for purpose in ['reservations', 'sales', 'general']:
                     if purpose in new_emails:
                         hotel_email = new_emails[purpose]
                         break
                 if not hotel_email and discovery_result['emails']:
                     hotel_email = discovery_result['emails'][0]['email']
                 logger.info(f"Proactive discovery found email for {hotel_name}: {hotel_email}")

        if not hotel_email:
             # Fallback to general search logic or placeholder
             hotel_email = f"reservations@{hotel_name.lower().replace(' ', '')}.com"
             logger.warning(f"No email found for {hotel_name}, using placeholder: {hotel_email}")

        # Initialize sender
        from email_handler.outlook_reader import OutlookReader
        reader = OutlookReader()
        if reader.authenticate():
             sender = OutlookSender(access_token=reader.access_token)
        else:
             return "❌ Authentication failed. Please check your credentials."
             
        # Generate draft
        details = {'season': 'Winter 2025/2026'} 
        
        try:
            draft_content = sender.generate_rate_request_email(hotel_name, hotel_email, details)
            draft_id = sender.create_draft_email(
                to_recipients=[hotel_email],
                subject=draft_content['subject'],
                body=draft_content['body']
            )
            
            if draft_id:
                return f"✅ Rate request draft created for **{hotel_name}** to **{hotel_email}**. Check your Outlook Drafts folder."
            else:
                return f"❌ Failed to create draft for {hotel_name}."
        except Exception as e:
            logger.error(f"Error creating rate request: {e}")
            return f"❌ Error creating draft: {str(e)}"

    def _handle_discovery(self, user_query: str) -> str:
        """
        Connect to HotelDiscoveryAgent for email/contact search.
        """
        # Extract hotel name
        pattern = r'(?:find|get|search|discover).*?email.*?(?:for|of)\s+(.+?)(?:\?|$)'
        match = re.search(pattern, user_query, re.IGNORECASE)
        
        if not match:
            # Try fallback if hotel name is simple at end
            pattern_alt = r'(?:find|discover)\s+(.+?)\s+email'
            match = re.search(pattern_alt, user_query, re.IGNORECASE)
            
        if not match:
            return "Please tell me which hotel to search for. Example: 'Find email for Galle Face Hotel'"
            
        hotel_name = match.group(1).strip()
        manager = HotelManager()
        
        # Check DB first
        emails = manager.get_hotel_emails(hotel_name)
        if emails:
            e_str = ", ".join([f"{v} ({k})" for k, v in emails.items()])
            return f"🔍 I found these contacts in our database for **{hotel_name}**: {e_str}"
            
        # Trigger live discovery
        agent = HotelDiscoveryAgent()
        print(f"\n🕷️ Triggering live discovery for {hotel_name}...")
        result = agent.run(hotel_name)
        
        if result.get('run_status') == 'success' and result.get('emails'):
            e_list = [f"{e['email']} ({e['purpose']})" for e in result['emails']]
            e_str = ", ".join(e_list)
            return f"✅ Discovery successful! I found these emails for **{hotel_name}**: {e_str}. They have been saved to the database."
        elif result.get('run_status') == 'sources_not_found':
            return f"❌ I couldn't find any credible contact sources for **{hotel_name}** online. Please check the website manually."
        else:
            return f"❌ Discovery failed for **{hotel_name}**. Reason: {result.get('error', 'Unknown error')}"

    def _handle_workflow_trigger(self, user_query: str) -> str:
        """
        Handle workflow triggering commands.
        Example: "Check for new emails", "Process inbox"
        """
        from main import process_email_workflow
        import threading
        
        # Run in a separate thread to not block chat? 
        # For CLI, blocking is fine for now to show logs.
        
        print("\n🚀 Starting email processing workflow...\n")
        try:
            process_email_workflow()
            return "✅ Workflow cycle completed. Check logs for details."
        except Exception as e:
            return f"❌ Workflow failed: {str(e)}"
            
    def _handle_client_quote(self, user_query: str) -> str:
         # Placeholder for client quote
         return "ℹ️ Client quote generation via chat is coming soon!"

    
    def _handle_budget_calculation(self, user_query: str) -> str:
        """
        Handle 'budget' or 'cost' queries with strict transparency.
        """
        from llm.itinerary_extractor import ItineraryExtractor
        from calculator.budget import BudgetCalculator
        
        # 1. Extract params
        extractor = ItineraryExtractor()
        
        # If we have existing context, merge it
        if self.current_flow == 'budget' and self.flow_context:
            extracted_data = extractor.extract(user_query, context=self.flow_context.get('last_query'))
            # Merge context data into newly extracted data if missing
            for key in ['stays', 'currency', 'meal_plan', 'guests', 'child_ages']:
                 if not extracted_data.get(key) and self.flow_context.get(key):
                     extracted_data[key] = self.flow_context[key]
        else:
            extracted_data = extractor.extract(user_query)

        if extracted_data.get("missing_info") and not extracted_data.get("stays"):
            # If we already have stays in context, try to merge again or rely on context
            if self.current_flow == 'budget' and self.flow_context.get('stays'):
                 extracted_data['stays'] = self.flow_context['stays']
                 # Re-check missing info now that stays are merged
                 # Actually, better to just let it fall through to calculation
            else:
                self.current_flow = 'budget'
                self.flow_context = extracted_data
                self.flow_context['last_query'] = user_query
                logger.info(f"Setting flow to 'budget'. Missing: {extracted_data['missing_info']}")
                return f"To calculate the budget, I need: {', '.join(extracted_data['missing_info'])}. Please provide these details."
            
        if not extracted_data.get("stays"):
            logger.warning(f"No stays found in budget calculation for: {user_query}")
            self.current_flow = None
            self.flow_context = {}
            return "I couldn't identify any hotels or nights in your request. Please format like: '3 nights at Hotel A, 2 nights at Hotel B'."
            
        # 2. Calculate
        calculator = BudgetCalculator(db_path=self.db_path)
        # Use calculate_trip_cost instead of data = calculator...
        result = calculator.calculate_trip_cost(extracted_data)
        
        # Reset flow on success
        self.current_flow = None
        self.flow_context = {}
        
        # 3. Format Response (Strict Format)
        output = []
        output.append("### 💰 Trip Budget Calculation\n")
        
        # Section 1: Per-Hotel Breakdown
        for h in result.hotel_results:
            output.append(f"**{h.hotel_name}** ({h.nights} Nights)")
            output.append("-" * 30)
            
            if h.status == "MISSING_RATE":
                output.append("❌ Rate not found in database. Excluded from total.")
            elif h.status == "NO_SEASONAL_RATE":
                output.append("⚠️ **Missing Seasonal Rate**: No valid rate contract found for these specific dates. Excluded from total.")
            else:
                # Room Cost
                rc = h.room_cost
                output.append(f"**Room Rate**:")
                output.append(f"- Type: {rc.description}")
                output.append(f"- Calculation: `{rc.calculation_str} = {result.currency} {rc.amount:,.2f}`")
                
                # Supplements would go here
                
                output.append(f"**Subtotal**: {result.currency} {h.subtotal:,.2f}")
            
            if h.notes:
                for n in h.notes:
                    output.append(f"> ⚠️ {n}")
            output.append("")
            
        # Section 2: Total
        output.append("=" * 30)
        output.append(f"**TOTAL TRIP COST**: {result.currency} {result.total_cost:,.2f}")
        output.append("=" * 30)
        
        return "\n".join(output)

    def query(self, user_query: str) -> str:
        """
        Process a user query with conversation context.
        """
        logger.info(f"Processing query: {user_query}")
        query_lower = user_query.lower()

        # 0. State-based routing (Priority)
        logger.debug(f"Current flow: {self.current_flow}")
        if self.current_flow == 'budget':
            # Check if this query is trying to cancel or start something else
            if any(w in query_lower for w in ['cancel', 'stop', 'reset', 'exit']):
                self.current_flow = None
                self.flow_context = {}
                return "OK, I've cleared the current budget request. How else can I help?"
            
            # Follow-up info for budget
            return self._handle_budget_calculation(user_query)

        # 1. Budget / Cost Calculation
        if any(w in query_lower for w in ['budget', 'calculate', 'cost', 'quote', 'price for trip']):
            return self._handle_budget_calculation(user_query)
        
        # 2. Workflow Trigger
        if any(phrase in query_lower for phrase in ['check emails', 'process inbox', 'check for new emails', 'run workflow']):
             return self._handle_workflow_trigger(user_query)

        # 2. Rate Request
        if 'rate request' in query_lower and ('send' in query_lower or 'draft' in query_lower or 'create' in query_lower):
             return self._handle_rate_request(user_query)

        # 3. Client Quote
        if 'quote' in query_lower and ('send' in query_lower or 'draft' in query_lower):
             return self._handle_client_quote(user_query)
        
        # 4. Save Email
        if 'save email' in query_lower or 'add email' in query_lower:
            return self._handle_save_email(user_query)
        
        # 5. Discovery
        is_discovery = (
            ('email' in query_lower and any(word in query_lower for word in ['find', 'get', 'search', 'discover'])) or
            ('contact' in query_lower and any(word in query_lower for word in ['find', 'get', 'search', 'discover'])) or
            'discover' in query_lower
        )
        if is_discovery:
            return self._handle_discovery(user_query)
        
        # 6. Database Query (Default)
        # Extract search criteria from query using LLM with conversation context
        from llm.llm_client import extract_search_params_with_llm
        from database.query_price_items import search_price_items, format_price_items_for_llm
        
        # Build context-aware query
        context_query = user_query
        if self.last_hotel and not any(word in user_query.lower() for word in ['hotel', 'property', 'resort']):
            if not any(word in user_query.lower() for word in ['hi', 'hello', 'help']): # Ignore greetings
                context_query = f"Regarding {self.last_hotel}: {user_query}"
                logger.info(f"Adding context - Last hotel: {self.last_hotel}")
        
        params = extract_search_params_with_llm(context_query)
        logger.info(f"Extracted params: {params}")
        
        if params.get('hotel_name'):
            self.last_hotel = params['hotel_name']
        
        # Search DB
        rates = search_rates(
            hotel_name=params.get('hotel_name'),
            occupancy=params.get('occupancy'),
            date_range=params.get('date_range'),
            max_rate=params.get('max_rate'),
            db_path=self.db_path
        )
        price_items = search_price_items(
            hotel_name=params.get('hotel_name'),
            db_path=self.db_path
        )
        
        if not rates and not price_items:
            return "I couldn't find any rates or pricing information matching your criteria in the database."
        
        # Format context
        context_parts = []
        if rates:
            context_parts.append("BASE ROOM RATES:")
            context_parts.append(format_rates_for_llm(rates))
        if price_items:
            context_parts.append("\n" + format_price_items_for_llm(price_items))
        
        context = "\n".join(context_parts)
        answer = answer_query_with_llm(user_query, context)
        
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
