# 🧪 Document Lifecycle Management - TDD Implementierungsplan

> **Status:** Phase 1 - Foundation  
> **Stand:** 2025-11-02  
> **Version:** 1.0  
> **Methode:** Test-Driven Development (RED → GREEN → REFACTOR)  
> **Context:** `documentupload` (Bounded Context)

---

## 🎯 Übersicht

Dieser Plan beschreibt die schrittweise TDD-Implementierung des Document Lifecycle Management Systems gemäß `docs/DOCUMENT_LIFECYCLE_PROPOSAL.md`.

**Prinzip:** Jede Phase folgt dem TDD-Workflow:
1. **RED:** Tests schreiben (sie schlagen fehl)
2. **GREEN:** Code implementieren (Tests werden grün)
3. **REFACTOR:** Code optimieren (Tests bleiben grün)

---

## 📋 Phase 1: Foundation (Kritisch)

**Ziel:** Basis-Funktionalitäten für Document Lifecycle Management implementieren.

### **1.1 File Hash Implementation (SHA-256)**

**Ziel:** SHA-256 Hash für jedes hochgeladene Dokument berechnen und speichern.

#### **1.1.1 RED: Value Object Tests**

**Datei:** `tests/unit/documentupload/test_value_objects.py` (neu/erweitern)

```python
import pytest
from contexts.documentupload.domain.value_objects import FileHash

def test_file_hash_valid_sha256():
    """Valider SHA-256 Hash wird akzeptiert"""
    # Arrange
    valid_hash = "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3"
    
    # Act
    file_hash = FileHash(valid_hash)
    
    # Assert
    assert file_hash.value == valid_hash

def test_file_hash_invalid_format_raises_error():
    """Ungültiger Hash-Format wirft ValueError"""
    # Arrange & Act & Assert
    with pytest.raises(ValueError, match="Invalid SHA-256 hash format"):
        FileHash("not-a-valid-hash")

def test_file_hash_empty_string_raises_error():
    """Leerer String wirft ValueError"""
    with pytest.raises(ValueError, match="Invalid SHA-256 hash format"):
        FileHash("")

def test_file_hash_too_short_raises_error():
    """Zu kurzer Hash (nicht 64 Zeichen) wirft ValueError"""
    with pytest.raises(ValueError, match="Invalid SHA-256 hash format"):
        FileHash("abc123")

def test_file_hash_invalid_characters_raises_error():
    """Hash mit ungültigen Zeichen (nicht hex) wirft ValueError"""
    with pytest.raises(ValueError, match="Invalid SHA-256 hash format"):
        FileHash("a" * 64 + "X")  # X ist nicht hex
```

#### **1.1.2 GREEN: Value Object Implementation**

**Datei:** `contexts/documentupload/domain/value_objects.py`

```python
import re
from dataclasses import dataclass

@dataclass(frozen=True)
class FileHash:
    """
    SHA-256 Hash einer Datei.
    
    Value Object für Datei-Hash (unveränderlich).
    Validiert SHA-256 Format (64 hexadezimale Zeichen).
    
    Attributes:
        value: SHA-256 Hash als String (64 hex Zeichen)
    """
    value: str
    
    def __post_init__(self):
        """Validiere Hash-Format nach Initialisierung."""
        if not isinstance(self.value, str):
            raise ValueError("FileHash value must be a string")
        
        # SHA-256: 64 hexadezimale Zeichen (a-f0-9)
        if not re.match(r'^[a-f0-9]{64}$', self.value.lower()):
            raise ValueError("Invalid SHA-256 hash format")
```

#### **1.1.3 RED: Entity Tests**

**Datei:** `tests/unit/documentupload/test_entities.py` (erweitern)

