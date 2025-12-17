"""
Prompts for the Hotel Discovery Agent (V2).
"""

def get_discovery_agent_prompt(source_type: str, source_text: str) -> str:
    """
    Generate prompt for extracting and classifying emails from a specific source.
    """
    return f"""
    You are an AI Hotel Contact Discovery Agent.
    
    TASK: Analyze the following text text from a hotel's {source_type} to find official contact emails.
    
    SOURCE TEXT:
    {source_text[:10000]}  # Limit context window if needed
    
    INSTRUCTIONS:
    1. Extract ALL explicitly listed email addresses.
    2. Do NOT guess or fabricate. Ignore obfuscated text you cannot decode.
    3. Classify each email:
       - Purpose: 'reservations', 'sales', 'contracts', 'general', 'unknown'.
       - Confidence: 0.0 to 1.0 (1.0 = Explicitly labeled, 0.8 = inferred from context/local-part, <0.5 = personal email like gmail).
    4. Reasoning: Brief explanation for the classification.
    
    OUTPUT FORMAT (Strict JSON):
    {{
      "emails": [
        {{
          "email": "example@hotel.com",
          "purpose": "reservations",
          "confidence": 0.95,
          "reasoning": "Listed under 'Reservations' heading"
        }}
      ]
    }}
    
    Return ONLY valid JSON. If no emails found, return {{ "emails": [] }}.
    """
    
def get_validation_prompt(existing_data: str, new_findings: str) -> str:
    """
    Prompt for Step 4 (Change Detection) - Optional, can be done via code, 
    but LLM helps with fuzzy matching or reasoning.
    For now, we might do strict matching in code, so this is a placeholder.
    """
    pass
