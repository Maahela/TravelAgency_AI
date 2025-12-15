"""
File storage utilities for handling email attachments.
"""

import os
from pathlib import Path
from typing import Optional
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)


def save_attachment(
    file_data: bytes,
    filename: str,
    base_dir: Optional[Path] = None
) -> Path:
    """
    Save email attachment to local storage.
    
    Args:
        file_data: Binary data of the file
        filename: Name of the file
        base_dir: Base directory for storage (defaults to ATTACHMENTS_DIR from config)
    
    Returns:
        Path object pointing to the saved file
    
    TODO:
        - Implement virus scanning before saving
        - Add file size validation
        - Implement duplicate detection
    """
    if base_dir is None:
        from config import ATTACHMENTS_DIR
        base_dir = ATTACHMENTS_DIR
    
    # Create timestamped subdirectory
    date_folder = datetime.now().strftime("%Y-%m-%d")
    save_dir = base_dir / date_folder
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename if file exists
    file_path = save_dir / filename
    counter = 1
    while file_path.exists():
        name, ext = os.path.splitext(filename)
        file_path = save_dir / f"{name}_{counter}{ext}"
        counter += 1
    
    # Save file
    try:
        with open(file_path, 'wb') as f:
            f.write(file_data)
        logger.info(f"Saved attachment: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Failed to save attachment {filename}: {e}")
        raise


def get_file_type(file_path: Path) -> str:
    """
    Determine file type based on extension.
    
    Args:
        file_path: Path to the file
    
    Returns:
        File type: 'pdf', 'image', or 'unknown'
    """
    from config import SUPPORTED_PDF_EXTENSIONS, SUPPORTED_IMAGE_EXTENSIONS
    
    ext = file_path.suffix.lower()
    
    if ext in SUPPORTED_PDF_EXTENSIONS:
        return 'pdf'
    elif ext in SUPPORTED_IMAGE_EXTENSIONS:
        return 'image'
    else:
        return 'unknown'


def cleanup_old_files(days: int = 30, base_dir: Optional[Path] = None) -> None:
    """
    Remove files older than specified days.
    
    Args:
        days: Number of days to keep files
        base_dir: Base directory to clean (defaults to ATTACHMENTS_DIR)
    
    TODO:
        - Implement archive functionality before deletion
        - Add configuration for retention policy
        - Implement selective cleanup based on file type
    """
    if base_dir is None:
        from config import ATTACHMENTS_DIR
        base_dir = ATTACHMENTS_DIR
    
    logger.info(f"TODO: Implement cleanup of files older than {days} days in {base_dir}")
    pass
