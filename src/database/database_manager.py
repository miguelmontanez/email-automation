import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
from src.config import DATABASE_PATH, DATABASE_BACKUP_PATH

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, db_path: str = str(DATABASE_PATH)):
        self.db_path = db_path
        self.backup_dir = DATABASE_BACKUP_PATH
        self.backup_dir.mkdir(exist_ok=True)
        self.init_database()

    def init_database(self):
        """Initialize database with required tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Customers table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fresha_customer_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    phone TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Appointments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fresha_appointment_id TEXT UNIQUE NOT NULL,
                    customer_id INTEGER NOT NULL,
                    service_type TEXT,
                    appointment_date TIMESTAMP NOT NULL,
                    completion_date TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(customer_id) REFERENCES customers(id)
                )
            """)

            # Thank you emails table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS thank_you_emails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    appointment_id INTEGER NOT NULL,
                    customer_id INTEGER NOT NULL,
                    email_address TEXT NOT NULL,
                    scheduled_time TIMESTAMP,
                    sent_time TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    retry_count INTEGER DEFAULT 0,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(appointment_id) REFERENCES appointments(id),
                    FOREIGN KEY(customer_id) REFERENCES customers(id)
                )
            """)

            # Follow-up emails table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS followup_emails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    appointment_id INTEGER NOT NULL,
                    customer_id INTEGER NOT NULL,
                    email_address TEXT NOT NULL,
                    scheduled_date TIMESTAMP NOT NULL,
                    sent_time TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    retry_count INTEGER DEFAULT 0,
                    error_message TEXT,
                    feedback_token TEXT UNIQUE,
                    feedback_provided BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(appointment_id) REFERENCES appointments(id),
                    FOREIGN KEY(customer_id) REFERENCES customers(id)
                )
            """)

            # Email logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS email_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email_address TEXT NOT NULL,
                    email_type TEXT NOT NULL,
                    subject TEXT,
                    status TEXT,
                    appointment_id INTEGER,
                    sent_at TIMESTAMP,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Script execution logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS script_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    script_name TEXT NOT NULL,
                    execution_date TIMESTAMP NOT NULL,
                    status TEXT NOT NULL,
                    emails_sent INTEGER DEFAULT 0,
                    emails_skipped INTEGER DEFAULT 0,
                    emails_failed INTEGER DEFAULT 0,
                    error_message TEXT,
                    execution_time_seconds FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for better query performance
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_appointments_customer ON appointments(customer_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(appointment_date)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_thank_you_status ON thank_you_emails(status)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_followup_status ON followup_emails(status)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_email_logs_type ON email_logs(email_type)"
            )

            conn.commit()
            logger.info("Database initialized successfully")

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def backup_database(self):
        """Create a backup of the database."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = (
                self.backup_dir / f"nail_salon_automation_backup_{timestamp}.db"
            )

            with self.get_connection() as conn:
                backup_conn = sqlite3.connect(str(backup_path))
                conn.backup(backup_conn)
                backup_conn.close()

            logger.info(f"Database backed up to {backup_path}")
            return str(backup_path)
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            return None

    def add_customer(self, fresha_id: str, name: str, email: str, phone: str = None):
        """Add or update a customer."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO customers 
                    (fresha_customer_id, name, email, phone, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (fresha_id, name, email, phone),
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error adding customer: {e}")
            return None

    def get_customer_by_email(self, email: str):
        """Get customer by email."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM customers WHERE email = ?", (email,))
                return cursor.fetchone()
        except Exception as e:
            logger.error(f"Error fetching customer: {e}")
            return None

    def add_appointment(
        self,
        fresha_id: str,
        customer_id: int,
        service_type: str,
        appointment_date: str,
        completion_date: str = None,
    ):
        """Add appointment."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO appointments
                    (fresha_appointment_id, customer_id, service_type, appointment_date, completion_date, status)
                    VALUES (?, ?, ?, ?, ?, 'completed')
                    """,
                    (fresha_id, customer_id, service_type, appointment_date, completion_date),
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error adding appointment: {e}")
            return None

    def add_thank_you_email(
        self, appointment_id: int, customer_id: int, email_address: str, scheduled_time: str
    ):
        """Add thank you email record."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO thank_you_emails
                    (appointment_id, customer_id, email_address, scheduled_time, status)
                    VALUES (?, ?, ?, ?, 'pending')
                    """,
                    (appointment_id, customer_id, email_address, scheduled_time),
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error adding thank you email: {e}")
            return None

    def get_pending_thank_you_emails(self):
        """Get all pending thank you emails for current time."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT tye.* FROM thank_you_emails tye
                    WHERE tye.status = 'pending'
                    AND tye.retry_count < 3
                    AND datetime(tye.scheduled_time) <= datetime('now')
                    ORDER BY tye.created_at ASC
                    """
                )
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error fetching pending thank you emails: {e}")
            return []

    def update_thank_you_email_status(
        self, email_id: int, status: str, error_message: str = None
    ):
        """Update thank you email status."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE thank_you_emails
                    SET status = ?, error_message = ?, sent_time = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (status, error_message, email_id),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Error updating thank you email status: {e}")

    def increment_thank_you_retry(self, email_id: int):
        """Increment retry count for thank you email."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE thank_you_emails
                    SET retry_count = retry_count + 1
                    WHERE id = ?
                    """,
                    (email_id,),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Error incrementing retry count: {e}")

    def add_followup_email(
        self, appointment_id: int, customer_id: int, email_address: str, scheduled_date: str, feedback_token: str
    ):
        """Add follow-up email record."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO followup_emails
                    (appointment_id, customer_id, email_address, scheduled_date, feedback_token, status)
                    VALUES (?, ?, ?, ?, ?, 'pending')
                    """,
                    (appointment_id, customer_id, email_address, scheduled_date, feedback_token),
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error adding follow-up email: {e}")
            return None

    def get_pending_followup_emails(self):
        """Get all pending follow-up emails due for sending."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT fye.* FROM followup_emails fye
                    WHERE fye.status = 'pending'
                    AND fye.retry_count < 3
                    AND datetime(fye.scheduled_date) <= datetime('now')
                    ORDER BY fye.created_at ASC
                    """
                )
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error fetching pending follow-up emails: {e}")
            return []

    def update_followup_email_status(
        self, email_id: int, status: str, error_message: str = None
    ):
        """Update follow-up email status."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE followup_emails
                    SET status = ?, error_message = ?, sent_time = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (status, error_message, email_id),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Error updating follow-up email status: {e}")

    def increment_followup_retry(self, email_id: int):
        """Increment retry count for follow-up email."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE followup_emails
                    SET retry_count = retry_count + 1
                    WHERE id = ?
                    """,
                    (email_id,),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Error incrementing retry count: {e}")

    def log_email(
        self,
        email_address: str,
        email_type: str,
        subject: str,
        status: str,
        error_message: str = None,
        appointment_id: int = None,
    ):
        """Log email sending attempt."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO email_logs
                    (email_address, email_type, subject, status, error_message, appointment_id, sent_at)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (email_address, email_type, subject, status, error_message, appointment_id),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Error logging email: {e}")

    def log_script_execution(
        self,
        script_name: str,
        status: str,
        emails_sent: int = 0,
        emails_skipped: int = 0,
        emails_failed: int = 0,
        error_message: str = None,
        execution_time: float = None,
    ):
        """Log script execution."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO script_logs
                    (script_name, execution_date, status, emails_sent, emails_skipped, emails_failed, error_message, execution_time_seconds)
                    VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?)
                    """,
                    (script_name, status, emails_sent, emails_skipped, emails_failed, error_message, execution_time),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Error logging script execution: {e}")

    def check_duplicate_followup(self, customer_id: int, appointment_id: int) -> bool:
        """Check if follow-up already exists for appointment."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id FROM followup_emails
                    WHERE customer_id = ? AND appointment_id = ?
                    """,
                    (customer_id, appointment_id),
                )
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking duplicate follow-up: {e}")
            return False

    def get_script_stats(self, script_name: str, days: int = 7):
        """Get script execution stats for last N days."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT 
                        SUM(emails_sent) as total_sent,
                        SUM(emails_skipped) as total_skipped,
                        SUM(emails_failed) as total_failed,
                        COUNT(*) as executions,
                        AVG(execution_time_seconds) as avg_time
                    FROM script_logs
                    WHERE script_name = ? 
                    AND execution_date >= datetime('now', '-' || ? || ' days')
                    """,
                    (script_name, days),
                )
                return cursor.fetchone()
        except Exception as e:
            logger.error(f"Error fetching script stats: {e}")
            return None
