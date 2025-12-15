"""
Database insert operations for hotel rate data.
"""

from typing import Dict, List
from pathlib import Path
from database.db_init import get_db_connection
from utils.logger import get_logger

logger = get_logger(__name__)


def insert_rate(rate_data: Dict, db_path: Path) -> bool:
    """
    Insert a single rate record into the database.
    
    Args:
        rate_data: Dictionary containing rate information
        db_path: Path to SQLite database file
    
    Returns:
        True if successful, False otherwise
    
    TODO:
        - Add duplicate detection
        - Implement upsert logic (update if exists)
        - Add validation before insert
        - Handle constraint violations
    """
    logger.info(f"Inserting rate for {rate_data.get('hotel_name', 'Unknown')}")
    
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO rates (
                hotel_name, room_type, rate_per_night, currency,
                meal_plan, season_start_date, season_end_date,
                conditions, validity_date, source_file, 
                extracted_at, confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rate_data.get('hotel_name'),
            rate_data.get('room_type'),
            rate_data.get('rate_per_night'),
            rate_data.get('currency'),
            rate_data.get('meal_plan'),
            rate_data.get('season_start_date'),
            rate_data.get('season_end_date'),
            rate_data.get('conditions'),
            rate_data.get('validity_date'),
            rate_data.get('source_file'),
            rate_data.get('extracted_at'),
            rate_data.get('confidence', 1.0)
        ))
        
        conn.commit()
        rate_id = cursor.lastrowid
        conn.close()
        
        logger.info(f"Rate inserted successfully with ID {rate_id}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to insert rate: {e}")
        return False


def insert_rates_batch(rates: List[Dict], db_path: Path) -> int:
    """
    Insert multiple rate records in a single transaction.
    
    Args:
        rates: List of rate dictionaries
        db_path: Path to SQLite database file
    
    Returns:
        Number of successfully inserted records
    
    TODO:
        - Implement batch insert for better performance
        - Add rollback on partial failure
        - Return list of failed items
    """
    logger.info(f"Batch inserting {len(rates)} rates")
    
    success_count = 0
    for rate in rates:
        if insert_rate(rate, db_path):
            success_count += 1
    
    logger.info(f"Successfully inserted {success_count}/{len(rates)} rates")
    return success_count


def log_processing_status(
    email_id: str,
    filename: str,
    status: str,
    error_message: str = None,
    db_path: Path = None
) -> bool:
    """
    Log file processing status to database.
    
    Args:
        email_id: Email identifier
        filename: Name of processed file
        status: Processing status (success, failed, pending)
        error_message: Error message if failed
        db_path: Path to database
    
    Returns:
        True if logged successfully
    
    TODO:
        - Add more detailed status tracking
        - Implement retry mechanism
    """
    if db_path is None:
        from config import DB_PATH
        db_path = DB_PATH
    
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO processing_log (email_id, filename, status, error_message)
            VALUES (?, ?, ?, ?)
        """, (email_id, filename, status, error_message))
        
        conn.commit()
        conn.close()
        
        return True
    
    except Exception as e:
        logger.error(f"Failed to log processing status: {e}")
        return False
