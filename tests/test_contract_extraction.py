"""
Script to test the new Extended Contract Data Extraction pipeline.
Runs extraction on the most recent attachment found in the data/attachments folder.
"""
from extractor.rate_parser import RateParser
from extractor.image_ocr_extractor import ImageOCRExtractor
from config import ATTACHMENTS_DIR
import os
from pathlib import Path

def test_extraction():
    print("🚀 Testing Extended Contract Extraction...")
    
    # Find a test file (prioritize most recent PDF, then image)
    files = []
    pdf_files = []
    
    for root, dirs, filenames in os.walk(ATTACHMENTS_DIR):
        for f in filenames:
            full_path = os.path.join(root, f)
            if f.lower().endswith('.pdf'):
                pdf_files.append(full_path)
            elif f.lower().endswith(('.png', '.jpg', '.jpeg')):
                 files.append(full_path)
    
    # Priority: Latest PDF -> Latest Image
    test_file = None
    if pdf_files:
        test_file = max(pdf_files, key=os.path.getctime)
    elif files:
        test_file = max(files, key=os.path.getctime)
    
    if not test_file:
        print("❌ No attachment files found to test.")
        return

    print(f"📄 Using test file: {test_file}")
    
    # 1. Text Extraction (PDF or OCR)
    text = ""
    if test_file.lower().endswith('.pdf'):
        from extractor.pdf_text_extractor import PDFTextExtractor
        extractor = PDFTextExtractor()
        result = extractor.extract_text(Path(test_file))
        if result['success']:
            text = result['text']
        else:
            print(f"❌ PDF extraction failed: {result.get('error')}")
            return
    else:
        ocr = ImageOCRExtractor()
        text = ocr.extract_text(test_file)
    
    if not text:
        print("❌ Failed to extract text.")
        return
        
    print(f"✅ Extracted {len(text)} characters.")
    
    # 2. Extract Extended Data
    parser = RateParser()
    success = parser.extract_and_store_contract_data(text, os.path.basename(test_file))
    
    if success:
        print("✅ Extended data extracted and stored in DB (contract_data table).")
        
        # 3. Verify DB Content
        from database.db_init import get_db_connection
        from config import DB_PATH
        import json
        
        try:
            conn = get_db_connection(DB_PATH)
            # Check row count
            count = conn.execute("SELECT COUNT(*) FROM contract_data").fetchone()[0]
            print(f"📊 Total contracts in DB: {count}")
            
            row = conn.execute("SELECT * FROM contract_data ORDER BY id DESC LIMIT 1").fetchone()
            conn.close()
            
            if row:
                print("\n💾 Stored JSON Preview (Latest):")
                data = json.loads(row['raw_json'])
                print(json.dumps(data, indent=2)[:800] + "...") 
            else:
                 print("❌ Verification failed: No row found in DB.")
        except Exception as e:
            print(f"❌ DB verification error: {e}")
        
    else:
        print("❌ Extraction failed.")

if __name__ == "__main__":
    test_extraction()
