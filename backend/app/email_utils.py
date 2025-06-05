# backend/app/email_utils.py
"""
SendGrid-based e-mail helpers.

We send only two kinds of messages:
  • OTP codes  (send_otp_email)
  • Plain “guide / notification” e-mails (send_plain_email)
"""

import logging
from typing import Final

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from backend.app.config import settings

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
#  Shared client & helpers
# --------------------------------------------------------------------------- #

SENDGRID_CLIENT: Final = SendGridAPIClient(settings.sendgrid_api_key)
SENDER_EMAIL:     Final = settings.email_sender          # verified sender

def _send(mail: Mail) -> bool:
    """
    Low-level wrapper that actually calls SendGrid and returns True/False
    depending on whether the response status code is 2xx.
    """
    try:
        resp = SENDGRID_CLIENT.send(mail)
        ok = 200 <= resp.status_code < 300
        if not ok:
            logger.warning(
                "SendGrid returned %s (%s)",
                resp.status_code,
                resp.body.decode() if resp.body else "no body",
            )
        return ok
    except Exception as exc:                             # pragma: no cover
        logger.error("SendGrid exception: %s", exc, exc_info=True)
        return False

# --------------------------------------------------------------------------- #
#  Public helpers
# --------------------------------------------------------------------------- #

def send_otp_email(receiver_email: str, otp: str) -> bool:
    """
    Send an OTP email (unchanged template, still used by the workflow).
    """
    body_text = (
        "Hello,\n\n"
        f"Your OTP code is: {otp}\n\n"
        "This OTP is valid for 5 minutes.\n\n"
        "If you didn’t request this OTP, please ignore this email.\n\n"
        "Best regards,\nYour Application Team"
    )

    mail = Mail(
        from_email=SENDER_EMAIL,
        to_emails=receiver_email,
        subject="Your OTP Code",
        plain_text_content=body_text,
        html_content=body_text.replace("\n", "<br>")
    )
    return _send(mail)


def send_plain_email(receiver_email: str, subject: str, body: str) -> bool:
    """
    Generic helper for any *non-OTP* message (e.g. detailed monument guide).

    Example:
        send_plain_email(
            "alice@example.com",
            "Extra details about Taj Mahal",
            "Here’s more info … Enjoy your visit!"
        )
    """
    mail = Mail(
        from_email=SENDER_EMAIL,
        to_emails=receiver_email,
        subject=subject,
        plain_text_content=body,
        html_content=body.replace("\n", "<br>")
    )
    return _send(mail)
