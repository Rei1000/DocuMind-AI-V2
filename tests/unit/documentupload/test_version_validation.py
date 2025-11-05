"""
Unit Tests für Document Version Validation.

Test-Driven Development: RED Phase für Version-Prüfung und Warnungen.
"""

import pytest
from contexts.documentupload.domain.value_objects import DocumentMetadata


class TestVersionValidation:
    """Tests für Version Validation."""
    
    def test_metadata_validates_version_format(self):
        """DocumentMetadata validiert Versions-Format"""
        # Arrange & Act
        metadata = DocumentMetadata(
            filename="test.pdf",
            original_filename="test.pdf",
            qm_chapter="1.2",
            version="v1.0.0"
        )
        
        # Assert
        assert metadata.version == "v1.0.0"
    
    def test_metadata_accepts_various_version_formats(self):
        """DocumentMetadata akzeptiert verschiedene Versions-Formate"""
        # Arrange & Act
        test_cases = [
            "v1.0",
            "v1.0.0",
            "v2.1.3",
            "1.0",
            "1.0.0",
            "v2.0"
        ]
        
        for version in test_cases:
            metadata = DocumentMetadata(
                filename="test.pdf",
                original_filename="test.pdf",
                qm_chapter="1.2",
                version=version
            )
            assert metadata.version == version
    
    def test_metadata_version_optional(self):
        """Version ist optional in DocumentMetadata"""
        # Arrange & Act
        metadata = DocumentMetadata(
            filename="test.pdf",
            original_filename="test.pdf",
            qm_chapter="1.2",
            version=None
        )
        
        # Assert
        assert metadata.version is None

