"""Streamlit entry point for the chat_Ai_Tool application."""

from __future__ import annotations

import streamlit as st

from src.chat_ai_tool.config import get_settings
from src.chat_ai_tool.database import initialize_database
from src.chat_ai_tool.services.auth_service import restore_session
from src.chat_ai_tool.ui.pages import render_app


def main() -> None:
    """Boot the app and render the correct screen."""

    settings = get_settings()

    st.set_page_config(
        page_title=settings.app_name,
        page_icon="Chat",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    initialize_database(settings)
    current_user = restore_session(settings)
    render_app(settings, current_user)


if __name__ == "__main__":
    main()
