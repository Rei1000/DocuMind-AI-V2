"""
Application Use Cases: DocumentTypes Context

Implementiert die Anwendungslogik (Use Cases).
Orchestriert Domain Entities und Repository.
"""

from typing import List, Optional

from ..domain.entities import DocumentType
from ..domain.repositories import IDocumentTypeRepository


class CreateDocumentTypeUseCase:
    """
    Use Case: Erstelle neuen Dokumenttyp
    
    Business Flow:
        1. Validiere Input-Daten
        2. Prüfe ob Code bereits existiert
        3. Erstelle Entity
        4. Speichere via Repository
        5. Return Entity
    """
    
    def __init__(self, repository: IDocumentTypeRepository):
        """
        Args:
            repository: DocumentType Repository (Dependency Injection)
        """
        self.repository = repository
    
    def execute(
        self,
        name: str,
        code: str,
        description: str,
        allowed_file_types: List[str],
        max_file_size_mb: int,
        requires_ocr: bool,
        requires_vision: bool,
        created_by: int,
        sort_order: int = 0
    ) -> DocumentType:
        """
        Execute Use Case
        
        Args:
            name: Anzeigename
            code: Technischer Code (eindeutig)
            description: Beschreibung
            allowed_file_types: Liste erlaubter Dateitypen
            max_file_size_mb: Max Dateigröße in MB
            requires_ocr: OCR benötigt?
            requires_vision: Vision AI benötigt?
            created_by: User ID
            sort_order: Sortierung
            
        Returns:
            Erstellte DocumentType Entity
            
        Raises:
            ValueError: Wenn Code bereits existiert oder Validation fehlschlägt
        """
        # Business Rule: Code muss eindeutig sein
        if self.repository.exists_by_code(code):
            raise ValueError(f"DocumentType mit Code '{code}' existiert bereits")
        
        # Erstelle Entity
        document_type = DocumentType(
            name=name,
            code=code.upper(),  # Enforce UPPERCASE
            description=description,
            allowed_file_types=allowed_file_types,
            max_file_size_mb=max_file_size_mb,
            requires_ocr=requires_ocr,
            requires_vision=requires_vision,
            created_by=created_by,
            sort_order=sort_order,
            is_active=True
        )
        
        # Business Rule: Entity muss valid sein
        if not document_type.is_valid():
            raise ValueError("DocumentType Validation fehlgeschlagen")
        
        # Speichere
        return self.repository.save(document_type)


class UpdateDocumentTypeUseCase:
    """
    Use Case: Aktualisiere existierenden Dokumenttyp
    """
    
    def __init__(self, repository: IDocumentTypeRepository):
        self.repository = repository
    
    def execute(
        self,
        document_type_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        allowed_file_types: Optional[List[str]] = None,
        max_file_size_mb: Optional[int] = None,
        requires_ocr: Optional[bool] = None,
        requires_vision: Optional[bool] = None,
        default_prompt_template_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        sort_order: Optional[int] = None
    ) -> DocumentType:
        """
        Execute Use Case
        
        Args:
            document_type_id: ID des zu aktualisierenden Typs
            name: Optional neuer Name
            description: Optional neue Beschreibung
            allowed_file_types: Optional neue Dateitypen
            max_file_size_mb: Optional neue Max-Größe
            requires_ocr: Optional OCR-Flag
            requires_vision: Optional Vision-Flag
            default_prompt_template_id: Optional Template ID
            is_active: Optional Aktiv-Flag
            sort_order: Optional neue Sortierung
            
        Returns:
            Aktualisierte DocumentType Entity
            
        Raises:
            ValueError: Wenn DocumentType nicht gefunden oder Validation fehlschlägt
        """
        # Lade existierende Entity
        document_type = self.repository.get_by_id(document_type_id)
        if not document_type:
            raise ValueError(f"DocumentType mit ID {document_type_id} nicht gefunden")
        
        # Update Fields (nur wenn angegeben)
        if name is not None:
            document_type.name = name
        if description is not None:
            document_type.description = description
        if allowed_file_types is not None:
            document_type.allowed_file_types = allowed_file_types
        if max_file_size_mb is not None:
            document_type.max_file_size_mb = max_file_size_mb
        if requires_ocr is not None:
            document_type.requires_ocr = requires_ocr
        if requires_vision is not None:
            document_type.requires_vision = requires_vision
        if default_prompt_template_id is not None:
            document_type.default_prompt_template_id = default_prompt_template_id
        if is_active is not None:
            document_type.is_active = is_active
        if sort_order is not None:
            document_type.sort_order = sort_order
        
        # Mark as updated
        document_type.mark_as_updated()
        
        # Business Rule: Entity muss valid sein
        if not document_type.is_valid():
            raise ValueError("DocumentType Validation fehlgeschlagen")
        
        # Speichere
        return self.repository.save(document_type)


class GetDocumentTypeUseCase:
    """
    Use Case: Hole Dokumenttyp by ID
    """
    
    def __init__(self, repository: IDocumentTypeRepository):
        self.repository = repository
    
    def execute(self, document_type_id: int) -> Optional[DocumentType]:
        """
        Execute Use Case
        
        Args:
            document_type_id: ID des Dokumenttyps
            
        Returns:
            DocumentType Entity oder None
        """
        return self.repository.get_by_id(document_type_id)


class ListDocumentTypesUseCase:
    """
    Use Case: Liste alle Dokumenttypen
    """
    
    def __init__(self, repository: IDocumentTypeRepository):
        self.repository = repository
    
    def execute(self, active_only: bool = True) -> List[DocumentType]:
        """
        Execute Use Case
        
        Args:
            active_only: Nur aktive Typen?
            
        Returns:
            Liste von DocumentType Entities (sortiert nach sort_order)
        """
        document_types = self.repository.get_all(active_only=active_only)
        # Sort by sort_order, dann by name
        return sorted(document_types, key=lambda dt: (dt.sort_order, dt.name))


class DeleteDocumentTypeUseCase:
    """
    Use Case: Lösche Dokumenttyp (Soft Delete - deactivate)
    """
    
    def __init__(self, repository: IDocumentTypeRepository):
        self.repository = repository
    
    def execute(self, document_type_id: int) -> bool:
        """
        Execute Use Case
        
        Args:
            document_type_id: ID des zu löschenden Typs
            
        Returns:
            True wenn gelöscht, False wenn nicht gefunden
        """
        document_type = self.repository.get_by_id(document_type_id)
        if not document_type:
            return False
        
        # Soft Delete: Deactivate
        document_type.deactivate()
        self.repository.save(document_type)
        return True

