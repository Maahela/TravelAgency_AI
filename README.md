# Travel Agency Email Automation System

## Overview

Automated system for processing hotel rate emails, extracting data from PDFs and images, and storing structured rate information.

## Features

- ✉️ **Microsoft Outlook Integration** - Connect to Outlook via Microsoft Graph API
- 📄 **PDF Text Extraction** - Extract text from digital and scanned PDFs
- 🖼️ **OCR Processing** - Extract text from images using Tesseract/cloud OCR
- 🤖 **LLM-Powered Parsing** - Parse unstructured text into structured rate data
- 💾 **Database Storage** - Store rates in SQLite (Airtable support planned)
- 💬 **Chat Interface** - Query stored rates via natural language
- 📧 **Draft Email Generation** - Create draft emails for hotels and clients
- 🔔 **Notifications** - Internal alerts for system events

## Project Structure

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
│   └── query_rates.py       # Query operations
├── llm/                     # LLM integration
│   ├── llm_client.py        # LLM API client
│   └── prompts.py           # Prompt templates
├── chat/                    # Chat interface
│   └── chat_interface.py    # Query interface
├── utils/                   # Utilities
│   ├── logger.py            # Logging configuration
│   └── file_storage.py      # File handling
├── main.py                  # Main workflow
├── config.py                # Configuration
├── requirements.txt         # Dependencies
└── .env.example             # Environment variables template
```

## Installation

### Prerequisites

- Python 3.10+
- Tesseract OCR (for local OCR)
- Microsoft 365 account with Graph API access

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

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Install Tesseract OCR**

- **Windows**: Download from https://github.com/UB-Mannheim/tesseract/wiki
- **macOS**: `brew install tesseract`
- **Linux**: `sudo apt-get install tesseract-ocr`

5. **Configure environment variables**

```bash
cp .env.example .env
# Edit .env with your credentials
```

## Configuration

### Microsoft Graph API Setup

1. Register an app in Azure Portal
2. Grant Mail permissions (Mail.Read, Mail.Send)
3. Create client secret
4. Add credentials to `.env`

### Environment Variables

See `.env.example` for required variables:

- `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`
- `OPENAI_API_KEY` (for LLM)
- `TESSERACT_PATH` (path to Tesseract executable)

## Usage

### Main Workflow

Process incoming emails automatically:

```bash
python main.py
```

### Chat Interface

Query stored rates interactively:

```bash
python -m chat.chat_interface
```

## Workflow

1. **Authenticate** with Microsoft Graph API
2. **Fetch** unread emails from Outlook
3. **Download** email attachments (PDFs/images)
4. **Extract** text using OCR/PDF extraction
5. **Parse** rate data using LLM
6. **Validate** extracted data
7. **Store** valid rates in database
8. **Notify** on success/failure
9. **Flag** items needing manual review

## Development Status

⚠️ **This is a scaffold project** - Core functionality is outlined but not fully implemented.

### TODO Items

- Implement Microsoft Graph API authentication
- Complete PDF and OCR extraction logic
- Integrate OpenAI API for parsing
- Build chat interface NLP capabilities
- Add Airtable support
- Implement scheduling/automation
- Add web UI dashboard

## Contributing

This is an internal agency tool. For questions or contributions, contact the development team.

## License

Proprietary - Internal use only
