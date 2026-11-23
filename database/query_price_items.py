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
    """
    if db_path is None:
        from config import DB_PATH
        db_path = DB_PATH
    
    from database.db_init import get_db_connection
    
    logger.info(f"Searching price items: hotel={hotel_name}, category={category}")
    
    try:
        # 1. Try Airtable first
        from database.airtable_client import AirtableClient, formula_str as q
        try:
            airtable = AirtableClient()
            if airtable.is_connected():
                formulas = []
                if hotel_name:
                    formulas.append(f"SEARCH(LOWER({q(hotel_name)}), LOWER({{Hotel Name}}))")
                if category:
                    formulas.append(f"{{Category}}={q(category)}")
                
                formula = f"AND({', '.join(formulas)})" if formulas else None
                records = airtable.price_items_table.all(formula=formula)
                
                if records:
                    logger.info(f"Found {len(records)} price items in Airtable")
                    results = []
                    for r in records:
                        f = r['fields']
                        results.append({
                            'hotel_name': f.get('Hotel Name'),
                            'category': f.get('Category'),
                            'description': f.get('Description'),
                            'price': f.get('Price'),
                            'currency': f.get('Currency'),
                            'per_unit': f.get('Per Unit'),
                            'adult_or_child': f.get('Adult or Child'),
                            'age_range': f.get('Age Range'),
                            'applicable_room_types': f.get('Applicable Room Types'),
                            'applicable_dates': f.get('Applicable Dates'),
                            'meal_type': f.get('Meal Type'),
                            'conditions': f.get('Conditions'),
                            'source_text_snippet': f.get('Source Text'),
                            'source_file': f.get('Source File')
                        })
                    return results
        except Exception as e:
            logger.warning(f"Airtable price_items query failed: {e}")

        # 2. Fallback to SQLite
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
        
        results = [dict(row) for row in rows]
        return results
    except Exception as e:
        logger.error(f"Failed to search price items: {e}")
        return []


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
