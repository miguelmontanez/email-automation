# Handover & Operations Guide

## 📚 Quick Reference Card

### Critical Files & Locations
```
Project Root: c:\Users\vm_user\Documents\WorkSpace\python-automation\nail-salon-automation
├── .env                           ← Your credentials (KEEP SECURE!)
├── logs/                          ← Daily execution logs
├── src/database/                  ← SQLite database
├── src/scripts/
│   ├── thank_you_emails.py        ← Script 1 (12 PM, 7 PM)
│   └── followup_emails.py         ← Script 2 (daily, 7-day emails)
└── monitor.py                     ← Monitoring & maintenance tool
```

### Daily Operations (No Action Required)
- Scripts run automatically via Task Scheduler
- Check logs folder if concerned about status
- Review alert emails if sent

### Weekly Operations (5 minutes)
```powershell
# Check system status
python monitor.py status

# View recent executions
python monitor.py executions 15

# Check for any failures
python monitor.py failures
```

### Emergency Procedures

**Script Stopped Running?**
```powershell
# 1. Check Task Scheduler
tasklist | findstr "python"

# 2. Restart scheduler
net stop "Task Scheduler"
net start "Task Scheduler"

# 3. Verify scripts still exist
dir "src\scripts\*.py"
```

**Email Not Sending?**
```powershell
# Test email connection
python monitor.py test-email

# Check logs
Get-Content logs\thank_you_script.log -Tail 30
```

**Database Issues?**
```powershell
# Create backup
python monitor.py backup

# Check database integrity
sqlite3 src/database/nail_salon_automation.db "PRAGMA integrity_check;"
```

---

## 🎯 Implementation Checklist

### Pre-Launch (1 hour)
- [ ] Review `.env.example` file
- [ ] Fill in Fresha API credentials
- [ ] Generate Gmail app password (if using Gmail)
- [ ] Set SENDER_EMAIL, SENDER_PASSWORD
- [ ] Set ALERT_EMAIL for yourself
- [ ] Test connection: `python monitor.py test-fresha`
- [ ] Test email: `python monitor.py test-email`

### Deployment (30 minutes)
- [ ] Create Windows Task Scheduler jobs
  - [ ] "Salon - Thank You 12 PM"
  - [ ] "Salon - Thank You 7 PM"
  - [ ] "Salon - Follow-Up Daily"
- [ ] Verify tasks appear in Task Scheduler
- [ ] Set tasks to "Run with highest privileges"
- [ ] Test one manual run: `python src\scripts\thank_you_emails.py`

### Post-Launch (Daily first week)
- [ ] Check alert email each morning
- [ ] Verify thank-you emails sent at 12 PM and 7 PM
- [ ] Check logs for any errors
- [ ] Monitor database growth

### Ongoing (Weekly)
- [ ] Run `python monitor.py status`
- [ ] Review failure analysis
- [ ] Back up database
- [ ] Update documentation as needed

---

## 📊 Key Metrics to Monitor

### Email Delivery
- **Target**: 95%+ success rate
- **Warning**: Below 85% - investigate immediately
- **Command**: `python monitor.py failures`

### Execution Time
- **Typical**: 30-120 seconds per run
- **Concern**: Taking >5 minutes - check database size
- **Command**: `python monitor.py executions 10`

### Database Size
- **Typical**: 100 KB per 1,000 customers
- **Concern**: Exceeds 500 MB - archive old data
- **Command**: `dir src\database\nail_salon_automation.db`

---

## 🔐 Security Reminders

⚠️ **CRITICAL - Never Forget:**
1. **Never commit `.env` to Git** - It's in `.gitignore`
2. **Never share `.env` file** - Contains all credentials
3. **Use app-specific passwords** - Not regular passwords
4. **Keep backups** - Daily is ideal
5. **Rotate credentials quarterly** - Good security practice

---

## 💻 Command Reference

### System Status
```powershell
# Show full system status
python monitor.py status

# View recent email activity
python monitor.py emails 30

# Analyze failures
python monitor.py failures

# Create backup
python monitor.py backup
```

### Manual Script Execution
```powershell
# Run thank-you emails manually
python src\scripts\thank_you_emails.py

# Run follow-up emails manually
python src\scripts\followup_emails.py
```

### Database Management
```powershell
# Enter SQLite console
sqlite3 src\database\nail_salon_automation.db

# Useful queries (in SQLite console):
SELECT * FROM script_logs ORDER BY execution_date DESC LIMIT 5;
SELECT COUNT(*), status FROM thank_you_emails GROUP BY status;
SELECT COUNT(*), status FROM followup_emails GROUP BY status;
```

### Troubleshooting
```powershell
# Test Fresha connection
python monitor.py test-fresha

# Test email service
python monitor.py test-email

# Check last 50 lines of logs
Get-Content logs\thank_you_script.log -Tail 50
Get-Content logs\followup_script.log -Tail 50
```

---

## 📱 Video Walkthrough Script

### Scene 1: Project Overview (2 min)
"Hello! This is your Nail Salon Email Automation System. It includes two powerful scripts:

