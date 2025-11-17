"""
Tests für QDRANT_URL Resolution (Fix 1).

TDD Phase 1: RED - Tests für Environment-Variable-basierte Qdrant-URL.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock


class TestQdrantURLResolution:
    """Tests für QDRANT_URL Resolution in QdrantVectorStoreAdapter."""
    
    def test_qdrant_url_default_when_env_not_set(self):
        """
        Test: Default localhost:6333 wenn QDRANT_URL nicht gesetzt.
        
        RED → GREEN → REFACTOR
        """
        from contexts.ragintegration.infrastructure.vector_store_adapter import (
            QdrantVectorStoreAdapter
        )
        
        # Arrange: Keine Environment-Variable
        with patch.dict(os.environ, {}, clear=True):
            with patch('contexts.ragintegration.infrastructure.vector_store_adapter.QdrantClient') as mock_client_class:
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                mock_client.get_collections.return_value = MagicMock(collections=[])
                
                # Act: Erstelle Adapter
                adapter = QdrantVectorStoreAdapter(collection_name="test_collection")
                
                # Assert: QdrantClient wurde mit localhost:6333 aufgerufen
                mock_client_class.assert_called_once()
                call_args = mock_client_class.call_args
                assert call_args[1]['host'] == 'localhost', "Host sollte 'localhost' sein"
                assert call_args[1]['port'] == 6333, "Port sollte 6333 sein"
    
    def test_qdrant_url_host_port_format(self):
        """
        Test: QDRANT_URL=qdrant:6333 Format.
        
        RED → GREEN → REFACTOR
        """
        from contexts.ragintegration.infrastructure.vector_store_adapter import (
            QdrantVectorStoreAdapter
        )
        
        # Arrange: QDRANT_URL als Host:Port
        with patch.dict(os.environ, {'QDRANT_URL': 'qdrant:6333'}, clear=False):
            with patch('contexts.ragintegration.infrastructure.vector_store_adapter.QdrantClient') as mock_client_class:
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                mock_client.get_collections.return_value = MagicMock(collections=[])
                
                # Act: Erstelle Adapter
                adapter = QdrantVectorStoreAdapter(collection_name="test_collection")
                
                # Assert: QdrantClient wurde mit qdrant:6333 aufgerufen
                mock_client_class.assert_called_once()
                call_args = mock_client_class.call_args
                assert call_args[1]['host'] == 'qdrant', "Host sollte 'qdrant' sein"
                assert call_args[1]['port'] == 6333, "Port sollte 6333 sein"
    
    def test_qdrant_url_http_format(self):
        """
        Test: QDRANT_URL=http://qdrant:6333 Format.
        
        RED → GREEN → REFACTOR
        """
        from contexts.ragintegration.infrastructure.vector_store_adapter import (
            QdrantVectorStoreAdapter
        )
        
        # Arrange: QDRANT_URL als HTTP-URL
        with patch.dict(os.environ, {'QDRANT_URL': 'http://qdrant:6333'}, clear=False):
            with patch('contexts.ragintegration.infrastructure.vector_store_adapter.QdrantClient') as mock_client_class:
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                mock_client.get_collections.return_value = MagicMock(collections=[])
                
                # Act: Erstelle Adapter
                adapter = QdrantVectorStoreAdapter(collection_name="test_collection")
                
                # Assert: QdrantClient wurde mit qdrant:6333 aufgerufen
                mock_client_class.assert_called_once()
                call_args = mock_client_class.call_args
                assert call_args[1]['host'] == 'qdrant', "Host sollte 'qdrant' sein"
                assert call_args[1]['port'] == 6333, "Port sollte 6333 sein"
    
    def test_qdrant_url_https_format(self):
        """
        Test: QDRANT_URL=https://qdrant:6333 Format.
        
        RED → GREEN → REFACTOR
        """
        from contexts.ragintegration.infrastructure.vector_store_adapter import (
            QdrantVectorStoreAdapter
        )
        
        # Arrange: QDRANT_URL als HTTPS-URL
        with patch.dict(os.environ, {'QDRANT_URL': 'https://qdrant:6333'}, clear=False):
            with patch('contexts.ragintegration.infrastructure.vector_store_adapter.QdrantClient') as mock_client_class:
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                mock_client.get_collections.return_value = MagicMock(collections=[])
                
                # Act: Erstelle Adapter
                adapter = QdrantVectorStoreAdapter(collection_name="test_collection")
                
                # Assert: QdrantClient wurde mit qdrant:6333 aufgerufen
                mock_client_class.assert_called_once()
                call_args = mock_client_class.call_args
                assert call_args[1]['host'] == 'qdrant', "Host sollte 'qdrant' sein"
                assert call_args[1]['port'] == 6333, "Port sollte 6333 sein"
    
    def test_qdrant_url_custom_port(self):
        """
        Test: QDRANT_URL mit custom Port.
        
        RED → GREEN → REFACTOR
        """
        from contexts.ragintegration.infrastructure.vector_store_adapter import (
            QdrantVectorStoreAdapter
        )
        
        # Arrange: QDRANT_URL mit custom Port
        with patch.dict(os.environ, {'QDRANT_URL': 'localhost:6334'}, clear=False):
            with patch('contexts.ragintegration.infrastructure.vector_store_adapter.QdrantClient') as mock_client_class:
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                mock_client.get_collections.return_value = MagicMock(collections=[])
                
                # Act: Erstelle Adapter
                adapter = QdrantVectorStoreAdapter(collection_name="test_collection")
                
                # Assert: QdrantClient wurde mit localhost:6334 aufgerufen
                mock_client_class.assert_called_once()
                call_args = mock_client_class.call_args
                assert call_args[1]['host'] == 'localhost', "Host sollte 'localhost' sein"
                assert call_args[1]['port'] == 6334, "Port sollte 6334 sein"
    
    def test_qdrant_url_no_hardcoded_localhost(self):
        """
        Test: Keine Hardcodings von localhost oder 6333 im Code.
        
        RED → GREEN → REFACTOR
        """
        import inspect
        from contexts.ragintegration.infrastructure.vector_store_adapter import (
            QdrantVectorStoreAdapter
        )
        
        # Arrange: Lese Source-Code
        source = inspect.getsource(QdrantVectorStoreAdapter.__init__)
        
        # Assert: Keine Hardcodings (außer als Default-Wert)
        # Erlaubt: "localhost" oder "6333" als Default in os.getenv()
        # Nicht erlaubt: QdrantClient(host="localhost", port=6333) direkt
        
        # Prüfe ob QdrantClient direkt mit hardcoded Werten aufgerufen wird
        has_hardcoded_call = 'QdrantClient(host="localhost"' in source or \
                             'QdrantClient(host=\'localhost\'' in source
        
        assert not has_hardcoded_call, \
            "QdrantClient sollte nicht mit hardcoded 'localhost' aufgerufen werden. Verwende QDRANT_URL Environment-Variable."

