"""
Test script for RateParser validation and standardization logic.
"""
from extractor.rate_parser import RateParser

def test_currency_standardization():
    print("\n💵 Testing Currency Standardization...")
    parser = RateParser()
    
    cases = [
        ("$", "USD"),
        ("€", "EUR"),
        ("USD ", "USD"),
        ("Rs", "LKR"),
        ("GBP", "GBP"),
        ("Unknown", "USD"),
        ("", "USD"),
    ]
    
    for input_val, expected in cases:
        result = parser.standardize_currency(input_val)
        status = "✅" if result == expected else f"❌ (Got {result})"
        print(f"   Input: '{input_val}' -> Expected: {expected} {status}")

def test_date_parsing():
    print("\n📅 Testing Date Parsing...")
    parser = RateParser()
    
    cases = [
        ("2025-12-25", "2025-12-25"),
        ("25/12/2025", "2025-12-25"),
        ("12/25/2025", "2025-12-25"), # Ambiguous dayfirst=True pref
        ("1st Jan 2026", "2026-01-01"),
        ("Dec 31, 2025", "2025-12-31"),
        ("Invalid Date", None),
    ]
    
    for input_val, expected in cases:
        result = parser.parse_date(input_val)
        status = "✅" if result == expected else f"❌ (Got {result})"
        print(f"   Input: '{input_val}' -> Expected: {expected} {status}")

def test_validation():
    print("\n🛡️ Testing Data Validation...")
    parser = RateParser()
    
    # CASE 1: Valid Data
    valid_data = {
        'hotel_name': 'Test Hotel',
        'room_type': 'Deluxe',
        'rate_per_night': 100.0,
        'currency': 'USD',
        'season_start_date': '2025-01-01',
        'season_end_date': '2025-01-31'
    }
    res = parser.validate_rate_data(valid_data)
    print(f"   Valid Data: {'✅ Passed' if res['valid'] else '❌ Failed'}")
    if not res['valid']: print(res['errors'])

    # CASE 2: Invalid Date Range
    invalid_dates = valid_data.copy()
    invalid_dates['season_start_date'] = '2025-02-01' # After end date
    res = parser.validate_rate_data(invalid_dates)
    print(f"   Invalid Dates: {'✅ Detected' if not res['valid'] else '❌ Missed'} ({res['errors']})")

    # CASE 3: Missing Field
    missing_field = valid_data.copy()
    del missing_field['hotel_name']
    res = parser.validate_rate_data(missing_field)
    print(f"   Missing Field: {'✅ Detected' if not res['valid'] else '❌ Missed'} ({res['errors']})")

    # CASE 4: Negative Rate
    neg_rate = valid_data.copy()
    neg_rate['rate_per_night'] = -50
    res = parser.validate_rate_data(neg_rate)
    print(f"   Negative Rate: {'✅ Detected' if not res['valid'] else '❌ Missed'} ({res['errors']})")

if __name__ == "__main__":
    test_currency_standardization()
    test_date_parsing()
    test_validation()
