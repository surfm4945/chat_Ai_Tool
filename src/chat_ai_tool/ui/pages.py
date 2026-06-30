"""Streamlit pages and UI wiring."""

from __future__ import annotations

import streamlit as st

from src.chat_ai_tool.config import Settings
from src.chat_ai_tool.models import Contact, ConversationPreview, User
from src.chat_ai_tool.services.ai_service import generate_gemini_reply
from src.chat_ai_tool.services.auth_service import (
    change_password,
    login_user,
    logout_user,
    register_user,
    reset_password_by_email,
)
from src.chat_ai_tool.services.chat_service import (
    get_ai_context_messages,
    get_contacts,
    get_conversations,
    get_thread_messages,
    send_message,
)
from src.chat_ai_tool.services.presence_service import format_contact_status, is_online


def _theme_tokens(theme: str) -> dict[str, str]:
    """Return color tokens for the selected visual mode."""

    if theme == "dark":
        return {
            "app_bg": "#0b1220",
            "panel_bg": "rgba(15, 23, 42, 0.88)",
            "panel_border": "rgba(148, 163, 184, 0.14)",
            "text_main": "#e2e8f0",
            "text_muted": "#94a3b8",
            "accent": "#60a5fa",
            "accent_soft": "rgba(96, 165, 250, 0.16)",
            "accent_text": "#bfdbfe",
            "sidebar_bg": "rgba(15, 23, 42, 0.94)",
            "shadow": "0 18px 40px rgba(2, 6, 23, 0.35)",
            "message_bg": "rgba(15, 23, 42, 0.72)",
            "message_alt": "rgba(37, 99, 235, 0.16)",
        }
    if theme == "light":
        return {
            "app_bg": "#f4f7fb",
            "panel_bg": "rgba(255, 255, 255, 0.78)",
            "panel_border": "rgba(15, 23, 42, 0.08)",
            "text_main": "#0f172a",
            "text_muted": "#64748b",
            "accent": "#2563eb",
            "accent_soft": "rgba(37, 99, 235, 0.12)",
            "accent_text": "#1d4ed8",
            "sidebar_bg": "rgba(255, 255, 255, 0.92)",
            "shadow": "0 18px 40px rgba(15, 23, 42, 0.08)",
            "message_bg": "rgba(255, 255, 255, 0.58)",
            "message_alt": "rgba(37, 99, 235, 0.08)",
        }
    # system follows the browser preference with light defaults
    return {
        "app_bg": "#eef2ff",
        "panel_bg": "rgba(255, 255, 255, 0.74)",
        "panel_border": "rgba(15, 23, 42, 0.08)",
        "text_main": "#0f172a",
        "text_muted": "#64748b",
        "accent": "#2563eb",
        "accent_soft": "rgba(37, 99, 235, 0.12)",
        "accent_text": "#1d4ed8",
        "sidebar_bg": "rgba(255, 255, 255, 0.94)",
        "shadow": "0 18px 40px rgba(15, 23, 42, 0.08)",
        "message_bg": "rgba(255, 255, 255, 0.60)",
        "message_alt": "rgba(37, 99, 235, 0.08)",
    }


