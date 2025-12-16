"""
Database initialization module.
Sets up SQLite database for storing hotel rate data.
"""

import sqlite3
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)


def initialize_database(db_path: Path) -> bool:
    """
    Initialize the SQLite database with required tables.
    
    Args:
        db_path: Path to SQLite database file
    
    Returns:
        True if successful, False otherwise
    
    TODO:
        - Create rates table with all required fields
        - Create indexes for common queries
        - Add audit/tracking tables
        - Implement migration system for schema changes
        - Add support for Airtable as alternative backend
    """
    logger.info(f"Initializing database at {db_path}")
    
    try:
        # Ensure directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create rates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hotel_name TEXT NOT NULL,
                room_type TEXT NOT NULL,
                rate_per_night REAL NOT NULL,
                currency TEXT NOT NULL,
                meal_plan TEXT,
                season_start_date TEXT NOT NULL,
                season_end_date TEXT NOT NULL,
                conditions TEXT,
                validity_date TEXT,
                source_file TEXT,
                extracted_at TEXT,
                confidence REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_hotel_name 
            ON rates(hotel_name)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_dates 
            ON rates(season_start_date, season_end_date)
        """)
        
        # Create processing log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processing_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id TEXT,
                filename TEXT,
                status TEXT,
                error_message TEXT,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create extended contract data table (JSON storage)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contract_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hotel_name TEXT,
                source_file TEXT,
                raw_json TEXT,  -- Storing the full JSON output here
                extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create price items table (granular pricing data)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hotel_name TEXT,
                source_file TEXT,
                category TEXT,
                description TEXT,
                price REAL,
                currency TEXT,
                per_unit TEXT,
                adult_or_child TEXT,
                age_range TEXT,
                applicable_room_types TEXT,
                applicable_dates TEXT,
                meal_type TEXT,
                conditions TEXT,
                source_text_snippet TEXT,
                extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        
        logger.info("Database initialized successfully")
        return True
    
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False


def get_db_connection(db_path: Path) -> sqlite3.Connection:
    """
    Get a connection to the database.
    
    Args:
        db_path: Path to SQLite database file
    
    Returns:
        SQLite connection object
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn
