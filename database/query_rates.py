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
