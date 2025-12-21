# JAK Travel Agency Email Automation System

## Overview

Intelligent automation system for processing hotel rate emails, extracting structured data from PDFs and images, and providing natural language query capabilities through an AI-powered chat interface.

## ✨ Features

### Core Functionality

- ✉️ **Microsoft Outlook Integration** - Automated email processing via Microsoft Graph API
- 📄 **PDF Text Extraction** - Extract text from digital and scanned PDFs
- 🖼️ **OCR Processing** - Extract text from images using Tesseract OCR
- 🤖 **LLM-Powered Parsing** - Parse unstructured text into structured rate data using Google Gemini
- 💾 **Dual Database Storage** - SQLite local storage + Airtable cloud sync (3NF normalized)
- 🔄 **API Key Rotation** - Automatic rotation across multiple Google API keys to maximize free-tier usage

### Intelligent Chat Interface

- 💬 **Natural Language Queries** - Ask questions about rates in plain English
- 🔍 **Smart Rate Search** - Query rates by hotel, date range, room type, meal plan
- 💰 **Budget Calculator** - Calculate trip costs from itinerary descriptions
- 📧 **Hotel Email Discovery** - Automatically find hotel contact emails via web scraping
- 🧠 **Function Calling** - Gemini-powered tool selection for complex queries
- 📝 **Conversation Memory** - Multi-turn dialogue with context retention

### Data Extraction & Management

- 🏨 **Hotel Data Normalization** - Separate Hotels, Room Types, and Meal Plans tables
- 💵 **Granular Price Extraction** - Meal supplements, gala dinners, extra charges
- 📋 **Contract Data Extraction** - Cancellation policies, payment terms, special conditions
- 🔧 **Data Standardization** - Automatic meal plan name normalization (e.g., "B&B" → "BB")
- 🌐 **Hotel Discovery Agent** - Web scraping with LLM-based email classification

### Admin Dashboard

- 📊 **Web Dashboard** - Next.js frontend with TypeScript
- 🔌 **REST API Backend** - FastAPI server for data access
- 📈 **Statistics & Analytics** - View processing stats and rate summaries
- 🏨 **Hotel Management** - View and manage hotel contacts
- 💸 **Price Item Viewer** - Browse granular pricing details

### Automation & Notifications

- 🔔 **Internal Notifications** - Email alerts for system events
- 📧 **Draft Email Generation** - Create draft emails for hotels and clients
- ⚡ **Automated Workflow** - End-to-end processing from email to database

## 🏗️ Project Structure

```
JAKEmailBot/
├── email_handler/           # Outlook email operations
│   ├── outlook_reader.py    # Read emails and attachments
│   ├── outlook_sender.py    # Create draft emails
│   └── notifications.py     # Internal notifications
├── extractor/               # Text extraction
│   ├── pdf_text_extractor.py
│   ├── image_ocr_extractor.py
│   └── rate_parser.py       # Parse rates from text
├── database/                # Data storage
│   ├── db_init.py           # Database initialization
│   ├── insert_rates.py      # Insert operations
│   ├── query_rates.py       # Query operations
│   ├── query_price_items.py # Price item queries
│   ├── airtable_client.py   # Airtable integration
│   └── hotel_management.py  # Hotel CRUD operations
├── llm/                     # LLM integration
│   ├── llm_client.py        # Multi-key LLM client with rotation
│   ├── prompts.py           # Prompt templates
│   └── itinerary_extractor.py # Budget calculator
├── chat/                    # Chat interface
│   ├── chat_interface.py    # Basic query interface
│   └── smart_chat_interface.py # Advanced function-calling interface
├── calculator/              # Budget calculation
│   └── budget.py            # Trip cost calculator
├── workflow/                # Automation workflows
│   └── hotel_discovery_agent.py # Web scraping for hotel emails
├── admin_dashboard/         # Web dashboard
│   ├── backend/             # FastAPI backend
│   └── frontend/            # Next.js frontend
├── scripts/                 # Utility scripts
│   ├── setup/               # Setup and initialization
│   ├── verification/        # Testing and verification
│   ├── migration/           # Database migration
│   ├── ops/                 # Operational scripts
│   └── debug/               # Debugging utilities
├── tests/                   # Test suite
├── utils/                   # Utilities
│   ├── logger.py            # Logging configuration
│   └── file_storage.py      # File handling
├── main.py                  # Main workflow
├── config.py                # Configuration
├── requirements.txt         # Dependencies
└── .env                     # Environment variables
```

## 🚀 Installation

### Prerequisites

- Python 3.10+
- Node.js 18+ (for admin dashboard)
- Tesseract OCR
- Microsoft 365 account with Graph API access
- Google Gemini API key(s)
- Airtable account (optional)

