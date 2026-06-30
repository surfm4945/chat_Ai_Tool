"""Database access helpers."""

from __future__ import annotations

import sqlite3

from src.chat_ai_tool.models import Contact, ConversationPreview, MessageView, SessionRecord, User
from src.chat_ai_tool.security import utc_now_iso


def _user_from_row(row: sqlite3.Row | None) -> User | None:
    if row is None:
        return None
    return User(
        id=row["id"],
        username=row["username"],
        email=row["email"],
        created_at=row["created_at"],
        last_login_at=row["last_login_at"],
        is_active=bool(row["is_active"]),
    )


def _contact_from_row(row: sqlite3.Row) -> Contact:
    return Contact(
        user=User(
            id=row["id"],
            username=row["username"],
            email=row["email"],
            created_at=row["created_at"],
            last_login_at=row["last_login_at"],
            is_active=bool(row["is_active"]),
        ),
        last_seen_at=row["last_seen_at"],
    )


def _session_from_row(row: sqlite3.Row | None) -> SessionRecord | None:
    if row is None:
        return None
    return SessionRecord(
        id=row["id"],
        user_id=row["user_id"],
        session_token=row["session_token"],
        created_at=row["created_at"],
        last_seen_at=row["last_seen_at"],
        expires_at=row["expires_at"],
        revoked_at=row["revoked_at"],
    )


def _preview_from_row(row: sqlite3.Row) -> ConversationPreview:
    return ConversationPreview(
        conversation_id=row["conversation_id"],
        other_user=User(
            id=row["other_user_id"],
            username=row["other_username"],
            email=row["other_email"],
            created_at=row["other_created_at"],
            last_login_at=row["other_last_login_at"],
            is_active=bool(row["other_is_active"]),
        ),
        last_message_preview=row["last_message_preview"],
        updated_at=row["updated_at"],
    )


def _message_from_row(row: sqlite3.Row) -> MessageView:
    return MessageView(
        id=row["id"],
        conversation_id=row["conversation_id"],
        sender_id=row["sender_id"],
        sender_username=row["sender_username"] or "AI Assistant",
        role=row["role"],
        content=row["content"],
        created_at=row["created_at"],
    )


def create_user(
    connection: sqlite3.Connection,
    username: str,
    email: str,
    password_salt: str,
    password_hash: str,
) -> User:
    """Insert a new user into the database."""

    created_at = utc_now_iso()
    cursor = connection.execute(
        """
        INSERT INTO users (username, email, password_salt, password_hash, created_at, is_active)
        VALUES (?, ?, ?, ?, ?, 1)
        """,
        (username, email, password_salt, password_hash, created_at),
    )
    return User(
        id=cursor.lastrowid,
        username=username,
        email=email,
        created_at=created_at,
        last_login_at=None,
        is_active=True,
    )


def get_user_by_id(connection: sqlite3.Connection, user_id: int) -> User | None:
    row = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return _user_from_row(row)


def get_user_by_username(connection: sqlite3.Connection, username: str) -> User | None:
    row = connection.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    return _user_from_row(row)


def get_user_by_email(connection: sqlite3.Connection, email: str) -> User | None:
    row = connection.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return _user_from_row(row)