def _apply_styles(theme: str) -> None:
    """Add polished app-wide styles."""

    t = _theme_tokens(theme)
    system_override = ""
    if theme == "system":
        system_override = """
        <style>
        @media (prefers-color-scheme: dark) {
            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(37, 99, 235, 0.16), transparent 26%),
                    radial-gradient(circle at bottom right, rgba(14, 165, 233, 0.14), transparent 22%),
                    #0b1220;
                color: #e2e8f0;
            }
            section[data-testid="stSidebar"] {
                background: rgba(15, 23, 42, 0.94);
                border-right: 1px solid rgba(148, 163, 184, 0.14);
            }
        }
        </style>
        """
    st.markdown(
        f"""
        <style>
        .stApp {{
            background:
                radial-gradient(circle at top left, rgba(37, 99, 235, 0.16), transparent 26%),
                radial-gradient(circle at bottom right, rgba(14, 165, 233, 0.14), transparent 22%),
                {t['app_bg']};
            color: {t['text_main']};
        }}
        section[data-testid="stSidebar"] {{
            background: {t['sidebar_bg']};
            border-right: 1px solid {t['panel_border']};
        }}
        .sidebar-shell {{
            display: flex;
            flex-direction: column;
            gap: 1rem;
            padding: 0.2rem 0;
        }}
        .sidebar-brand {{
            padding: 1rem 1rem 0.25rem 1rem;
        }}
        .brand-title {{
            font-size: 1.35rem;
            font-weight: 800;
            color: {t['text_main']};
            margin: 0;
        }}
        .brand-subtitle {{
            color: {t['text_muted']};
            font-size: 0.92rem;
            margin-top: 0.25rem;
        }}
        .sidebar-section {{
            padding: 0 1rem;
        }}
        .sidebar-label {{
            font-size: 0.74rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: {t['text_muted']};
            margin-bottom: 0.55rem;
        }}
        .contact-card {{
            display: block;
            width: 100%;
            padding: 0.82rem 0.9rem;
            border-radius: 16px;
            border: 1px solid transparent;
            background: transparent;
            color: {t['text_main']};
            text-align: left;
        }}
        .contact-card:hover {{
            background: {t['accent_soft']};
            border-color: {t['panel_border']};
        }}
        .contact-card.active {{
            background: {t['accent_soft']};
            border-color: {t['accent']};
        }}
        .contact-name {{
            font-weight: 700;
            font-size: 0.98rem;
        }}
        .contact-meta {{
            color: {t['text_muted']};
            font-size: 0.84rem;
        }}
        .app-shell {{
            background: {t['panel_bg']};
            border-radius: 28px;
            padding: 1.25rem;
            border: 1px solid {t['panel_border']};
            box-shadow: {t['shadow']};
            backdrop-filter: blur(18px);
        }}
        .hero-shell {{
            display: flex;
            flex-direction: column;
            gap: 0.35rem;
            margin-bottom: 1rem;
        }}
        .hero-title {{
            margin: 0;
            font-size: 1.55rem;
            font-weight: 800;
        }}
        .hero-subtitle {{
            color: {t['text_muted']};
            margin: 0;
        }}
        .chat-empty {{
            border: 1px dashed {t['panel_border']};
            border-radius: 22px;
            padding: 2rem;
            background: rgba(255, 255, 255, 0.35);
            color: {t['text_main']};
        }}
        .status-pill {{
            display: inline-block;
            padding: 0.25rem 0.65rem;
            border-radius: 999px;
            background: {t['accent_soft']};
            color: {t['accent_text']};
            font-weight: 600;
        }}
        .status-pill.offline {{
            background: rgba(148, 163, 184, 0.12);
            color: {t['text_muted']};
        }}
        .message-card {{
            border-radius: 18px;
            padding: 0.9rem 1rem;
            margin-bottom: 0.75rem;
            border: 1px solid {t['panel_border']};
            background: {t['message_bg']};
        }}
        .message-card.outgoing {{
            background: {t['message_alt']};
            border-color: rgba(37, 99, 235, 0.18);
        }}
        .message-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: 0.35rem;
            color: {t['text_muted']};
            font-size: 0.8rem;
        }}
        .chat-composer {{
            border: 1px solid {t['panel_border']};
            border-radius: 20px;
            padding: 0.75rem;
            background: {t['message_bg']};
            margin-top: 1rem;
        }}
        </style>
        {system_override}
        """,
        unsafe_allow_html=True,
    )


def _initialize_ui_state() -> None:
    """Set default UI state for the dashboard."""

    st.session_state.setdefault("ui_theme", "system")
    st.session_state.setdefault("selected_contact_id", None)
    st.session_state.setdefault("contact_search", "")


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

        with st.expander("Forgot password?", expanded=False):
            with st.form("reset_password_form", clear_on_submit=False):
                reset_email = st.text_input("Email for your account")
                new_password = st.text_input("New password", type="password")
                confirm_password = st.text_input("Confirm new password", type="password")
                reset_submitted = st.form_submit_button("Reset password")
            if reset_submitted:
                try:
                    reset_password_by_email(settings, reset_email, new_password, confirm_password)
                    st.success("Password updated. You can log in with the new password now.")
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