### Setup Steps

1. **Clone or navigate to the project directory**

```bash
cd JAKEmailBot
```

2. **Create virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Python dependencies**

```bash
pip install -r requirements.txt
```

4. **Install Tesseract OCR**

- **Windows**: Download from https://github.com/UB-Mannheim/tesseract/wiki
- **macOS**: `brew install tesseract`
- **Linux**: `sudo apt-get install tesseract-ocr`

5. **Configure environment variables**

Create a `.env` file in the project root with the following variables:

```env
# Microsoft Graph API
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret
AZURE_TENANT_ID=your_tenant_id
OUTLOOK_EMAIL=your_email@example.com

# Google Gemini API (supports multiple keys for rotation)
GOOGLE_API_KEY_1=your_first_key
GOOGLE_API_KEY_2=your_second_key
GOOGLE_API_KEY_3=your_third_key

# Google Custom Search (for hotel discovery)
GOOGLE_SEARCH_API_KEY=your_search_key
GOOGLE_SEARCH_CX=your_search_engine_id

# Airtable (optional)
AIRTABLE_API_KEY=your_airtable_key
AIRTABLE_BASE_ID=your_base_id

# Database
DB_PATH=data/rates.db

# OCR
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe

# Notifications
NOTIFICATION_EMAIL=alerts@example.com
ENABLE_NOTIFICATIONS=true
```

6. **Install admin dashboard dependencies** (optional)

```bash
cd admin_dashboard/frontend
npm install
cd ../..
```

## 📖 Usage

### Main Email Processing Workflow

Process incoming emails automatically:

```bash
python main.py
```

This will:

1. Authenticate with Microsoft Graph API
2. Fetch unread emails from Outlook
3. Download and process attachments (PDFs/images)
4. Extract text using OCR/PDF extraction
5. Parse rate data, price items, and contract data using LLM
6. Store structured data in SQLite and Airtable
7. Mark emails as read

### Chat Interface

Query stored rates interactively:

```bash
python -m chat.smart_chat_interface
```

**Example queries:**

- "What are the rates for Galle Face Hotel in December?"
- "Find me hotels with BB meal plan under $150"
- "Calculate budget for 2 nights at Hotel A and 3 nights at Hotel B"
- "What's the email address for Cinnamon Grand?"

### Admin Dashboard

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed dashboard setup instructions.

Quick start:

```bash
# Start backend (from project root)
cd admin_dashboard/backend
python main.py

# Start frontend (in new terminal)
cd admin_dashboard/frontend
npm run dev
```

Access dashboard at: http://localhost:3000

## 🔄 Workflow

1. **Authenticate** with Microsoft Graph API
2. **Fetch** unread emails from Outlook inbox
3. **Download** email attachments (PDFs/images) and extract body text
4. **Extract** text using Tesseract OCR or PDF extraction
5. **Parse** rate data using Google Gemini LLM with structured prompts
6. **Extract** granular price items (meal supplements, extras)
7. **Extract** contract data (policies, terms, conditions)
8. **Normalize** hotel names and meal plans
9. **Validate** extracted data against schema
10. **Store** valid data in SQLite and sync to Airtable
11. **Notify** on success/failure via email
12. **Mark** email as read

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run specific test
python tests/test_budget.py

# Run with verbose output
pytest -v
```

## 🛠️ Development

### Database Schema

The system uses a normalized 3NF schema:

- **hotels** - Hotel information and contact details
- **room_types** - Room types linked to hotels
- **meal_plans** - Global meal plan definitions
- **rates** - Base room rates
- **price_items** - Granular pricing (supplements, extras)
- **contract_data** - Policies and terms
- **processing_log** - Processing status tracking

### API Key Rotation

The system automatically rotates through multiple Google API keys when quota limits are reached, maximizing free-tier usage.

### Adding New Features

1. Create feature branch
2. Implement changes
3. Add tests in `tests/`
4. Update documentation
5. Test end-to-end workflow

## 📝 Configuration

All configuration is managed through environment variables in `.env`. See `config.py` for available options.

Key settings:

- `DB_PATH` - SQLite database location
- `GOOGLE_API_KEY_N` - Multiple API keys for rotation
- `TESSERACT_PATH` - Path to Tesseract executable
- `LOG_LEVEL` - Logging verbosity (DEBUG, INFO, WARNING, ERROR)

## 🤝 Contributing

This is an internal agency tool. For questions or contributions, contact the development team.

## 📄 License

Proprietary - Internal use only

## 🔗 Additional Documentation

- [DEPLOYMENT.md](DEPLOYMENT.md) - Detailed deployment guide for admin dashboard
- [scripts/README.md](scripts/README.md) - Script documentation
- [tests/README.md](tests/README.md) - Testing guide
