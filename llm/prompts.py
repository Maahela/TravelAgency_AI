"""
Prompt templates for LLM interactions.
"""

from typing import Dict


def get_rate_parsing_prompt(extracted_text: str) -> str:
    """Generate prompt for parsing hotel rate data."""
    prompt = f"""Extract hotel rate information from text as JSON.
Required: hotel_name, room_type, rate_per_night, currency, meal_plan,
season_start_date, season_end_date, conditions, validity_date.

Text: {extracted_text}

Return ONLY valid JSON."""
    return prompt


def get_email_generation_prompt(email_type: str, context: Dict) -> str:
    """Generate prompt for creating email content."""
    if email_type == 'rate_request':
        return f"""Write professional hotel rate request email.
Hotel: {context.get('hotel_name', '[Hotel Name]')}
Return JSON with 'subject' and 'body' keys."""
    return f"Generate email type '{email_type}' with context: {context}"


def get_query_answering_prompt(query: str, context: str) -> str:
    """Generate prompt for answering queries."""
    return f"""Answer based ONLY on provided rate information.
Rates: {context}
Question: {query}
Answer:"""