1. **Same-Day Thank You Emails**: Sends at 12 PM and 7 PM to customers who visited today
2. **7-Day Follow-Up Emails**: Sends feedback requests 7 days after their appointment

Everything runs automatically. No daily action needed. We've added comprehensive logging and alerts so you know if anything goes wrong."

### Scene 2: Project Structure (2 min)
"Let me show you the project structure. Everything is organized logically:

- **src/** contains the main code
  - **scripts/** - The two automation scripts
  - **modules/** - Reusable components (Fresha API, Email, Alerts)
  - **database/** - SQLite database manager
- **logs/** - Daily execution logs
- **config/** - Configuration files
- **.env** - Your sensitive credentials

The beauty is: once set up, it runs hands-free."

### Scene 3: Configuration (3 min)
"Configuration is simple. Just fill in your credentials in the `.env` file:

1. **Fresha API Key** - From Fresha admin panel
2. **Email credentials** - Your salon's email account
3. **Alert email** - Where to send failure notifications

We support Gmail, Office 365, and custom SMTP servers. We use secure connections and app-specific passwords, so your credentials are safe."

### Scene 4: Task Scheduler Setup (4 min)
"Once configured, setting up automated execution is straightforward. We use Windows Task Scheduler to run the scripts at specific times:

- 12 PM: Thank you emails
- 7 PM: Thank you emails
- 8 AM: Follow-up emails (for those 7+ days old)

Each task is simple: runs a Python script. We've included detailed instructions in the setup guide."

### Scene 5: Monitoring (3 min)
"Monitoring is built-in and easy. Use the `monitor.py` tool:

```
python monitor.py status
```

This shows you:
- Number of customers
- Pending and failed emails
- Recent executions
- Email success rate

If anything fails, you get alerted immediately to your email."

### Scene 6: Database & Logging (2 min)
"Everything is logged comprehensively. Every email attempt is recorded:

- When it was sent
- If it succeeded or failed
- Any error messages
- Retry attempts

The database is SQLite - lightweight, embedded, no separate database server needed. Backups are automatic."

### Scene 7: Support & Resources (2 min)
"We've provided extensive documentation:

1. **README.md** - Overview and quick start
2. **SETUP_DEPLOYMENT.md** - Detailed setup and troubleshooting
3. **monitor.py** - Built-in monitoring tool
4. **This video** - Visual walkthrough

If something goes wrong, check the logs first. They're detailed and helpful. All scripts have error handling and will alert you."

### Scene 8: Best Practices (2 min)
"A few best practices:

1. **Keep `.env` secure** - It has all your credentials
2. **Check the system weekly** - Just run `monitor.py status`
3. **Back up your database monthly** - Run `python monitor.py backup`
4. **Review logs if you see alert emails** - They're helpful diagnostic tools
5. **Update credentials quarterly** - Good security practice

That's it! The system is designed to run hands-free."

### Scene 9: Troubleshooting (2 min)
"If you ever need to troubleshoot:

First, check if it's running:
```
python monitor.py status
```

Test your connections:
```
python monitor.py test-fresha
python monitor.py test-email
```

View detailed logs:
```
Get-Content logs\thank_you_script.log -Tail 50
```

Most issues have simple solutions detailed in the setup guide."

### Scene 10: Closing (1 min)
"That's your complete nail salon automation system! It will:

✓ Automatically send thank-you emails same-day
✓ Automatically send follow-up emails after 7 days
✓ Track everything in the database
✓ Alert you if anything goes wrong
✓ Require minimal maintenance

Thanks for watching, and good luck with your salon!"

---

## 📞 Support Contacts

### For Fresha API Issues
- Documentation: https://docs.fresha.com
- Support: contact@fresha.com

### For Email Issues
- Gmail: https://support.google.com/mail
- Office 365: https://support.microsoft.com/en-us/office

### For Script Issues
1. Check log files in `logs/` folder
2. Run `python monitor.py status`
3. Review `SETUP_DEPLOYMENT.md` troubleshooting section

---

## ✅ Success Indicators

You'll know everything is working when:

1. ✓ You receive alert confirmation emails (optional)
2. ✓ `python monitor.py status` shows customers count > 0
3. ✓ Logs show "Emails sent successfully" entries
4. ✓ No error alerts in your email
5. ✓ Database grows gradually (good sign - data being tracked)

---

## 🎉 Maintenance Checklist

### Monthly
- [ ] Run `python monitor.py status`
- [ ] Run `python monitor.py backup`
- [ ] Review failure analysis
- [ ] Check email alert inbox

### Quarterly
- [ ] Update Fresha API credentials if changed
- [ ] Review and update email address if changed
- [ ] Check Python dependencies: `pip list`

### Annually
- [ ] Review all logs and archive old logs
- [ ] Plan for growth/scaling
- [ ] Security audit of credentials

---

**Remember**: This system is designed to be reliable and hands-free. The logs and alerts will tell you everything you need to know. You're all set! 🎉
