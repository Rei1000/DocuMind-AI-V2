"""
Integration Tests: Verschiedene LLM-Models pro Nachricht in einer Session

TDD: RED → GREEN → REFACTOR
Testet dass verschiedene Models in einer Chat-Session verwendet werden können
und korrekt pro Nachricht gespeichert werden.
"""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from contexts.ragintegration.domain.entities import ChatMessage, ChatSession
from contexts.ragintegration.infrastructure.repositories import (
    SQLAlchemyChatSessionRepository,
    SQLAlchemyChatMessageRepository
)
from backend.app.database import SessionLocal


class TestModelPerMessage:
    """Integration Tests für verschiedene Models pro Nachricht."""

    @pytest.fixture
    def db_session(self):
        """Erstelle DB Session für Tests."""
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    @pytest.fixture
    def test_session(self, db_session: Session):
        """Erstelle Test-Session."""
        session_repo = SQLAlchemyChatSessionRepository(db_session)
        chat_session = ChatSession(
            id=None,
            user_id=1,
            session_name="Test Session",
            created_at=datetime.now(),
            last_message_at=None,
            is_active=True
        )
        saved_session = session_repo.save(chat_session)
        return saved_session

    def test_different_models_in_same_session(self, db_session: Session, test_session: ChatSession):
        """Test: Verschiedene Models können in derselben Session verwendet werden."""
        message_repo = SQLAlchemyChatMessageRepository(db_session)
        
        # Message 1 mit GPT-4o Mini
        message1 = ChatMessage(
            id=None,
            session_id=test_session.id,
            role="assistant",
            content="Answer from GPT-4o Mini",
            created_at=datetime.now(),
            ai_model_used="gpt-4o-mini"
        )
        saved1 = message_repo.save(message1)
        
        # Message 2 mit Gemini
        message2 = ChatMessage(
            id=None,
            session_id=test_session.id,
            role="assistant",
            content="Answer from Gemini",
            created_at=datetime.now(),
            ai_model_used="gemini-2.5-flash"
        )
        saved2 = message_repo.save(message2)
        
        # Lade Messages zurück
        loaded_messages = message_repo.get_by_session_id(test_session.id)
        
        # Prüfe dass beide Messages korrekte Model-Info haben
        assert len(loaded_messages) == 2
        
        gpt_message = next(m for m in loaded_messages if m.ai_model_used == "gpt-4o-mini")
        gemini_message = next(m for m in loaded_messages if m.ai_model_used == "gemini-2.5-flash")
        
        assert gpt_message is not None
        assert gemini_message is not None
        assert gpt_message.content == "Answer from GPT-4o Mini"
        assert gemini_message.content == "Answer from Gemini"

    def test_model_persistence_across_reload(self, db_session: Session, test_session: ChatSession):
        """Test: Model-Info bleibt nach Reload erhalten."""
        message_repo = SQLAlchemyChatMessageRepository(db_session)
        
        # Erstelle Message mit spezifischem Model
        message = ChatMessage(
            id=None,
            session_id=test_session.id,
            role="assistant",
            content="Test answer",
            created_at=datetime.now(),
            ai_model_used="gpt-5-mini"
        )
        saved = message_repo.save(message)
        
        # Lade Message neu
        reloaded = message_repo.get_by_id(saved.id)
        
        assert reloaded is not None
        assert reloaded.ai_model_used == "gpt-5-mini"



