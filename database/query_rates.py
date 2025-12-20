"""
Database query operations for retrieving hotel rate data.
"""

from typing import List, Dict, Optional
from pathlib import Path
from database.db_init import get_db_connection
from utils.logger import get_logger

logger = get_logger(__name__)


def search_rates(
    hotel_name: Optional[str] = None,
    room_type: Optional[str] = None,
    date_range: Optional[tuple] = None,
    occupancy: Optional[str] = None,
    max_rate: Optional[float] = None,
    db_path: Optional[Path] = None
) -> List[Dict]:
    """
    Search for hotel rates based on criteria.
    
    Args:
        hotel_name: Filter by hotel name (partial match)
        room_type: Filter by room type
        date_range: Tuple of (start_date, end_date) to search within
        max_rate: Maximum rate per night
        db_path: Path to database
    
    Returns:
        List of matching rate records
    
    TODO:
        - Implement fuzzy search for hotel names
        - Add sorting options
        - Implement pagination
        - Add relevance scoring
    """
    if db_path is None:
        from config import DB_PATH
        db_path = DB_PATH
    
    logger.info(f"Searching rates: hotel={hotel_name}, room={room_type}")
    
    try:
        # 1. Try Airtable first
        from database.airtable_client import AirtableClient
        try:
            airtable = AirtableClient()
            if airtable.is_connected():
                # Build formula
                # Example: AND({Hotel Name}="X", {Price}<=Y)
                formulas = []
                if hotel_name:
                    # Case-insensitive search in Airtable
                    formulas.append(f"SEARCH(LOWER('{hotel_name}'), LOWER({{Hotel Name}}))")
                
                if occupancy:
                    # Flexible occupancy: match field OR room_type containing the word OR empty field
                    formulas.append(f"OR({{Occupancy}}='{occupancy}', SEARCH(LOWER('{occupancy}'), LOWER({{Room Type}})), {{Occupancy}}=BLANK())")
                
                if date_range:
                    # Precise date overlap for Airtable
                    start, end = date_range
                    formulas.append(f"{{Season Start}} <= '{end}'")
                    formulas.append(f"{{Season End}} >= '{start}'")
                
                formula = f"AND({', '.join(formulas)})" if formulas else None
                
                records = airtable.rates_table.all(formula=formula)
                if records:
                    logger.info(f"Found {len(records)} rates in Airtable")
                    
                    # Get room type and meal plan record names
                    # We need to resolve linked records to get actual names
                    room_type_cache = {}
                    meal_plan_cache = {}
                    
                    # Fetch all room types and meal plans for efficient lookup
                    try:
                        all_room_types = airtable.room_types_table.all()
                        for rt in all_room_types:
                            room_type_cache[rt['id']] = rt['fields'].get('Name', '')
                        
                        all_meal_plans = airtable.meal_plans_table.all()
                        for mp in all_meal_plans:
                            meal_plan_cache[mp['id']] = mp['fields'].get('Name', '')
                    except Exception as e:
                        logger.warning(f"Failed to fetch room types/meal plans cache: {e}")
                    
                    # Map back to standardized format
                    results = []
                    for r in records:
                        f = r['fields']
                        # Apply max_rate filter in python since Price is text/number mixed
                        price_str = str(f.get('Price', 0)).replace(',', '').replace('USD', '').replace('LKR', '').strip() or '0'
                        try:
                            price = float(price_str)
                        except:
                            price = 0
                        
                        if max_rate and price > max_rate:
                            continue
                        
                        # Resolve linked Room Type record to actual name
                        room_type_ids = f.get('Room Type', [])
                        room_type_name = ''
                        if isinstance(room_type_ids, list) and room_type_ids:
                            room_type_name = room_type_cache.get(room_type_ids[0], 'Unknown')
                        
                        # Resolve linked Meal Plan record to actual name
                        meal_plan_ids = f.get('Meal Plan', [])
                        meal_plan_name = ''
                        if isinstance(meal_plan_ids, list) and meal_plan_ids:
                            meal_plan_name = meal_plan_cache.get(meal_plan_ids[0], 'BB')
                            
                        results.append({
                            'hotel_name': f.get('Hotel Name'),
                            'room_type': room_type_name,
                            'occupancy': f.get('Occupancy'), # Added field
                            'rate_per_night': price, # Aligning with SQLite's 'rate_per_night'
                            'currency': f.get('Currency', 'USD'),
                            'meal_plan': meal_plan_name,
                            'source': 'Airtable',
                            'season_start_date': f.get('Season Start'),
                            'season_end_date': f.get('Season End'),
                            'conditions': f.get('Conditions')
                        })
                    return results
        except Exception as e:
            logger.warning(f"Airtable query failed, falling back to SQLite: {e}")

        # 2. Fallback to SQLite (Legacy)
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM rates WHERE 1=1"
        params = []
        
        if hotel_name:
            query += " AND hotel_name LIKE ?"
            params.append(f"%{hotel_name}%")
        
        if room_type:
            query += " AND room_type LIKE ?"
            params.append(f"%{room_type}%")
        
        if room_type:
            query += " AND room_type LIKE ?"
            params.append(f"%{room_type}%")
        
        if occupancy:
            # Flexible occupancy: match field OR room_type containing the word
            query += " AND (occupancy = ? OR room_type LIKE ? OR occupancy IS NULL)"
            params.extend([occupancy, f"%{occupancy}%"])
        
        if date_range:
            start_date, end_date = date_range
            query += " AND season_start_date <= ? AND season_end_date >= ?"
            params.extend([end_date, start_date])
        
        if max_rate:
            query += " AND rate_per_night <= ?"
            params.append(max_rate)
        
        query += " ORDER BY hotel_name, rate_per_night"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        results = [dict(row) for row in rows]
        conn.close()
        
        logger.info(f"Found {len(results)} matching rates")
        return results
    
    except Exception as e:
        logger.error(f"Failed to search rates: {e}")
        return []


