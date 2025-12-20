"""
LLM client for parsing and processing text using AI models.
Abstracted to support multiple LLM providers.
"""

from typing import Optional, Dict
from utils.logger import get_logger

logger = get_logger(__name__)


def generate_llm_response(
    prompt: str,
    system_message: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.1
) -> str:
    """
    Generate a response from the LLM based on the prompt.
    Supports automatic rotation between multiple Google API keys on quota exhaustion.
    """
    from config import OPENAI_API_KEY, GOOGLE_API_KEYS, LLM_MODEL
    import google.generativeai as genai
    
    # Try Google API Keys with rotation
    if GOOGLE_API_KEYS:
        for key_index, api_key in enumerate(GOOGLE_API_KEYS):
            try:
                genai.configure(api_key=api_key)
                model_name = "gemini-2.5-flash"
                
                # Construct prompt with system message
                full_prompt = ""
                if system_message:
                    full_prompt += f"System: {system_message}\n\n"
                full_prompt += f"User: {prompt}"
                
                model = genai.GenerativeModel(model_name)
                logger.info(f"Sending request to Google Gemini (Key #{key_index + 1})")
                response = model.generate_content(full_prompt)
                return response.text
                
            except Exception as e:
                error_str = str(e)
                
                # Check if it's a quota error (check both exception message and type)
                is_quota_error = (
                    "quota" in error_str.lower() or 
                    "429" in error_str or
                    "resourceexhausted" in error_str.lower() or
                    type(e).__name__ == "ResourceExhausted"
                )
                
                if is_quota_error:
                    logger.info(f"Key #{key_index + 1} quota exceeded. Trying next key...")
                    
                    # If this was the last key, raise the error
                    if key_index == len(GOOGLE_API_KEYS) - 1:
                        logger.error(f"All {len(GOOGLE_API_KEYS)} Google API keys exhausted.")
                        return f"Error: All Google API keys have exceeded their quota. Please try again later."
                    
                    # Otherwise, continue to next key
                    continue
                else:
                    # Non-quota error, don't retry
                    logger.error(f"LLM generation failed (Key #{key_index + 1}): {e}")
                    return f"Error generating response: {e}"
    
    # Fallback to OpenAI
    elif OPENAI_API_KEY:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        return "Error: OpenAI fallback not fully implemented. Please use Google Keys."
    else:
        logger.error("No valid API Key found (GOOGLE_API_KEYS or OPENAI_API_KEY).")
        return "Error: API key missing."












def generate_email_with_llm(
    email_type: str,
    context: Dict
) -> Dict[str, str]:
    """
    Generate email content using LLM.
    
    Args:
        email_type: Type of email ('rate_request', 'client_quote', etc.)
        context: Context data for email generation
    
    Returns:
        Dictionary with 'subject' and 'body'
    
    TODO:
        - Load email generation prompt templates
        - Add personalization based on context
        - Ensure professional tone and formatting
        - Support multiple languages
        - Add agency branding/signature
    """
    from llm.prompts import get_email_generation_prompt
    import json
    
    logger.info(f"Generating {email_type} email with LLM")
    
    prompt = get_email_generation_prompt(email_type, context)
    # Heat up temperature slightly for creative writing, but keep it low for structure
    response = generate_llm_response(prompt, temperature=0.2)
    
    try:
        # Clean response
        clean_json = response.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json.split("```json")[1].split("```")[0]
        elif clean_json.startswith("```"):
             clean_json = clean_json.split("```")[1].split("```")[0]
             
        data = json.loads(clean_json)
        
        # Validation
        if 'subject' not in data or 'body' not in data:
            logger.error("LLM email generation missing subject or body")
            return {
                'subject': f"Draft: {email_type} (Generation Failed)",
                'body': f"<p>Error generating email. Raw output:</p><pre>{response}</pre>"
            }
            
        return data
        
    except Exception as e:
        logger.error(f"Failed to generate email JSON: {e}")
        return {
            'subject': f"Draft: {email_type} (Error)",
            'body': f"<p>Error parsing LLM response: {e}</p>"
        }


def answer_query_with_llm(query: str, context: str) -> str:
    """
    Answer a query using LLM with provided context (RAG pattern).
    """
    system_message = """
    You are a professional travel agency assistant. Answer the user's question using ONLY the provided hotel rate data.
    
    CRITICAL FORMATTING RULES:
    1. **Structured Layout**: Use Markdown headers (###) and bold text for clarity.
    2. **Group by Room**: Group rates by Room Type first.
    3. **Markdown Tables**: For each room type, use a table to show:
       | Rate (Standardized) | Meal Plan | Season | Notes |
       | :--- | :--- | :--- | :--- |
    4. **Supplemental Info**: If 'ADDITIONAL CHARGES' are in context, create a separate section "📋 Related Information & Charges" for supplements, extra beds, etc.
    5. **Tone**: Be helpful and concise.
    """
    prompt = f"Context Data:\n{context}\n\nUser Question: {query}\n\nAnswer:"
    
    return generate_llm_response(prompt, system_message, temperature=0.1)


def extract_search_params_with_llm(query: str) -> Dict:
    """
    Extract search parameters from natural language query using LLM.
    Returns a dictionary matching search_rates arguments.
    """
    import json
    
    system_message = """
    You are a search query parser. Extract search parameters from the user's query into a JSON object.
    Fields allowed: 
    - 'hotel_name' (string): Name of the hotel.
    - 'max_rate' (number): Maximum price per night.
    - 'occupancy' (string): Look for "Single", "Double", "Triple", "Extra Adult", "Extra Child".
    - 'date_range' (array of 2 strings): Extract year-month-day (e.g., ["2026-01-01", "2026-01-31"]).
    
    Do NOT extract descriptions - we want to retrieve all matching rooms for the hotel.
    Return ONLY valid JSON.
    """
    prompt = f"Query: {query}\n\nJSON:"
    
    response = generate_llm_response(prompt, system_message, temperature=0.0)
    
    try:
        # Clean response to ensure only JSON
        clean_json = response.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json.split("```json")[1].split("```")[0]
        elif clean_json.startswith("```"):
             clean_json = clean_json.split("```")[1].split("```")[0]
             
        return json.loads(clean_json)
    except Exception as e:
        logger.error(f"Failed to parse search params JSON: {e}")
        return {}


def extract_contact_info_with_llm(search_snippets: str) -> Dict:
    """
    Extract hotel contact info from search result snippets using LLM.
    """
    from llm.prompts import get_contact_extraction_prompt
    import json
    
    prompt = get_contact_extraction_prompt(search_snippets)
    response = generate_llm_response(prompt, temperature=0.0)
    
    try:
        clean_json = response.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json.split("```json")[1].split("```")[0]
        elif clean_json.startswith("```"):
             clean_json = clean_json.split("```")[1].split("```")[0]
             
        data = json.loads(clean_json)
        return data
    except Exception as e:
        logger.error(f"Failed to parse contact info JSON: {e}")
        return {}
