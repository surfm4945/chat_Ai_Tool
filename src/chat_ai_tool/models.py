"""Typed data objects used across the app."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class User:
    """A registered user account."""

    id: int
    username: str
    email: str
    created_at: str
    last_login_at: str | None
    is_active: bool


@dataclass(slots=True)
class Contact:
    """A chat contact plus presence metadata."""

    user: User
    last_seen_at: str | None


@dataclass(slots=True)
class SessionRecord:
    """A login session stored in SQLite."""

    id: int
    user_id: int
    session_token: str
    created_at: str
    last_seen_at: str
    expires_at: str
    revoked_at: str | None


@dataclass(slots=True)
class ConversationPreview:
    """A conversation with the latest message preview."""

    conversation_id: int
    other_user: User
    last_message_preview: str
    updated_at: str


@dataclass(slots=True)
class MessageView:
    """A chat message ready for display."""

    id: int
    conversation_id: int
    sender_id: int | None
    sender_username: str
    role: str
    content: str
    created_at: str