def get_rate_by_id(rate_id: int, db_path: Optional[Path] = None) -> Optional[Dict]:
    """
    Retrieve a specific rate by ID.
    
    Args:
        rate_id: Rate record ID
        db_path: Path to database
    
    Returns:
        Rate record dictionary or None
    """
    if db_path is None:
        from config import DB_PATH
        db_path = DB_PATH
    
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM rates WHERE id = ?", (rate_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    except Exception as e:
        logger.error(f"Failed to get rate by ID: {e}")
        return None


def get_all_hotels(db_path: Optional[Path] = None) -> List[str]:
    """
    Get list of all unique hotel names.
    
    Args:
        db_path: Path to database
    
    Returns:
        List of hotel names
    """
    if db_path is None:
        from config import DB_PATH
        db_path = DB_PATH
    
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT hotel_name FROM rates ORDER BY hotel_name")
        rows = cursor.fetchall()
        conn.close()
        
        return [row['hotel_name'] for row in rows]
    
    except Exception as e:
        logger.error(f"Failed to get hotel list: {e}")
        return []


def format_rates_for_llm(rates: List[Dict]) -> str:
    """
    Format rate data as text context for LLM queries.
    
    Args:
        rates: List of rate dictionaries
    
    Returns:
        Formatted text string
    
    TODO:
        - Optimize formatting for LLM context window
        - Add structured formatting (tables, JSON)
        - Include relevance indicators
    """
    if not rates:
        return "No rates found."
    
    formatted = []
    for rate in rates:
        formatted.append(f"""
Hotel: {rate['hotel_name']}
Room: {rate['room_type']}
Rate: {rate['currency']} {rate['rate_per_night']}/night
Meal Plan: {rate.get('meal_plan', 'N/A')}
Season: {rate['season_start_date']} to {rate['season_end_date']}
Conditions: {rate.get('conditions', 'N/A')}
---""")
    
    return "\n".join(formatted)
