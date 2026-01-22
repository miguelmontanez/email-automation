#!/usr/bin/env python3
"""
Script 2: 7-Day Follow-Up Email Automation
Sends follow-up emails 7 days after appointment with feedback request.
Prevents duplicate emails using unique tokens.
"""

import logging
import sys
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import (
    FOLLOWUP_DAYS,
    LOG_DIR,
    LOG_LEVEL,
    LOG_FORMAT,
    BATCH_SIZE,
    EMAIL_DELAY_BETWEEN_BATCH,
)
from src.database.database_manager import DatabaseManager
from src.modules.email_service import EmailService
from src.modules.alert_service import AlertService

# Setup logging
log_file = LOG_DIR / "followup_script.log"
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class FollowUpEmailAutomation:
    def __init__(self, base_url: str = "https://your-salon.com/feedback"):
        self.db_manager = DatabaseManager()
        self.email_service = EmailService()
        self.alert_service = AlertService()
        self.base_url = base_url
        self.stats = {
            "emails_sent": 0,
            "emails_skipped": 0,
            "emails_failed": 0,
            "duplicates_prevented": 0,
            "errors": [],
        }

    def prepare_followup_emails(self):
        """Prepare follow-up emails for appointments that are 7 days old."""
        logger.info(
            f"Preparing follow-up emails for appointments {FOLLOWUP_DAYS} days old..."
        )
        
        try:
            # Calculate date range
            today = datetime.now()
            target_date = today - timedelta(days=FOLLOWUP_DAYS)
            target_date_str = target_date.strftime("%Y-%m-%d")

            # Get appointments from 7 days ago (with some tolerance)
            # In real implementation, query database for appointments from that date
            logger.info(
                f"Looking for appointments from around {target_date_str}"
            )

            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                # Get completed appointments from around 7 days ago that don't have follow-up yet
                cursor.execute(
                    """
                    SELECT DISTINCT a.id, a.fresha_appointment_id, a.customer_id, a.appointment_date,
                           c.name, c.email
                    FROM appointments a
                    JOIN customers c ON a.customer_id = c.id
                    WHERE a.status = 'completed'
                    AND date(a.appointment_date) >= date(?, '-1 day')
                    AND date(a.appointment_date) <= date(?, '+1 day')
                    AND a.id NOT IN (
                        SELECT appointment_id FROM followup_emails
                    )
                    ORDER BY a.appointment_date DESC
                    """,
                    (target_date_str, target_date_str),
                )
                appointments = cursor.fetchall()

            logger.info(f"Found {len(appointments)} appointments eligible for follow-up")

            # Process each appointment
            followup_count = 0
            for appointment in appointments:
                if self._create_followup_email(appointment):
                    followup_count += 1

            logger.info(f"Created {followup_count} follow-up email records")
            return True

        except Exception as e:
            error_msg = f"Error preparing follow-up emails: {str(e)}"
            logger.error(error_msg)
            self.stats["errors"].append(error_msg)
            return False

    def _create_followup_email(self, appointment) -> bool:
        """Create follow-up email record for appointment."""
        try:
            appointment_dict = dict(appointment)
            appointment_id = appointment_dict["id"]
            customer_id = appointment_dict["customer_id"]
            email_address = appointment_dict["email"]
            customer_name = appointment_dict["name"]

            # Check for duplicate
            if self.db_manager.check_duplicate_followup(customer_id, appointment_id):
                logger.debug(
                    f"Follow-up already exists for appointment {appointment_id}"
                )
                self.stats["duplicates_prevented"] += 1
                return False

            # Generate unique feedback token
            feedback_token = str(uuid.uuid4())

            # Schedule follow-up for today (or now, depending on logic)
            scheduled_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Add follow-up email record
            email_id = self.db_manager.add_followup_email(
                appointment_id=appointment_id,
                customer_id=customer_id,
                email_address=email_address,
                scheduled_date=scheduled_date,
                feedback_token=feedback_token,
            )

            if email_id:
                logger.info(
                    f"Created follow-up email for {customer_name} ({email_address})"
                )
                return True
            else:
                logger.error(
                    f"Failed to create follow-up email for {customer_name}"
                )
                self.stats["emails_failed"] += 1
                return False

        except Exception as e:
            logger.error(f"Error creating follow-up email: {e}")
            self.stats["errors"].append(str(e))
            return False

    def send_pending_followups(self):
        """Send all pending follow-up emails that are due."""
        logger.info("Checking for pending follow-up emails to send...")
        
        try:
            pending_emails = self.db_manager.get_pending_followup_emails()
            logger.info(f"Found {len(pending_emails)} pending follow-up emails")

            if not pending_emails:
                logger.info("No pending follow-up emails to send")
                return True

            # Process in batches
            for i in range(0, len(pending_emails), BATCH_SIZE):
                batch = pending_emails[i : i + BATCH_SIZE]
                self._send_followup_batch(batch)
                
                # Delay between batches
                if i + BATCH_SIZE < len(pending_emails):
                    logger.info(
                        f"Waiting {EMAIL_DELAY_BETWEEN_BATCH}s before next batch..."
                    )
                    time.sleep(EMAIL_DELAY_BETWEEN_BATCH)

            return True

        except Exception as e:
            error_msg = f"Error sending pending follow-up emails: {str(e)}"
            logger.error(error_msg)
            self.stats["errors"].append(error_msg)
            return False

    def _send_followup_batch(self, batch: list):
        """Send a batch of follow-up emails."""
        for email_record in batch:
            try:
                email_record_dict = dict(email_record)
                email_id = email_record_dict["id"]
                customer_email = email_record_dict["email_address"]
                feedback_token = email_record_dict["feedback_token"]
                
                # Build feedback link
                feedback_link = f"{self.base_url}?token={feedback_token}"

                # Get customer info (basic - could be enhanced with DB lookup)
                customer_name = "Valued Customer"

                # Send email
                success, error = self.email_service.send_followup_email(
                    recipient_email=customer_email,
                    customer_name=customer_name,
                    feedback_link=feedback_link,
                )

                if success:
                    self.db_manager.update_followup_email_status(
                        email_id=email_id, status="sent"
                    )
                    self.db_manager.log_email(
                        email_address=customer_email,
                        email_type="followup",
                        subject="How did your nails last? We'd love to know!",
                        status="sent",
                    )
                    self.stats["emails_sent"] += 1
                    logger.info(f"Follow-up email sent to {customer_email}")
                else:
                    # Increment retry count
                    self.db_manager.increment_followup_retry(email_id)
                    retry_count = email_record_dict.get("retry_count", 0)

                    if retry_count < 2:
                        logger.warning(
                            f"Failed to send follow-up email to {customer_email}, will retry"
                        )
                        self.stats["emails_skipped"] += 1
                    else:
                        self.db_manager.update_followup_email_status(
                            email_id=email_id, status="failed", error_message=error
                        )
                        self.stats["emails_failed"] += 1
                        logger.error(
                            f"Failed to send follow-up email to {customer_email} after retries: {error}"
                        )

                    self.db_manager.log_email(
                        email_address=customer_email,
                        email_type="followup",
                        subject="How did your nails last? We'd love to know!",
                        status="failed",
                        error_message=error,
                    )

            except Exception as e:
                error_msg = f"Error sending follow-up email in batch: {str(e)}"
                logger.error(error_msg)
                self.stats["errors"].append(error_msg)

    def run(self, base_url: str = None):
        """Main execution method."""
        if base_url:
            self.base_url = base_url

        start_time = time.time()
        logger.info("=" * 60)
        logger.info("Starting Follow-Up Email Automation Script")
        logger.info("=" * 60)

        try:
            # Prepare follow-up emails for 7-day old appointments
            if not self.prepare_followup_emails():
                logger.error("Failed to prepare follow-up emails")

            # Send pending follow-up emails
            if not self.send_pending_followups():
                logger.error("Failed to send pending follow-up emails")

            # Calculate execution time
            execution_time = time.time() - start_time

            # Log script execution
            self.db_manager.log_script_execution(
                script_name="followup_emails",
                status="completed",
                emails_sent=self.stats["emails_sent"],
                emails_skipped=self.stats["emails_skipped"],
                emails_failed=self.stats["emails_failed"],
                error_message="\n".join(self.stats["errors"])
                if self.stats["errors"]
                else None,
                execution_time=execution_time,
            )

            # Send alert with summary if there were issues
            if self.stats["emails_failed"] > 0 or self.stats["errors"]:
                self.alert_service.send_execution_summary(
                    script_name="Follow-Up Email Script",
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
            logger.info(
                f"⊕ Duplicates Prevented: {self.stats['duplicates_prevented']}"
            )
            logger.info(f"⏱ Execution Time: {execution_time:.2f}s")
            logger.info("=" * 60)

            return (
                self.stats["emails_failed"] == 0
                and len(self.stats["errors"]) == 0
            )

        except Exception as e:
            logger.error(f"Fatal error in automation: {str(e)}", exc_info=True)
            self.alert_service.send_alert(
                subject="Follow-Up Email Script - Fatal Error",
                body=str(e),
                alert_type="CRITICAL",
            )
            return False


def main():
    """Entry point."""
    automation = FollowUpEmailAutomation()
    success = automation.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
