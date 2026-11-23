"""
Database query operations for retrieving hotel rate data.
"""

from typing import List, Dict, Optional
import sqlite3
from pathlib import Path
from database.db_init import get_db_connection
from utils.logger import get_logger

logger = get_logger(__name__)


def search_rates(
    hotel_name: Optional[str] = None,
    room_type: Optional[str] = None,
    meal_plan: Optional[str] = None,  # Added meal_plan argument
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
        meal_plan: Filter by meal plan (e.g., 'BB', 'HB')
        date_range: Tuple of (start_date, end_date) to search within
        max_rate: Maximum rate per night
        db_path: Path to database
    
    Returns:
        List of matching rate records
    """
    if db_path is None:
        from config import DB_PATH
        db_path = DB_PATH
    
    logger.info(f"Searching rates: hotel={hotel_name}, room={room_type}, meal={meal_plan}, max_price={max_rate}")
    
    try:
        # 1. Try Airtable first
        from database.airtable_client import AirtableClient, formula_str as q
        try:
            airtable = AirtableClient()
            if airtable.is_connected():
                # Build formula (all user/LLM-supplied values are escaped via q())
                formulas = []
                if hotel_name:
                    formulas.append(f"SEARCH(LOWER({q(hotel_name)}), LOWER({{Hotel Name}}))")

                if meal_plan:
                    # Flexible search for meal plan code or name
                    formulas.append(f"OR(SEARCH(LOWER({q(meal_plan)}), LOWER({{Meal Plan}})), {{Meal Plan}}={q(meal_plan)})")

                if occupancy:
                    formulas.append(f"OR({{Occupancy}}={q(occupancy)}, SEARCH(LOWER({q(occupancy)}), LOWER({{Room Type}})), {{Occupancy}}=BLANK())")

                if date_range:
                    start, end = date_range
                    formulas.append(f"{{Season Start}} <= {q(end)}")
                    formulas.append(f"{{Season End}} >= {q(start)}")
                
                formula = f"AND({', '.join(formulas)})" if formulas else None
                
                records = airtable.rates_table.all(formula=formula)
                if records:
                    logger.info(f"Found {len(records)} rates in Airtable")
                    
                    # Cache room/meal names
                    room_type_cache = {}
                    meal_plan_cache = {}
                    try:
                        all_room_types = airtable.room_types_table.all()
                        for rt in all_room_types:
                            room_type_cache[rt['id']] = rt['fields'].get('Name', '')
                        
                        all_meal_plans = airtable.meal_plans_table.all()
                        for mp in all_meal_plans:
                            meal_plan_cache[mp['id']] = mp['fields'].get('Name', '')
                    except Exception as e:
                        logger.warning(f"Failed to fetch room types/meal plans cache: {e}")
                    
                    results = []
                    for r in records:
                        f = r['fields']
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
                        resolved_meal_plan_name = ''
                        if isinstance(meal_plan_ids, list) and meal_plan_ids:
                            resolved_meal_plan_name = meal_plan_cache.get(meal_plan_ids[0], 'BB')
                        
                        # Verify Meal Plan logic if not filtered in API
                        if meal_plan and meal_plan.lower() not in resolved_meal_plan_name.lower():
                             continue

                        results.append({
                            'hotel_name': f.get('Hotel Name'),
                            'room_type': room_type_name,
                            'occupancy': f.get('Occupancy'),
                            'rate_per_night': price,
                            'currency': f.get('Currency', 'USD'),
                            'meal_plan': resolved_meal_plan_name,
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
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Enhanced query with JOINs
        query = """
            SELECT 
                r.*, 
                rt.name as joined_room_type, 
                mp.name as joined_meal_plan 
            FROM rates r
            LEFT JOIN room_types rt ON r.room_type_id = rt.id
            LEFT JOIN meal_plans mp ON r.meal_plan_id = mp.id
            WHERE 1=1
        """
        params = []
        
        if hotel_name:
            query += " AND r.hotel_name LIKE ?"
            params.append(f"%{hotel_name}%")
        
        if room_type:
            query += " AND (r.room_type LIKE ? OR rt.name LIKE ?)"
            params.extend([f"%{room_type}%", f"%{room_type}%"])
            
        if meal_plan:
             # Check explicit meal plan column or joined name
            query += " AND (r.meal_plan LIKE ? OR mp.name LIKE ?)"
            params.extend([f"%{meal_plan}%", f"%{meal_plan}%"])
        
        if occupancy:
            query += " AND (r.occupancy = ? OR r.room_type LIKE ? OR rt.name LIKE ? OR r.occupancy IS NULL)"
            params.extend([occupancy, f"%{occupancy}%", f"%{occupancy}%"])
        
        if date_range:
            start_date, end_date = date_range
            query += " AND r.season_start_date <= ? AND r.season_end_date >= ?"
            params.extend([end_date, start_date])
        
        if max_rate:
            query += " AND r.rate_per_night <= ?"
            params.append(max_rate)
        
        query += " ORDER BY r.hotel_name, r.rate_per_night"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Normalize results
        results = []
        for row in rows:
            d = dict(row)
            if d.get('joined_room_type'):
                d['room_type'] = d['joined_room_type']
            if d.get('joined_meal_plan'):
                d['meal_plan'] = d['joined_meal_plan']
            results.append(d)

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
