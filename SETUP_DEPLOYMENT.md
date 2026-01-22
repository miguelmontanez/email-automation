# Nail Salon Automation - Setup & Deployment Guide

## 📋 Table of Contents
1. [Overview](#overview)
2. [System Requirements](#system-requirements)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Deployment](#deployment)
6. [Scheduling](#scheduling)
7. [Monitoring & Troubleshooting](#monitoring--troubleshooting)
8. [Database Management](#database-management)
9. [Security Best Practices](#security-best-practices)

---

## Overview

This automation suite includes two reliable scripts for your nail salon:

### Script 1: Same-Day Thank You Emails
- **Purpose**: Sends personalized thank-you emails to customers on their appointment day
- **Schedule**: 12:00 PM and 7:00 PM (configurable)
- **Source**: Fresha API - pulls completed appointments
- **Tracking**: Comprehensive logging with retry logic
- **File**: `src/scripts/thank_you_emails.py`

### Script 2: 7-Day Follow-Up Emails
- **Purpose**: Requests feedback on nail service longevity
- **Trigger**: 7 days after appointment completion
- **Deduplication**: Unique tokens prevent duplicate emails
- **Tracking**: Full audit trail with feedback tracking
- **File**: `src/scripts/followup_emails.py`

---

## System Requirements

### Minimum Hardware
- **CPU**: 1 core (1.5+ GHz)
- **RAM**: 512 MB minimum (1 GB recommended)
- **Disk**: 50 MB (includes database)
- **Network**: Stable internet connection

### Software Requirements
- **Python**: 3.8 or higher
- **OS**: Windows, macOS, or Linux
- **Database**: SQLite 3.6+ (included with Python)

### Internet Dependencies
- **Fresha API** access with valid credentials
- **SMTP Server** (Gmail, Office 365, or custom)
- Email account with app-specific password (if using Gmail)

---

## Installation

### Step 1: Clone or Download the Project

```bash
# Windows
cd c:\Users\vm_user\Documents\WorkSpace\python-automation
git clone <repo-url> nail-salon-automation
cd nail-salon-automation
```

### Step 2: Set Up Python Virtual Environment

```bash
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1

# Or on Command Prompt
python -m venv venv
venv\Scripts\activate.bat
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Verify Installation

```bash
python -c "import sqlite3; print(f'SQLite version: {sqlite3.version}')"
python -c "import requests; print(f'Requests installed: {requests.__version__}')"
```

---

## Configuration

### Step 1: Create Environment File

Create `.env` file in the project root:

```env
# Fresha API Configuration
FRESHA_API_KEY=your_fresha_api_key_here
FRESHA_BUSINESS_ID=your_business_id_here

# Email Configuration (Gmail Example)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-specific-password
SENDER_NAME=Your Nail Salon

# Alert Configuration
ALERT_EMAIL=owner@example.com
ENABLE_ALERTS=true

# Logging
LOG_LEVEL=INFO
TIMEZONE=America/New_York

# Headless Mode (for server deployment)
HEADLESS_MODE=true
```

### Step 2: Obtain Fresha API Credentials

1. Log in to **Fresha Business Portal**
2. Go to **Settings → Integrations → API**
3. Generate API Key and copy Business ID
4. Paste into `.env` file

### Step 3: Set Up Email Account

#### For Gmail:
1. Enable **2-Factor Authentication** on your Google Account
2. Generate **App Password** at https://myaccount.google.com/apppasswords
3. Use this 16-character password in `.env` (SENDER_PASSWORD)

#### For Office 365:
```env
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SENDER_EMAIL=your-email@yourcompany.com
SENDER_PASSWORD=your_office365_password
```

#### For Custom SMTP Server:
```env
SMTP_SERVER=smtp.your-server.com
SMTP_PORT=587
SENDER_EMAIL=your-email@your-domain.com
SENDER_PASSWORD=your_password
```

### Step 4: Secure Your .env File

```bash
# Windows PowerShell - Restrict access to current user only
icacls .env /inheritance:r /grant:r "%USERNAME%:F"

# Or add to .gitignore to prevent accidental commits
echo ".env" >> .gitignore
echo "logs/" >> .gitignore
echo "*.db" >> .gitignore
```

---

## Deployment

### Option 1: Local Machine (Windows)

#### Using Windows Task Scheduler

1. **Open Task Scheduler** (Win + R → taskschd.msc)

2. **Create Task for Thank You Emails (12 PM)**:
   - Name: "Salon - Thank You Emails 12PM"
   - Trigger: Daily at 12:00 PM
   - Action:
     ```
     Program: C:\path\to\venv\Scripts\python.exe
     Arguments: src\scripts\thank_you_emails.py
     Start in: C:\path\to\nail-salon-automation
     ```
   - Settings: "Run whether user is logged in or not"
   - Advanced: "Run with highest privileges"

3. **Create Task for Thank You Emails (7 PM)**:
   - Repeat Step 2 with 7:00 PM trigger

4. **Create Daily Task for Follow-Up Emails**:
   - Name: "Salon - Follow-Up Emails"
   - Trigger: Daily at 8:00 AM
   - Action: Same as above, but `followup_emails.py`

#### Create Helper Batch Script

Create `run_scripts.bat`:

```batch
@echo off
cd /d C:\path\to\nail-salon-automation
call venv\Scripts\activate.bat
python src\scripts\thank_you_emails.py
pause
```

### Option 2: Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ENV PYTHONUNBUFFERED=1

CMD ["python", "src/scripts/thank_you_emails.py"]
```

Build and run:

```bash
docker build -t nail-salon-automation .
docker run -d --name salon-bot --env-file .env nail-salon-automation
```

### Option 3: Cloud Deployment (AWS/DigitalOcean)

#### AWS Lambda with EventBridge

1. Package project into ZIP
2. Upload to AWS Lambda
3. Set EventBridge triggers:
   - `cron(0 12 * * ? *)` → thank_you_emails (12 PM UTC)
   - `cron(0 19 * * ? *)` → thank_you_emails (7 PM UTC)
   - `cron(0 8 * * ? *)` → followup_emails (8 AM UTC)

#### DigitalOcean App Platform

1. Connect GitHub repo
2. Create `app.yaml`:
```yaml
name: nail-salon-automation
services:
  - name: thank-you-scheduler
    github:
      repo: your-repo
      branch: main
    build_command: pip install -r requirements.txt
    run_command: python src/scripts/thank_you_emails.py
    envs:
      - key: FRESHA_API_KEY
        scope: RUN_AND_BUILD_TIME
        value: ${FRESHA_API_KEY}
```

---

## Scheduling

### Using APScheduler (Recommended for Long-Running Processes)

Create `scheduler.py`:

```python
import schedule
import time
from src.scripts.thank_you_emails import ThankYouEmailAutomation
from src.scripts.followup_emails import FollowUpEmailAutomation

def run_thank_you():
    automation = ThankYouEmailAutomation()
    automation.run()

def run_followup():
    automation = FollowUpEmailAutomation()
    automation.run()

# Schedule jobs
schedule.every().day.at("12:00").do(run_thank_you)
schedule.every().day.at("19:00").do(run_thank_you)
schedule.every().day.at("08:00").do(run_followup)

# Keep scheduler running
while True:
    schedule.run_pending()
    time.sleep(60)
```

Run with: `python scheduler.py`

---

## Monitoring & Troubleshooting

### Log Files Location

- **Thank You Script**: `logs/thank_you_script.log`
- **Follow-Up Script**: `logs/followup_script.log`
- **All Activity**: Check database `script_logs` table

### Check Execution Logs

```bash
# Windows PowerShell
Get-Content logs\thank_you_script.log -Tail 50
Get-Content logs\followup_script.log -Tail 50

# Linux/macOS
tail -50 logs/thank_you_script.log
tail -50 logs/followup_script.log
```

### Common Issues & Solutions

#### Issue: "Authentication failed" in email logs
**Solution**: 
- Verify SENDER_PASSWORD is app-specific password (not regular password)
- For Gmail: Ensure 2FA is enabled and app password is 16 characters
- Check that SMTP_SERVER and SMTP_PORT are correct

#### Issue: "API connection failed"
**Solution**:
- Verify FRESHA_API_KEY and FRESHA_BUSINESS_ID in .env
- Check internet connection
- Contact Fresha support to verify API access is enabled

#### Issue: Emails not sending at scheduled times
**Solution**:
- Check Windows Task Scheduler is running (services.msc → Task Scheduler)
- Verify task shows "Last Run Result: 0x0 (success)"
- Check log files for specific errors
- Ensure system time is correct

#### Issue: Database locked errors
**Solution**:
- Ensure only one script instance runs at a time
- Increase timeout in database_manager.py if needed
- Close any other SQLite connections to the database

### Database Inspection

```bash
# Launch SQLite CLI
sqlite3 src/database/nail_salon_automation.db

# Useful queries
SELECT * FROM email_logs WHERE email_type = 'thank_you' ORDER BY created_at DESC LIMIT 10;
SELECT * FROM script_logs ORDER BY execution_date DESC LIMIT 5;
SELECT COUNT(*), status FROM thank_you_emails GROUP BY status;
SELECT COUNT(*), status FROM followup_emails GROUP BY status;
```

---

## Database Management

### Backup Database

```bash
# Windows PowerShell
Copy-Item src\database\nail_salon_automation.db src\database\backups\backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').db

# Linux/macOS
cp src/database/nail_salon_automation.db src/database/backups/backup_$(date +%Y%m%d_%H%M%S).db
```

### Restore from Backup

```bash
# Windows PowerShell
Copy-Item src\database\backups\backup_20240101_120000.db src\database\nail_salon_automation.db

# Linux/macOS
cp src/database/backups/backup_20240101_120000.db src/database/nail_salon_automation.db
```

### View Database Stats

```bash
sqlite3 src/database/nail_salon_automation.db << EOF
.headers on
.mode column
SELECT 'Customers' as table_name, COUNT(*) as count FROM customers
UNION
SELECT 'Appointments', COUNT(*) FROM appointments
UNION
SELECT 'Thank You Emails', COUNT(*) FROM thank_you_emails
UNION
SELECT 'Follow-Up Emails', COUNT(*) FROM followup_emails
UNION
SELECT 'Email Logs', COUNT(*) FROM email_logs;
EOF
```

---

## Security Best Practices

### 1. Credential Management

✅ **DO:**
- Store credentials in `.env` file (never in code)
- Use app-specific passwords (not regular passwords)
- Restrict `.env` file permissions
- Add `.env` to `.gitignore`

❌ **DON'T:**
- Hardcode credentials in source code
- Share `.env` file in email or chat
- Use weak passwords
- Store passwords in plain text files

### 2. API Security

```python
# Use environment variables for all credentials
import os
API_KEY = os.getenv('FRESHA_API_KEY')
if not API_KEY:
    raise ValueError("FRESHA_API_KEY not set in environment")
```

### 3. Email Security

```python
# Use TLS/SSL for email
SMTP_PORT = 587  # TLS port
# or
SMTP_PORT = 465  # SSL port
```

### 4. Database Security

```python
# Enable SQLite encryption (optional)
# Install: pip install sqlalchemy sqlcipher3
# Then use: sqlite:///file:path.db?cipher=sqlcipher
```

### 5. Access Control

```bash
# Windows - Restrict file access
icacls nail-salon-automation /inheritance:r /grant:r "%USERNAME%:F"

# Linux/macOS
chmod 700 nail-salon-automation
chmod 600 .env
```

### 6. Audit Logging

- All email sending is logged with timestamp
- Failed attempts are logged with error details
- Script execution is tracked in `script_logs` table
- Create regular backups of logs

### 7. Monitoring & Alerts

- Set up alert email for failures
- Monitor ALERT_EMAIL inbox
- Review logs weekly
- Keep database backups offsite

---

## Maintenance Schedule

### Daily
- Monitor alert emails
- Check system logs for errors

### Weekly
- Review script execution logs
- Verify email delivery rates
- Check database size growth

### Monthly
- Backup database to external storage
- Review Fresha API quota usage
- Test disaster recovery procedures
- Update dependencies if needed

### Quarterly
- Security audit of credentials
- Performance optimization
- Plan for growth/scaling

---

## Support & Resources

### Getting Help

1. Check `logs/` directory for error messages
2. Review database `script_logs` table for execution history
3. Consult Fresha API documentation: https://docs.fresha.com
4. Review email service provider's SMTP settings

### Useful Commands

```bash
# Test Fresha API connection
python -c "from src.modules.fresha_api import FreshaAPIClient; client = FreshaAPIClient(); print(client.verify_connection())"

# Test email service
python -c "from src.modules.email_service import EmailService; service = EmailService(); print(service.send_thank_you_email('test@example.com', 'John'))"

# Check database integrity
sqlite3 src/database/nail_salon_automation.db "PRAGMA integrity_check;"
```

---

## Version History

- **v1.0** (Jan 2024): Initial release
  - Same-day thank-you email automation
  - 7-day follow-up email system
  - SQLite database tracking
  - Comprehensive error handling

---

Last Updated: January 2024
