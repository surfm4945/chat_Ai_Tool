"""Online status helpers."""

from __future__ import annotations

from datetime import datetime, timezone

from src.chat_ai_tool.models import Contact


def is_online(last_seen_at: str | None, active_window_minutes: int = 5) -> bool:
    """Return True when a contact has been active recently."""

    if not last_seen_at:
        return False
    last_seen = datetime.fromisoformat(last_seen_at)
    now = datetime.now(timezone.utc)
    delta = now - last_seen
    return delta.total_seconds() <= active_window_minutes * 60


def status_label(last_seen_at: str | None) -> str:
    """Return a user-friendly status label."""

    return "Online" if is_online(last_seen_at) else "Offline"


def format_contact_status(contact: Contact) -> str:
    """Format a contact label for select boxes and lists."""

    suffix = "online" if is_online(contact.last_seen_at) else "offline"
    return f"{contact.user.username} ({suffix})"