```python
import pytest
from contexts.documentupload.domain.entities import UploadedDocument
from contexts.documentupload.domain.value_objects import FileHash, FileType, DocumentMetadata, FilePath, ProcessingMethod, ProcessingStatus, WorkflowStatus
from datetime import datetime

def test_uploaded_document_with_file_hash():
    """UploadedDocument kann mit FileHash erstellt werden"""
    # Arrange
    file_hash = FileHash("a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3")
    metadata = DocumentMetadata(
        filename="test.pdf",
        original_filename="test.pdf",
        qm_chapter="1.2",
        version="v1.0"
    )
    
    # Act
    document = UploadedDocument(
        id=1,
        file_type=FileType.PDF,
        file_size_bytes=1024,
        document_type_id=1,
        metadata=metadata,
        file_path=FilePath("data/uploads/test.pdf"),
        processing_method=ProcessingMethod.OCR,
        processing_status=ProcessingStatus.PENDING,
        uploaded_by_user_id=1,
        uploaded_at=datetime.utcnow(),
        file_hash=file_hash
    )
    
    # Assert
    assert document.file_hash.value == file_hash.value

def test_uploaded_document_file_hash_optional():
    """FileHash ist optional für Rückwärtskompatibilität"""
    # Arrange & Act
    document = UploadedDocument(
        id=1,
        file_type=FileType.PDF,
        file_size_bytes=1024,
        document_type_id=1,
        metadata=DocumentMetadata(
            filename="test.pdf",
            original_filename="test.pdf",
            qm_chapter="1.2",
            version="v1.0"
        ),
        file_path=FilePath("data/uploads/test.pdf"),
        processing_method=ProcessingMethod.OCR,
        processing_status=ProcessingStatus.PENDING,
        uploaded_by_user_id=1,
        uploaded_at=datetime.utcnow(),
        file_hash=None  # Optional
    )
    
    # Assert
    assert document.file_hash is None
```

#### **1.1.4 GREEN: Entity Implementation**

**Datei:** `contexts/documentupload/domain/entities.py`

```python
from typing import Optional
from .value_objects import FileHash, ...

@dataclass
class UploadedDocument:
    # ... existing fields ...
    file_hash: Optional[FileHash] = None  # NEU: Optional für Rückwärtskompatibilität
    is_duplicate: bool = False  # NEU: Flag für Duplikat-Warnung
    duplicate_of_document_id: Optional[int] = None  # NEU: Link zum Original
```

#### **1.1.5 RED: Use Case Tests**

**Datei:** `tests/unit/documentupload/test_use_cases.py` (erweitern)

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from contexts.documentupload.application.use_cases import UploadDocumentUseCase
from contexts.documentupload.domain.repositories import UploadRepository
from contexts.documentupload.domain.value_objects import FileHash
import hashlib

def test_upload_document_calculates_file_hash(mock_upload_repo):
    """UploadDocumentUseCase berechnet SHA-256 Hash"""
    # Arrange
    use_case = UploadDocumentUseCase(mock_upload_repo)
    
    # Mock: File-Pfad
    test_file_path = "data/uploads/test.pdf"
    
    # Mock: File-Lesen für Hash-Berechnung
    test_content = b"test file content"
    expected_hash = hashlib.sha256(test_content).hexdigest()
    
    with patch('builtins.open', create=True) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = test_content
        
        # Act
        result = await use_case.execute(
            original_filename="test.pdf",
            file_size_bytes=len(test_content),
            document_type_id=1,
            qm_chapter="1.2",
            version="v1.0",
            file_path=test_file_path,
            processing_method="ocr",
            uploaded_by_user_id=1
        )
        
        # Assert
        assert result.file_hash is not None
        assert result.file_hash.value == expected_hash

def test_upload_document_hash_calculation_error_handling(mock_upload_repo):
    """Fehler bei Hash-Berechnung wird abgefangen"""
    # Arrange
    use_case = UploadDocumentUseCase(mock_upload_repo)
    
    with patch('builtins.open', side_effect=IOError("File not found")):
        # Act & Assert
        with pytest.raises(ValueError, match="Failed to calculate file hash"):
            await use_case.execute(...)
```

#### **1.1.6 GREEN: Use Case Implementation**

**Datei:** `contexts/documentupload/application/use_cases.py`

```python
import hashlib
from .value_objects import FileHash

class UploadDocumentUseCase:
    # ... existing code ...
    
    async def execute(self, ...):
        # ... existing validation ...
        
        # NEU: Berechne File Hash
        file_hash = None
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
                hash_value = hashlib.sha256(file_content).hexdigest()
                file_hash = FileHash(hash_value)
        except Exception as e:
            raise ValueError(f"Failed to calculate file hash: {str(e)}")
        
        # Erstelle UploadedDocument mit Hash
        document = UploadedDocument(
            # ... existing fields ...
            file_hash=file_hash
        )
        
        # ... rest of code ...
