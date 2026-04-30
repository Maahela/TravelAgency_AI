
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
import os
import sys
import os
import certifi

# Fix for SSL: Set SSL_CERT_FILE to certifi's bundle
ca_bundle = certifi.where()
os.environ['SSL_CERT_FILE'] = ca_bundle
os.environ['REQUESTS_CA_BUNDLE'] = ca_bundle
os.environ['GRPC_DEFAULT_SSL_ROOTS_FILE_PATH'] = ca_bundle
from pydantic import BaseModel
import sqlite3
from datetime import datetime

# Add parent directory to path to import existing modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from database.airtable_client import AirtableClient
from database.query_rates import search_rates, format_rates_for_llm
from database.query_price_items import search_price_items
from database.hotel_management import HotelManager
from chat.smart_chat_interface import SmartChatInterface
from utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(title="JAKEmailBot Admin API")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Log DB path for debugging
from config import DB_PATH
logger.info(f"Backend using DB_PATH: {DB_PATH}")
logger.info(f"DB exists: {DB_PATH.exists()}")

# Initialize Chat Interface
# Use the new Smart Chat Interface with function calling
chat_bot = SmartChatInterface(db_path=DB_PATH)

# Sync contacts ensuring fresh data
try:
    from scripts.ops.sync_contacts import sync_contacts
    logger.info("Syncing contacts from Airtable...")
    sync_contacts()
except Exception as e:
    logger.error(f"Failed to sync contacts on startup: {e}")

# ============================================
# Audit Logging System
# ============================================
audit_log: List[Dict] = []

def log_audit_event(event_type: str, details: str, data_source: str = "unknown"):
    """Log an audit event with timestamp and data source."""
    event = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "details": details,
        "data_source": data_source
    }
    audit_log.append(event)
    if len(audit_log) > 100:
        audit_log.pop(0)
    logger.info(f"AUDIT: {event_type} - {details} (source: {data_source})")

class QueryRequest(BaseModel):
    message: str

class RateUpdate(BaseModel):
    hotel_name: Optional[str] = None
    room_type: Optional[str] = None
    price: Optional[str] = None
    currency: Optional[str] = None
    meal_plan: Optional[str] = None

@app.get("/")
async def root():
    return {"status": "online", "message": "JAKEmailBot Admin API is running"}

@app.get("/debug-db")
async def debug_db():
    """Debug endpoint to show DB path"""
    from config import DB_PATH, BASE_DIR, DATA_DIR
    import sqlite3
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in cur.fetchall()]
        conn.close()
        return {
            "BASE_DIR": str(BASE_DIR),
            "DATA_DIR": str(DATA_DIR),
            "DB_PATH": str(DB_PATH),
            "DB_exists": DB_PATH.exists(),
            "tables": tables
        }
    except Exception as e:
        return {"error": str(e), "DB_PATH": str(DB_PATH)}

@app.get("/stats")
async def get_stats():
    """Get statistics with Airtable/SQLite fallback."""
    data_source = "unknown"
    
    # Try Airtable first
    try:
        airtable = AirtableClient()
        if airtable.is_connected():
            data_source = "airtable"
            all_rates = airtable.rates_table.all()
            all_price_items = airtable.price_items_table.all()
            all_logs = airtable.processing_log_table.all()
            all_hotels = airtable.hotels_table.all()
            
            log_audit_event("stats_fetched", "Retrieved statistics from Airtable", data_source)
            
            return {
                "total_rates": len(all_rates),
                "rates_trend": "+5%",
                "total_price_items": len(all_price_items),
                "price_items_trend": "+12%",
                "total_logs": len(all_logs),
                "logs_trend": "+8%",
                "live_hotels": len(all_hotels),
                "data_source": data_source
            }
    except Exception as e:
        logger.warning(f"Airtable stats failed: {e}, falling back to SQLite")
    
    # Fallback to SQLite
    try:
        data_source = "sqlite"
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM rates")
        rates_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM price_items")
        price_items_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM processing_log")
        logs_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(DISTINCT id) FROM hotels")
        hotels_count = cur.fetchone()[0]
        
        conn.close()
        
        log_audit_event("stats_fetched", "Retrieved statistics from SQLite (fallback)", data_source)
        
        return {
            "total_rates": rates_count,
            "rates_trend": "N/A",
            "total_price_items": price_items_count,
            "price_items_trend": "N/A",
            "total_logs": logs_count,
            "logs_trend": "N/A",
            "live_hotels": hotels_count,
            "data_source": data_source
        }
    except Exception as e:
        logger.error(f"Both Airtable and SQLite failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rates")
async def get_rates(hotel: Optional[str] = None):
    try:
        rates = search_rates(hotel_name=hotel)
        log_audit_event("rates_queried", f"Queried rates for: {hotel or 'all hotels'}", "sqlite")
        return rates[:100] # Limit to 100 for dashboard
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/price-items")
async def get_price_items(hotel: Optional[str] = None):
    try:
        items = search_price_items(hotel_name=hotel)
        return items[:100]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/rates/{rate_id}")
async def update_rate(rate_id: str, update: RateUpdate):
    """Update a rate in Airtable."""
    try:
        airtable = AirtableClient()
        # Filter None values
        fields = {k.replace('_', ' ').title(): v for k, v in update.dict().items() if v is not None}
        # Special mapping for hotel name if it's "Hotel Name" in Airtable
        if "Hotel Name" in fields:
            fields["Hotel Name"] = update.hotel_name
            
        airtable.rates_table.update(rate_id, fields)
        return {"status": "success", "message": f"Rate {rate_id} updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics")
