"""
Budget logic engine.
Calculates costs based on structured itinerary data using DB/Airtable rates.
"""
from typing import Dict, List, Any
from database.query_rates import search_rates
from database.query_price_items import search_price_items
from dataclasses import dataclass, field
from utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class CostBreakdown:
    description: str
    calculation_str: str  # e.g. "120 * 2 rooms * 3 nights"
    amount: float

@dataclass
class HotelResult:
    hotel_name: str
    nights: int
    room_cost: CostBreakdown
    meal_cost: Optional[CostBreakdown] = None
    subtotal: float = 0.0
    status: str = "OK" # OK, MISSING_RATE, PARTIAL
    notes: List[str] = field(default_factory=list)

@dataclass
class CalculationResult:
    total_cost: float
    currency: str
    hotel_results: List[HotelResult]
    global_notes: List[str] = field(default_factory=list)

class BudgetCalculator:
    def __init__(self, db_path=None):
        self.db_path = db_path # Optional, passed to search_rates

    def calculate_trip_cost(self, itinerary: Dict) -> CalculationResult:
        """
        Calculate total trip cost from itinerary structure.
        """
        stays = itinerary.get("stays", [])
        currency = itinerary.get("currency", "USD")
        
        hotel_results = []
        total_trip_cost = 0.0
        
        for stay in stays:
            hotel_name = stay.get("hotel_name")
            nights = int(stay.get("nights", 1))
            rooms = int(stay.get("rooms", 1))
            guests = int(stay.get("guests_per_room", 2)) * rooms
            room_type = stay.get("room_type", "Standard")
            meal_plan = stay.get("meal_plan", "BB")
            occupancy = stay.get("occupancy") # Single/Double/Triple
            
            # 1. Get Rate
            # We fetch all rates for this hotel to find best match
            rates = search_rates(hotel_name=hotel_name, db_path=self.db_path)
            
            # Find matching rate logic (Seasonality & Occupancy Aware)
            check_in = stay.get('check_in') # YYYY-MM-DD
            selected_rate = None
            
            # Helper to check date overlap
            def is_in_season(rate, check_in_date_str):
                if not rate.get('season_start_date') or not check_in_date_str:
                    return True # Assume distinct if no dates
                try:
                    s_start = str(rate['season_start_date'])[:10]
                    s_end = str(rate['season_end_date'])[:10]
                    c_in = str(check_in_date_str)[:10]
                    return s_start <= c_in <= s_end
                except:
                    return True

            candidates = []
            for r in rates:
                # 1. Room Type Match (case-insensitive)
                r_type = str(r.get('room_type', '')).lower()
                r_occ = str(r.get('occupancy', r.get('Occupancy', ''))).lower()
                
                if room_type.lower() in r_type:
                    candidates.append(r)
            
            # 1.5 Occupancy Refinement
            if occupancy and candidates:
                occ_matches = [r for r in candidates if occupancy.lower() in str(r.get('occupancy', r.get('Occupancy', ''))).lower()]
                if occ_matches:
                    candidates = occ_matches
            
            if not candidates:
                 candidates = rates # Fallback to all if no match
            
            result = HotelResult(hotel_name=hotel_name, nights=nights, room_cost=None)

            # 2. Date Match (Seasonality)
            date_matches = [r for r in candidates if is_in_season(r, check_in)]
            
            if date_matches:
                selected_rate = date_matches[0] # Pick best date match
            elif check_in:
                # STRICT MODE: If we have a date, but no rate for that date -> FAIL
                selected_rate = None
                result.status = "NO_SEASONAL_RATE"
                result.notes.append(f"No rate found covering date {check_in}")
            elif candidates:
                 # No date provided, so provide generic/first available rate with warning
                selected_rate = candidates[0] 
                result.notes.append("Generic rate used (no date specified)")
            
            if selected_rate:
                # Base Rate Math
                rate_val = float(selected_rate.get('rate_per_night', 0) or 0)
                rate_currency = selected_rate.get('currency', 'USD')
                
                # Check currency mismatch (simplified: ignore or note)
                if rate_currency != currency:
                    result.notes.append(f"Rate in {rate_currency}, unconverted.")
                
                cost_val = rate_val * rooms * nights
                date_info = f" [{stay.get('check_in')} to {stay.get('check_out')}]" if stay.get('check_in') else ""
                
                result.room_cost = CostBreakdown(
                    description=f"{room_type} ({meal_plan}){date_info}",
                    calculation_str=f"{rate_currency} {rate_val} x {rooms} room(s) x {nights} night(s)",
                    amount=cost_val
                )
                
                result.subtotal += cost_val
                
                # Meal Supplements (Placeholder logic - requires PriceItems table integration)
                # If we had a supplement for "HB" -> look it up.
                # For now, assuming rate includes the base meal plan matched.
                # If user asked for HB but rate is BB, we'd add supplement.
                
            else:
                result.status = "MISSING_RATE"
                result.room_cost = CostBreakdown(
                    description="Rate not found",
                    calculation_str="N/A",
                    amount=0.0
                )
                result.notes.append("Could not find rate for this hotel.")
            
            # Valid subtotal
            if result.status == "OK":
                total_trip_cost += result.subtotal
                
            hotel_results.append(result)
            
        return CalculationResult(
            total_cost=total_trip_cost,
            currency=currency,
            hotel_results=hotel_results
        )
