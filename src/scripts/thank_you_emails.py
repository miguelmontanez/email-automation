#!/usr/bin/env python3
"""
Script 1: Same-day Thank You Email Automation
Sends thank-you emails at scheduled times (12pm and 7pm) for completed appointments.
Includes comprehensive logging and error handling.
"""

import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import (
    THANK_YOU_SEND_TIMES,
    LOG_DIR,
    LOG_LEVEL,
    LOG_FORMAT,
    BATCH_SIZE,
    EMAIL_DELAY_BETWEEN_BATCH,
    TIMEZONE,
)
from src.database.database_manager import DatabaseManager
from src.modules.fresha_api import FreshaAPIClient
from src.modules.email_service import EmailService
from src.modules.alert_service import AlertService

# Setup logging
log_file = LOG_DIR / "thank_you_script.log"
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class ThankYouEmailAutomation:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.fresha_client = FreshaAPIClient()
        self.email_service = EmailService()
        self.alert_service = AlertService()
        self.stats = {
            "emails_sent": 0,
            "emails_skipped": 0,
            "emails_failed": 0,
            "errors": [],
        }

    def fetch_and_process_today_appointments(self):
        """Fetch today's completed appointments and prepare thank-you emails."""
        logger.info("Fetching today's completed appointments from Fresha...")
        
        try:
            # Verify Fresha API connection
            if not self.fresha_client.verify_connection():
                error_msg = "Failed to verify Fresha API connection"
                logger.error(error_msg)
                self.stats["errors"].append(error_msg)
                return False

            # Get today's appointments
            appointments = self.fresha_client.get_today_appointments()
            logger.info(f"Found {len(appointments)} completed appointments today")

            if not appointments:
                logger.info("No appointments to process")
                return True

            # Process each appointment
            for appointment in appointments:
                try:
                    self._process_appointment(appointment)
                except Exception as e:
                    error_msg = f"Error processing appointment {appointment.get('id')}: {str(e)}"
                    logger.error(error_msg)
                    self.stats["errors"].append(error_msg)
                    continue

            return True

        except Exception as e:
            error_msg = f"Error fetching appointments: {str(e)}"
            logger.error(error_msg)
            self.stats["errors"].append(error_msg)
            return False

    def _process_appointment(self, appointment: dict):
        """Process a single appointment and create thank-you email record."""
        try:
            fresha_appointment_id = appointment.get("id")
            customer_data = appointment.get("customer", {})
            fresha_customer_id = customer_data.get("id")
            customer_name = customer_data.get("name", "Valued Customer")
            customer_email = customer_data.get("email")

            if not customer_email:
                logger.warning(
                    f"No email found for appointment {fresha_appointment_id}"
                )
                self.stats["emails_skipped"] += 1
                return

            # Add or update customer
            customer_id = self.db_manager.add_customer(
                fresha_id=fresha_customer_id,
                name=customer_name,
                email=customer_email,
                phone=customer_data.get("phone"),
            )

            if not customer_id:
                logger.error(
                    f"Failed to add customer for appointment {fresha_appointment_id}"
                )
                self.stats["emails_failed"] += 1
                return

            # Add appointment
            appointment_id = self.db_manager.add_appointment(
                fresha_id=fresha_appointment_id,
                customer_id=customer_id,
                service_type=appointment.get("service", {}).get("name", "Nail Service"),
                appointment_date=appointment.get("start_date"),
            )

            if not appointment_id:
                logger.error(
                    f"Failed to add appointment {fresha_appointment_id}"
                )
                self.stats["emails_failed"] += 1
                return

            # Schedule thank-you emails for configured times
            for send_time in THANK_YOU_SEND_TIMES:
                scheduled_time = f"{datetime.now().strftime('%Y-%m-%d')} {send_time}:00"
                self.db_manager.add_thank_you_email(
                    appointment_id=appointment_id,
                    customer_id=customer_id,
                    email_address=customer_email,
                    scheduled_time=scheduled_time,
                )
                logger.info(
                    f"Scheduled thank-you email for {customer_email} at {send_time}"
                )

        except Exception as e:
            logger.error(f"Error processing appointment: {e}")
            raise

    def send_pending_emails(self):
        """Send all pending thank-you emails that are due."""
        logger.info("Checking for pending thank-you emails to send...")
        
        try:
            pending_emails = self.db_manager.get_pending_thank_you_emails()
            logger.info(f"Found {len(pending_emails)} pending thank-you emails")

            if not pending_emails:
                logger.info("No pending emails to send")
                return True

            # Process in batches
            for i in range(0, len(pending_emails), BATCH_SIZE):
                batch = pending_emails[i : i + BATCH_SIZE]
                self._send_email_batch(batch)
                
                # Delay between batches
                if i + BATCH_SIZE < len(pending_emails):
                    logger.info(
                        f"Waiting {EMAIL_DELAY_BETWEEN_BATCH}s before next batch..."
                    )
                    time.sleep(EMAIL_DELAY_BETWEEN_BATCH)

            return True

        except Exception as e:
            error_msg = f"Error sending pending emails: {str(e)}"
            logger.error(error_msg)
            self.stats["errors"].append(error_msg)
            return False

    def _send_email_batch(self, batch: list):
        """Send a batch of emails."""
        for email_record in batch:
            try:
                email_id = email_record["id"]
                customer_email = email_record["email_address"]
                
                # Get customer info for personalization
                # Note: In real implementation, fetch from DB
                customer_name = "Valued Customer"

                # Send email
                success, error = self.email_service.send_thank_you_email(
                    recipient_email=customer_email, customer_name=customer_name
                )

                if success:
                    self.db_manager.update_thank_you_email_status(
                        email_id=email_id, status="sent"
                    )
                    self.db_manager.log_email(
                        email_address=customer_email,
                        email_type="thank_you",
                        subject="Thank You for Your Visit!",
                        status="sent",
                    )
                    self.stats["emails_sent"] += 1
                    logger.info(f"Thank-you email sent to {customer_email}")
                else:
                    # Increment retry count
                    self.db_manager.increment_thank_you_retry(email_id)
                    email_record_dict = dict(email_record)
                    retry_count = email_record_dict.get("retry_count", 0)

                    if retry_count < 2:
                        logger.warning(
                            f"Failed to send email to {customer_email}, will retry"
                        )
                        self.stats["emails_skipped"] += 1
                    else:
                        self.db_manager.update_thank_you_email_status(
                            email_id=email_id, status="failed", error_message=error
                        )
                        self.stats["emails_failed"] += 1
                        logger.error(
                            f"Failed to send email to {customer_email} after retries: {error}"
                        )

                    self.db_manager.log_email(
                        email_address=customer_email,
                        email_type="thank_you",
                        subject="Thank You for Your Visit!",
                        status="failed",
                        error_message=error,
                    )

            except Exception as e:
                error_msg = f"Error sending email in batch: {str(e)}"
                logger.error(error_msg)
                self.stats["errors"].append(error_msg)

    def run(self):
        """Main execution method."""
        start_time = time.time()
        logger.info("=" * 60)
        logger.info("Starting Thank You Email Automation Script")
        logger.info("=" * 60)

        try:
            # Fetch and process appointments
            if not self.fetch_and_process_today_appointments():
                logger.error("Failed to fetch and process appointments")

            # Send pending emails
            if not self.send_pending_emails():
                logger.error("Failed to send pending emails")

            # Calculate execution time
            execution_time = time.time() - start_time

            # Log script execution
            self.db_manager.log_script_execution(
                script_name="thank_you_emails",
                status="completed",
                emails_sent=self.stats["emails_sent"],
                emails_skipped=self.stats["emails_skipped"],
                emails_failed=self.stats["emails_failed"],
                error_message="\n".join(self.stats["errors"]) if self.stats["errors"] else None,
                execution_time=execution_time,
            )

            # Send alert with summary
            if self.stats["emails_failed"] > 0 or self.stats["errors"]:
                self.alert_service.send_execution_summary(
                    script_name="Thank You Email Script",
                    emails_sent=self.stats["emails_sent"],
                    emails_skipped=self.stats["emails_skipped"],
                    emails_failed=self.stats["emails_failed"],
                    execution_time=execution_time,
                    errors=self.stats["errors"],
                )

            logger.info("=" * 60)
            logger.info(f"✓ Emails Sent: {self.stats['emails_sent']}")
            logger.info(f"⊘ Emails Skipped: {self.stats['emails_skipped']}")
            logger.info(f"✗ Emails Failed: {self.stats['emails_failed']}")
            logger.info(f"⏱ Execution Time: {execution_time:.2f}s")
            logger.info("=" * 60)

            return (
                self.stats["emails_failed"] == 0
                and len(self.stats["errors"]) == 0
            )

        except Exception as e:
            logger.error(f"Fatal error in automation: {str(e)}", exc_info=True)
            self.alert_service.send_alert(
                subject="Thank You Email Script - Fatal Error",
                body=str(e),
                alert_type="CRITICAL",
            )
            return False


def main():
    """Entry point."""
    automation = ThankYouEmailAutomation()
    success = automation.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
