import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from src.config import (
    SMTP_SERVER,
    SMTP_PORT,
    SENDER_EMAIL,
    SENDER_PASSWORD,
    SENDER_NAME,
)

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self.sender_email = SENDER_EMAIL
        self.sender_password = SENDER_PASSWORD
        self.sender_name = SENDER_NAME

    def send_email(
        self, recipient_email: str, subject: str, html_body: str, plain_body: str = None
    ) -> tuple:
        """
        Send email with both HTML and plain text versions.

        Returns:
            tuple: (success: bool, error_message: str or None)
        """
        try:
            if not recipient_email or not self.sender_email or not self.sender_password:
                error_msg = "Missing email configuration"
                logger.warning(f"Email not sent: {error_msg}")
                return False, error_msg

            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = formataddr((self.sender_name, self.sender_email))
            message["To"] = recipient_email

            # Attach plain text and HTML versions
            if plain_body:
                message.attach(MIMEText(plain_body, "plain"))
            message.attach(MIMEText(html_body, "html"))

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)

            logger.info(f"Email sent successfully to {recipient_email}")
            return True, None

        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"SMTP Authentication failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def send_thank_you_email(
        self, recipient_email: str, customer_name: str, salon_name: str = None
    ) -> tuple:
        """Send thank you email."""
        if salon_name is None:
            salon_name = self.sender_name

        subject = "Thank You for Your Visit! 💅"
        
        plain_body = f"""
Dear {customer_name},

Thank you for choosing us for your nails today! We hope you love your new look.

If you have any questions or concerns, feel free to reach out anytime.

Best regards,
{salon_name}
"""

        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #d946a6;">Thank You for Your Visit!</h2>
        
        <p>Dear {customer_name},</p>
        
        <p>Thank you for choosing us for your nails today! We hope you love your new look. 💅</p>
        
        <p>If you have any questions or concerns, feel free to reach out anytime.</p>
        
        <br>
        <p>Best regards,<br>
        <strong>{salon_name}</strong></p>
    </div>
</body>
</html>
"""

        return self.send_email(recipient_email, subject, html_body, plain_body)

    def send_followup_email(
        self,
        recipient_email: str,
        customer_name: str,
        feedback_link: str,
        salon_name: str = None,
    ) -> tuple:
        """Send follow-up email with feedback link."""
        if salon_name is None:
            salon_name = self.sender_name

        subject = "How did your nails last? We'd love to know! 💖"
        
        plain_body = f"""
Dear {customer_name},

It's been a week since your last visit! We hope your nails are still looking fabulous.

Could you let us know how long your manicure/pedicure lasted? Your feedback helps us improve our services.

Feedback: {feedback_link}

Thank you for being a valued customer!

Best regards,
{salon_name}
"""

        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #d946a6;">How did your nails last? 💖</h2>
        
        <p>Dear {customer_name},</p>
        
        <p>It's been a week since your last visit! We hope your nails are still looking fabulous.</p>
        
        <p>Could you let us know how long your manicure/pedicure lasted? Your feedback helps us improve our services.</p>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{feedback_link}" style="background-color: #d946a6; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                Share Your Feedback
            </a>
        </div>
        
        <p>Thank you for being a valued customer!</p>
        
        <br>
        <p>Best regards,<br>
        <strong>{salon_name}</strong></p>
    </div>
</body>
</html>
"""

        return self.send_email(recipient_email, subject, html_body, plain_body)
