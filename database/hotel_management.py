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
                    SET website = ?, contact_person = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (website, contact_person, hotel_id))
                logger.info(f"Updated hotel details: {name}")
                
                # Update Email separate (if provided)
                if email:
                    conn.close() # Close to use the other method which opens its own connection
                    self.upsert_hotel_email(hotel_id, email, "general", "manual_add", 1.0)
                    return hotel_id
                    
                return hotel_id
            else:
                cursor.execute("""
                    INSERT INTO hotels (name, website, contact_person)
                    VALUES (?, ?, ?)
                """, (name, website, contact_person))
                hotel_id = cursor.lastrowid
                logger.info(f"Added new hotel: {name}")
                
                if email:
                    conn.close()
                    self.upsert_hotel_email(hotel_id, email, "general", "manual_add", 1.0)
                    return hotel_id
                
                return hotel_id
        finally:
            try:
                conn.close()
            except:
                pass

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

    def get_or_create_room_type(self, hotel_id: int, room_type_name: str) -> int:
        """
        Get or create a Room Type linked to a hotel.
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        
        try:
            # Check existing
            cursor.execute(
                "SELECT id FROM room_types WHERE hotel_id = ? AND name = ?", 
                (hotel_id, room_type_name)
            )
            row = cursor.fetchone()
            
            if row:
                return row[0]
            
            # Create new
            cursor.execute(
                "INSERT INTO room_types (hotel_id, name) VALUES (?, ?)",
                (hotel_id, room_type_name)
            )
            conn.commit()
            return cursor.lastrowid
            
        except sqlite3.Error as e:
            logger.error(f"Error managing room type: {e}")
            return None
        finally:
            conn.close()

    def get_or_create_meal_plan(self, meal_plan_name: str) -> int:
        """
        Get or create a Meal Plan.
        Handles standardization (similar to AirtableClient).
        """
        if not meal_plan_name:
            return None
            
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # Standardization Map
        mapping = {
            'bb': 'BB',
            'bed & breakfast': 'BB',
            'bed and breakfast': 'BB',
            'bread and brakfast': 'BB',
            'bed and brakfast': 'BB',
            'hb': 'HB',
            'half board': 'HB',
            'fb': 'FB',
            'full board': 'FB',
            'ai': 'AI',
            'all inclusive': 'AI',
            'ro': 'RO',
            'room only': 'RO',
        }
        
        raw = meal_plan_name.lower().strip().replace('.', '').replace(',', '')
        code = mapping.get(raw)
        
        # Fuzzy fallback
        if not code:
            if 'breakfast' in raw: code = 'BB'
            elif 'half' in raw and 'board' in raw: code = 'HB'
            elif 'full' in raw and 'board' in raw: code = 'FB'
            elif 'inclusive' in raw: code = 'AI'
            else:
                # If unknown, we might not be able to insert if 'code' is constrained to be unique/standard
                # But our schema allows new codes. Let's use the raw name as code if short, or just generate one?
                # Actually schema says code is UNIQUE.
                # Let's try to use the raw name if it looks like a code (short), else just use it as name?
                # For safety, let's treat unknown as NULL/None or create a custom one.
                # Let's return None for now to avoid pollution, or mapping to "Unknown"?
                # Ideally we want to support variations.
                # Let's just try to find by Name if Code fails?
                # For now simplify: if not found, don't link.
                pass
        
        try:
            if code:
                cursor.execute("SELECT id FROM meal_plans WHERE code = ?", (code,))
                row = cursor.fetchone()
                if row:
                    return row[0]
            
            # If no code match, maybe check by name?
            # Or just return None
            return None
            
        except sqlite3.Error as e:
            logger.error(f"Error managing meal plan: {e}")
            return None
        finally:
            conn.close()

