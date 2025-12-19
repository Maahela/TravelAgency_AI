"""
Prompt templates for LLM interactions.
"""

from typing import Dict


def get_rate_parsing_prompt(extracted_text: str) -> str:
    """Generate prompt for parsing hotel rate data."""
    prompt = f"""Extract hotel rate information from text as JSON.
Required: hotel_name, room_type, occupancy (Single/Double/Triple), rate_per_night, currency, meal_plan,
season_start_date, season_end_date, conditions, validity_date.

Text: {extracted_text}

Return ONLY valid JSON."""
    return prompt


def get_email_generation_prompt(email_type: str, context: Dict) -> str:
    """Generate prompt for creating email content."""
    
    base_instructions = """
    You are a professional travel agency assistant. Write a polite, professional email based on the context provided.
    
    OUTPUT FORMAT (JSON ONLY):
    {
        "subject": "Clear, professional subject line",
        "body": "The email body in HTML format. Use <p>, <br>, <ul>, <li> tags for formatting. Do NOT use markdown in the body."
    }
    """
    
    if email_type == 'rate_request':
        specifics = f"""
        TASK: Write a Rate Request email to a hotel.
        Target Hotel: {context.get('hotel_name', '[Hotel Name]')}
        Specific Request: {context.get('request_details', 'General contract rates for the upcoming season')}
        
        Keep it concise but polite. Mention that we are updating our database for the upcoming season.
        """
    elif email_type == 'client_quote':
        specifics = f"""
        TASK: Write a Quote email to a client.
        Client Name: {context.get('client_name', 'Valued Client')}
        Hotel: {context.get('hotel_name')}
        Rates to Quote: {context.get('rate_data')}
        
        Present the rates clearly (you can use an HTML table if multiple options).
        """
    else:
        specifics = f"TASK: Write a generic email of type '{email_type}' with context: {context}"
        
    return f"{base_instructions}\n\n{specifics}\n\nReturn ONLY valid JSON."


def get_contact_extraction_prompt(search_results: str) -> str:
    """Generate prompt for extracting contact info from search snippets."""
    return f"""Analyze these search results for a hotel to find contact details.
    
    SEARCH RESULTS:
    {search_results}
    
    TASK: Extract valid email addresses and the official website.
    - Prioritize 'reservations@', 'info@', 'booking@' emails.
    - Ignore generic OTA emails (booking.com, expedia, etc.).
    - Output format (JSON):
    {{
        "email": "string or null",
        "website": "string or null",
        "phone": "string or null",
        "confidence": "high/medium/low"
    }}
    
    Return ONLY valid JSON."""


def get_query_answering_prompt(query: str, context: str) -> str:
    """Generate prompt for answering queries."""
    return f"""Answer based ONLY on provided rate information.
Rates: {context}
Question: {query}
Answer:"""


def get_extended_contract_extraction_prompt(extracted_text: str) -> str:
    """Generate prompt for deep contract data extraction."""
    return f"""You are a travel industry rate engine. Extract commercially relevant data from the contract text into structured JSON.

SECTIONS TO EXTRACT:
1) ROOM METADATA: room_name, max_adults, max_children, occupancy, size, description, allowed_beds (extra/sofa/cot).
2) OCCUPANCY rules: single/double/triple rules, child definitions.
3) MEAL SUPPLEMENTS: price_per_adult/child, meal_plans (HB, FB), inclusions.
4) EXTRA BED SUPPLEMENTS: prices for adults/children.
5) SPECIAL PACKAGES: Honeymoon, Anniversary, etc. (inclusions, prices).
6) OFFERS: "Stay X Pay Y", percentage discounts, booking windows.
7) SEASONAL RESTRICTIONS: Min stay, blackout dates.
8) POLICIES: Check-in/out, cancellation, payment.
9) OPERATIONAL NOTES: Transfers, child policies.

OUTPUT FORMAT (JSON ONLY):
{{
  "room_metadata": [],
  "occupancy_rules": [],
  "meal_supplements": [],
  "extra_bed_supplements": [],
  "special_packages": [],
  "offers_and_discounts": [],
  "seasonal_restrictions": [],
  "policies_and_terms": {{}},
  "operational_notes": [],
  "notes_for_manual_review": []
}}

TEXT TO EXTRACT FROM:
{extracted_text}

Return ONLY valid JSON."""


def get_price_items_extraction_prompt(extracted_text: str) -> str:
    """Generate prompt for extracting ALL priced items beyond base rates."""
    return f"""You are analyzing a hotel contract. Extract EVERY price mentioned that is NOT a base room rate.

CATEGORIES TO USE:
- meal_rate (e.g., "Breakfast $12")
- meal_plan_supplement (e.g., "HB supplement: $25")
- extra_person_charge
- extra_bed_charge
- child_rate
- deduction (e.g., "RO deduction: -$10")
- package_price
- upgrade_price
- offer_discount
- cancellation_fee
- policy_fee
- other_charge

FOR EACH PRICE, EXTRACT:
- category
- description
- price (numeric value)
- currency
- per_unit (per_person/per_night/per_meal/per_stay)
- adult_or_child (if specified)
- age_range (if applicable)
- applicable_room_types (if specified)
- applicable_dates (if specified)
- meal_type (breakfast/lunch/dinner if applicable)
- conditions
- source_text_snippet (exact quote from contract)

OUTPUT FORMAT (JSON ONLY):
{{
  "priced_items": [
    {{
      "category": "meal_rate",
      "description": "Breakfast per person",
      "price": 12.0,
      "currency": "USD",
      "per_unit": "per_person",
      "adult_or_child": "adult",
      "source_text_snippet": "Breakfast – $12 per person"
    }}
  ],
  "unclassified_prices": [],
  "notes_for_manual_review": []
}}

RULES:
- Do NOT skip prices in paragraphs
- If unsure about category, use "other_charge"
- Preserve exact wording in source_text_snippet
- Extract negative prices as deductions

TEXT TO ANALYZE:
{extracted_text}

Return ONLY valid JSON."""

