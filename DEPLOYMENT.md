# Deployment Guide

This guide covers how to deploy and run the JAK Email Automation System, including the admin dashboard.

## Table of Contents

- [System Requirements](#system-requirements)
- [Initial Setup](#initial-setup)
- [Running the Email Processor](#running-the-email-processor)
- [Admin Dashboard Deployment](#admin-dashboard-deployment)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)

## System Requirements

### Hardware

- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 10GB free space (for attachments and database)

### Software

- **Python**: 3.10 or higher
- **Node.js**: 18.0 or higher (for admin dashboard)
- **Tesseract OCR**: Latest version
- **Git**: For version control

### Accounts & API Keys

- Microsoft 365 account with Graph API access
- Google Gemini API key(s) - multiple keys recommended for rotation
- Google Custom Search API key (for hotel discovery)
- Airtable account (optional, for cloud sync)

## Initial Setup

### 1. Clone the Repository

```bash
cd /path/to/your/projects
git clone <repository-url>
cd JAKEmailBot
```

### 2. Python Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Install Tesseract OCR

#### Windows

1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run installer (default path: `C:\Program Files\Tesseract-OCR`)
3. Add to PATH or note installation path for `.env`

#### macOS

```bash
brew install tesseract
```

#### Linux (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
# ============================================
# Microsoft Graph API Configuration
# ============================================
AZURE_CLIENT_ID=your_azure_client_id
AZURE_CLIENT_SECRET=your_azure_client_secret
AZURE_TENANT_ID=your_azure_tenant_id
OUTLOOK_EMAIL=your_email@example.com
OUTLOOK_FOLDER_ID=inbox

# ============================================
# Google Gemini API Keys (Multiple for Rotation)
# ============================================
GOOGLE_API_KEY_1=your_first_gemini_key
GOOGLE_API_KEY_2=your_second_gemini_key
GOOGLE_API_KEY_3=your_third_gemini_key

# ============================================
# Google Custom Search (for Hotel Discovery)
# ============================================
GOOGLE_SEARCH_API_KEY=your_google_search_key
GOOGLE_SEARCH_CX=your_custom_search_engine_id

# ============================================
# Airtable Configuration (Optional)
# ============================================
AIRTABLE_API_KEY=your_airtable_api_key
AIRTABLE_BASE_ID=your_airtable_base_id
AIRTABLE_TABLE_NAME=rates

# ============================================
# Database Configuration
# ============================================
DB_PATH=data/rates.db

# ============================================
# OCR Configuration
# ============================================
# Windows default path:
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
# macOS/Linux (usually auto-detected):
# TESSERACT_PATH=/usr/local/bin/tesseract

# ============================================
# Notification Settings
# ============================================
NOTIFICATION_EMAIL=alerts@example.com
ENABLE_NOTIFICATIONS=true

# ============================================
# Logging
# ============================================
LOG_LEVEL=INFO
```

### 5. Initialize Database

```bash
python -c "from database.db_init import initialize_database; from config import DB_PATH; initialize_database(DB_PATH)"
```

### 6. Verify Setup

```bash
# Test configuration
python -c "from config import *; print('✅ Configuration loaded successfully')"

# Test database connection
python -c "from database.db_init import get_db_connection; from config import DB_PATH; conn = get_db_connection(DB_PATH); print('✅ Database connection successful')"
```

## Running the Email Processor

### Manual Execution

Process emails on-demand:

```bash
# Activate virtual environment first
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Run main workflow
python main.py
```

### Scheduled Execution

#### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., every 15 minutes)
4. Action: Start a program
   - Program: `C:\path\to\JAKEmailBot\venv\Scripts\python.exe`
   - Arguments: `main.py`
   - Start in: `C:\path\to\JAKEmailBot`

#### macOS/Linux (Cron)

```bash
# Edit crontab
crontab -e

# Add entry to run every 15 minutes
*/15 * * * * cd /path/to/JAKEmailBot && /path/to/JAKEmailBot/venv/bin/python main.py >> logs/cron.log 2>&1
```

## Admin Dashboard Deployment

### Development Mode

#### Backend Setup

1. **Navigate to backend directory**

```bash
cd admin_dashboard/backend
```

2. **Ensure database path is correct**

The backend uses the same database as the main application. Verify `config.py` points to the correct `DB_PATH`.

3. **Start backend server**

```bash
# From admin_dashboard/backend directory
python main.py
```

Backend will run on: http://localhost:8000

**API Endpoints:**

- `GET /stats` - System statistics
- `GET /rates` - List all rates
- `GET /hotels` - List all hotels
- `GET /contacts` - Hotel contacts
- `GET /price-items` - Granular price items

#### Frontend Setup

1. **Navigate to frontend directory**

```bash
cd admin_dashboard/frontend
```

2. **Install dependencies** (first time only)

```bash
npm install
```

3. **Configure API endpoint**

Create `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

4. **Start development server**

```bash
npm run dev
```

Frontend will run on: http://localhost:3000

#### Using the Convenience Script

For easier startup, use the provided script:

**Windows:**

```bash
# From project root
start_dashboard.bat
```

**macOS/Linux:**

```bash
# From project root
chmod +x start_dashboard.sh
./start_dashboard.sh
```

This script will:

1. Start the backend server
2. Wait for backend to be ready
3. Start the frontend development server
4. Open browser to http://localhost:3000

### Production Deployment

#### Backend (FastAPI)

**Option 1: Uvicorn with systemd (Linux)**

1. Create systemd service file: `/etc/systemd/system/jak-backend.service`

```ini
[Unit]
Description=JAK Email Bot Backend
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/JAKEmailBot/admin_dashboard/backend
Environment="PATH=/path/to/JAKEmailBot/venv/bin"
ExecStart=/path/to/JAKEmailBot/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

2. Enable and start service:

```bash
sudo systemctl enable jak-backend
sudo systemctl start jak-backend
sudo systemctl status jak-backend
```

**Option 2: Docker**

Create `Dockerfile` in `admin_dashboard/backend`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Copy requirements from root
COPY ../../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .
COPY ../../database ./database
COPY ../../config.py .
COPY ../../utils ./utils

EXPOSE 8000

CMD ["python", "main.py"]
```

Build and run:

```bash
docker build -t jak-backend .
docker run -d -p 8000:8000 --env-file ../../.env jak-backend
```

#### Frontend (Next.js)

**Option 1: Vercel (Recommended)**

1. Push code to GitHub
2. Import project in Vercel
3. Set environment variables:
   - `NEXT_PUBLIC_API_URL=https://your-backend-url.com`
4. Deploy

**Option 2: Self-hosted with PM2**

```bash
cd admin_dashboard/frontend

# Build production bundle
npm run build

# Install PM2 globally
npm install -g pm2

# Start with PM2
pm2 start npm --name "jak-frontend" -- start

# Save PM2 configuration
pm2 save

# Setup PM2 to start on boot
pm2 startup
```

**Option 3: Docker**

Create `Dockerfile` in `admin_dashboard/frontend`:

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
```

Build and run:

```bash
docker build -t jak-frontend .
docker run -d -p 3000:3000 --env-file .env.local jak-frontend
```

**Option 4: Static Export**

If you don't need server-side features:

```bash
# Update next.config.ts to add:
# output: 'export'

npm run build

# Deploy the 'out' directory to any static host
# (Netlify, GitHub Pages, S3, etc.)
```

## Troubleshooting

### Common Issues

#### 1. "Authentication failed" error

**Problem**: Microsoft Graph API authentication fails

**Solutions**:

- Verify `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID` in `.env`
- Check that app has correct permissions in Azure Portal:
  - Mail.Read
  - Mail.Send
  - Mail.ReadWrite
  - User.Read
- Delete `.token_cache.bin` and re-authenticate

#### 2. "Tesseract not found" error

**Problem**: OCR extraction fails

**Solutions**:

- Verify Tesseract is installed: `tesseract --version`
- Check `TESSERACT_PATH` in `.env` points to correct executable
- Windows: Ensure path uses double backslashes or raw string
  - Correct: `C:\\Program Files\\Tesseract-OCR\\tesseract.exe`

#### 3. "API quota exceeded" error

**Problem**: Google Gemini API quota exhausted

**Solutions**:

- Add more API keys to `.env` (GOOGLE_API_KEY_2, GOOGLE_API_KEY_3, etc.)
- System will automatically rotate through available keys
- Check quota limits in Google Cloud Console

#### 4. Frontend can't connect to backend

**Problem**: Dashboard shows "Failed to fetch" errors

**Solutions**:

- Verify backend is running: `curl http://localhost:8000/stats`
- Check `NEXT_PUBLIC_API_URL` in frontend `.env.local`
- Ensure no firewall blocking port 8000
- Check CORS settings in backend `main.py`

#### 5. Database locked error

**Problem**: "Database is locked" when running multiple processes

**Solutions**:

- SQLite doesn't handle concurrent writes well
- Don't run `main.py` and dashboard backend simultaneously if both write to DB
- Consider using separate read-only connection for dashboard
- For production, migrate to PostgreSQL

#### 6. "No module named 'X'" error

**Problem**: Import errors when running scripts

**Solutions**:

- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.10+)

#### 7. Admin dashboard shows no data

**Problem**: Dashboard loads but shows empty tables

**Solutions**:

- Run `python main.py` at least once to process emails
- Verify database path is correct in backend
- Check backend logs for errors
- Verify database file exists: `ls data/rates.db`

### Logs and Debugging

#### Enable Debug Logging

Edit `.env`:

```env
LOG_LEVEL=DEBUG
```

#### Check Logs

```bash
# Application logs
tail -f logs/app.log

# Backend logs (if running in terminal)
cd admin_dashboard/backend
python main.py  # Watch console output

# Frontend logs
cd admin_dashboard/frontend
npm run dev  # Watch console output
```

#### Test Individual Components

```bash
# Test email reading
python -c "from email_handler.outlook_reader import OutlookReader; r = OutlookReader(); r.authenticate()"

# Test LLM connection
python -c "from llm.llm_client import LLMClient; c = LLMClient(); print(c.generate('Hello'))"

# Test database
python -c "from database.query_rates import search_rates; print(search_rates('Galle'))"

# Test chat interface
python -m chat.smart_chat_interface
```

## Performance Optimization

### For Large Datasets

1. **Add database indexes**:

```sql
CREATE INDEX idx_hotel_name ON rates(hotel_name);
CREATE INDEX idx_check_in ON rates(check_in_date);
CREATE INDEX idx_room_type ON rates(room_type);
```

2. **Enable WAL mode** (better concurrency):

```sql
PRAGMA journal_mode=WAL;
```

3. **Batch processing**: Process emails in smaller batches

### For Production

1. **Use PostgreSQL** instead of SQLite for better concurrency
2. **Add Redis** for caching frequently accessed data
3. **Use Nginx** as reverse proxy for backend
4. **Enable gzip compression** in Next.js config
5. **Set up monitoring** (e.g., Sentry, DataDog)

## Security Considerations

### Production Checklist

- [ ] Use environment-specific `.env` files (never commit to git)
- [ ] Rotate API keys regularly
- [ ] Enable HTTPS for dashboard (use Let's Encrypt)
- [ ] Add authentication to admin dashboard
- [ ] Restrict backend API access (API keys, IP whitelist)
- [ ] Regular database backups
- [ ] Monitor logs for suspicious activity
- [ ] Keep dependencies updated (`pip list --outdated`)

## Backup and Recovery

### Database Backup

```bash
# Manual backup
cp data/rates.db data/rates_backup_$(date +%Y%m%d).db

# Automated daily backup (cron)
0 2 * * * cp /path/to/JAKEmailBot/data/rates.db /path/to/backups/rates_$(date +\%Y\%m\%d).db
```

### Restore from Backup

```bash
cp data/rates_backup_20231221.db data/rates.db
```

## Support

For issues or questions:

1. Check this troubleshooting guide
2. Review logs in `logs/app.log`
3. Contact the development team

## Next Steps

After successful deployment:

1. ✅ Process your first email: `python main.py`
2. ✅ Query data via chat: `python -m chat.smart_chat_interface`
3. ✅ View dashboard: http://localhost:3000
4. ✅ Set up scheduled execution (cron/Task Scheduler)
5. ✅ Configure monitoring and alerts