def get_user_auth_row(
    connection: sqlite3.Connection, username_or_email: str
) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT *
        FROM users
        WHERE username = ? OR email = ?
        """,
        (username_or_email, username_or_email.lower()),
    ).fetchone()


def update_last_login(connection: sqlite3.Connection, user_id: int) -> None:
    connection.execute(
        "UPDATE users SET last_login_at = ? WHERE id = ?",
        (utc_now_iso(), user_id),
    )


def list_contacts(connection: sqlite3.Connection, current_user_id: int) -> list[Contact]:
    """List other active users and their latest session activity."""

    rows = connection.execute(
        """
        SELECT
            u.id,
            u.username,
            u.email,
            u.created_at,
            u.last_login_at,
            u.is_active,
            MAX(s.last_seen_at) AS last_seen_at
        FROM users AS u
        LEFT JOIN sessions AS s
            ON s.user_id = u.id
            AND s.revoked_at IS NULL
        WHERE u.is_active = 1
          AND u.id != ?
        GROUP BY u.id
        ORDER BY u.username COLLATE NOCASE
        """,
        (current_user_id,),
    ).fetchall()
    return [_contact_from_row(row) for row in rows]


def create_session(
    connection: sqlite3.Connection,
    user_id: int,
    session_token: str,
    created_at: str,
    expires_at: str,
) -> SessionRecord:
    cursor = connection.execute(
        """
        INSERT INTO sessions (user_id, session_token, created_at, last_seen_at, expires_at, revoked_at)
        VALUES (?, ?, ?, ?, ?, NULL)
        """,
        (user_id, session_token, created_at, created_at, expires_at),
    )
    return SessionRecord(
        id=cursor.lastrowid,
        user_id=user_id,
        session_token=session_token,
        created_at=created_at,
        last_seen_at=created_at,
        expires_at=expires_at,
        revoked_at=None,
    )


def get_session_by_token(connection: sqlite3.Connection, session_token: str) -> SessionRecord | None:
    row = connection.execute(
        "SELECT * FROM sessions WHERE session_token = ?",
        (session_token,),
    ).fetchone()
    return _session_from_row(row)


def touch_session(connection: sqlite3.Connection, session_token: str, seen_at: str) -> None:
    connection.execute(
        "UPDATE sessions SET last_seen_at = ? WHERE session_token = ? AND revoked_at IS NULL",
        (seen_at, session_token),
    )


def revoke_session(connection: sqlite3.Connection, session_token: str) -> None:
    connection.execute(
        "UPDATE sessions SET revoked_at = ? WHERE session_token = ? AND revoked_at IS NULL",
        (utc_now_iso(), session_token),
    )


def revoke_all_user_sessions(connection: sqlite3.Connection, user_id: int) -> None:
    connection.execute(
        "UPDATE sessions SET revoked_at = ? WHERE user_id = ? AND revoked_at IS NULL",
        (utc_now_iso(), user_id),
    )


def get_or_create_conversation(
    connection: sqlite3.Connection,
    user_a_id: int,
    user_b_id: int,
) -> int:
    """Create a deterministic one-to-one conversation."""

    user_low_id, user_high_id = sorted((user_a_id, user_b_id))
    row = connection.execute(
        """
        SELECT id
        FROM conversations
        WHERE user_low_id = ? AND user_high_id = ?
        """,
        (user_low_id, user_high_id),
    ).fetchone()
    if row is not None:
        return row["id"]

    created_at = utc_now_iso()
    cursor = connection.execute(
        """
        INSERT INTO conversations (user_low_id, user_high_id, created_at, updated_at)
        VALUES (?, ?, ?, ?)
        """,
        (user_low_id, user_high_id, created_at, created_at),
    )
    return cursor.lastrowid


def list_conversations(
    connection: sqlite3.Connection,
    current_user_id: int,
) -> list[ConversationPreview]:
    rows = connection.execute(
        """
        SELECT
            c.id AS conversation_id,
            CASE WHEN c.user_low_id = ? THEN u_high.id ELSE u_low.id END AS other_user_id,
            CASE WHEN c.user_low_id = ? THEN u_high.username ELSE u_low.username END AS other_username,
            CASE WHEN c.user_low_id = ? THEN u_high.email ELSE u_low.email END AS other_email,
            CASE WHEN c.user_low_id = ? THEN u_high.created_at ELSE u_low.created_at END AS other_created_at,
            CASE WHEN c.user_low_id = ? THEN u_high.last_login_at ELSE u_low.last_login_at END AS other_last_login_at,
            CASE WHEN c.user_low_id = ? THEN u_high.is_active ELSE u_low.is_active END AS other_is_active,
            COALESCE(
                (
                    SELECT m.content
                    FROM messages AS m
                    WHERE m.conversation_id = c.id
                    ORDER BY m.created_at DESC, m.id DESC
                    LIMIT 1
                ),
                'No messages yet'
            ) AS last_message_preview,
            c.updated_at AS updated_at
        FROM conversations AS c
        JOIN users AS u_low ON u_low.id = c.user_low_id
        JOIN users AS u_high ON u_high.id = c.user_high_id
        WHERE c.user_low_id = ? OR c.user_high_id = ?
        ORDER BY c.updated_at DESC, c.id DESC
        """,
        (
            current_user_id,
            current_user_id,
            current_user_id,
            current_user_id,
            current_user_id,
            current_user_id,
            current_user_id,
            current_user_id,
        ),
    ).fetchall()
    return [_preview_from_row(row) for row in rows]


def add_message(
    connection: sqlite3.Connection,
    conversation_id: int,
    sender_id: int | None,
    role: str,
    content: str,
) -> MessageView:
    created_at = utc_now_iso()
    sender_username = "AI Assistant" if sender_id is None else ""
    if sender_id is not None:
        row = connection.execute(
            "SELECT username FROM users WHERE id = ?",
            (sender_id,),
        ).fetchone()
        sender_username = row["username"] if row else "Unknown"

    cursor = connection.execute(
        """
        INSERT INTO messages (conversation_id, sender_id, role, content, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (conversation_id, sender_id, role, content, created_at),
    )
    connection.execute(
        "UPDATE conversations SET updated_at = ? WHERE id = ?",
        (created_at, conversation_id),
    )
    return MessageView(
        id=cursor.lastrowid,
        conversation_id=conversation_id,
        sender_id=sender_id,
        sender_username=sender_username,
        role=role,
        content=content,
        created_at=created_at,
    )


def list_messages(
    connection: sqlite3.Connection,
    conversation_id: int,
    limit: int = 200,
) -> list[MessageView]:
    rows = connection.execute(
        """
        SELECT
            m.id,
            m.conversation_id,
            m.sender_id,
            COALESCE(u.username, 'AI Assistant') AS sender_username,
            m.role,
            m.content,
            m.created_at
        FROM messages AS m
        LEFT JOIN users AS u ON u.id = m.sender_id
        WHERE m.conversation_id = ?
        ORDER BY m.created_at ASC, m.id ASC
        LIMIT ?
        """,
        (conversation_id, limit),
    ).fetchall()
    return [_message_from_row(row) for row in rows]


def list_message_dicts_for_ai(
    connection: sqlite3.Connection,
    conversation_id: int,
    limit: int = 12,
) -> list[dict[str, str]]:
    rows = connection.execute(
        """
        SELECT
            COALESCE(u.username, 'AI Assistant') AS sender_username,
            m.role,
            m.content
        FROM messages AS m
        LEFT JOIN users AS u ON u.id = m.sender_id
        WHERE m.conversation_id = ?
        ORDER BY m.created_at DESC, m.id DESC
        LIMIT ?
        """,
        (conversation_id, limit),
    ).fetchall()
    rows_reversed = list(reversed(rows))
    return [
        {
            "sender_username": row["sender_username"],
            "role": row["role"],
            "content": row["content"],
        }
        for row in rows_reversed
    ]
