"""
PDF text extraction module.
Handles both digital and scanned PDFs.
"""

from pathlib import Path
from typing import Optional, Dict
from utils.logger import get_logger

logger = get_logger(__name__)


class PDFTextExtractor:
    """
    Extracts text from PDF files (digital and scanned).
    """
    
    def __init__(self):
        """
        Initialize PDF text extractor.
        
        TODO:
            - Initialize PDF processing libraries
            - Configure OCR fallback settings
        """
        logger.info("PDFTextExtractor initialized")
    
    def extract_text(self, pdf_path: Path) -> Dict[str, any]:
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
        
        Returns:
            Dictionary with extraction results
        """
        result = {
            'success': False,
            'text': '',
            'is_scanned': False,
            'error': None
        }
        
        try:
            # 1. Determine if scanned
            is_scanned = self.is_scanned_pdf(pdf_path)
            result['is_scanned'] = is_scanned
            
            text = ""
            if is_scanned:
                # 2. Use OCR fallback
                logger.info(f"PDF {pdf_path.name} detected as SCANNED. Using OCR.")
                text = self._ocr_fallback(pdf_path)
            else:
                # 3. Use digital extraction
                logger.info(f"PDF {pdf_path.name} detected as DIGITAL. Using pdfplumber.")
                text = self._try_digital_extraction(pdf_path)
                
                # If digital extraction yielded nothing, try OCR anyway
                if not text.strip():
                    logger.warning("Digital extraction yielded empty text. Retrying with OCR.")
                    text = self._ocr_fallback(pdf_path)
                    result['is_scanned'] = True  # Treat as scanned
            
            result['text'] = text
            result['success'] = bool(text)
            
        except Exception as e:
            logger.error(f"Failed to extract text from {pdf_path}: {e}")
            result['error'] = str(e)
        
        return result
    
    def _try_digital_extraction(self, pdf_path: Path) -> str:
        """
        Attempt to extract text from a digital (text-based) PDF.
        
        Args:
            pdf_path: Path to the PDF file
        
        Returns:
            Extracted text
        """
        import pdfplumber
        
        text_content = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    # Extract text, preserving layout density
                    page_text = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
                    text_content.append(page_text)
            
            return "\n\n".join(text_content)
            
        except Exception as e:
            logger.error(f"Digital extraction failed for {pdf_path}: {e}")
            return ""
    
    def _ocr_fallback(self, pdf_path: Path) -> str:
        """
        Use OCR to extract text from scanned PDF.
        
        Args:
            pdf_path: Path to the PDF file
        
        Returns:
            OCR-extracted text
        """
        from pdf2image import convert_from_path
        from extractor.image_ocr_extractor import ImageOCRExtractor
        
        logger.info(f"Starting OCR fallback for {pdf_path}")
        text_content = []
        ocr_extractor = ImageOCRExtractor(use_cloud=False)
        
        try:
            # Convert PDF pages to images
            # specific poppler_path can be added if not in PATH
            images = convert_from_path(str(pdf_path))
            
            for i, image in enumerate(images):
                logger.debug(f"Processing page {i+1} with OCR")
                
                # Save temp image for OCR SDK
                temp_img_path = pdf_path.parent / f"temp_page_{i}.jpg"
                image.save(temp_img_path, "JPEG")
                
                try:
                    result = ocr_extractor.extract_text(temp_img_path)
                    if result['success']:
                        text_content.append(result['text'])
                finally:
                    # Clean up temp file
                    if temp_img_path.exists():
                        temp_img_path.unlink()
            
            return "\n\n".join(text_content)
            
        except Exception as e:
            logger.error(f"OCR fallback failed: {e}")
            return ""
    
    def is_scanned_pdf(self, pdf_path: Path) -> bool:
        """
        Detect if a PDF is scanned (image-based) or digital (text-based).
        
        Args:
            pdf_path: Path to the PDF file
        
        Returns:
            True if scanned, False if digital
        """
        import pdfplumber
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if len(pdf.pages) == 0:
                    return False
                
                # Check first 3 pages
                pages_to_check = pdf.pages[:3]
                total_chars = 0
                for page in pages_to_check:
                    text = page.extract_text() or ""
                    total_chars += len(text.strip())
                
                # If average characters per page is very low, assume scanned
                avg_chars = total_chars / len(pages_to_check)
                return avg_chars < 50  # Threshold: fewer than 50 chars considers it scanned
                
        except Exception as e:
            logger.error(f"Failed to detect PDF type for {pdf_path}: {e}")
            return True  # Fail safe to OCR if uncertain
