
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
import os
import sys
from pydantic import BaseModel

# Add parent directory to path to import existing modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from database.airtable_client import AirtableClient
from database.query_rates import search_rates, format_rates_for_llm
from database.query_price_items import search_price_items
from database.hotel_management import HotelManager
from chat.chat_interface import ChatInterface

app = FastAPI(title="JAKEmailBot Admin API")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Chat Interface
chat_bot = ChatInterface()

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

@app.get("/stats")
async def get_stats():
    """Get high-level statistics from Airtable/SQLite."""
    try:
        airtable = AirtableClient()
        if not airtable.is_connected():
            return {"error": "Airtable disconnected"}
        
        rates_count = len(airtable.rates_table.all())
        price_items_count = len(airtable.price_items_table.all())
        processing_logs_count = len(airtable.processing_log_table.all())
        
        return {
            "total_rates": rates_count,
            "total_price_items": price_items_count,
            "total_logs": processing_logs_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rates")
async def get_rates(hotel: Optional[str] = None):
    try:
        rates = search_rates(hotel_name=hotel)
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
    """Get extraction trends."""
    try:
        airtable = AirtableClient()
        logs = airtable.processing_log_table.all()
        
        # Simple count by status
        stats = {}
        for log in logs:
            status = log['fields'].get('Status', 'Unknown')
            stats[status] = stats.get(status, 0) + 1
            
        return {
            "processing_stats": stats,
            "total_processed": len(logs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/contacts")
async def get_contacts():
    """Get all hotel contacts (Airtable + SQLite fallback)."""
    try:
        results = []
        # 1. Try Airtable
        airtable = AirtableClient()
        if airtable.is_connected():
            records = airtable.contacts_table.all()
            for r in records:
                f = r['fields']
                results.append({
                    "id": r['id'],
                    "name": f.get("Hotel Name"),
                    "email_address": f.get("Email"),
                    "website": f.get("Website"),
                    "contact_person": f.get("Contact Person"),
                    "discovery_source": f.get("Discovery Source"),
                    "source": "Airtable"
                })
        
        # 2. Add SQLite contacts if not already present or if Airtable failed
        manager = HotelManager()
        sqlite_contacts = manager.get_all_hotels()
        
        # Simple merge: if name matching exist in results, skip
        existing_names = {c['name'].lower() for c in results if c.get('name')}
        for c in sqlite_contacts:
            if c['name'].lower() not in existing_names:
                results.append({
                    "id": c['id'],
                    "name": c['name'],
                    "email_address": c.get('email_address'),
                    "website": c.get('website'),
                    "contact_person": c.get('contact_person'),
                    "last_rate_request_date": c.get('last_rate_request_date'),
                    "source": "Local DB"
                })
                
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_endpoint(request: QueryRequest):
    """Integrated Chat Interface endpoint."""
    try:
        response = chat_bot.query(request.message)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