```

#### **1.1.7 RED: Repository Tests**

**Datei:** `tests/integration/documentupload/test_repositories.py` (erweitern)

```python
async def test_save_document_with_hash(db_session, upload_repo):
    """Repository speichert FileHash korrekt"""
    # Arrange
    file_hash = FileHash("a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3")
    document = UploadedDocument(...file_hash=file_hash)
    
    # Act
    saved = await upload_repo.save(document)
    
    # Assert
    assert saved.file_hash is not None
    assert saved.file_hash.value == file_hash.value
    
    # Prüfe DB
    model = db_session.query(UploadDocumentModel).filter_by(id=saved.id).first()
    assert model.file_hash == file_hash.value

async def test_find_by_hash(db_session, upload_repo):
    """Repository kann Dokument nach Hash finden"""
    # Arrange
    file_hash = FileHash("a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3")
    document = UploadedDocument(...file_hash=file_hash)
    saved = await upload_repo.save(document)
    
    # Act
    found = await upload_repo.find_by_hash(file_hash)
    
    # Assert
    assert found is not None
    assert found.id == saved.id
    assert found.file_hash.value == file_hash.value
```

#### **1.1.8 GREEN: Repository Implementation**

**Datei:** `contexts/documentupload/domain/repositories.py` & `infrastructure/repositories.py`

```python
# Domain Repository Interface
class UploadRepository(ABC):
    # ... existing methods ...
    
    @abstractmethod
    async def find_by_hash(self, file_hash: FileHash) -> Optional[UploadedDocument]:
        """Finde Dokument nach File Hash."""
        pass

# Infrastructure Implementation
class SQLAlchemyUploadRepository(UploadRepository):
    # ... existing code ...
    
    async def find_by_hash(self, file_hash: FileHash) -> Optional[UploadedDocument]:
        """Finde Dokument nach File Hash."""
        model = self.db.query(UploadDocumentModel).filter(
            UploadDocumentModel.file_hash == file_hash.value
        ).first()
        
        if not model:
            return None
        
        return self.mapper.to_entity(model)
```

#### **1.1.9 RED: Schema Tests**

**Datei:** `tests/unit/documentupload/test_schemas.py` (neu/erweitern)

```python
def test_uploaded_document_schema_includes_file_hash():
    """UploadedDocumentSchema enthält file_hash Feld"""
    # Arrange & Act
    schema = UploadedDocumentSchema(
        id=1,
        filename="test.pdf",
        original_filename="test.pdf",
        file_hash="a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
        # ... other fields ...
    )
    
    # Assert
    assert schema.file_hash == "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3"
```

#### **1.1.10 GREEN: Schema Implementation**

**Datei:** `contexts/documentupload/interface/schemas.py`

```python
class UploadedDocumentSchema(BaseModel):
    # ... existing fields ...
    file_hash: Optional[str] = None  # NEU: SHA-256 Hash
    is_duplicate: bool = False  # NEU
    duplicate_of_document_id: Optional[int] = None  # NEU
    
    class Config:
        from_attributes = True
```

#### **1.1.11 RED: API Tests (E2E)**

**Datei:** `tests/e2e/test_document_lifecycle.py` (neu)

```python
import pytest
from httpx import AsyncClient
from backend.app.main import app

@pytest.mark.asyncio
async def test_upload_document_includes_hash(authenticated_client: AsyncClient):
    """Upload-Endpoint berechnet und liefert File Hash"""
    # Arrange
    file_content = b"test document content"
    files = {"file": ("test.pdf", file_content, "application/pdf")}
    data = {
        "filename": "test.pdf",
        "original_filename": "test.pdf",
        "document_type_id": 1,
        "qm_chapter": "1.2",
        "version": "v1.0"
    }
    
    # Act
    response = await authenticated_client.post("/api/documents/upload", files=files, data=data)
    
    # Assert
    assert response.status_code == 200
    result = response.json()
    assert "file_hash" in result["document"]
    assert len(result["document"]["file_hash"]) == 64  # SHA-256 = 64 hex chars
```

#### **1.1.12 GREEN: API Implementation**

**Datei:** `contexts/documentupload/interface/router.py`

```python
@router.post("/upload", response_model=UploadDocumentResponse)
async def upload_document(...):
    # ... existing code ...
    
    # Use Case führt Hash-Berechnung durch (bereits implementiert)
    document = await use_case.execute(...)
    
    # Schema enthält file_hash (bereits implementiert)
    return UploadDocumentResponse(
        success=True,
        document=UploadedDocumentSchema(...)
    )
