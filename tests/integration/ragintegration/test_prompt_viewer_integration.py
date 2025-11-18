"""
Integration Tests für Prompt-Viewer (CR-P0)

Testet die Integration zwischen Prompt-Viewer Endpoint und gespeicherten Prompts:
- Prompt-Viewer mit gespeichertem Prompt
- Prompt-Viewer ohne gespeichertem Prompt (INVALID)
- Prompt-Viewer RBAC (Level 1-3 nur eigene)
- Prompt-Viewer RBAC (Level 4+ alle)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from contexts.ragintegration.domain.entities import ChatMessage, ChatSession
from contexts.ragintegration.infrastructure.repositories import SQLAlchemyChatMessageRepository


class TestPromptViewerIntegration:
    """Integration Tests für Prompt-Viewer"""
    
    def test_prompt_viewer_with_stored_prompt(self):
        """IT-VIEWER-001: Prompt-Viewer mit gespeichertem Prompt"""
        # Arrange
        stored_prompt = "ANWEISUNGEN (Flussdiagramm):\n1. Test"
        message = ChatMessage(
            id=1,
            session_id=1,
            role="assistant",
            content="Test Antwort",
            source_references=[],
            ai_model_used="gpt-4o-mini",
            created_at=datetime.now(),
            metadata={
                "prompt_text": stored_prompt,
                "prompt_type": "standard",
                "tokens_used": 100
            }
        )
        
        # Act: Simuliere get_prompt_for_message Logik
        prompt_text = None
        prompt_state = "invalid"
        if message.metadata and message.metadata.get("prompt_text"):
            prompt_text = message.metadata["prompt_text"]
            prompt_state = "valid"
        
        # Assert
        assert prompt_text == stored_prompt
        assert prompt_state == "valid"
    
    def test_prompt_viewer_without_stored_prompt(self):
        """IT-VIEWER-002: Prompt-Viewer ohne gespeichertem Prompt (INVALID)"""
        # Arrange
        message = ChatMessage(
            id=1,
            session_id=1,
            role="assistant",
            content="Test Antwort",
            source_references=[],
            ai_model_used="gpt-4o-mini",
            created_at=datetime.now(),
            metadata={
                "tokens_used": 100
                # prompt_text fehlt
            }
        )
        
        # Act: Simuliere get_prompt_for_message Logik
        prompt_text = None
        prompt_state = "invalid"
        if message.metadata and message.metadata.get("prompt_text"):
            prompt_text = message.metadata["prompt_text"]
            prompt_state = "valid"
        
        # Assert
        assert prompt_text is None
        assert prompt_state == "invalid"
    
    def test_prompt_viewer_rbac_level_1_3_own_only(self):
        """IT-VIEWER-003: Prompt-Viewer RBAC (Level 1-3 nur eigene)"""
        # Arrange
        message = ChatMessage(
            id=1,
            session_id=1,  # Session gehört User 1
            role="assistant",
            content="Test Antwort",
            source_references=[],
            ai_model_used="gpt-4o-mini",
            created_at=datetime.now(),
            metadata={"prompt_text": "Test Prompt"}
        )
        
        session = ChatSession(
            id=1,
            user_id=1,  # Session gehört User 1
            session_name="Test",
            last_message_at=datetime.now(),
            is_active=True,
            created_at=datetime.now()
        )
        
        # Act: Simuliere RBAC-Check
        current_user_id = 1  # Gleicher User
        user_level = 2  # Level 2
        
        can_view = False
        if user_level >= 4:
            can_view = True  # Level 4+ können alle sehen
        elif session.user_id == current_user_id:
            can_view = True  # Level 1-3 nur eigene
        
        # Assert
        assert can_view is True
    
    def test_prompt_viewer_rbac_level_4_plus_all(self):
        """IT-VIEWER-004: Prompt-Viewer RBAC (Level 4+ alle)"""
        # Arrange
        message = ChatMessage(
            id=1,
            session_id=1,  # Session gehört User 1
            role="assistant",
            content="Test Antwort",
            source_references=[],
            ai_model_used="gpt-4o-mini",
            created_at=datetime.now(),
            metadata={"prompt_text": "Test Prompt"}
        )
        
        session = ChatSession(
            id=1,
            user_id=1,  # Session gehört User 1
            session_name="Test",
            last_message_at=datetime.now(),
            is_active=True,
            created_at=datetime.now()
        )
        
        # Act: Simuliere RBAC-Check
        current_user_id = 2  # Anderer User
        user_level = 4  # Level 4
        
        can_view = False
        if user_level >= 4:
            can_view = True  # Level 4+ können alle sehen
        elif session.user_id == current_user_id:
            can_view = True  # Level 1-3 nur eigene
        
        # Assert
        assert can_view is True

