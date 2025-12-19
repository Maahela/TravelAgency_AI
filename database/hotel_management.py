"""
Database operations for managing hotel contacts and tracking rate freshness.
"""
import sqlite3
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from config import DB_PATH
from utils.logger import get_logger

logger = get_logger(__name__)

class HotelManager:
    """
    Manages hotel data and rate freshness queries.
    """
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def add_hotel(self, name: str, email: str, website: str = None, contact_person: str = None) -> int:
        """Add a new hotel or update existing one."""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        try:
            # Check if exists
            cursor.execute("SELECT id FROM hotels WHERE name = ?", (name,))
            existing = cursor.fetchone()
            
            if existing:
                hotel_id = existing[0]
                cursor.execute("""
                    UPDATE hotels 
                    SET email_address = ?, website = ?, contact_person = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (email, website, contact_person, hotel_id))
                logger.info(f"Updated hotel: {name}")
                return hotel_id
            else:
                cursor.execute("""
                    INSERT INTO hotels (name, email_address, website, contact_person)
                    VALUES (?, ?, ?, ?)
                """, (name, email, website, contact_person))
                logger.info(f"Added new hotel: {name}")
                return cursor.lastrowid
        finally:
            conn.commit()
            conn.close()

    def get_stale_hotels(self, days_threshold: int = 30) -> List[Dict]:
        """
        Find hotels that haven't been contacted in `days_threshold` days
        OR have never been contacted.
        """
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        threshold_date = (datetime.now() - timedelta(days=days_threshold)).strftime('%Y-%m-%d')
        
        try:
            # Query for hotels with NULL last_rate_request_date OR date < threshold
            query = """
                SELECT * FROM hotels 
                WHERE last_rate_request_date IS NULL 
                OR last_rate_request_date < ?
            """
            cursor.execute(query, (threshold_date,))
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def update_last_contact(self, hotel_id: int):
        """Update the last_rate_request_date to now."""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE hotels 
                SET last_rate_request_date = ? 
                WHERE id = ?
            """, (datetime.now().strftime('%Y-%m-%d'), hotel_id))
            conn.commit()
        finally:
            conn.close()

    def get_all_hotels(self) -> List[Dict]:
        """Get all hotels."""
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM hotels")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_or_create_hotel(self, name: str, website: str = None) -> int:
        """
        Get hotel ID by name, creating if necessary. Optionally update website.
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # Try to find existing
        cursor.execute("SELECT id, website FROM hotels WHERE name = ?", (name,))
        row = cursor.fetchone()
        
        if row:
            hotel_id = row[0]
            existing_website = row[1]
            
            # Update website if provided and different
            if website and website != existing_website:
                cursor.execute(
                    "UPDATE hotels SET website = ? WHERE id = ?",
                    (website, hotel_id)
                )
                conn.commit()
                logger.info(f"Updated website for hotel '{name}': {website}")
            
            conn.close()
            return hotel_id
        
        # Create new
        if website:
            cursor.execute(
                "INSERT INTO hotels (name, website) VALUES (?, ?)",
                (name, website)
            )
        else:
            cursor.execute("INSERT INTO hotels (name) VALUES (?)", (name,))
        
        hotel_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Created hotel '{name}' with ID {hotel_id}")
        return hotel_id

    def get_hotel_emails(self, hotel_name: str) -> Dict[str, str]:
        """Get all active emails for a hotel by name."""
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            # Join with hotels table to find by name
            cursor.execute("""
                SELECT e.email, e.purpose 
                FROM hotel_emails e
                JOIN hotels h ON e.hotel_id = h.id
                WHERE h.name LIKE ? AND e.is_active = 1
            """, (f"%{hotel_name}%",))
            
            rows = cursor.fetchall()
            return {row['purpose']: row['email'] for row in rows}
        finally:
            conn.close()

    def upsert_hotel_email(self, hotel_id: int, email: str, purpose: str, source_type: str, confidence: float):
        """Insert or Update email record for a hotel."""
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO hotel_emails (hotel_id, email, purpose, source_type, confidence_score, last_verified_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(hotel_id, email) DO UPDATE SET
                    purpose=excluded.purpose,
                    source_type=excluded.source_type,
                    confidence_score=excluded.confidence_score,
                    last_verified_at=CURRENT_TIMESTAMP,
                    is_active=1
            """, (hotel_id, email, purpose, source_type, confidence))
            conn.commit()
            logger.info(f"Upserted email {email} for hotel ID {hotel_id}")
        except sqlite3.Error as e:
            logger.error(f"Error upserting email: {e}")
        finally:
            conn.close()