```

---

### **1.2 Duplikat-Prüfung im Upload-Use Case**

**Ziel:** Prüfen ob identisches Dokument bereits existiert (Warnung + Flag setzen).

#### **1.2.1 RED: Use Case Tests**

**Datei:** `tests/unit/documentupload/test_use_cases.py` (erweitern)

```python
def test_upload_duplicate_document_sets_duplicate_flag(mock_upload_repo):
    """UploadDocumentUseCase erkennt Duplikat und setzt Flag"""
    # Arrange
    existing_hash = FileHash("a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3")
    existing_doc = UploadedDocument(id=1, ...file_hash=existing_hash)
    
    mock_upload_repo.find_by_hash = AsyncMock(return_value=existing_doc)
    
    use_case = UploadDocumentUseCase(mock_upload_repo)
    
    # Act
    with patch('builtins.open') as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = b"content"
        with patch('hashlib.sha256') as mock_hash:
            mock_hash.return_value.hexdigest.return_value = existing_hash.value
            
            result = await use_case.execute(
                original_filename="duplicate.pdf",
                file_size_bytes=100,
                document_type_id=1,
                qm_chapter="1.2",
                version="v1.0",
                file_path="test.pdf",
                processing_method="ocr",
                uploaded_by_user_id=1
            )
    
    # Assert
    assert result.is_duplicate is True
    assert result.duplicate_of_document_id == 1

def test_upload_unique_document_no_duplicate_flag(mock_upload_repo):
    """Eindeutiges Dokument setzt kein Duplikat-Flag"""
    # Arrange
    mock_upload_repo.find_by_hash = AsyncMock(return_value=None)
    use_case = UploadDocumentUseCase(mock_upload_repo)
    
    # Act
    result = await use_case.execute(...)
    
    # Assert
    assert result.is_duplicate is False
    assert result.duplicate_of_document_id is None
```

#### **1.2.2 GREEN: Use Case Implementation**

**Datei:** `contexts/documentupload/application/use_cases.py`

```python
class UploadDocumentUseCase:
    # ... existing code ...
    
    async def execute(self, ...):
        # ... calculate file_hash ...
        
        # NEU: Prüfe auf Duplikat
        existing_doc = await self.upload_repo.find_by_hash(file_hash)
        
        if existing_doc:
            # Duplikat gefunden - setze Flags
            document = UploadedDocument(
                # ... existing fields ...
                file_hash=file_hash,
                is_duplicate=True,
                duplicate_of_document_id=existing_doc.id
            )
        else:
            # Eindeutiges Dokument
            document = UploadedDocument(
                # ... existing fields ...
                file_hash=file_hash,
                is_duplicate=False,
                duplicate_of_document_id=None
            )
        
        # ... save document ...
```

#### **1.2.3 RED: API Tests**

**Datei:** `tests/e2e/test_document_lifecycle.py` (erweitern)

```python
@pytest.mark.asyncio
async def test_upload_duplicate_returns_warning(authenticated_client: AsyncClient):
    """Upload-Endpoint warnt bei Duplikat"""
    # Arrange: Erstes Dokument hochladen
    file_content = b"identical content"
    files1 = {"file": ("doc1.pdf", file_content, "application/pdf")}
    data1 = {...}
    
    response1 = await authenticated_client.post("/api/documents/upload", files=files1, data=data1)
    doc1_id = response1.json()["document"]["id"]
    
    # Act: Gleiches Dokument nochmal hochladen
    files2 = {"file": ("doc2.pdf", file_content, "application/pdf")}
    data2 = {...}
    response2 = await authenticated_client.post("/api/documents/upload", files=files2, data=data2)
    
    # Assert
    assert response2.status_code == 200
    result = response2.json()
    assert result["document"]["is_duplicate"] is True
    assert result["document"]["duplicate_of_document_id"] == doc1_id
    assert "warning" in result or "duplicate" in result.get("message", "").lower()
```

---

### **1.3 Soft Delete Implementation**

**Ziel:** Soft Delete statt Hard Delete (Dokument bleibt in DB, aber markiert als gelöscht).

#### **1.3.1 RED: Value Object Tests**

**Datei:** `tests/unit/documentupload/test_value_objects.py` (erweitern)

```python
def test_workflow_status_deleted():
    """WorkflowStatus.DELETED existiert"""
    from contexts.documentupload.domain.value_objects import WorkflowStatus
    
    assert WorkflowStatus.DELETED.value == "deleted"

