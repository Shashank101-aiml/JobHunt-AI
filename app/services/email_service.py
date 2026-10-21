import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Optional, List, Tuple
import os

from app.config import settings

class EmailServiceError(Exception):
    pass

def validate_email_address(email: str) -> bool:
    """Validates that email is well-formed and not an example placeholder."""
    if not email or not isinstance(email, str):
        return False
    if "@example.com" in email.lower() or "candidate@example.com" in email.lower():
        return False
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(pattern, email.strip()))

def is_smtp_configured() -> bool:
    """Checks if valid SMTP credentials are configured and email is enabled."""
    return bool(
        settings.EMAIL_ENABLED and
        settings.SMTP_HOST and
        settings.SMTP_USER and
        settings.SMTP_USER not in ["mock_user", "your_smtp_user", ""] and
        settings.SMTP_PASSWORD and
        settings.SMTP_PASSWORD not in ["mock_password", ""]
    )

def send_email(
    to_email: str,
    subject: str,
    body: str,
    attachment_paths: Optional[List[str]] = None
) -> Tuple[bool, str]:
    """
    Sends email via real SMTP credentials.
    Rejects mock credentials and fake addresses with honest error reporting.
    """
    if not validate_email_address(to_email):
        return False, f"Invalid or placeholder recipient address: '{to_email}'"

    if not is_smtp_configured():
        return False, (
            "Email service is disabled or credentials are not configured in .env "
            "(set EMAIL_ENABLED=true with valid SMTP_USER/SMTP_PASSWORD)."
        )

    try:
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = settings.FROM_EMAIL
        msg["To"] = to_email

        msg.attach(MIMEText(body, "plain"))

        if attachment_paths:
            for path in attachment_paths:
                if os.path.exists(path):
                    with open(path, "rb") as f:
                        part = MIMEApplication(f.read(), Name=os.path.basename(path))
                    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(path)}"'
                    msg.attach(part)

        port = settings.SMTP_PORT or 587
        if settings.SMTP_SECURE or port == 465:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, port, timeout=15)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, port, timeout=15)
            server.starttls()

        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.FROM_EMAIL, [to_email], msg.as_string())
        server.quit()
        return True, f"Email delivered to {to_email}"
    except Exception as e:
        return False, f"SMTP delivery failed: {str(e)}"
