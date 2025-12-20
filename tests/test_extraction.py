"""
Test script for verifying PDF and Image text extraction.
"""
import sys
import logging
from pathlib import Path
from extractor.pdf_text_extractor import PDFTextExtractor
from extractor.image_ocr_extractor import ImageOCRExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_extraction():
    print("Testing Text Extraction Modules...")
    
    pdf_extractor = PDFTextExtractor()
    ocr_extractor = ImageOCRExtractor(use_cloud=False)
    
    # Create dummy text PDF for testing (if not exists)
    # Note: Creating a real PDF programmatically requires reportlab, which isn't in requirements.
    # We will just print instructions if files don't exist.
    
    test_pdf = Path("test_sample.pdf")
    test_image = Path("test_sample.png")
    
    if test_pdf.exists():
        print(f"\n--- Testing PDF: {test_pdf} ---")
        result = pdf_extractor.extract_text(test_pdf)
        print(f"Success: {result['success']}")
        print(f"Is Scanned: {result['is_scanned']}")
        print(f"Text Preview: {result['text'][:100]}...")
    else:
        print(f"\n⚠️  No test PDF found at {test_pdf}. Add one to test PDF extraction.")

    if test_image.exists():
        print(f"\n--- Testing Image: {test_image} ---")
        result = ocr_extractor.extract_text(test_image)
        print(f"Success: {result['success']}")
        print(f"Text Preview: {result['text'][:100]}...")
    else:
        print(f"\n⚠️  No test Image found at {test_image}. Add one to test OCR.")

if __name__ == "__main__":
    test_extraction()
