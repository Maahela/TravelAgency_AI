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

