"""Authentication and session management."""

from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

from src.chat_ai_tool.config import Settings
from src.chat_ai_tool.database import database_session
from src.chat_ai_tool.models import User
from src.chat_ai_tool.repositories import (
    create_session,
    create_user,
    get_session_by_token,
    get_user_auth_row,
    get_user_by_id,
    get_user_by_email,
    get_user_by_username,
    revoke_all_user_sessions,
    revoke_session,
    touch_session,
    update_last_login,
)
from src.chat_ai_tool.security import (
    expiry_from_now,
    generate_token,
    hash_password,
    normalize_email,
    normalize_username,
    parse_utc,
    utc_now_iso,
    verify_password,
)


def _session_is_active(expires_at: str | None, revoked_at: str | None) -> bool:
    if revoked_at:
        return False
    parsed = parse_utc(expires_at)
    return parsed is not None and parsed > datetime.now(timezone.utc)


def _clear_auth_state() -> None:
    st.session_state.pop("auth_token", None)
    st.session_state.pop("current_user_id", None)
    st.session_state.pop("current_username", None)


def validate_registration_input(username: str, email: str, password: str, confirm_password: str) -> None:
    """Validate the registration form before touching the database."""

    username = normalize_username(username)
    email = normalize_email(email)
    if len(username) < 3:
        raise ValueError("Username must be at least 3 characters long.")
    if "@" not in email or "." not in email.split("@")[-1]:
        raise ValueError("Please enter a valid email address.")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if password != confirm_password:
        raise ValueError("Passwords do not match.")


def register_user(settings: Settings, username: str, email: str, password: str, confirm_password: str) -> User:
    """Register a new account and log the user in immediately."""

    validate_registration_input(username, email, password, confirm_password)
    username = normalize_username(username)
    email = normalize_email(email)

    with database_session(settings) as connection:
        if get_user_by_username(connection, username):
            raise ValueError("That username is already taken.")
        if get_user_by_email(connection, email):
            raise ValueError("That email is already registered.")

        salt_hex, password_hash = hash_password(password)
        user = create_user(connection, username, email, salt_hex, password_hash)
        update_last_login(connection, user.id)

        session_token = generate_token()
        create_session(
            connection,
            user.id,
            session_token,
            created_at=utc_now_iso(),
            expires_at=expiry_from_now(settings.session_ttl_minutes),
        )

    st.session_state.auth_token = session_token
    st.session_state.current_user_id = user.id
    st.session_state.current_username = user.username
    return user


def login_user(settings: Settings, username_or_email: str, password: str) -> User:
    """Authenticate a user and create a fresh session."""

    lookup_value = username_or_email.strip()
    normalized_email = normalize_email(lookup_value)

    with database_session(settings) as connection:
        row = get_user_auth_row(connection, lookup_value) or get_user_auth_row(connection, normalized_email)
        if row is None:
            raise ValueError("Invalid username/email or password.")
        if not bool(row["is_active"]):
            raise ValueError("This account is inactive.")
        if not verify_password(password, row["password_salt"], row["password_hash"]):
            raise ValueError("Invalid username/email or password.")

        update_last_login(connection, row["id"])
        session_token = generate_token()
        create_session(
            connection,
            row["id"],
            session_token,
            created_at=utc_now_iso(),
            expires_at=expiry_from_now(settings.session_ttl_minutes),
        )

    user = User(
        id=row["id"],
        username=row["username"],
        email=row["email"],
        created_at=row["created_at"],
        last_login_at=utc_now_iso(),
        is_active=bool(row["is_active"]),
    )
    st.session_state.auth_token = session_token
    st.session_state.current_user_id = user.id
    st.session_state.current_username = user.username
    return user


def restore_session(settings: Settings) -> User | None:
    """Restore the current user from the Streamlit session token."""

    token = st.session_state.get("auth_token")
    if not token:
        return None

    with database_session(settings) as connection:
        session_record = get_session_by_token(connection, token)
        if session_record is None:
            _clear_auth_state()
            return None
        if not _session_is_active(session_record.expires_at, session_record.revoked_at):
            revoke_session(connection, token)
            _clear_auth_state()
            return None

        now_iso = utc_now_iso()
        touch_session(connection, token, now_iso)
        user = get_user_by_id(connection, session_record.user_id)
        if user is None or not user.is_active:
            revoke_session(connection, token)
            _clear_auth_state()
            return None

    st.session_state.current_user_id = user.id
    st.session_state.current_username = user.username
    return user


def logout_user(settings: Settings) -> None:
    """Log the user out everywhere in the current browser session."""

    token = st.session_state.get("auth_token")
    user_id = st.session_state.get("current_user_id")
    if token is not None:
        with database_session(settings) as connection:
            revoke_session(connection, token)
            if user_id is not None:
                revoke_all_user_sessions(connection, int(user_id))
    _clear_auth_state()
