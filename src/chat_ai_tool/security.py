"""Security helpers for passwords, sessions, and timestamps."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

PASSWORD_ITERATIONS = 390_000


def utc_now() -> datetime:
    """Return the current UTC time with timezone awareness."""

    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    """Return the current UTC time in ISO-8601 format."""

    return utc_now().isoformat()


def parse_utc(value: str | None) -> datetime | None:
    """Parse an ISO UTC timestamp stored in the database."""

    if not value:
        return None
    return datetime.fromisoformat(value)


def expiry_from_now(minutes: int) -> str:
    """Create an expiry timestamp a number of minutes from now."""

    return (utc_now() + timedelta(minutes=minutes)).isoformat()


def hash_password(password: str, salt_hex: str | None = None) -> tuple[str, str]:
    """Hash a password with PBKDF2 using a random salt."""

    salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )
    return salt.hex(), digest.hex()


def verify_password(password: str, salt_hex: str, expected_hash_hex: str) -> bool:
    """Compare a password against the stored hash."""

    _, calculated_hash = hash_password(password, salt_hex)
    return secrets.compare_digest(calculated_hash, expected_hash_hex)


def generate_token() -> str:
    """Generate a secure random session token."""

    return secrets.token_urlsafe(48)


def normalize_username(value: str) -> str:
    """Normalize usernames for consistency."""

    return value.strip()


def normalize_email(value: str) -> str:
    """Normalize emails so lookups stay predictable."""

    return value.strip().lower()
