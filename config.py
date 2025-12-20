"""
Configuration module for the Email Automation System.
Loads environment variables and provides centralized configuration.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directories - use absolute paths to prevent issues when running from subdirectories
BASE_DIR = Path(os.path.realpath(__file__)).parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
ATTACHMENTS_DIR = Path(os.getenv("ATTACHMENTS_DIR", "./data/attachments"))

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)

# Microsoft Graph API Configuration
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
OUTLOOK_EMAIL = os.getenv("OUTLOOK_EMAIL")
OUTLOOK_FOLDER_ID = os.getenv("OUTLOOK_FOLDER_ID", "inbox")

# LLM API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Google API Keys (supports multiple for quota rotation)
# Format in .env: GOOGLE_API_KEY_1=key1, GOOGLE_API_KEY_2=key2, etc.
GOOGLE_API_KEYS = []
key_index = 1
while True:
    key = os.getenv(f"GOOGLE_API_KEY_{key_index}")
    if key:
        GOOGLE_API_KEYS.append(key)
        key_index += 1
    else:
        break

# Fallback to single key if no numbered keys found
if not GOOGLE_API_KEYS and os.getenv("GOOGLE_API_KEY"):
    GOOGLE_API_KEYS.append(os.getenv("GOOGLE_API_KEY"))

# Google Custom Search Configuration
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_CX = os.getenv("GOOGLE_SEARCH_CX")

LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")

# OCR Configuration
# OCR Configuration
# Default to standard Windows path if not set
TESSERACT_PATH = os.getenv("TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe")

# Database Configuration
raw_db_path = os.getenv("DB_PATH")
if raw_db_path:
    # If absolute, use as is. If relative, anchor to BASE_DIR.
    p = Path(raw_db_path)
    if p.is_absolute():
        DB_PATH = p.resolve()
    else:
        DB_PATH = (BASE_DIR / p).resolve()
else:
    DB_PATH = (DATA_DIR / "rates.db").resolve()
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "rates")

# Notification Settings
NOTIFICATION_EMAIL = os.getenv("NOTIFICATION_EMAIL")
ENABLE_NOTIFICATIONS = os.getenv("ENABLE_NOTIFICATIONS", "true").lower() == "true"

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / "app.log"

# Supported file types
SUPPORTED_PDF_EXTENSIONS = [".pdf"]
SUPPORTED_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".tiff", ".bmp"]

# File Storage Settings
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))  # Maximum file size in MB
FILE_RETENTION_DAYS = int(os.getenv("FILE_RETENTION_DAYS", "30"))  # Days to keep files before archiving
ARCHIVE_DIR = Path(os.getenv("ARCHIVE_DIR", "./data/archive"))  # Archive directory
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

# Microsoft Graph API Scopes
# Microsoft Graph API Scopes
GRAPH_SCOPES = [
    "User.Read",
    "Mail.Read",
    "Mail.Send",
    "Mail.ReadWrite"
]
