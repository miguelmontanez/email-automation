import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from src.config import ALERT_EMAIL, SENDER_EMAIL, SENDER_PASSWORD, SENDER_NAME, SMTP_SERVER, SMTP_PORT

logger = logging.getLogger(__name__)


class AlertService:
    def __init__(self):
        self.alert_email = ALERT_EMAIL
        self.sender_email = SENDER_EMAIL
        self.sender_password = SENDER_PASSWORD
        self.sender_name = SENDER_NAME
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT

    def send_alert(self, subject: str, body: str, alert_type: str = "ERROR") -> bool:
        """Send alert email."""
        if not self.alert_email:
            logger.warning("Alert email not configured")
            return False

        try:
            message = MIMEMultipart()
            message["Subject"] = f"[{alert_type}] {subject}"
            message["From"] = self.sender_email
            message["To"] = self.alert_email

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            html_body = f"""
<html>
<body style="font-family: Arial, sans-serif;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 2px solid #ff6b6b; border-radius: 5px;">
        <h2 style="color: #ff6b6b;">⚠️ {alert_type} Alert</h2>
        <p><strong>Subject:</strong> {subject}</p>
        <p><strong>Time:</strong> {timestamp}</p>
        <hr>
        <pre style="background-color: #f5f5f5; padding: 10px; border-radius: 3px; overflow-x: auto;">
{body}
        </pre>
        <hr>
        <p style="color: #666; font-size: 12px;">This is an automated alert from your Nail Salon Automation system.</p>
    </div>
</body>
</html>
"""

            message.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)

            logger.info(f"Alert sent to {self.alert_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
            return False

    def send_execution_summary(
        self,
        script_name: str,
        emails_sent: int,
        emails_skipped: int,
        emails_failed: int,
        execution_time: float,
        errors: list = None,
    ) -> bool:
        """Send execution summary email."""
        if not self.alert_email:
            logger.warning("Alert email not configured")
            return False

        try:
            message = MIMEMultipart()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message["Subject"] = f"[SUMMARY] {script_name} - {timestamp}"
            message["From"] = self.sender_email
            message["To"] = self.alert_email

            status = "SUCCESS" if emails_failed == 0 else "COMPLETED WITH ERRORS"
            status_color = "#28a745" if emails_failed == 0 else "#ffc107"

            errors_html = ""
            if errors:
                errors_html = "<hr><h3 style='color: #ff6b6b;'>Errors:</h3><ul>"
                for error in errors:
                    errors_html += f"<li>{error}</li>"
                errors_html += "</ul>"

            html_body = f"""
<html>
<body style="font-family: Arial, sans-serif;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 2px solid {status_color}; border-radius: 5px;">
        <h2 style="color: {status_color};">📊 Execution Summary</h2>
        
        <p><strong>Script:</strong> {script_name}</p>
        <p><strong>Status:</strong> {status}</p>
        <p><strong>Execution Time:</strong> {execution_time:.2f} seconds</p>
        
        <hr>
        
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd; background-color: #f9f9f9;">
                    <strong>Emails Sent</strong>
                </td>
                <td style="padding: 10px; border: 1px solid #ddd; text-align: center; font-size: 18px; color: #28a745;">
                    {emails_sent}
                </td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd; background-color: #f9f9f9;">
                    <strong>Emails Skipped</strong>
                </td>
                <td style="padding: 10px; border: 1px solid #ddd; text-align: center; font-size: 18px; color: #17a2b8;">
                    {emails_skipped}
                </td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd; background-color: #f9f9f9;">
                    <strong>Emails Failed</strong>
                </td>
                <td style="padding: 10px; border: 1px solid #ddd; text-align: center; font-size: 18px; color: #dc3545;">
                    {emails_failed}
                </td>
            </tr>
        </table>
        
        {errors_html}
        
        <hr>
        <p style="color: #666; font-size: 12px;">Generated at {timestamp}</p>
    </div>
</body>
</html>
"""

            message.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)

            logger.info(f"Execution summary sent to {self.alert_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send execution summary: {e}")
            return False
