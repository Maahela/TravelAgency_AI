"""
Budget logic engine.
Calculates costs based on structured itinerary data using DB/Airtable rates.
"""
from typing import Dict, List, Any, Optional
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
        global_guests = itinerary.get("guests", {"adults": 2, "children": 0, "child_ages": []})
        
        hotel_results = []
        total_trip_cost = 0.0
        
        for stay in stays:
            hotel_name = stay.get("hotel_name")
            nights = int(stay.get("nights", 1))
            rooms = int(stay.get("rooms", 1))
            room_type = stay.get("room_type", "Standard")
            meal_plan = stay.get("meal_plan", "BB")
            occupancy = stay.get("occupancy") 
            
            # Use global guests if not specified in stay
            stay_guests = stay.get("guests", global_guests)
            adults = stay_guests.get("adults", 2)
            children = stay_guests.get("children", 0)
            child_ages = stay_guests.get("child_ages", [])
            
            # 1. Get Rates and Price Items
            rates = search_rates(hotel_name=hotel_name, db_path=self.db_path)
            price_items = search_price_items(hotel_name=hotel_name, db_path=self.db_path)
            
            result = HotelResult (hotel_name=hotel_name, nights=nights, room_cost=None)
            
            # 2. Logic for Cross-Seasonal Stays
            # Split stay into individual nights and find rate for each
            from datetime import datetime, timedelta
            
            # Check if we have check_in date
            check_in_str = stay.get('check_in')
            
            if check_in_str:
                # Use date-specific calculation
                try:
                    check_in = datetime.strptime(check_in_str, "%Y-%m-%d")
                    total_base_cost = 0.0
                    calc_details = []
                    
                    for i in range(nights):
                        current_night = (check_in + timedelta(days=i)).strftime("%Y-%m-%d")
                        # Find rate for this specific night
                        match = self._find_best_rate(rates, room_type, occupancy, current_night)
                        if match:
                            rate_val = float(match.get('rate_per_night', 0) or 0)
                            total_base_cost += (rate_val * rooms)
                            # Track for calc string (simplified)
                            if not calc_details or calc_details[-1][0] != rate_val:
                                calc_details.append([rate_val, 1])
                            else:
                                calc_details[-1][1] += 1
                        else:
                            result.status = "PARTIAL"
                            result.notes.append(f"No rate found for {current_night}")
                    
                    if result.status != "PARTIAL":
                        calc_str = " + ".join([f"({r} x {rooms} room x {n} nights)" for r, n in calc_details])
                        result.room_cost = CostBreakdown(
                            description=f"{room_type} ({meal_plan})",
                            calculation_str=calc_str,
                            amount=total_base_cost
                        )
                        result.subtotal = total_base_cost
                    else:
                        result.status = "NO_SEASONAL_RATE"
                except Exception as e:
                    logger.error(f"Error in date calculation: {e}")
                    result.status = "MISSING_RATE"
            else:
                # Fallback: Use average/best available rate when no dates provided
                try:
                    match = self._find_best_rate_general(rates, room_type, occupancy)
                    if match:
                        rate_val = float(match.get('rate_per_night', 0) or 0)
                        total_base_cost = rate_val * rooms * nights
                        calc_str = f"{rate_val} x {rooms} room x {nights} nights"
                        result.room_cost = CostBreakdown(
                            description=f"{room_type} ({meal_plan})",
                             calculation_str=calc_str,
                            amount=total_base_cost
                        )
                        result.subtotal = total_base_cost
                        result.notes.append("⚠️ Using average rate (dates not specified)")
                    else:
                        result.status = "MISSING_RATE"
                except Exception as e:
                    logger.error(f"Error in rate calculation: {e}")
                    result.status = "MISSING_RATE"

            # 3. Apply Supplements (Price Items)
            if result.status == "OK" or result.status == "PARTIAL":
                # Meal Upgrades (if not BB)
                if meal_plan.upper() != "BB":
                    # Look for meal_plan_supplement
                    supp = self._find_price_item(price_items, "meal_plan_supplement", meal_plan)
                    if supp:
                        s_price = float(supp.get('price', 0))
                        total_supp = s_price * (adults + children) * nights
                        result.subtotal += total_supp
                        result.meal_cost = CostBreakdown(
                            description=f"{meal_plan} Supplement",
                            calculation_str=f"{s_price} x {adults+children} guests x {nights} nights",
                            amount=total_supp
                        )

                # Extra Person / Bed logic (Simplified)
                # If occupancy is Triple but rate is Double, add extra bed
                if occupancy == "Triple":
                     extra_bed = self._find_price_item(price_items, "extra_bed_charge")
                     if extra_bed:
                         eb_price = float(extra_bed.get('price', 0))
                         eb_total = eb_price * rooms * nights
                         result.subtotal += eb_total
                         result.notes.append(f"Added Extra Bed: {currency} {eb_total}")

                # Child Rates
                for age in child_ages:
                    child_rate = self._find_price_item(price_items, "child_rate", age=age)
                    if child_rate:
                        c_price = float(child_rate.get('price', 0))
                        c_total = c_price * nights
                        result.subtotal += c_total
                        result.notes.append(f"Child ({age}y): {currency} {c_total}")

            if result.status in ["OK", "PARTIAL"]:
                total_trip_cost += result.subtotal
            
            hotel_results.append(result)
            
        return CalculationResult(
            total_cost=total_trip_cost,
            currency=currency,
            hotel_results=hotel_results
        )

    def _find_best_rate(self, rates, room_type, occupancy, date_str):
        """Find best matching rate for a specific date."""
        candidates = [r for r in rates if room_type.lower() in str(r.get('room_type', '')).lower()]
        if occupancy:
            occ_matches = [r for r in candidates if occupancy.lower() in str(r.get('occupancy', r.get('Occupancy', ''))).lower()]
            if occ_matches: candidates = occ_matches
        
        for r in candidates:
            s_start = str(r.get('season_start_date', ''))[:10]
            s_end = str(r.get('season_end_date', ''))[:10]
            if s_start <= date_str <= s_end:
                return r
        return None

    def _find_best_rate_general(self, rates, room_type, occupancy):
        """Find best matching rate without specific date (fallback)."""
        candidates = [r for r in rates if room_type.lower() in str(r.get('room_type', '')).lower()]
        if occupancy:
            occ_matches = [r for r in candidates if occupancy.lower() in str(r.get('occupancy', r.get('Occupancy', ''))).lower()]
            if occ_matches: candidates = occ_matches
        
        # Return first match or None
        return candidates[0] if candidates else None

    def _find_price_item(self, items, category, sub_type=None, age=None):
        """Find specific supplement item."""
        for it in items:
            if it.get('category') == category:
                if sub_type and sub_type.lower() not in str(it.get('description', '')).lower(): continue
                if age is not None:
                    # check age range "5-12"
                    age_range = str(it.get('age_range', ''))
                    if "-" in age_range:
                         low, high = map(int, age_range.split("-"))
                         if low <= age <= high: return it
                    else: return it # fallback
                return it
        return None
