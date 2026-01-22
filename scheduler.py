#!/usr/bin/env python3
"""
Scheduler script - Run this continuously to automatically execute scripts at scheduled times.
Recommended for server/cloud deployments.
"""

import schedule
import time
import logging
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from src.config import THANK_YOU_SEND_TIMES, LOG_DIR, LOG_LEVEL, LOG_FORMAT
from src.scripts.thank_you_emails import ThankYouEmailAutomation
from src.scripts.followup_emails import FollowUpEmailAutomation

# Setup logging
log_file = LOG_DIR / "scheduler.log"
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def run_thank_you_emails():
    """Execute thank-you email script."""
    logger.info("=" * 60)
    logger.info("Executing Thank-You Email Script")
    logger.info("=" * 60)
    try:
        automation = ThankYouEmailAutomation()
        automation.run()
    except Exception as e:
        logger.error(f"Error in thank-you email script: {e}", exc_info=True)


def run_followup_emails():
    """Execute follow-up email script."""
    logger.info("=" * 60)
    logger.info("Executing Follow-Up Email Script")
    logger.info("=" * 60)
    try:
        automation = FollowUpEmailAutomation()
        automation.run()
    except Exception as e:
        logger.error(f"Error in follow-up email script: {e}", exc_info=True)


def schedule_tasks():
    """Configure all scheduled tasks."""
    logger.info("Configuring scheduled tasks...")

    # Schedule thank-you emails for configured times
    for time_str in THANK_YOU_SEND_TIMES:
        schedule.every().day.at(time_str).do(run_thank_you_emails)
        logger.info(f"Scheduled thank-you emails at {time_str} daily")

    # Schedule follow-up emails daily at 8 AM
    schedule.every().day.at("08:00").do(run_followup_emails)
    logger.info("Scheduled follow-up emails at 08:00 daily")

    logger.info("Task scheduling complete")


def main():
    """Main scheduler loop."""
    logger.info("=" * 60)
    logger.info("Nail Salon Automation Scheduler Started")
    logger.info(f"Start Time: {datetime.now()}")
    logger.info("=" * 60)

    schedule_tasks()

    logger.info("Scheduler running... (Press Ctrl+C to stop)")

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Fatal error in scheduler: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    # Note: Requires 'schedule' package: pip install schedule
    main()
