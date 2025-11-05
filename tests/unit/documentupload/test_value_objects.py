"""
Unit Tests für Value Objects im Document Upload Context.

Test-Driven Development: RED Phase für FileHash Value Object.
"""

import pytest
from contexts.documentupload.domain.value_objects import FileHash


class TestFileHash:
    """Tests für FileHash Value Object."""
    
    def test_file_hash_valid_sha256(self):
        """Valider SHA-256 Hash wird akzeptiert"""
        # Arrange
        valid_hash = "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3"
        
        # Act
        file_hash = FileHash(valid_hash)
        
        # Assert
        assert file_hash.value == valid_hash
    
    def test_file_hash_valid_sha256_uppercase(self):
        """SHA-256 Hash mit Großbuchstaben wird akzeptiert (wird in lowercase konvertiert)"""
        # Arrange
        valid_hash_upper = "A665A45920422F9D417E4867EFDC4FB8A04A1F3FFF1FA07E998E86F7F7A27AE3"
        expected_lower = valid_hash_upper.lower()
        
        # Act
        file_hash = FileHash(valid_hash_upper)
        
        # Assert
        assert file_hash.value == expected_lower
    
    def test_file_hash_invalid_format_raises_error(self):
        """Ungültiger Hash-Format wirft ValueError"""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="Invalid SHA-256 hash format"):
            FileHash("not-a-valid-hash")
    
    def test_file_hash_empty_string_raises_error(self):
        """Leerer String wirft ValueError"""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="Invalid SHA-256 hash format"):
            FileHash("")
    
    def test_file_hash_too_short_raises_error(self):
        """Zu kurzer Hash (nicht 64 Zeichen) wirft ValueError"""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="Invalid SHA-256 hash format"):
            FileHash("abc123")  # Nur 6 Zeichen
    
    def test_file_hash_too_long_raises_error(self):
        """Zu langer Hash (mehr als 64 Zeichen) wirft ValueError"""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="Invalid SHA-256 hash format"):
            FileHash("a" * 65)  # 65 Zeichen
    
    def test_file_hash_invalid_characters_raises_error(self):
        """Hash mit ungültigen Zeichen (nicht hex) wirft ValueError"""
        # Arrange & Act & Assert
        invalid_hash = "a" * 63 + "X"  # X ist nicht hexadezimal
        with pytest.raises(ValueError, match="Invalid SHA-256 hash format"):
            FileHash(invalid_hash)
    
    def test_file_hash_not_string_raises_error(self):
        """Non-String Input wirft ValueError"""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="FileHash value must be a string"):
            FileHash(12345)  # Integer statt String
    
    def test_file_hash_is_immutable(self):
        """FileHash ist immutable (frozen dataclass)"""
        # Arrange
        file_hash = FileHash("a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3")
        
        # Act & Assert
        with pytest.raises(Exception):  # frozen dataclass wirft Exception bei Änderung
            file_hash.value = "new_value"
    
    def test_file_hash_real_world_example(self):
        """Real-world SHA-256 Hash Beispiel"""
        # Arrange: Hash von "Hello World"
        real_hash = "64ec88ca00b268e5ba1a35678a1b5316d212f4f366b2477232534a8aeca37f3c"
        
        # Act
        file_hash = FileHash(real_hash)
        
        # Assert
        assert file_hash.value == real_hash.lower()

