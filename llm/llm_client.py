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
    
    if model is None:
        model = LLM_MODEL
    
    logger.info(f"TODO: Generate LLM response using {model}")
    logger.debug(f"Prompt length: {len(prompt)} characters")
    
    # Placeholder implementation:
    # import openai
    # openai.api_key = OPENAI_API_KEY
    # 
    # messages = []
    # if system_message:
    #     messages.append({"role": "system", "content": system_message})
    # messages.append({"role": "user", "content": prompt})
    # 
    # response = openai.ChatCompletion.create(
    #     model=model,
    #     messages=messages,
    #     temperature=temperature
    # )
    # 
    # return response.choices[0].message.content
    
    return ""


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
