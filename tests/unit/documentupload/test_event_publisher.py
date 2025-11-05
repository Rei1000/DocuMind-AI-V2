"""
Unit Tests für InMemoryEventPublisher.

Test-Driven Development: RED Phase für Event Publisher Implementation.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from contexts.documentupload.infrastructure.event_publisher import InMemoryEventPublisher
from contexts.documentupload.domain.events import DocumentRejectedEvent


class TestInMemoryEventPublisher:
    """Tests für InMemoryEventPublisher."""
    
    @pytest.fixture
    def publisher(self):
        """InMemoryEventPublisher Instanz."""
        return InMemoryEventPublisher()
    
    @pytest.fixture
    def mock_handler(self):
        """Mock Event Handler."""
        handler = Mock()
        handler.handle = AsyncMock()
        return handler
    
    @pytest.mark.asyncio
    async def test_publish_calls_registered_handler(self, publisher, mock_handler):
        """Publish ruft registrierten Handler auf"""
        # Arrange
        event = DocumentRejectedEvent(
            document_id=1,
            rejected_by_user_id=2,
            rejection_reason="Incomplete",
            timestamp=datetime.utcnow()
        )
        publisher.subscribe(DocumentRejectedEvent, mock_handler)
        
        # Act
        await publisher.publish(event)
        
        # Assert
        mock_handler.handle.assert_called_once_with(event)
    
    @pytest.mark.asyncio
    async def test_publish_calls_multiple_handlers(self, publisher):
        """Publish ruft mehrere registrierte Handler auf"""
        # Arrange
        handler1 = Mock()
        handler1.handle = AsyncMock()
        handler2 = Mock()
        handler2.handle = AsyncMock()
        
        event = DocumentRejectedEvent(
            document_id=1,
            rejected_by_user_id=2,
            rejection_reason="Incomplete",
            timestamp=datetime.utcnow()
        )
        publisher.subscribe(DocumentRejectedEvent, handler1)
        publisher.subscribe(DocumentRejectedEvent, handler2)
        
        # Act
        await publisher.publish(event)
        
        # Assert
        handler1.handle.assert_called_once_with(event)
        handler2.handle.assert_called_once_with(event)
    
    @pytest.mark.asyncio
    async def test_publish_without_handlers_does_nothing(self, publisher):
        """Publish ohne Handler tut nichts (kein Fehler)"""
        # Arrange
        event = DocumentRejectedEvent(
            document_id=1,
            rejected_by_user_id=2,
            rejection_reason="Incomplete",
            timestamp=datetime.utcnow()
        )
        # Kein Handler registriert
        
        # Act & Assert: Sollte ohne Fehler funktionieren
        await publisher.publish(event)
    
    @pytest.mark.asyncio
    async def test_publish_isolates_handler_errors(self, publisher):
        """Publish isoliert Handler-Fehler (ein Fehler blockiert andere Handler nicht)"""
        # Arrange
        failing_handler = Mock()
        failing_handler.handle = AsyncMock(side_effect=Exception("Handler error"))
        
        working_handler = Mock()
        working_handler.handle = AsyncMock()
        
        event = DocumentRejectedEvent(
            document_id=1,
            rejected_by_user_id=2,
            rejection_reason="Incomplete",
            timestamp=datetime.utcnow()
        )
        publisher.subscribe(DocumentRejectedEvent, failing_handler)
        publisher.subscribe(DocumentRejectedEvent, working_handler)
        
        # Act: Sollte nicht abstürzen
        await publisher.publish(event)
        
        # Assert: Beide Handler wurden aufgerufen (auch wenn einer fehlschlug)
        failing_handler.handle.assert_called_once()
        working_handler.handle.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_subscribe_multiple_times_same_handler(self, publisher, mock_handler):
        """Subscribe mit gleichem Handler mehrfach registriert Handler mehrfach"""
        # Arrange
        event = DocumentRejectedEvent(
            document_id=1,
            rejected_by_user_id=2,
            rejection_reason="Incomplete",
            timestamp=datetime.utcnow()
        )
        publisher.subscribe(DocumentRejectedEvent, mock_handler)
        publisher.subscribe(DocumentRejectedEvent, mock_handler)
        
        # Act
        await publisher.publish(event)
        
        # Assert: Handler sollte zweimal aufgerufen werden
        assert mock_handler.handle.call_count == 2
    
    def test_subscribe_different_event_types(self, publisher):
        """Subscribe für verschiedene Event-Typen funktioniert"""
        # Arrange
        handler1 = Mock()
        handler2 = Mock()
        
        from contexts.documentupload.domain.events import (
            DocumentRejectedEvent,
            DocumentDeletedEvent
        )
        
        # Act
        publisher.subscribe(DocumentRejectedEvent, handler1)
        publisher.subscribe(DocumentDeletedEvent, handler2)
        
        # Assert: Keine Fehler
        assert DocumentRejectedEvent in publisher._handlers
        assert DocumentDeletedEvent in publisher._handlers