async def get_analytics():
    """Get extraction trends with Airtable/SQLite fallback."""
    # Try Airtable first
    try:
        airtable = AirtableClient()
        if airtable.is_connected():
            logs = airtable.processing_log_table.all()
            
            # Simple count by status
            stats = {}
            for log in logs:
                status = log['fields'].get('Status', 'Unknown')
                stats[status] = stats.get(status, 0) + 1
            
            log_audit_event("analytics_fetched", "Retrieved analytics from Airtable", "airtable")
            
            return {
                "processing_stats": stats,
                "total_processed": len(logs)
            }
    except Exception as e:
        logger.warning(f"Airtable analytics failed: {e}, falling back to SQLite")
    
    # Fallback to SQLite
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Get status counts from processing_log
        cur.execute("SELECT status, COUNT(*) FROM processing_log GROUP BY status")
        rows = cur.fetchall()
        
        stats = {row[0]: row[1] for row in rows} if rows else {"success": 0}
        
        cur.execute("SELECT COUNT(*) FROM processing_log")
        total = cur.fetchone()[0]
        
        conn.close()
        
        log_audit_event("analytics_fetched", "Retrieved analytics from SQLite (fallback)", "sqlite")
        
        return {
            "processing_stats": stats,
            "total_processed": total
        }
    except Exception as e:
        logger.error(f"Both Airtable and SQLite analytics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/contacts")
async def get_contacts():
    """Get hotel contacts by merging Hotels and HotelContacts tables."""
    try:
        airtable = AirtableClient()
        if not airtable.is_connected():
            raise HTTPException(status_code=503, detail="Airtable not connected")
        
        # Get all hotels from the Hotels table
        all_hotels = airtable.hotels_table.all()
        
        # Get all contact details from HotelContacts table
        try:
            contacts_records = airtable.contacts_table.all()
            # Build comprehensive contact map indexed by hotel name
            contact_details = {}
            for r in contacts_records:
                fields = r['fields']
                h_name = fields.get('Hotel Name')
                if h_name:
                    contact_details[h_name] = {
                        'email': fields.get('Email'),
                        # Handle both 'Website' and 'Website ' (with trailing space)
                        'website': fields.get('Website') or fields.get('Website '),
                        # Handle both 'Contact Person' and with potential trailing space
                        'contact_person': fields.get('Contact Person') or fields.get('Contact Person '),
                        'source': fields.get('Discovery Source', 'Manual Entry'),
                        'created_at': r.get('createdTime', ''),
                        'updated_at': fields.get('Last Modified Time', r.get('createdTime', ''))
                    }
        except Exception as e:
            logger.error(f"Failed to fetch contacts details: {e}")
            contact_details = {}
        
        # Build merged hotel contact list
        results = []
        for hotel_record in all_hotels:
            fields = hotel_record['fields']
            hotel_name = fields.get('Name')
            
            if hotel_name:
                # Get contact details if available
                details = contact_details.get(hotel_name, {})
                
                # Use createdTime from the hotel record as default
                created_at = details.get('created_at', hotel_record.get('createdTime', ''))
                last_updated = details.get('updated_at', created_at)
                
                results.append({
                    "id": hotel_record['id'],
                    "name": hotel_name,
                    "email_address": details.get('email'),
                    "website": details.get('website'),
                    "contact_person": details.get('contact_person'),
                    "last_rate_request_date": last_updated,
                    "created_at": created_at,
                    "updated_at": last_updated
                })
        
        log_audit_event("contacts_fetched", f"Retrieved {len(results)} hotel contacts", "airtable")
        logger.info(f"Returning {len(results)} hotels from merged Hotels + HotelContacts data")
        return results
        
    except Exception as e:
        logger.error(f"Error in get_contacts: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_endpoint(request: QueryRequest):
    """Integrated Chat Interface endpoint."""
    try:
        response = chat_bot.query(request.message)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check with data source status."""
    airtable_status = "disconnected"
    sqlite_status = "disconnected"
    
    try:
        airtable = AirtableClient()
        if airtable.is_connected():
            airtable_status = "connected"
    except:
        pass
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.close()
        sqlite_status = "connected"
    except:
        pass
    
    return {
        "status": "healthy",
        "airtable": airtable_status,
        "sqlite": sqlite_status,
        "db_path": str(DB_PATH),
        "port": 4003
    }

@app.get("/system-status")
async def get_system_status():
    """Get comprehensive system status."""
    airtable_connected = False
    sqlite_connected = False
    
    try:
        airtable = AirtableClient()
        airtable_connected = airtable.is_connected()
    except:
        pass
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.close()
        sqlite_connected = True
    except:
        pass
    
    return {
        "airtable": {
            "status": "connected" if airtable_connected else "disconnected",
            "enabled": airtable_connected
        },
        "sqlite": {
            "status": "connected" if sqlite_connected else "disconnected",
            "path": str(DB_PATH),
            "enabled": sqlite_connected
        },
        "active_source": "airtable" if airtable_connected else "sqlite",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/audit-log")
async def get_audit_log(limit: int = 50):
    """Get recent audit log entries."""
    return audit_log[-limit:]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4005)
