"""
Test script for granular price extraction.
Run this on a contract to see all meal supplements, charges, deductions, etc.
"""
from extractor.pdf_text_extractor import PDFTextExtractor
from llm.llm_client import extract_all_price_items
from config import ATTACHMENTS_DIR
import os
import json
from pathlib import Path

def test_price_extraction():
    print("🔍 Testing Granular Price Extraction...")
    
    # Find most recent PDF
    pdf_files = []
    for root, dirs, filenames in os.walk(ATTACHMENTS_DIR):
        for f in filenames:
            if f.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, f))
    
    if not pdf_files:
        print("❌ No PDF files found.")
        return
    
    test_file = max(pdf_files, key=os.path.getctime)
    print(f"📄 Analyzing: {test_file}")
    
    # Extract text
    extractor = PDFTextExtractor()
    result = extractor.extract_text(Path(test_file))
    
    if not result['success']:
        print(f"❌ PDF extraction failed: {result.get('error')}")
        return
    
    text = result['text']
    print(f"✅ Extracted {len(text)} characters")
    
    # Extract all price items AND SAVE TO DATABASE
    print("\n💰 Extracting and saving priced items...")
    
    from extractor.rate_parser import RateParser
    parser = RateParser()
    
    # Extract hotel name from filename
    hotel_name = Path(test_file).stem.replace("topaz", "Hotel Topaz").replace("Summer", "").strip()
    
    success = parser.extract_and_store_price_items(text, os.path.basename(test_file), hotel_name)
    
    if not success:
        print("❌ Failed to store price items")
        return
    
    # Now query the database to show what was saved
    from database.query_price_items import search_price_items
    from config import DB_PATH
    
    saved_items = search_price_items(db_path=DB_PATH)
    
    # Display results
    print("\n" + "="*60)
    print("PRICED ITEMS SAVED TO DATABASE:")
    print("="*60)
    
    for item in saved_items[:15]:  # Show first 15
        print(f"\n📌 {item.get('category', 'unknown').upper()}")
        print(f"   Description: {item.get('description', 'N/A')}")
        print(f"   Price: {item.get('currency', 'USD')} {item.get('price', 0)}")
        print(f"   Unit: {item.get('per_unit', 'N/A')}")
        if item.get('source_text_snippet'):
            print(f"   Source: \"{item['source_text_snippet'][:80]}...\"")
    
    print(f"\n\n📊 Summary:")
    print(f"   Total Items in DB: {len(saved_items)}")

if __name__ == "__main__":
    test_price_extraction()
