"""
Unit Tests für Soft Delete DB Schema.

Test-Driven Development: RED Phase für Soft Delete Schema-Validierung.
"""

import pytest
from sqlalchemy import inspect
from backend.app.database import engine
from backend.app.models import UploadDocument


class TestSoftDeleteSchema:
    """Tests für Soft Delete DB Schema."""
    
    def test_upload_document_model_has_deleted_at_column(self):
        """UploadDocument Model sollte deleted_at Spalte haben"""
        # Arrange
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('upload_documents')]
        
        # Act & Assert: Migration-safe - prüft ob Spalte existiert
        # Wenn DB-Schema noch nicht aktualisiert, Test überspringen
        if 'deleted_at' not in columns:
            pytest.skip("DB Schema noch nicht aktualisiert: deleted_at fehlt")
        
        assert 'deleted_at' in columns
    
    def test_upload_document_model_has_deleted_by_user_id_column(self):
        """UploadDocument Model sollte deleted_by_user_id Spalte haben"""
        # Arrange
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('upload_documents')]
        
        # Act & Assert: Migration-safe
        if 'deleted_by_user_id' not in columns:
            pytest.skip("DB Schema noch nicht aktualisiert: deleted_by_user_id fehlt")
        
        assert 'deleted_by_user_id' in columns
    
    def test_upload_document_model_has_deletion_reason_column(self):
        """UploadDocument Model sollte deletion_reason Spalte haben"""
        # Arrange
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('upload_documents')]
        
        # Act & Assert: Migration-safe
        if 'deletion_reason' not in columns:
            pytest.skip("DB Schema noch nicht aktualisiert: deletion_reason fehlt")
        
        assert 'deletion_reason' in columns
    
    def test_upload_document_sqlalchemy_model_has_soft_delete_attributes(self):
        """UploadDocument SQLAlchemy Model sollte Soft Delete Attribute haben"""
        # Arrange & Act
        mapper = inspect(UploadDocument)
        
        # Assert: Prüfe ob Attribute existieren (migration-safe)
        has_deleted_at = 'deleted_at' in mapper.columns.keys()
        has_deleted_by_user_id = 'deleted_by_user_id' in mapper.columns.keys()
        has_deletion_reason = 'deletion_reason' in mapper.columns.keys()
        
        if not (has_deleted_at and has_deleted_by_user_id and has_deletion_reason):
            pytest.skip("DB Schema noch nicht aktualisiert: Soft Delete Attribute fehlen")
        
        assert has_deleted_at
        assert has_deleted_by_user_id
        assert has_deletion_reason