def test_workflow_status_archived():
    """WorkflowStatus.ARCHIVED existiert"""
    from contexts.documentupload.domain.value_objects import WorkflowStatus
    
    assert WorkflowStatus.ARCHIVED.value == "archived"
```

#### **1.3.2 GREEN: Value Object Implementation**

**Datei:** `contexts/documentupload/domain/value_objects.py`

```python
from enum import Enum

class WorkflowStatus(Enum):
    DRAFT = "draft"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"  # NEU
    DELETED = "deleted"     # NEU (Soft Delete)
```

#### **1.3.3 RED: Entity Tests**

**Datei:** `tests/unit/documentupload/test_entities.py` (erweitern)

```python
def test_uploaded_document_soft_delete_fields():
    """UploadedDocument hat Soft Delete Felder"""
    from datetime import datetime
    
    document = UploadedDocument(
        id=1,
        # ... existing fields ...
        deleted_at=datetime.utcnow(),
        deleted_by_user_id=1,
        deletion_reason="Test deletion"
    )
    
    assert document.deleted_at is not None
    assert document.deleted_by_user_id == 1
    assert document.deletion_reason == "Test deletion"

def test_uploaded_document_is_deleted_property():
    """is_deleted Property prüft workflow_status"""
    document = UploadedDocument(
        id=1,
        # ... existing fields ...
        workflow_status=WorkflowStatus.DELETED
    )
    
    assert document.is_deleted is True
    
    # Nicht gelöscht
    document.workflow_status = WorkflowStatus.APPROVED
    assert document.is_deleted is False
```

#### **1.3.4 GREEN: Entity Implementation**

**Datei:** `contexts/documentupload/domain/entities.py`

```python
@dataclass
class UploadedDocument:
    # ... existing fields ...
    deleted_at: Optional[datetime] = None  # NEU
    deleted_by_user_id: Optional[int] = None  # NEU
    deletion_reason: Optional[str] = None  # NEU
    
    @property
    def is_deleted(self) -> bool:
        """Prüfe ob Dokument gelöscht ist (Soft Delete)"""
        return self.workflow_status == WorkflowStatus.DELETED
```

#### **1.3.5 RED: Use Case Tests**

**Datei:** `tests/unit/documentupload/test_use_cases.py` (erweitern)

```python
def test_soft_delete_document(mock_upload_repo):
    """Soft Delete Use Case setzt Status auf DELETED"""
    # Arrange
    document = UploadedDocument(id=1, ...workflow_status=WorkflowStatus.APPROVED)
    mock_upload_repo.get_by_id = AsyncMock(return_value=document)
    
    use_case = SoftDeleteDocumentUseCase(mock_upload_repo)
    
    # Act
    result = await use_case.execute(
        document_id=1,
        deleted_by_user_id=1,
        reason="Test deletion"
    )
    
    # Assert
    assert result.workflow_status == WorkflowStatus.DELETED
    assert result.deleted_at is not None
    assert result.deleted_by_user_id == 1
    assert result.deletion_reason == "Test deletion"

def test_restore_document(mock_upload_repo):
    """Restore Use Case setzt Status zurück"""
    # Arrange
    document = UploadedDocument(
        id=1,
        ...workflow_status=WorkflowStatus.DELETED,
        deleted_at=datetime.utcnow()
    )
    mock_upload_repo.get_by_id = AsyncMock(return_value=document)
    
    use_case = RestoreDocumentUseCase(mock_upload_repo)
    
    # Act
    result = await use_case.execute(document_id=1, restored_by_user_id=1)
    
    # Assert
    assert result.workflow_status == WorkflowStatus.APPROVED  # Zurück zum letzten Status
    assert result.deleted_at is None
    assert result.deleted_by_user_id is None
