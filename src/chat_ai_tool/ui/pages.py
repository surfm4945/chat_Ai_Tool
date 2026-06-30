"""Streamlit pages and UI wiring."""

from __future__ import annotations

import streamlit as st

from src.chat_ai_tool.config import Settings
from src.chat_ai_tool.models import Contact, ConversationPreview, User
from src.chat_ai_tool.services.ai_service import generate_gemini_reply
from src.chat_ai_tool.services.auth_service import login_user, logout_user, register_user
from src.chat_ai_tool.services.chat_service import (
    get_ai_context_messages,
    get_contacts,
    get_conversations,
    get_thread_messages,
    send_message,
)
from src.chat_ai_tool.services.presence_service import format_contact_status, is_online


def _apply_styles() -> None:
    """Add a small visual system for a more polished layout."""

    st.markdown(
        """
        <style>
        .app-shell {
            background: linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
            border-radius: 24px;
            padding: 1.25rem;
            border: 1px solid rgba(15, 23, 42, 0.08);
        }
        .muted {
            color: #64748b;
            font-size: 0.95rem;
        }
        .status-pill {
            display: inline-block;
            padding: 0.25rem 0.65rem;
            border-radius: 999px;
            background: rgba(15, 118, 110, 0.12);
            color: #0f766e;
            font-weight: 600;
        }
        .status-pill.offline {
            background: rgba(100, 116, 139, 0.12);
            color: #475569;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_auth_tabs(settings: Settings) -> None:
    """Show login and registration forms."""

    st.markdown('<div class="app-shell">', unsafe_allow_html=True)
    st.title(settings.app_name)
    st.write("Private chat with a simple, secure, beginner-friendly flow.")

    login_tab, register_tab = st.tabs(["Login", "Register"])

    with login_tab:
        with st.form("login_form", clear_on_submit=False):
            username_or_email = st.text_input("Username or email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
        if submitted:
            try:
                login_user(settings, username_or_email, password)
                st.success("Login successful.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    with register_tab:
        with st.form("register_form", clear_on_submit=False):
            username = st.text_input("Username")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm password", type="password")
            submitted = st.form_submit_button("Create account")
        if submitted:
            try:
                register_user(settings, username, email, password, confirm_password)
                st.success("Account created and you are now signed in.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    st.markdown("</div>", unsafe_allow_html=True)


def _render_sidebar(settings: Settings, current_user: User, contacts: list[Contact]) -> None:
    """Render sidebar controls and presence information."""

    with st.sidebar:
        st.markdown("## Account")
        st.write(f"**{current_user.username}**")
        st.caption(current_user.email)
        st.markdown("<span class='status-pill'>Signed in</span>", unsafe_allow_html=True)
        if st.button("Logout", use_container_width=True):
            logout_user(settings)
            st.rerun()

        st.divider()
        st.markdown("## Online contacts")
        if not contacts:
            st.caption("No other users are registered yet.")
        for contact in contacts:
            online = is_online(contact.last_seen_at)
            pill_class = "" if online else "offline"
            st.markdown(
                f"<span class='status-pill {pill_class}'>{contact.user.username} - {'online' if online else 'offline'}</span>",
                unsafe_allow_html=True,
            )
            st.caption(contact.user.email)

        st.divider()
        st.markdown("## How it works")
        st.caption(
            "Pick a contact, send a private message, and ask Gemini for a reply idea if you want help drafting a response."
        )


def _render_conversation_list(conversations: list[ConversationPreview]) -> None:
    """Render a compact list of recent conversations."""

    if not conversations:
        st.info("No conversations yet. Send a message to start one.")
        return

    st.markdown("### Recent conversations")
    for preview in conversations[:5]:
        st.write(f"**{preview.other_user.username}**")
        st.caption(preview.last_message_preview)


def _render_chat_thread(
    settings: Settings,
    current_user: User,
    contact: Contact,
) -> None:
    """Render the selected private thread."""

    thread_messages = get_thread_messages(settings, current_user.id, contact.user.id)
    st.markdown(f"### Chat with {contact.user.username}")
    st.caption(f"Status: {'online' if is_online(contact.last_seen_at) else 'offline'}")

    if not thread_messages:
        st.info("No messages yet. Say hello first.")
    else:
        for message in thread_messages:
            role = "assistant" if message.role == "assistant" else "user"
            with st.chat_message(role):
                st.markdown(message.content)
                st.caption(f"{message.sender_username} | {message.created_at}")

    prompt = st.chat_input(f"Message {contact.user.username}")
    if prompt:
        send_message(settings, current_user.id, contact.user.id, prompt)
        st.rerun()

    with st.expander("Gemini reply helper", expanded=False):
        ai_request = st.text_input(
            "What should Gemini help with?",
            value="Suggest a short, friendly reply to the latest message.",
            key=f"ai_request_{contact.user.id}",
        )
        if st.button("Generate reply suggestion", key=f"ai_button_{contact.user.id}"):
            try:
                ai_messages = get_ai_context_messages(settings, current_user.id, contact.user.id)
                reply = generate_gemini_reply(settings, ai_messages, ai_request)
                st.session_state[f"ai_reply_{contact.user.id}"] = reply
            except Exception as exc:  # pragma: no cover - defensive UI guard
                st.session_state[f"ai_reply_{contact.user.id}"] = f"AI request failed: {exc}"

        if st.session_state.get(f"ai_reply_{contact.user.id}"):
            st.text_area(
                "AI suggestion",
                value=st.session_state[f"ai_reply_{contact.user.id}"],
                height=160,
                key=f"ai_reply_box_{contact.user.id}",
            )


def render_app(settings: Settings, current_user: User | None) -> None:
    """Render either the auth screen or the main chat dashboard."""

    _apply_styles()

    if current_user is None:
        _render_auth_tabs(settings)
        return

    contacts = get_contacts(settings, current_user.id)
    conversations = get_conversations(settings, current_user.id)
    _render_sidebar(settings, current_user, contacts)

    st.markdown('<div class="app-shell">', unsafe_allow_html=True)
    st.title(f"Welcome, {current_user.username}")
    st.write("Choose a person to chat with and start a private conversation.")

    if contacts:
        selected_contact = st.selectbox(
            "Select contact",
            options=contacts,
            format_func=format_contact_status,
            index=0,
            key="selected_contact",
        )
        _render_conversation_list(conversations)
        _render_chat_thread(settings, current_user, selected_contact)
    else:
        st.warning("Invite someone to register so you can start chatting.")

    st.markdown("</div>", unsafe_allow_html=True)