def _render_sidebar(
    settings: Settings,
    current_user: User,
    contacts: list[Contact],
    conversations: list[ConversationPreview],
) -> None:
    """Render the full navigation sidebar."""

    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-shell">
                <div class="sidebar-brand">
                    <p class="brand-title">Chat AI Tool</p>
                    <p class="brand-subtitle">Private conversations, simplified.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
        theme = st.selectbox(
            "Theme",
            options=["system", "light", "dark"],
            index=["system", "light", "dark"].index(st.session_state.ui_theme),
            help="Choose how the interface should look.",
        )
        st.session_state.ui_theme = theme
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
        st.markdown("<div class='sidebar-label'>Search people</div>", unsafe_allow_html=True)
        search_text = st.text_input(
            "Search",
            value=st.session_state.contact_search,
            placeholder="Search by username",
            label_visibility="collapsed",
        )
        st.session_state.contact_search = search_text
        st.markdown("</div>", unsafe_allow_html=True)

        filtered_contacts = [
            contact
            for contact in contacts
            if search_text.lower().strip() in contact.user.username.lower()
        ]

        st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
        st.markdown("<div class='sidebar-label'>Chats</div>", unsafe_allow_html=True)
        if not filtered_contacts:
            st.caption("No matching users found.")
        for contact in filtered_contacts:
            active = st.session_state.selected_contact_id == contact.user.id
            button_label = f"{contact.user.username}"
            button_type = "primary" if active else "secondary"
            if st.button(
                button_label,
                key=f"contact_button_{contact.user.id}",
                use_container_width=True,
                type=button_type,
            ):
                st.session_state.selected_contact_id = contact.user.id
                st.rerun()
            meta = "online" if is_online(contact.last_seen_at) else "offline"
            st.caption(meta)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
        st.markdown("<div class='sidebar-label'>Recent activity</div>", unsafe_allow_html=True)
        if conversations:
            for preview in conversations[:5]:
                st.caption(f"{preview.other_user.username} - {preview.last_message_preview}")
        else:
            st.caption("No recent chats yet.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
        st.markdown("<div class='sidebar-label'>Account</div>", unsafe_allow_html=True)
        st.markdown(f"**{current_user.username}**")
        st.markdown("<span class='status-pill'>Signed in</span>", unsafe_allow_html=True)
        if st.button("Logout", use_container_width=True):
            logout_user(settings)
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
        st.markdown("<div class='sidebar-label'>Security</div>", unsafe_allow_html=True)
        with st.form("change_password_form", clear_on_submit=False):
            current_password = st.text_input("Current password", type="password")
            new_password = st.text_input("New password", type="password", key="dashboard_new_password")
            confirm_password = st.text_input(
                "Confirm new password",
                type="password",
                key="dashboard_confirm_password",
            )
            change_submitted = st.form_submit_button("Change password")
        if change_submitted:
            try:
                change_password(
                    settings,
                    current_user.id,
                    current_password,
                    new_password,
                    confirm_password,
                )
                st.success("Password changed successfully. Please log in again.")
                logout_user(settings)
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
        st.markdown("</div>", unsafe_allow_html=True)


def _render_chat_thread(
    settings: Settings,
    current_user: User,
    contact: Contact,
) -> None:
    """Render the selected private thread."""

    thread_messages = get_thread_messages(settings, current_user.id, contact.user.id)
    status_text = "online" if is_online(contact.last_seen_at) else "offline"
    st.markdown(
        f"""
        <div class="hero-shell">
            <p class="hero-title">{contact.user.username}</p>
            <p class="hero-subtitle">{status_text}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="app-shell">', unsafe_allow_html=True)
    if not thread_messages:
        st.markdown(
            """
            <div class="chat-empty">
                <strong>Start the conversation</strong>
                <p style="margin-bottom: 0; color: var(--text-muted);">
                    Send your first message. The chat area stays clean and focused like a modern messenger app.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        for message in thread_messages:
            outgoing = message.sender_id == current_user.id
            card_class = "message-card outgoing" if outgoing else "message-card"
            st.markdown(
                f"""
                <div class="{card_class}">
                    <div class="message-header">
                        <span>{message.sender_username}</span>
                        <span>{message.created_at}</span>
                    </div>
                    <div>{message.content}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="chat-composer">', unsafe_allow_html=True)
    prompt = st.chat_input(f"Message {contact.user.username}")
    if prompt:
        send_message(settings, current_user.id, contact.user.id, prompt)
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    with st.expander("AI reply helper", expanded=False):
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

    _initialize_ui_state()

    if current_user is None:
        _apply_styles("system")
        _render_auth_tabs(settings)
        return

    contacts = get_contacts(settings, current_user.id)
    conversations = get_conversations(settings, current_user.id)

    _apply_styles(st.session_state.ui_theme)
    _render_sidebar(settings, current_user, contacts, conversations)

    active_contact = next(
        (contact for contact in contacts if contact.user.id == st.session_state.selected_contact_id),
        None,
    )

    if active_contact is None:
        st.markdown(
            """
            <div class="app-shell">
                <div class="hero-shell">
                    <p class="hero-title">Welcome back</p>
                    <p class="hero-subtitle">Choose a person from the sidebar to open the chat.</p>
                </div>
                <div class="chat-empty">
                    Your conversations will appear here once you select a user.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    _render_chat_thread(settings, current_user, active_contact)



