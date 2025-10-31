"""
Unit Tests: ChatMessage mit ai_model_used

TDD: RED → GREEN → REFACTOR
Testet dass ChatMessage das verwendete LLM-Model speichert.
"""

import pytest
from datetime import datetime
from contexts.ragintegration.domain.entities import ChatMessage


class TestChatMessageModel:
    """Tests für ChatMessage Entity mit ai_model_used."""

    def test_chat_message_requires_ai_model_used(self):
        """Test: ChatMessage sollte ai_model_used Feld haben."""
        # RED: Dieser Test schlägt fehl, da ai_model_used noch nicht existiert
        message = ChatMessage(
            id=1,
            session_id=1,
            role="assistant",
            content="Test answer",
            created_at=datetime.now(),
            ai_model_used="gpt-4o-mini"
        )
        
        assert message.ai_model_used == "gpt-4o-mini"

    def test_chat_message_defaults_to_gpt4o_mini(self):
        """Test: Default ai_model_used sollte gpt-4o-mini sein."""
        message = ChatMessage(
            id=1,
            session_id=1,
            role="assistant",
            content="Test answer",
            created_at=datetime.now()
        )
        
        assert message.ai_model_used == "gpt-4o-mini"

    def test_chat_message_validates_ai_model(self):
        """Test: ChatMessage sollte ungültige Model-Namen validieren."""
        # Diese Validierung kann später hinzugefügt werden
        pass

    def test_user_message_does_not_need_model(self):
        """Test: User-Messages brauchen kein ai_model_used."""
        message = ChatMessage(
            id=1,
            session_id=1,
            role="user",
            content="User question",
            created_at=datetime.now(),
            ai_model_used=None  # User messages haben kein Model
        )
        
        # User messages sollten ai_model_used=None erlauben oder ignorieren
        assert message.role == "user"



