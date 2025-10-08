"""
Application Services: DocumentTypes Context

Höhere Abstraktionsebene für komplexere Business-Flows.
Kombiniert mehrere Use Cases wenn nötig.
"""

from typing import List, Optional

from ..domain.entities import DocumentType
from ..domain.repositories import IDocumentTypeRepository
from .use_cases import (
    CreateDocumentTypeUseCase,
    UpdateDocumentTypeUseCase,
    GetDocumentTypeUseCase,
    ListDocumentTypesUseCase,
    DeleteDocumentTypeUseCase
)


class DocumentTypeService:
    """
    Application Service: Zentraler Service für DocumentType Operations
    
    Vereinfacht den Zugriff auf Use Cases für Interface Layer.
    Kann mehrere Use Cases kombinieren für komplexe Workflows.
    """
    
    def __init__(self, repository: IDocumentTypeRepository):
        """
        Args:
            repository: DocumentType Repository (Dependency Injection)
        """
        self.repository = repository
        
        # Initialize Use Cases
        self.create_use_case = CreateDocumentTypeUseCase(repository)
        self.update_use_case = UpdateDocumentTypeUseCase(repository)
        self.get_use_case = GetDocumentTypeUseCase(repository)
        self.list_use_case = ListDocumentTypesUseCase(repository)
        self.delete_use_case = DeleteDocumentTypeUseCase(repository)
    
    def create_document_type(
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
        Erstelle neuen Dokumenttyp
        
        Delegates to CreateDocumentTypeUseCase
        """
        return self.create_use_case.execute(
            name=name,
            code=code,
            description=description,
            allowed_file_types=allowed_file_types,
            max_file_size_mb=max_file_size_mb,
            requires_ocr=requires_ocr,
            requires_vision=requires_vision,
            created_by=created_by,
            sort_order=sort_order
        )
    
    def update_document_type(
        self,
        document_type_id: int,
        **kwargs
    ) -> DocumentType:
        """
        Aktualisiere existierenden Dokumenttyp
        
        Delegates to UpdateDocumentTypeUseCase
        """
        return self.update_use_case.execute(document_type_id, **kwargs)
    
    def get_document_type(self, document_type_id: int) -> Optional[DocumentType]:
        """
        Hole Dokumenttyp by ID
        
        Delegates to GetDocumentTypeUseCase
        """
        return self.get_use_case.execute(document_type_id)
    
    def get_document_type_by_code(self, code: str) -> Optional[DocumentType]:
        """
        Hole Dokumenttyp by Code
        
        Direct repository access for simple query
        """
        return self.repository.get_by_code(code)
    
    def list_document_types(self, active_only: bool = True) -> List[DocumentType]:
        """
        Liste alle Dokumenttypen
        
        Delegates to ListDocumentTypesUseCase
        """
        return self.list_use_case.execute(active_only=active_only)
    
    def delete_document_type(self, document_type_id: int) -> bool:
        """
        Lösche Dokumenttyp (Soft Delete)
        
        Delegates to DeleteDocumentTypeUseCase
        """
        return self.delete_use_case.execute(document_type_id)
    
    def validate_file_for_type(
        self,
        document_type_id: int,
        file_extension: str,
        file_size_mb: float
    ) -> tuple[bool, Optional[str]]:
        """
        Complex Business Flow: Validiere Datei gegen Dokumenttyp
        
        Kombiniert Get Use Case mit Entity Business Logic.
        
        Args:
            document_type_id: ID des Dokumenttyps
            file_extension: Dateiendung (z.B. ".pdf")
            file_size_mb: Dateigröße in MB
            
        Returns:
            Tuple: (is_valid, error_message)
        """
        document_type = self.get_document_type(document_type_id)
        
        if not document_type:
            return False, f"Dokumenttyp mit ID {document_type_id} nicht gefunden"
        
        if not document_type.is_active:
            return False, f"Dokumenttyp '{document_type.name}' ist nicht aktiv"
        
        if not document_type.validate_file_type(file_extension):
            allowed = ", ".join(document_type.allowed_file_types)
            return False, f"Dateityp {file_extension} nicht erlaubt. Erlaubt: {allowed}"
        
        if not document_type.validate_file_size(file_size_mb):
            return False, f"Datei zu groß ({file_size_mb:.2f} MB). Maximum: {document_type.max_file_size_mb} MB"
        
        return True, None

