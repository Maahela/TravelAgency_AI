"""
Test script for file storage enhancements.
Tests file validation, security checks, and cleanup functionality.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.file_storage import (
    save_attachment,
    validate_file_size,
    validate_file_extension,
    check_file_content,
    cleanup_old_files,
    archive_file,
    FileSizeError,
    FileSecurityError
)
from utils.logger import get_logger

logger = get_logger(__name__)


def test_file_size_validation():
    """Test file size validation."""
    print("\n=== Testing File Size Validation ===")
    
    # Test valid file size
    try:
        small_file = b"Small file content"
        validate_file_size(small_file, "small.pdf")
        print("✓ Small file passed validation")
    except FileSizeError as e:
        print(f"✗ Small file failed: {e}")
    
    # Test oversized file (simulate a large file)
    try:
        # Create a 51MB file (exceeds default 50MB limit)
        large_file = b"X" * (51 * 1024 * 1024)
        validate_file_size(large_file, "large.pdf")
        print("✗ Large file should have been rejected")
    except FileSizeError as e:
        print(f"✓ Large file correctly rejected: {e}")


def test_file_extension_validation():
    """Test file extension validation."""
    print("\n=== Testing File Extension Validation ===")
    
    # Test valid extensions
    valid_files = ["test.pdf", "image.jpg", "photo.png", "scan.tiff"]
    for filename in valid_files:
        try:
            validate_file_extension(filename)
            print(f"✓ {filename} passed extension validation")
        except FileSecurityError as e:
            print(f"✗ {filename} failed: {e}")
    
    # Test invalid extensions
    invalid_files = ["malware.exe", "script.js", "document.docx"]
    for filename in invalid_files:
        try:
            validate_file_extension(filename)
            print(f"✗ {filename} should have been rejected")
        except FileSecurityError as e:
            print(f"✓ {filename} correctly rejected")


def test_content_validation():
    """Test file content validation."""
    print("\n=== Testing File Content Validation ===")
    
    # Test valid PDF
    try:
        pdf_content = b"%PDF-1.4\nSample PDF content"
        check_file_content(pdf_content, "valid.pdf")
        print("✓ Valid PDF passed content check")
    except FileSecurityError as e:
        print(f"✗ Valid PDF failed: {e}")
    
    # Test fake PDF (wrong content)
    try:
        fake_pdf = b"This is not a PDF"
        check_file_content(fake_pdf, "fake.pdf")
        print("✗ Fake PDF should have been rejected")
    except FileSecurityError as e:
        print(f"✓ Fake PDF correctly rejected")
    
    # Test valid PNG
    try:
        png_content = b"\x89PNG\r\n\x1a\nSample PNG content"
        check_file_content(png_content, "valid.png")
        print("✓ Valid PNG passed content check")
    except FileSecurityError as e:
        print(f"✗ Valid PNG failed: {e}")


def test_save_attachment():
    """Test saving attachments with validation."""
    print("\n=== Testing Save Attachment ===")
    
    from config import ATTACHMENTS_DIR
    
    # Test saving valid PDF
    try:
        pdf_content = b"%PDF-1.4\nTest PDF content for attachment"
        file_path = save_attachment(pdf_content, "test_attachment.pdf")
        print(f"✓ PDF saved successfully: {file_path}")
        
        # Verify file exists
        if file_path.exists():
            print(f"✓ File exists on disk")
            # Clean up
            file_path.unlink()
            print(f"✓ Test file cleaned up")
        else:
            print(f"✗ File not found on disk")
    except Exception as e:
        print(f"✗ Failed to save PDF: {e}")
    
    # Test saving invalid file
    try:
        exe_content = b"MZ\x90\x00Fake executable"
        file_path = save_attachment(exe_content, "malware.exe")
        print(f"✗ Executable should have been rejected")
        if file_path.exists():
            file_path.unlink()
    except FileSecurityError as e:
        print(f"✓ Executable correctly rejected")


def test_save_attachment_blocks_path_traversal(tmp_path):
    """Attachment names from senders must not be able to escape the storage dir."""
    from utils.file_storage import sanitize_filename

    pdf_content = b"%PDF-1.4\nTraversal test"
    for evil in ["../../evil.pdf", "..\\..\\evil.pdf", "/etc/evil.pdf", "C:\\Windows\\evil.pdf"]:
        saved = save_attachment(pdf_content, evil, base_dir=tmp_path)
        assert tmp_path.resolve() in saved.resolve().parents
        assert saved.name.startswith("evil") and saved.suffix == ".pdf"
        assert saved.parent.parent == tmp_path

    for bad in ["", "..", "../", "...."]:
        try:
            sanitize_filename(bad)
            assert False, f"{bad!r} should be rejected"
        except FileSecurityError:
            pass


def test_cleanup_and_archive():
    """Test file cleanup and archiving."""
    print("\n=== Testing Cleanup and Archive ===")
    
    from config import ATTACHMENTS_DIR, ARCHIVE_DIR
    
    # Create test directory and files
    test_dir = ATTACHMENTS_DIR / "cleanup_test"
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Create some test files with different ages
    old_file = test_dir / "old_file.pdf"
    recent_file = test_dir / "recent_file.pdf"
    
    # Create files
    old_file.write_bytes(b"%PDF-1.4\nOld file content")
    recent_file.write_bytes(b"%PDF-1.4\nRecent file content")
    
    # Modify old file's timestamp to be 31 days ago
    old_timestamp = (datetime.now() - timedelta(days=31)).timestamp()
    os.utime(old_file, (old_timestamp, old_timestamp))
    
    print(f"Created test files:")
    print(f"  - {old_file} (31 days old)")
    print(f"  - {recent_file} (current)")
    
    # Run cleanup with archiving
    files_processed, size_mb = cleanup_old_files(days=30, base_dir=test_dir, archive=True)
    print(f"\n✓ Cleanup complete: {files_processed} file(s) archived, {size_mb:.2f}MB")
    
    # Verify old file was archived
    if not old_file.exists():
        print(f"✓ Old file was removed from attachments")
    else:
        print(f"✗ Old file still exists in attachments")
    
    # Verify recent file was not archived
    if recent_file.exists():
        print(f"✓ Recent file was preserved")
    else:
        print(f"✗ Recent file was incorrectly removed")
    
    # Check archive directory
    archived_files = list(ARCHIVE_DIR.rglob("old_file.pdf"))
    if archived_files:
        print(f"✓ Old file found in archive: {archived_files[0]}")
        # Clean up archive
        for f in archived_files:
            f.unlink()
    else:
        print(f"✗ Old file not found in archive")
    
    # Clean up test files
    if recent_file.exists():
        recent_file.unlink()
    if test_dir.exists() and not any(test_dir.iterdir()):
        test_dir.rmdir()
    print(f"✓ Test cleanup complete")


def main():
    """Run all tests."""
    print("=" * 60)
    print("File Storage Enhancement Tests")
    print("=" * 60)
    
    try:
        test_file_size_validation()
        test_file_extension_validation()
        test_content_validation()
        test_save_attachment()
        test_cleanup_and_archive()
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        print(f"\n✗ Test suite failed: {e}")


if __name__ == "__main__":
    main()
