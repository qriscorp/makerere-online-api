"""Optional SMTP email delivery for password reset and notifications."""
import logging
import smtplib
from email.message import EmailMessage

from app.config import settings

logger = logging.getLogger(__name__)


def smtp_configured() -> bool:
    return bool(settings.smtp_host and settings.smtp_from)


def send_email(to_email: str, subject: str, html_body: str, text_body: str) -> bool:
    """Send an email via SMTP. Returns True on success, False if SMTP is not configured."""
    if not smtp_configured():
        logger.warning("SMTP not configured — email not sent to %s", to_email)
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from
    message["To"] = to_email
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(message)
        return True
    except Exception:
        logger.exception("Failed to send email to %s", to_email)
        return False


def send_password_reset_email(to_email: str, name: str, reset_url: str) -> bool:
    subject = "Reset your Makerere Online password"
    minutes = settings.password_reset_expire_minutes
    text_body = (
        f"Hello {name},\n\n"
        f"We received a request to reset your Makerere Online password.\n\n"
        f"Open this link to choose a new password (valid for {minutes} minutes):\n"
        f"{reset_url}\n\n"
        "If you did not request this, you can safely ignore this email.\n\n"
        "Makerere Online School\n"
    )
    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:520px;margin:0 auto;color:#1f2937;">
      <p style="color:#6B1D1D;font-weight:bold;font-size:18px;">Makerere Online School</p>
      <p>Hello {name},</p>
      <p>We received a request to reset your password. Click the button below to choose a new one.</p>
      <p style="margin:28px 0;">
        <a href="{reset_url}"
           style="background:#6B1D1D;color:#fff;padding:12px 24px;border-radius:8px;
                  text-decoration:none;font-weight:bold;display:inline-block;">
          Reset password
        </a>
      </p>
      <p style="font-size:13px;color:#6b7280;">
        Or copy this link into your browser:<br>
        <a href="{reset_url}" style="color:#6B1D1D;word-break:break-all;">{reset_url}</a>
      </p>
      <p style="font-size:13px;color:#6b7280;">This link expires in {minutes} minutes.</p>
      <p style="font-size:13px;color:#6b7280;">If you did not request this, you can ignore this email.</p>
    </div>
  """
    return send_email(to_email, subject, html_body, text_body)


def send_verification_email(to_email: str, name: str, code: str) -> bool:
    subject = "Verify your Makerere Online account"
    minutes = settings.email_verification_expire_minutes
    text_body = (
        f"Hello {name},\n\n"
        f"Your Makerere Online verification code is: {code}\n\n"
        f"This code expires in {minutes} minutes.\n"
        "If you did not create an account, you can ignore this email.\n\n"
        "Makerere Online School\n"
    )
    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:520px;margin:0 auto;color:#1f2937;">
      <p style="color:#6B1D1D;font-weight:bold;font-size:18px;">Makerere Online School</p>
      <p>Hello {name},</p>
      <p>Thank you for registering. Enter this verification code to complete your account:</p>
      <p style="font-size:28px;font-weight:bold;letter-spacing:6px;color:#6B1D1D;margin:24px 0;">
        {code}
      </p>
      <p style="font-size:13px;color:#6b7280;">This code expires in {minutes} minutes.</p>
      <p style="font-size:13px;color:#6b7280;">If you did not create an account, you can ignore this email.</p>
    </div>
  """
    return send_email(to_email, subject, html_body, text_body)
