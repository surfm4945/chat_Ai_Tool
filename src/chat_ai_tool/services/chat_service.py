"""Private messaging helpers."""

from __future__ import annotations

from src.chat_ai_tool.config import Settings
from src.chat_ai_tool.database import database_session
from src.chat_ai_tool.models import ConversationPreview, Contact, MessageView
from src.chat_ai_tool.repositories import (
    add_message,
    get_or_create_conversation,
    list_conversations,
    list_contacts,
    list_message_dicts_for_ai,
    list_messages,
)


def get_contacts(settings: Settings, current_user_id: int) -> list[Contact]:
    """Return all other registered users."""

    with database_session(settings) as connection:
        return list_contacts(connection, current_user_id)


def get_conversations(settings: Settings, current_user_id: int) -> list[ConversationPreview]:
    """Return the current user's conversation list."""

    with database_session(settings) as connection:
        return list_conversations(connection, current_user_id)


def send_message(
    settings: Settings,
    sender_id: int,
    recipient_id: int,
    content: str,
) -> MessageView:
    """Send a private message to another user."""

    cleaned_content = content.strip()
    if not cleaned_content:
        raise ValueError("Message cannot be empty.")

    with database_session(settings) as connection:
        conversation_id = get_or_create_conversation(connection, sender_id, recipient_id)
        return add_message(
            connection,
            conversation_id=conversation_id,
            sender_id=sender_id,
            role="user",
            content=cleaned_content,
        )


def get_thread_messages(
    settings: Settings,
    current_user_id: int,
    other_user_id: int,
) -> list[MessageView]:
    """Load the chat history for a one-to-one conversation."""

    with database_session(settings) as connection:
        conversation_id = get_or_create_conversation(connection, current_user_id, other_user_id)
        return list_messages(connection, conversation_id)


def get_ai_context_messages(
    settings: Settings,
    current_user_id: int,
    other_user_id: int,
    limit: int = 12,
) -> list[dict[str, str]]:
    """Return recent messages for the Gemini helper."""

    with database_session(settings) as connection:
        conversation_id = get_or_create_conversation(connection, current_user_id, other_user_id)
        return list_message_dicts_for_ai(connection, conversation_id, limit=limit)
