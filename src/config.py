import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
DB_DIR = PROJECT_ROOT / "src" / "database"
CONFIG_DIR = PROJECT_ROOT / "config"

# Create directories if they don't exist
LOG_DIR.mkdir(exist_ok=True)
DB_DIR.mkdir(exist_ok=True)

# Fresha API Configuration
FRESHA_API_KEY = os.getenv("FRESHA_API_KEY", "")
FRESHA_BUSINESS_ID = os.getenv("FRESHA_BUSINESS_ID", "")
FRESHA_API_BASE_URL = "https://api.fresha.com/v1"

# Email Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")
SENDER_NAME = os.getenv("SENDER_NAME", "Your Nail Salon")

# Email Templates
THANK_YOU_EMAIL_SUBJECT = "Thank You for Your Visit!"
THANK_YOU_EMAIL_TEMPLATE = """
Dear {customer_name},

Thank you for choosing us for your nails today! We hope you love your new look.

If you have any questions or concerns, feel free to reach out.

Best regards,
{salon_name}
"""

FOLLOWUP_EMAIL_SUBJECT = "How did your nails last? We'd love to know!"
FOLLOWUP_EMAIL_TEMPLATE = """
Dear {customer_name},

It's been a week since your last visit! We hope your nails are still looking fabulous.

Could you let us know how long your manicure/pedicure lasted? Your feedback helps us improve our services.

[FEEDBACK_LINK]

Thank you for being a valued customer!

Best regards,
{salon_name}
"""

# Scheduling Configuration
THANK_YOU_SEND_TIMES = ["12:00", "19:00"]  # 12pm and 7pm
FOLLOWUP_DAYS = 7  # Send follow-up after 7 days

# Database Configuration
DATABASE_PATH = DB_DIR / "nail_salon_automation.db"
DATABASE_BACKUP_PATH = DB_DIR / "backups"

# Logging Configuration
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Headless Mode
HEADLESS_MODE = os.getenv("HEADLESS_MODE", "true").lower() == "true"
BROWSER_TIMEOUT = 30000  # 30 seconds in milliseconds

# Retry Configuration
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# Email Sending Configuration
BATCH_SIZE = 50  # Send emails in batches of 50
EMAIL_DELAY_BETWEEN_BATCH = 2  # seconds between batches

# Alert Configuration
ALERT_EMAIL = os.getenv("ALERT_EMAIL", "")
ENABLE_ALERTS = os.getenv("ENABLE_ALERTS", "true").lower() == "true"

# Timezone
TIMEZONE = os.getenv("TIMEZONE", "UTC")
