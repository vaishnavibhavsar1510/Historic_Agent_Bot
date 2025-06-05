# backend/app/otp.py
"""
OTP utilities: generation, Redis storage, validation, extraction helpers,
and e-mail delivery.
"""

from __future__ import annotations

import random
import re
import redis
from typing import Tuple, Optional

from backend.app.config import settings
from backend.app.email_utils import send_otp_email

# --------------------------------------------------------------------------- #
# Redis & constants
# --------------------------------------------------------------------------- #

DEFAULT_TTL_SECONDS = 300  # 5 minutes

redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)

# Regex patterns used across helpers
EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
OTP_REGEX = re.compile(r"\b(\d{4,8})\b")         # 4- to 8-digit number


# --------------------------------------------------------------------------- #
# Core helpers
# --------------------------------------------------------------------------- #

def generate_otp(length: int = 6) -> str:
    """Return a random numeric OTP (default 6 digits, zero-padded)."""
    return "".join(str(random.randint(0, 9)) for _ in range(length))


def store_otp(email: str, otp: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
    """
    Store ``otp`` under key ``otp:<email>`` with a configurable TTL.

    Signature kept compatible with existing calls that pass
    ``ttl_seconds=…`` explicitly.
    """
    redis_client.setex(f"otp:{email}", ttl_seconds, otp)


def retrieve_stored_otp(email: str) -> Optional[str]:
    """Return the stored OTP for ``email`` (or ``None`` if expired / missing)."""
    return redis_client.get(f"otp:{email}")


def delete_otp(email: str) -> None:
    """Remove the OTP for ``email`` – called after successful verification."""
    redis_client.delete(f"otp:{email}")


def verify_otp(email: str, otp: str) -> bool:
    """
    Return ``True`` if ``otp`` matches the stored value for ``email``.
    The stored OTP is deleted on a successful match.
    """
    stored = redis_client.get(f"otp:{email}")
    if stored and stored == otp:
        redis_client.delete(f"otp:{email}")
        return True
    return False


# --------------------------------------------------------------------------- #
# Validation / extraction helpers
# --------------------------------------------------------------------------- #

def is_valid_email(text: str) -> bool:
    """Return ``True`` if *text* looks like a standalone e-mail address."""
    return EMAIL_REGEX.fullmatch(text.strip()) is not None


def find_email(text: str) -> Optional[str]:
    """
    Scan an arbitrary string and return the **first** e-mail‐looking token,
    or ``None`` if none is found.
    """
    match = EMAIL_REGEX.search(text)
    return match.group(0) if match else None


def extract_otp(text: str, digits: int = 6) -> Optional[str]:
    """
    Return the **first** *digits*-long number found in *text*
    (default 6).  If none is found, return ``None``.
    """
    pattern = re.compile(rf"\b(\d{{{digits}}})\b")
    match = pattern.search(text)
    return match.group(1) if match else None


# --------------------------------------------------------------------------- #
# Convenience wrapper
# --------------------------------------------------------------------------- #

def generate_and_send_otp(
    email: str, ttl_seconds: int = DEFAULT_TTL_SECONDS
) -> Tuple[bool, str]:
    """
    1. Generate an OTP.
    2. Store it in Redis.
    3. E-mail it to *email*.

    Returns ``(True, "…")`` on success, ``(False, "error…")`` on failure.
    """
    otp_code = generate_otp()
    store_otp(email, otp_code, ttl_seconds=ttl_seconds)

    if send_otp_email(email, otp_code):
        return True, "OTP sent successfully!"
    return False, f"Failed to send OTP to {email}."
