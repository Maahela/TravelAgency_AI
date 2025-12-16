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
    
    Args:
        prompt: User prompt/query
        system_message: System instructions for the LLM
        model: Model name (defaults to config.LLM_MODEL)
        temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
    
    Returns:
        LLM response as string
    
    TODO:
        - Implement OpenAI API integration
        - Add error handling and retries
        - Implement token counting and cost tracking
        - Add response caching for identical prompts
        - Support streaming responses for long outputs
        - Add timeout handling
    """
    from config import OPENAI_API_KEY, LLM_MODEL
    import os
    import google.generativeai as genai
    
    # Check for Google API Key first (since user requested switch)
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    try:
        if GOOGLE_API_KEY:
            # Use Google Gemini
            genai.configure(api_key=GOOGLE_API_KEY)
            # gemini-flash-latest is the stable alias, safer for free tier
            model_name = "gemini-flash-latest" 
            
            # Construct prompt with system message
            full_prompt = ""
            if system_message:
                full_prompt += f"System: {system_message}\n\n"
            full_prompt += f"User: {prompt}"
            
            model = genai.GenerativeModel(model_name)
            logger.debug(f"Sending request to Google Gemini")
            response = model.generate_content(full_prompt)
            return response.text

        elif OPENAI_API_KEY:
            # Fallback to OpenAI if Google key missing but OpenAI key present
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            # ... (OpenAI implementation omitted for brevity, keeping existing logic if needed)
            # For now, replacing strictly with Gemini focus as requested
            return "Error: OpenAI fallback not fully implemented in this switch. Please use Google Key."
            
        else:
            logger.error("No valid API Key found (GOOGLE_API_KEY or OPENAI_API_KEY).")
            return "Error: API key missing."

    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        return f"Error generating response: {e}"


def parse_rate_with_llm(extracted_text: str) -> Dict:
    """
    Parse hotel rate information from extracted text using LLM.
    
    Args:
        extracted_text: Raw text extracted from PDF/image
    
    Returns:
        Structured rate data dictionary
    
    TODO:
        - Load rate parsing prompt template
        - Use structured output (JSON mode)
        - Validate LLM response format
        - Handle partial/incomplete extractions
        - Add confidence scoring based on LLM output
    """
    from llm.prompts import get_rate_parsing_prompt
    
    logger.info("TODO: Parse rate data with LLM")
    
    # system_message = "You are an expert at extracting structured hotel rate information from text."
    # prompt = get_rate_parsing_prompt(extracted_text)
    # 
    # response = generate_llm_response(prompt, system_message, temperature=0.0)
    # 
    # # Parse JSON response
    # import json
    # rate_data = json.loads(response)
    
    rate_data = {}
    
    return rate_data


def parse_extended_contract_data(extracted_text: str) -> Dict:
    """
    Parse complex contract data (policies, supplements) using LLM.
    """
    from llm.prompts import get_extended_contract_extraction_prompt
    import json
    
    prompt = get_extended_contract_extraction_prompt(extracted_text)
    # Use a creative temperature to allow for better interpretation of complex policy text
    # but strict enough for JSON structure.
    response = generate_llm_response(prompt, temperature=0.1)
    
    try:
        # Clean response
        clean_json = response.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json.split("```json")[1].split("```")[0]
        elif clean_json.startswith("```"):
             clean_json = clean_json.split("```")[1].split("```")[0]
             
        data = json.loads(clean_json)
        return data
    except Exception as e:
        logger.error(f"Failed to parse extended contract JSON: {e}")
        return {"error": str(e), "raw_response": response}


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
    
    logger.info(f"TODO: Generate {email_type} email with LLM")
    
    # system_message = "You are a professional travel agency assistant writing emails."
    # prompt = get_email_generation_prompt(email_type, context)
    # 
    # response = generate_llm_response(prompt, system_message, temperature=0.3)
    
    return {
        'subject': 'TODO: Generate subject',
        'body': 'TODO: Generate body'
    }


def answer_query_with_llm(query: str, context: str) -> str:
    """
    Answer a query using LLM with provided context (RAG pattern).
    """
    system_message = "You are a helpful travel agency assistant. Answer the user's question based ONLY on the provided hotel rate data. If the answer is not in the context, say you don't know."
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
    Fields allowed: 'hotel_name' (string), 'max_rate' (number).
    Do NOT extract 'room_type' or descriptions - we want to retrieve all rooms for the hotel.
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
