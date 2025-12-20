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
                occupancy TEXT,
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
        
        # Migration: Add occupancy column if missing
        cursor.execute("PRAGMA table_info(rates)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'occupancy' not in columns:
            cursor.execute("ALTER TABLE rates ADD COLUMN occupancy TEXT")
        
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
        
        # Create hotels table (for rate refresh automation) - Updated V2
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hotels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                website TEXT,
                last_rate_request_date TEXT,
                last_discovery_run_at TEXT,
                contact_person TEXT,
                phone_number TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_rate_refresh_at TIMESTAMP
            )
        """)
        
        # Create hotel_emails table (Discovery Agent V2)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hotel_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hotel_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                purpose TEXT, -- 'reservations', 'sales', 'contracts', 'general', 'unknown'
                source_type TEXT, -- 'website', 'google_maps', 'ota', 'group_site'
                confidence_score REAL,
                is_active BOOLEAN DEFAULT 1,
                last_verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (hotel_id) REFERENCES hotels (id),
                UNIQUE(hotel_id, email)
            )
        """)
        
        # Index on hotel name for lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_hotels_name 
            ON hotels(name)
        """)
        
        # ---------------------------------------------------------
        # 3NF Normalization Tables (Matching Airtable Structure)
        # ---------------------------------------------------------
        
        # Create room_types table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS room_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hotel_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (hotel_id) REFERENCES hotels (id),
                UNIQUE(hotel_id, name)
            )
        """)
        
        # Create meal_plans table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meal_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,  -- e.g., 'BB', 'HB'
                name TEXT,                  -- e.g., 'Bed & Breakfast'
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Ensure we have common meal plans pre-populated
        meal_plans = [
            ('BB', 'Bed & Breakfast'),
            ('HB', 'Half Board'),
            ('FB', 'Full Board'),
            ('AI', 'All Inclusive'),
            ('RO', 'Room Only')
        ]
        cursor.executemany("""
            INSERT OR IGNORE INTO meal_plans (code, name) VALUES (?, ?)
        """, meal_plans)
        
        # Add Foreign Keys to rates table (Migration)
        # We add columns if they don't exist
        cursor.execute("PRAGMA table_info(rates)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'room_type_id' not in columns:
            cursor.execute("ALTER TABLE rates ADD COLUMN room_type_id INTEGER REFERENCES room_types(id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rates_room_type ON rates(room_type_id)")
            
        if 'meal_plan_id' not in columns:
            cursor.execute("ALTER TABLE rates ADD COLUMN meal_plan_id INTEGER REFERENCES meal_plans(id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rates_meal_plan ON rates(meal_plan_id)")

        
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
