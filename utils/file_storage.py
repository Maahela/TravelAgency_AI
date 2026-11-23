"""
File storage utilities for handling email attachments.
"""

import os
import re
import shutil
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
from utils.logger import get_logger

logger = get_logger(__name__)


class FileSizeError(Exception):
    """Raised when file size exceeds maximum allowed size."""
    pass


class FileSecurityError(Exception):
    """Raised when file fails security validation."""
    pass


def sanitize_filename(filename: str) -> str:
    """
    Reduce an untrusted filename (e.g. from an email attachment) to a safe basename.

    Strips any directory components (both / and \\), replaces characters outside a
    conservative allow-list, and rejects names that are empty or only dots.
    """
    # Drop any path components, regardless of the sender's OS conventions
    name = re.split(r"[\\/]", filename or "")[-1]
    # Keep letters, digits, dot, dash, underscore and space
    name = re.sub(r"[^A-Za-z0-9._\- ]", "_", name).strip(" .")
    if not name:
        raise FileSecurityError(f"Invalid filename: {filename!r}")
    # Keep names to a sane length while preserving the extension
    stem, ext = os.path.splitext(name)
    return stem[:150] + ext[:10]


def validate_file_size(file_data: bytes, filename: str) -> None:
    """
    Validate that file size is within acceptable limits.
    
    Args:
        file_data: Binary data of the file
        filename: Name of the file
    
    Raises:
        FileSizeError: If file size exceeds MAX_FILE_SIZE_MB
    """
    from config import MAX_FILE_SIZE_MB
    
    file_size_mb = len(file_data) / (1024 * 1024)
    
    if file_size_mb > MAX_FILE_SIZE_MB:
        error_msg = f"File '{filename}' size ({file_size_mb:.2f}MB) exceeds maximum allowed size ({MAX_FILE_SIZE_MB}MB)"
        logger.error(error_msg)
        raise FileSizeError(error_msg)
    
    logger.debug(f"File size validation passed for '{filename}': {file_size_mb:.2f}MB")


def validate_file_extension(filename: str) -> None:
    """
    Validate that file extension is in the allowed list.
    
    Args:
        filename: Name of the file
    
    Raises:
        FileSecurityError: If file extension is not supported
    """
    from config import SUPPORTED_PDF_EXTENSIONS, SUPPORTED_IMAGE_EXTENSIONS
    
    ext = Path(filename).suffix.lower()
    allowed_extensions = SUPPORTED_PDF_EXTENSIONS + SUPPORTED_IMAGE_EXTENSIONS
    
    if ext not in allowed_extensions:
        error_msg = f"File extension '{ext}' for '{filename}' is not allowed. Supported: {allowed_extensions}"
        logger.error(error_msg)
        raise FileSecurityError(error_msg)
    
    logger.debug(f"File extension validation passed for '{filename}'")


def check_file_content(file_data: bytes, filename: str) -> None:
    """
    Perform basic content validation to ensure file matches its extension.
    
    Args:
        file_data: Binary data of the file
        filename: Name of the file
    
    Raises:
        FileSecurityError: If file content doesn't match expected format
    """
    ext = Path(filename).suffix.lower()
    
    # Check PDF files
    if ext == '.pdf':
        if not file_data.startswith(b'%PDF'):
            error_msg = f"File '{filename}' claims to be PDF but doesn't have PDF signature"
            logger.error(error_msg)
            raise FileSecurityError(error_msg)
    
    # Check common image formats
    elif ext in ['.jpg', '.jpeg']:
        if not (file_data.startswith(b'\xff\xd8\xff')):
            error_msg = f"File '{filename}' claims to be JPEG but doesn't have JPEG signature"
            logger.warning(error_msg)
            # Warning only, some JPEGs may have variations
    
    elif ext == '.png':
        if not file_data.startswith(b'\x89PNG\r\n\x1a\n'):
            error_msg = f"File '{filename}' claims to be PNG but doesn't have PNG signature"
            logger.error(error_msg)
            raise FileSecurityError(error_msg)
    
    logger.debug(f"Content validation passed for '{filename}'")


