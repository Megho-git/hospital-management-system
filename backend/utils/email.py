import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logger = logging.getLogger(__name__)


def send_email(to, subject, body, html=None):
    """
    Send an email via SMTP. Falls back to console logging when
    SMTP is not configured (MAIL_USERNAME is empty).
    """
    mail_server = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    mail_port = int(os.getenv("MAIL_PORT", "587"))
    mail_username = os.getenv("MAIL_USERNAME", "")
    mail_password = os.getenv("MAIL_PASSWORD", "")
    mail_sender = os.getenv("MAIL_DEFAULT_SENDER", "hms@example.com")

    if not mail_username or not mail_password:
        logger.info("[EMAIL-MOCK] To: %s | Subject: %s | Body: %s", to, subject, body[:200])
        print(f"[EMAIL-MOCK] To: {to} | Subject: {subject}")
        print(f"  Body: {body[:300]}")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = mail_sender
        msg["To"] = to

        msg.attach(MIMEText(body, "plain"))
        if html:
            msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(mail_server, mail_port) as server:
            server.starttls()
            server.login(mail_username, mail_password)
            server.sendmail(mail_sender, [to], msg.as_string())

        logger.info("[EMAIL-SENT] To: %s | Subject: %s", to, subject)
        return True
    except Exception as e:
        logger.error("[EMAIL-FAIL] To: %s | Error: %s", to, str(e))
        print(f"[EMAIL-FAIL] To: {to} | Error: {e}")
        return False
