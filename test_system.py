#!/usr/bin/env python3
"""
Test & Validation Script
Helps verify all components are working correctly before production deployment.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.config import (
    FRESHA_API_KEY,
    SENDER_EMAIL,
    ALERT_EMAIL,
    DATABASE_PATH,
)
from src.database.database_manager import DatabaseManager
from src.modules.fresha_api import FreshaAPIClient
from src.modules.email_service import EmailService
from src.modules.alert_service import AlertService


class TestSuite:
    def __init__(self):
        self.results = []
        self.db = DatabaseManager()

    def print_header(self, title):
        """Print test header."""
        print(f"\n{'=' * 60}")
        print(f"  {title}")
        print(f"{'=' * 60}\n")

    def add_result(self, test_name, passed, message=""):
        """Record test result."""
        status = "✓ PASS" if passed else "✗ FAIL"
        self.results.append((test_name, passed, message))
        print(f"{status}: {test_name}")
        if message:
            print(f"       {message}")

    def test_configuration(self):
        """Test configuration loading."""
        self.print_header("Configuration Tests")

        # Test required env variables
        tests = [
            ("FRESHA_API_KEY", FRESHA_API_KEY),
            ("SENDER_EMAIL", SENDER_EMAIL),
            ("ALERT_EMAIL", ALERT_EMAIL),
        ]

        for var_name, var_value in tests:
            passed = bool(var_value) and var_value != ""
            message = f"Value: {var_value[:20]}..." if var_value else "Not configured"
            self.add_result(
                f"Environment variable: {var_name}",
                passed,
                message if not passed else "",
            )

    def test_database(self):
        """Test database functionality."""
        self.print_header("Database Tests")

        # Test database file exists
        db_exists = DATABASE_PATH.exists()
        self.add_result(
            f"Database file exists",
            db_exists,
            f"Path: {DATABASE_PATH}",
        )

        if db_exists:
            # Test database connection
            try:
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                    tables = cursor.fetchall()
                    
                self.add_result(
                    "Database connection",
                    len(tables) > 0,
                    f"Found {len(tables)} tables",
                )

                # Test required tables exist
                required_tables = [
                    "customers",
                    "appointments",
                    "thank_you_emails",
                    "followup_emails",
                    "script_logs",
                    "email_logs",
                ]

                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                    table_names = [row[0] for row in cursor.fetchall()]

                for table in required_tables:
                    self.add_result(
                        f"Table exists: {table}",
                        table in table_names,
                    )

            except Exception as e:
                self.add_result(
                    "Database connection",
                    False,
                    str(e),
                )

    def test_fresha_api(self):
        """Test Fresha API integration."""
        self.print_header("Fresha API Tests")

        try:
            client = FreshaAPIClient()

            # Test API connection
            connection_ok = client.verify_connection()
            self.add_result(
                "API connection to Fresha",
                connection_ok,
                "Verify FRESHA_API_KEY and FRESHA_BUSINESS_ID if failed",
            )

            if connection_ok:
                # Test fetching appointments
                try:
                    appointments = client.get_today_appointments()
                    self.add_result(
                        "Fetch today's appointments",
                        isinstance(appointments, list),
                        f"Retrieved {len(appointments)} appointments",
                    )
                except Exception as e:
                    self.add_result(
                        "Fetch today's appointments",
                        False,
                        str(e),
                    )

        except Exception as e:
            self.add_result(
                "Fresha API initialization",
                False,
                str(e),
            )

    def test_email_service(self):
        """Test email service configuration."""
        self.print_header("Email Service Tests")

        try:
            service = EmailService()

            # Test email configuration
            config_ok = (
                service.sender_email
                and service.sender_password
                and service.smtp_server
            )
            self.add_result(
                "Email configuration loaded",
                config_ok,
                "Check SENDER_EMAIL, SENDER_PASSWORD, SMTP_SERVER in .env",
            )

            if config_ok:
                # Test SMTP settings
                self.add_result(
                    "SMTP server configured",
                    bool(service.smtp_server),
                    f"Server: {service.smtp_server}:{service.smtp_port}",
                )

                # Note: We can't test actual sending without auth, but we validate config
                self.add_result(
                    "Sender details configured",
                    service.sender_email and service.sender_name,
                    f"From: {service.sender_name} <{service.sender_email}>",
                )

        except Exception as e:
            self.add_result(
                "Email service initialization",
                False,
                str(e),
            )

    def test_alert_service(self):
        """Test alert service configuration."""
        self.print_header("Alert Service Tests")

        try:
            alert = AlertService()

            # Test alert configuration
            alert_configured = bool(alert.alert_email)
            self.add_result(
                "Alert email configured",
                alert_configured,
                f"Alert email: {alert.alert_email}" if alert_configured else "Set ALERT_EMAIL in .env",
            )

        except Exception as e:
            self.add_result(
                "Alert service initialization",
                False,
                str(e),
            )

    def test_script_imports(self):
        """Test that automation scripts can be imported."""
        self.print_header("Script Import Tests")

        try:
            from src.scripts.thank_you_emails import ThankYouEmailAutomation
            self.add_result(
                "Import ThankYouEmailAutomation",
                True,
                "Script can be imported successfully",
            )
        except Exception as e:
            self.add_result(
                "Import ThankYouEmailAutomation",
                False,
                str(e),
            )

        try:
            from src.scripts.followup_emails import FollowUpEmailAutomation
            self.add_result(
                "Import FollowUpEmailAutomation",
                True,
                "Script can be imported successfully",
            )
        except Exception as e:
            self.add_result(
                "Import FollowUpEmailAutomation",
                False,
                str(e),
            )

    def print_summary(self):
        """Print test summary."""
        self.print_header("Test Summary")

        total = len(self.results)
        passed = sum(1 for _, p, _ in self.results if p)
        failed = total - passed

        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ({100 * passed // total}%)")
        print(f"Failed: {failed}\n")

        if failed > 0:
            print("Failed Tests:")
            for test_name, passed, message in self.results:
                if not passed:
                    print(f"  ✗ {test_name}")
                    if message:
                        print(f"    → {message}")

        print()
        if failed == 0:
            print("✓ All tests passed! System is ready for deployment.")
            return True
        else:
            print("✗ Some tests failed. Please review the configuration.")
            return False

    def run_all(self):
        """Run all tests."""
        self.print_header("Running Complete Test Suite")
        print("Testing all components of your Nail Salon Automation System\n")

        self.test_configuration()
        self.test_database()
        self.test_fresha_api()
        self.test_email_service()
        self.test_alert_service()
        self.test_script_imports()

        success = self.print_summary()
        return success


def main():
    """Main entry point."""
    suite = TestSuite()
    success = suite.run_all()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