def save_attachment(
    file_data: bytes,
    filename: str,
    base_dir: Optional[Path] = None
) -> Path:
    """
    Save email attachment to local storage with validation and security checks.
    
    Args:
        file_data: Binary data of the file
        filename: Name of the file
        base_dir: Base directory for storage (defaults to ATTACHMENTS_DIR from config)
    
    Returns:
        Path object pointing to the saved file
    
    Raises:
        FileSizeError: If file size exceeds maximum allowed
        FileSecurityError: If file fails security validation
    """
    # Attachment names come from external senders: never trust them as paths
    filename = sanitize_filename(filename)

    # Perform security validations
    validate_file_size(file_data, filename)
    validate_file_extension(filename)
    check_file_content(file_data, filename)
    
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

    # Defence in depth: the final path must stay inside the storage directory
    if save_dir.resolve() not in file_path.resolve().parents:
        raise FileSecurityError(f"Refusing to write outside storage directory: {filename!r}")

    # Save file
    try:
        with open(file_path, 'wb') as f:
            f.write(file_data)
        logger.info(f"Saved attachment: {file_path} ({len(file_data) / 1024:.2f}KB)")
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


def archive_file(file_path: Path, archive_dir: Optional[Path] = None) -> Path:
    """
    Archive a file by moving it to the archive directory.
    
    Args:
        file_path: Path to the file to archive
        archive_dir: Archive directory (defaults to ARCHIVE_DIR from config)
    
    Returns:
        Path to the archived file
    """
    if archive_dir is None:
        from config import ARCHIVE_DIR
        archive_dir = ARCHIVE_DIR
    
    # Maintain the same subfolder structure in archive
    try:
        # Get relative path from attachments to maintain structure
        from config import ATTACHMENTS_DIR
        rel_path = file_path.relative_to(ATTACHMENTS_DIR)
    except ValueError:
        # If file is not in attachments dir, use just the filename
        rel_path = file_path.name
    
    archive_path = archive_dir / rel_path
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Move file to archive
    shutil.move(str(file_path), str(archive_path))
    logger.info(f"Archived file: {file_path} -> {archive_path}")
    
    return archive_path


def cleanup_old_files(
    days: Optional[int] = None,
    base_dir: Optional[Path] = None,
    archive: bool = True
) -> Tuple[int, int]:
    """
    Archive or remove files older than specified days.
    
    Args:
        days: Number of days to keep files (defaults to FILE_RETENTION_DAYS from config)
        base_dir: Base directory to clean (defaults to ATTACHMENTS_DIR)
        archive: If True, move files to archive; if False, delete them
    
    Returns:
        Tuple of (files_processed, total_size_mb)
    """
    if base_dir is None:
        from config import ATTACHMENTS_DIR
        base_dir = ATTACHMENTS_DIR
    
    if days is None:
        from config import FILE_RETENTION_DAYS
        days = FILE_RETENTION_DAYS
    
    cutoff_date = datetime.now() - timedelta(days=days)
    files_processed = 0
    total_size = 0
    
    logger.info(f"Starting cleanup of files older than {days} days in {base_dir}")
    logger.info(f"Cutoff date: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Walk through all files in the directory
    for file_path in base_dir.rglob('*'):
        if not file_path.is_file():
            continue
        
        # Check file modification time
        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
        
        if file_mtime < cutoff_date:
            file_size = file_path.stat().st_size
            total_size += file_size
            
            try:
                if archive:
                    archive_file(file_path)
                    logger.info(f"Archived old file: {file_path} (modified: {file_mtime.strftime('%Y-%m-%d')})")
                else:
                    file_path.unlink()
                    logger.info(f"Deleted old file: {file_path} (modified: {file_mtime.strftime('%Y-%m-%d')})")
                
                files_processed += 1
            except Exception as e:
                logger.error(f"Failed to process file {file_path}: {e}")
    
    # Clean up empty directories
    for dir_path in sorted(base_dir.rglob('*'), reverse=True):
        if dir_path.is_dir() and not any(dir_path.iterdir()):
            try:
                dir_path.rmdir()
                logger.debug(f"Removed empty directory: {dir_path}")
            except Exception as e:
                logger.warning(f"Failed to remove empty directory {dir_path}: {e}")
    
    total_size_mb = total_size / (1024 * 1024)
    action = "archived" if archive else "deleted"
    logger.info(f"Cleanup complete: {files_processed} files {action}, {total_size_mb:.2f}MB freed")
    
    return files_processed, total_size_mb
