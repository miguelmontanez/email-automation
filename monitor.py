#!/usr/bin/env python3
"""
Utility script to monitor and manage the automation system.
Provides command-line tools for checking status, running manual scripts, and maintenance.
"""

import sqlite3
import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path
from tabulate import tabulate

sys.path.insert(0, str(Path(__file__).parent))

from src.database.database_manager import DatabaseManager
from src.modules.fresha_api import FreshaAPIClient
from src.modules.email_service import EmailService
from src.config import DATABASE_PATH

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SalonAutomationMonitor:
    def __init__(self):
        self.db = DatabaseManager()

    def print_header(self, title):
        """Print formatted header."""
        print(f"\n{'=' * 60}")
        print(f"  {title}")
        print(f"{'=' * 60}\n")

    def show_status(self):
        """Show current system status."""
        self.print_header("System Status")

        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Customer count
            cursor.execute("SELECT COUNT(*) as count FROM customers")
            customers = cursor.fetchone()["count"]

            # Appointment count
            cursor.execute("SELECT COUNT(*) as count FROM appointments")
            appointments = cursor.fetchone()["count"]

            # Pending emails
            cursor.execute(
                "SELECT COUNT(*) as count FROM thank_you_emails WHERE status = 'pending'"
            )
            pending_thank_you = cursor.fetchone()["count"]

            cursor.execute(
                "SELECT COUNT(*) as count FROM followup_emails WHERE status = 'pending'"
            )
            pending_followup = cursor.fetchone()["count"]

            # Failed emails
            cursor.execute(
                "SELECT COUNT(*) as count FROM thank_you_emails WHERE status = 'failed'"
            )
            failed_thank_you = cursor.fetchone()["count"]

            cursor.execute(
                "SELECT COUNT(*) as count FROM followup_emails WHERE status = 'failed'"
            )
            failed_followup = cursor.fetchone()["count"]

        status_data = [
            ["Customers in Database", customers],
            ["Total Appointments", appointments],
            ["Pending Thank You Emails", pending_thank_you],
            ["Pending Follow-Up Emails", pending_followup],
            ["Failed Thank You Emails", failed_thank_you],
            ["Failed Follow-Up Emails", failed_followup],
            ["Database File", str(DATABASE_PATH)],
            ["Database Size (MB)", round(DATABASE_PATH.stat().st_size / 1024 / 1024, 2)],
        ]

        print(tabulate(status_data, headers=["Metric", "Value"], tablefmt="grid"))

    def show_recent_executions(self, limit=10):
        """Show recent script executions."""
        self.print_header(f"Recent Script Executions (Last {limit})")

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT script_name, execution_date, status, emails_sent, 
                       emails_failed, execution_time_seconds
                FROM script_logs
                ORDER BY execution_date DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()

        if not rows:
            print("No execution logs found.")
            return

        data = [
            [
                row["script_name"],
                row["execution_date"],
                row["status"],
                row["emails_sent"],
                row["emails_failed"],
                f"{row['execution_time_seconds']:.2f}s" if row["execution_time_seconds"] else "N/A",
            ]
            for row in rows
        ]

        print(
            tabulate(
                data,
                headers=[
                    "Script",
                    "Execution Time",
                    "Status",
                    "Sent",
                    "Failed",
                    "Duration",
                ],
                tablefmt="grid",
            )
        )

    def show_email_logs(self, limit=20):
        """Show recent email logs."""
        self.print_header(f"Recent Email Activity (Last {limit})")

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT email_address, email_type, status, sent_at, error_message
                FROM email_logs
                ORDER BY sent_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()

        if not rows:
            print("No email logs found.")
            return

        data = [
            [
                row["email_address"],
                row["email_type"],
                row["status"],
                row["sent_at"],
                row["error_message"][:30] + "..." if row["error_message"] else "—",
            ]
            for row in rows
        ]

        print(
            tabulate(
                data,
                headers=["Email", "Type", "Status", "Time", "Error"],
                tablefmt="grid",
            )
        )

    def show_failure_analysis(self):
        """Analyze and show failure patterns."""
        self.print_header("Failure Analysis (Last 7 Days)")

        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Failure rate
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
                FROM email_logs
                WHERE sent_at >= datetime('now', '-7 days')
                """
            )
            stats = cursor.fetchone()

            total = stats["total"] or 0
            sent = stats["sent"] or 0
            failed = stats["failed"] or 0
            success_rate = (sent / total * 100) if total > 0 else 0

            # Top errors
            cursor.execute(
                """
                SELECT error_message, COUNT(*) as count
                FROM email_logs
                WHERE status = 'failed' AND sent_at >= datetime('now', '-7 days')
                GROUP BY error_message
                ORDER BY count DESC
                LIMIT 5
                """
            )
            errors = cursor.fetchall()

        print(f"Total Emails Processed: {total}")
        print(f"Successfully Sent: {sent}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {success_rate:.2f}%\n")

        if errors:
            print("Top Failure Reasons:")
            error_data = [
                [i + 1, err["error_message"][:50], err["count"]]
                for i, err in enumerate(errors)
            ]
            print(tabulate(error_data, headers=["#", "Error", "Count"], tablefmt="grid"))
        else:
            print("✓ No failures in the last 7 days!")

    def test_fresha_connection(self):
        """Test Fresha API connection."""
        self.print_header("Fresha API Connection Test")

        client = FreshaAPIClient()
        if client.verify_connection():
            print("✓ Fresha API connection successful!")
            
            # Get customer count
            customers = client.get_customers(limit=1)
            if customers:
                print(f"✓ Business has customers in Fresha")
            
            return True
        else:
            print("✗ Fresha API connection failed!")
            print("  Check FRESHA_API_KEY and FRESHA_BUSINESS_ID in .env")
            return False

    def test_email_connection(self):
        """Test email service connection."""
        self.print_header("Email Service Connection Test")

        service = EmailService()
        if not service.sender_email or not service.sender_password:
            print("✗ Email credentials not configured in .env")
            return False

        # We can't fully test without sending, but we can validate config
        print(f"✓ Email configured:")
        print(f"  - SMTP Server: {service.smtp_server}:{service.smtp_port}")
        print(f"  - Sender: {service.sender_email}")
        print(f"  - Name: {service.sender_name}")
        print("\nNote: Full email test requires sending test email.")
        return True

    def backup_database(self):
        """Create database backup."""
        self.print_header("Database Backup")

        backup_path = self.db.backup_database()
        if backup_path:
            print(f"✓ Database backed up successfully!")
            print(f"  Location: {backup_path}")
        else:
            print(f"✗ Backup failed. Check logs for details.")

    def show_help(self):
        """Show help message."""
        print(f"""