```

#### **1.3.6 GREEN: Use Case Implementation**

**Datei:** `contexts/documentupload/application/use_cases.py`

```python
class SoftDeleteDocumentUseCase:
    """Use Case: Dokument Soft Delete."""
    
    def __init__(self, upload_repository: UploadRepository):
        self.upload_repository = upload_repository
    
    async def execute(
        self,
        document_id: int,
        deleted_by_user_id: int,
        reason: str
    ) -> UploadedDocument:
        """Lösche Dokument (Soft Delete)."""
        document = await self.upload_repository.get_by_id(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # Soft Delete
        document.workflow_status = WorkflowStatus.DELETED
        document.deleted_at = datetime.utcnow()
        document.deleted_by_user_id = deleted_by_user_id
        document.deletion_reason = reason
        
        return await self.upload_repository.update(document)

class RestoreDocumentUseCase:
    """Use Case: Gelöschtes Dokument wiederherstellen."""
    
    def __init__(self, upload_repository: UploadRepository):
        self.upload_repository = upload_repository
    
    async def execute(
        self,
        document_id: int,
        restored_by_user_id: int
    ) -> UploadedDocument:
        """Stelle gelöschtes Dokument wieder her."""
        document = await self.upload_repository.get_by_id(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        if not document.is_deleted:
            raise ValueError(f"Document {document_id} is not deleted")
        
        # Restore: Setze zurück zum letzten gültigen Status (oder APPROVED)
        document.workflow_status = WorkflowStatus.APPROVED  # TODO: Letzten Status speichern
        document.deleted_at = None
        document.deleted_by_user_id = None
        document.deletion_reason = None
        
        return await self.upload_repository.update(document)
```

#### **1.3.7 RED: Repository Tests**

**Datei:** `tests/integration/documentupload/test_repositories.py` (erweitern)

```python
async def test_soft_delete_updates_status(db_session, upload_repo):
    """Soft Delete aktualisiert Status in DB"""
    # Arrange
    document = await upload_repo.save(UploadedDocument(...workflow_status=WorkflowStatus.APPROVED))
    
    # Act
    document.workflow_status = WorkflowStatus.DELETED
    document.deleted_at = datetime.utcnow()
    document.deleted_by_user_id = 1
    document.deletion_reason = "Test"
    updated = await upload_repo.update(document)
    
    # Assert
    assert updated.workflow_status == WorkflowStatus.DELETED
    assert updated.deleted_at is not None
    
    # Prüfe DB
    model = db_session.query(UploadDocumentModel).filter_by(id=document.id).first()
    assert model.workflow_status == "deleted"
    assert model.deleted_at is not None
```

#### **1.3.8 GREEN: Repository Implementation**

**Datei:** `contexts/documentupload/infrastructure/repositories.py` & `mappers.py`

```python
# Mapper erweitern
class UploadDocumentMapper:
    @staticmethod
    def to_model(entity: UploadedDocument) -> UploadDocumentModel:
        # ... existing code ...
        model.deleted_at = entity.deleted_at
        model.deleted_by_user_id = entity.deleted_by_user_id
        model.deletion_reason = entity.deletion_reason
        return model
    
    @staticmethod
    def to_entity(model: UploadDocumentModel) -> UploadedDocument:
        # ... existing code ...
        deleted_at = getattr(model, 'deleted_at', None)
        deleted_by_user_id = getattr(model, 'deleted_by_user_id', None)
        deletion_reason = getattr(model, 'deletion_reason', None)
        
        return UploadedDocument(
            # ... existing fields ...
            deleted_at=deleted_at,
            deleted_by_user_id=deleted_by_user_id,
            deletion_reason=deletion_reason
        )
```

#### **1.3.9 RED: API Tests**

**Datei:** `tests/e2e/test_document_lifecycle.py` (erweitern)

```python
@pytest.mark.asyncio
async def test_soft_delete_endpoint(authenticated_client: AsyncClient):
    """API Endpoint für Soft Delete"""
    # Arrange: Dokument hochladen
    doc_response = await authenticated_client.post("/api/documents/upload", ...)
    doc_id = doc_response.json()["document"]["id"]
    
    # Act: Soft Delete
    delete_response = await authenticated_client.delete(
        f"/api/documents/{doc_id}",
        json={"reason": "Test deletion", "deleted_by_user_id": 1}
    )
    
    # Assert
    assert delete_response.status_code == 200
    result = delete_response.json()
    assert result["document"]["workflow_status"] == "deleted"
    assert result["document"]["deleted_at"] is not None

@pytest.mark.asyncio
async def test_restore_endpoint(authenticated_client: AsyncClient):
    """API Endpoint für Restore"""
    # Arrange: Dokument löschen
    doc_id = ...
    await authenticated_client.delete(f"/api/documents/{doc_id}", ...)
    
    # Act: Restore
    restore_response = await authenticated_client.post(
        f"/api/documents/{doc_id}/restore",
        json={"restored_by_user_id": 1}
    )
    
    # Assert
    assert restore_response.status_code == 200
    result = restore_response.json()
    assert result["document"]["workflow_status"] != "deleted"
    assert result["document"]["deleted_at"] is None
```

---

### **1.4 Workflow-Status Erweiterung**

**Ziel:** `archived` und `deleted` Status in Workflow integrieren.

#### **1.4.1 RED: Integration Tests**

**Datei:** `tests/integration/documentupload/test_workflow_status.py` (neu)

```python
async def test_workflow_status_transitions():
    """Workflow-Status Transitions mit neuen Status"""
    # Test: approved → archived
    # Test: approved → deleted
    # Test: archived → restored (optional)
    # Test: deleted → restored
    pass

async def test_get_documents_by_status_includes_archived():
    """get_by_workflow_status unterstützt ARCHIVED Status"""
    pass

async def test_get_documents_by_status_includes_deleted():
    """get_by_workflow_status unterstützt DELETED Status"""
    pass
```

#### **1.4.2 GREEN: Workflow Integration**

**Datei:** `contexts/documentupload/infrastructure/repositories.py`

```python
# Erweitere get_by_workflow_status() um ARCHIVED und DELETED
# Filter für Soft Deleted Dokumente (nur für QMS Admin sichtbar)
```

---

## 📊 Phase 1 - Zusammenfassung

### **Test-Übersicht:**

| Schritt | Test-Datei | Status |
|---------|-----------|--------|
| 1.1.1-1.1.2 | `test_value_objects.py` | 🔴 TODO |
| 1.1.3-1.1.4 | `test_entities.py` | 🔴 TODO |
| 1.1.5-1.1.6 | `test_use_cases.py` | 🔴 TODO |
| 1.1.7-1.1.8 | `test_repositories.py` | 🔴 TODO |
| 1.1.9-1.1.10 | `test_schemas.py` | 🔴 TODO |
| 1.1.11-1.1.12 | `test_document_lifecycle.py` | 🔴 TODO |
| 1.2.1-1.2.2 | `test_use_cases.py` | 🔴 TODO |
| 1.2.3 | `test_document_lifecycle.py` | 🔴 TODO |
| 1.3.1-1.3.10 | Multiple Files | 🔴 TODO |
| 1.4.1-1.4.2 | `test_workflow_status.py` | 🔴 TODO |

### **Schema-Änderungen:**

```sql
-- upload_documents Tabelle
ALTER TABLE upload_documents ADD COLUMN file_hash TEXT UNIQUE;
ALTER TABLE upload_documents ADD COLUMN is_duplicate BOOLEAN DEFAULT FALSE;
ALTER TABLE upload_documents ADD COLUMN duplicate_of_document_id INTEGER;
ALTER TABLE upload_documents ADD COLUMN deleted_at TIMESTAMP;
ALTER TABLE upload_documents ADD COLUMN deleted_by_user_id INTEGER;
ALTER TABLE upload_documents ADD COLUMN deletion_reason TEXT;

-- Indizes
CREATE INDEX idx_upload_documents_file_hash ON upload_documents(file_hash);
CREATE INDEX idx_upload_documents_is_duplicate ON upload_documents(is_duplicate);
CREATE INDEX idx_upload_documents_deleted_at ON upload_documents(deleted_at) WHERE deleted_at IS NOT NULL;
```

---

## 🎯 Nächste Schritte

1. **Phase 1.1 starten:** File Hash Implementation (RED → GREEN → REFACTOR)
2. **Schema-Änderungen:** Database Migration vorbereiten
3. **Schrittweise durcharbeiten:** Jede Sub-Phase komplett abschließen
4. **Tests dokumentieren:** Jeder Test sollte klar und nachvollziehbar sein

---

## 📝 Wichtige Hinweise

- **TDD-Prinzip:** Immer Tests ZUERST (RED)
- **Keine Shortcuts:** Jede Phase vollständig abschließen
- **DDD-Architektur:** Domain → Application → Infrastructure → Interface
- **Schema-Sync:** Bei DB-Änderungen: Models + Dokumentation + Tests synchron halten

---

**Erstellt von:** AI Assistant  
**Datum:** 2025-11-02  
**Version:** 1.0  
**Status:** Bereit für Implementierung 🚀

