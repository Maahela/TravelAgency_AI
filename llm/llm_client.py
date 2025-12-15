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
    
    Args:
        query: User's question
        context: Relevant context from database
    
    Returns:
        LLM-generated answer
    
    TODO:
        - Implement retrieval-augmented generation (RAG)
        - Format context for optimal LLM understanding
        - Add citation of sources in response
        - Handle "I don't know" cases gracefully
    """
    logger.info(f"TODO: Answer query with LLM: {query}")
    
    # system_message = "Answer the user's question based only on the provided context."
    # prompt = f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
    # 
    # response = generate_llm_response(prompt, system_message)
    
    return ""