Nail Salon Automation - Monitor & Maintenance Tool

Usage: python monitor.py <command>

Commands:
  status              - Show current system status
  executions [N]      - Show recent N script executions (default: 10)
  emails [N]          - Show recent N email activities (default: 20)
  failures            - Analyze failure patterns (last 7 days)
  test-fresha         - Test Fresha API connection
  test-email          - Test email service configuration
  backup              - Create database backup
  help                - Show this help message

Examples:
  python monitor.py status
  python monitor.py executions 20
  python monitor.py emails 50
  python monitor.py failures
  python monitor.py test-fresha

For detailed documentation, see README.md and SETUP_DEPLOYMENT.md
        """)

    def run(self):
        """Main execution."""
        if len(sys.argv) < 2:
            self.show_help()
            return

        command = sys.argv[1].lower()

        if command == "status":
            self.show_status()
        elif command == "executions":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            self.show_recent_executions(limit)
        elif command == "emails":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            self.show_email_logs(limit)
        elif command == "failures":
            self.show_failure_analysis()
        elif command == "test-fresha":
            self.test_fresha_connection()
        elif command == "test-email":
            self.test_email_connection()
        elif command == "backup":
            self.backup_database()
        elif command == "help":
            self.show_help()
        else:
            print(f"Unknown command: {command}")
            self.show_help()


if __name__ == "__main__":
    monitor = SalonAutomationMonitor()
    monitor.run()
