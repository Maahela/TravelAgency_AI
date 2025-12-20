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
        # 1. Check for duplicates in SQLite (Source of Truth for state)
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        if check_duplicate(cursor, rate_data):
            conn.close()
            # We return True because it's "successfully processed" (skipped)
            # rather than an error that needs retrying
            return True
            
        # 2. Sync to Airtable (if not duplicate)
        from database.airtable_client import AirtableClient
        try:
            airtable = AirtableClient()
            if airtable.is_connected():
                airtable.insert_rate(rate_data)
        except Exception as e:
            logger.warning(f"Failed to sync rate to Airtable: {e}")
            
        # 3. Resolve 3NF IDs (Hotel, Room Type, Meal Plan)
        from database.hotel_management import HotelManager
        hm = HotelManager(db_path)
        
        # Hotel
        hotel_id = hm.get_or_create_hotel(rate_data.get('hotel_name'))
        
        # Room Type
        room_type_id = None
        if hotel_id and rate_data.get('room_type'):
            room_type_id = hm.get_or_create_room_type(hotel_id, rate_data.get('room_type'))
            
        # Meal Plan
        meal_plan_id = hm.get_or_create_meal_plan(rate_data.get('meal_plan'))

        # 4. Insert to SQLite
        cursor.execute("""
            INSERT INTO rates (
                hotel_name, room_type, occupancy, rate_per_night, currency,
                meal_plan, season_start_date, season_end_date,
                conditions, validity_date, source_file, 
                extracted_at, confidence,
                room_type_id, meal_plan_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rate_data.get('hotel_name'),
            rate_data.get('room_type'),
            rate_data.get('occupancy'),
            rate_data.get('rate_per_night'),
            rate_data.get('currency'),
            rate_data.get('meal_plan'),
            rate_data.get('season_start_date'),
            rate_data.get('season_end_date'),
            rate_data.get('conditions'),
            rate_data.get('validity_date'),
            rate_data.get('source_file'),
            rate_data.get('extracted_at'),
            rate_data.get('confidence', 1.0),
            room_type_id,
            meal_plan_id
        ))
        
        conn.commit()
        rate_id = cursor.lastrowid
        conn.close()

        # 3. Log Hotel Contact if email exists in rate_data (from discovery)
        email = rate_data.get('hotel_email') or rate_data.get('email')
        if email and rate_data.get('hotel_name'):
            try:
                from database.airtable_client import AirtableClient
                airtable = AirtableClient()
                if airtable.is_connected():
                    airtable.log_hotel_contact(
                        hotel_name=rate_data['hotel_name'],
                        email=email,
                        source="Email Extraction",
                        confidence=rate_data.get('confidence', 1.0)
                    )
            except Exception as e:
                logger.warning(f"Failed to log hotel contact: {e}")
        
        logger.info(f"Rate inserted successfully with ID {rate_id}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to insert rate: {e}")
        return False


def check_duplicate(cursor, rate_data: Dict) -> bool:
    """
    Check if a rate already exists in the database.
    Matches against: Hotel, Room, Meal Plan, Dates, and Occupancy.
    """
    try:
        # Build query components dynamically based on available fields
        conditions = [
            "hotel_name = ?",
            "room_type = ?",
            "meal_plan = ?",
            "season_start_date = ?",
            "season_end_date = ?"
        ]
        params = [
            rate_data.get('hotel_name'),
            rate_data.get('room_type'),
            rate_data.get('meal_plan'),
            rate_data.get('season_start_date'),
            rate_data.get('season_end_date')
        ]
        
        # Check occupancy if present in data
        if rate_data.get('occupancy'):
            conditions.append("occupancy = ?")
            params.append(rate_data.get('occupancy'))
            
        query = f"SELECT id FROM rates WHERE {' AND '.join(conditions)}"
        
        cursor.execute(query, tuple(params))
        result = cursor.fetchone()
        
        if result:
            logger.info("Duplicate rate found (ID: %s) - Skipping", result[0])
            return True
            
        return False
        
    except Exception as e:
        logger.error(f"Error checking duplicates: {e}")
        return False


def insert_rates_batch(rates: List[Dict], db_path: Path) -> int:
    """
    Insert multiple rate records in a single transaction.
    """
    logger.info(f"Batch processing {len(rates)} rates...")
    
    success_count = 0
    for rate in rates:
        if insert_rate(rate, db_path):
            success_count += 1
    
    logger.info(f"Batch complete. Inserted {success_count}/{len(rates)} rates.")
    return success_count


def log_processing_status(
    email_id: str,
    filename: str,
    status: str,
    error_message: str = None,
    db_path: Path = None
) -> bool:
    """
    Log file processing status to database and Airtable.
    """
    # 1. Log to Airtable
    from database.airtable_client import AirtableClient
    try:
        airtable = AirtableClient()
        if airtable.is_connected():
            airtable.log_processing(email_id, filename, status, error_message)
    except Exception as e:
        logger.warning(f"Failed to log to Airtable (non-critical): {e}")

    # 2. Log to SQLite
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
