"""
Query functions for price_items table.
"""
from pathlib import Path
from typing import List, Dict, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


def search_price_items(
    hotel_name: Optional[str] = None,
    category: Optional[str] = None,
    db_path: Optional[Path] = None
) -> List[Dict]:
    """
    Search price items table.
    
    Args:
        hotel_name: Filter by hotel name
        category: Filter by category (meal_rate, extra_bed_charge, etc.)
        db_path: Path to database
    
    Returns:
        List of matching price items
    """
    if db_path is None:
        from config import DB_PATH
        db_path = DB_PATH
    
    from database.db_init import get_db_connection
    
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    # Build query
    query = "SELECT * FROM price_items WHERE 1=1"
    params = []
    
    if hotel_name:
        query += " AND LOWER(hotel_name) LIKE LOWER(?)"
        params.append(f"%{hotel_name}%")
    
    if category:
        query += " AND category = ?"
        params.append(category)
    
    query += " ORDER BY id DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    logger.info(f"Found {len(rows)} price items")
    
    # Convert to dictionaries
    results = []
    for row in rows:
        results.append(dict(row))
    
    return results


def format_price_items_for_llm(items: List[Dict]) -> str:
    """
    Format price items for LLM context.
    """
    if not items:
        return ""
    
    lines = ["ADDITIONAL CHARGES AND RATES:\n"]
    
    for item in items:
        line = f"- {item.get('description', 'N/A')}: "
        line += f"{item.get('currency', 'USD')} {item.get('price', 0)} "
        line += f"({item.get('per_unit', 'N/A')})"
        
        if item.get('adult_or_child'):
            line += f" [{item['adult_or_child']}]"
        
        if item.get('source_text_snippet'):
            line += f" - Source: \"{item['source_text_snippet'][:60]}...\""
        
        lines.append(line)
    
    return "\n".join(lines)
