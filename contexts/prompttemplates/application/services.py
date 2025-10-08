"""
Application Services: PromptTemplates Context

Höhere Abstraktionsebene für komplexere Business-Flows.
Kombiniert mehrere Use Cases wenn nötig.
"""

from typing import List, Optional

from ..domain.entities import PromptTemplate, PromptStatus
from ..domain.repositories import IPromptTemplateRepository
from .use_cases import (
    CreatePromptTemplateUseCase,
    CreateFromPlaygroundUseCase,
    UpdatePromptTemplateUseCase,
    GetPromptTemplateUseCase,
    ListPromptTemplatesUseCase,
    ActivateTemplateUseCase,
    ArchiveTemplateUseCase,
    DeletePromptTemplateUseCase
)


class PromptTemplateService:
    """
    Application Service: Zentraler Service für PromptTemplate Operations
    
    Vereinfacht den Zugriff auf Use Cases für Interface Layer.
    Kann mehrere Use Cases kombinieren für komplexe Workflows.
    """
    
    def __init__(self, repository: IPromptTemplateRepository):
        """
        Args:
            repository: PromptTemplate Repository (Dependency Injection)
        """
        self.repository = repository
        
        # Initialize Use Cases
        self.create_use_case = CreatePromptTemplateUseCase(repository)
        self.create_from_playground_use_case = CreateFromPlaygroundUseCase(repository)
        self.update_use_case = UpdatePromptTemplateUseCase(repository)
        self.get_use_case = GetPromptTemplateUseCase(repository)
        self.list_use_case = ListPromptTemplatesUseCase(repository)
        self.activate_use_case = ActivateTemplateUseCase(repository)
        self.archive_use_case = ArchiveTemplateUseCase(repository)
        self.delete_use_case = DeletePromptTemplateUseCase(repository)
    
    def create_template(
        self,
        name: str,
        prompt_text: str,
        description: str = "",
        document_type_id: Optional[int] = None,
        ai_model: str = "gpt-4o-mini",
        temperature: float = 0.0,
        max_tokens: int = 4000,
        top_p: float = 1.0,
        detail_level: str = "high",
        system_instructions: Optional[str] = None,
        created_by: Optional[int] = None,
        tags: List[str] = None
    ) -> PromptTemplate:
        """
        Erstelle neues Template
        
        Delegates to CreatePromptTemplateUseCase
        """
        return self.create_use_case.execute(
            name=name,
            prompt_text=prompt_text,
            description=description,
            document_type_id=document_type_id,
            ai_model=ai_model,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            detail_level=detail_level,
            system_instructions=system_instructions,
            created_by=created_by,
            tags=tags
        )
    
    def create_from_playground(
        self,
        name: str,
        prompt_text: str,
        ai_model: str,
        temperature: float,
        max_tokens: int,
        top_p: float,
        detail_level: str,
        tokens_sent: int,
        tokens_received: int,
        response_time_ms: float,
        description: str = "",
        document_type_id: Optional[int] = None,
        created_by: Optional[int] = None,
        example_output: Optional[str] = None
    ) -> PromptTemplate:
        """
        Erstelle Template aus Playground-Test
        
        Delegates to CreateFromPlaygroundUseCase
        """
        return self.create_from_playground_use_case.execute(
            name=name,
            prompt_text=prompt_text,
            ai_model=ai_model,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            detail_level=detail_level,
            tokens_sent=tokens_sent,
            tokens_received=tokens_received,
            response_time_ms=response_time_ms,
            description=description,
            document_type_id=document_type_id,
            created_by=created_by,
            example_output=example_output
        )
    
    def update_template(self, template_id: int, **kwargs) -> PromptTemplate:
        """
        Aktualisiere existierendes Template
        
        Delegates to UpdatePromptTemplateUseCase
        """
        return self.update_use_case.execute(template_id, **kwargs)
    
    def get_template(self, template_id: int) -> Optional[PromptTemplate]:
        """
        Hole Template by ID
        
        Delegates to GetPromptTemplateUseCase
        """
        return self.get_use_case.execute(template_id)
    
    def list_templates(
        self,
        status: Optional[PromptStatus] = None,
        document_type_id: Optional[int] = None,
        active_only: bool = False
    ) -> List[PromptTemplate]:
        """
        Liste alle Templates
        
        Delegates to ListPromptTemplatesUseCase
        """
        return self.list_use_case.execute(
            status=status,
            document_type_id=document_type_id,
            active_only=active_only
        )
    
    def get_active_templates_for_document_type(
        self,
        document_type_id: int
    ) -> List[PromptTemplate]:
        """
        Hole alle aktiven Templates für einen Dokumenttyp
        
        Direct repository access für häufige Query
        """
        return self.repository.get_active_for_document_type(document_type_id)
    
    def activate_template(self, template_id: int) -> PromptTemplate:
        """
        Aktiviere Template
        
        Delegates to ActivateTemplateUseCase
        """
        return self.activate_use_case.execute(template_id)
    
    def archive_template(self, template_id: int) -> PromptTemplate:
        """
        Archiviere Template
        
        Delegates to ArchiveTemplateUseCase
        """
        return self.archive_use_case.execute(template_id)
    
    def delete_template(self, template_id: int) -> bool:
        """
        Lösche Template
        
        Delegates to DeletePromptTemplateUseCase
        """
        return self.delete_use_case.execute(template_id)
    
    def mark_template_as_used(
        self,
        template_id: int,
        success: bool = True
    ) -> PromptTemplate:
        """
        Complex Business Flow: Markiere Template als verwendet
        
        Wird beim Document Upload aufgerufen.
        
        Args:
            template_id: ID des Templates
            success: War die Verwendung erfolgreich?
            
        Returns:
            Aktualisierte PromptTemplate Entity
        """
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template mit ID {template_id} nicht gefunden")
        
        # Business Logic in Entity
        template.mark_as_used(success=success)
        
        return self.repository.save(template)
    
    def search_templates_by_tags(self, tags: List[str]) -> List[PromptTemplate]:
        """
        Suche Templates nach Tags
        
        Direct repository access
        """
        return self.repository.search_by_tags(tags)
    
    def duplicate_template(
        self,
        source_template_id: int,
        new_name: str,
        created_by: Optional[int] = None
    ) -> PromptTemplate:
        """
        Complex Business Flow: Dupliziere Template
        
        Erstellt eine Kopie eines existierenden Templates mit neuem Namen.
        
        Args:
            source_template_id: ID des zu duplizierenden Templates
            new_name: Name für das neue Template
            created_by: User ID des Erstellers
            
        Returns:
            Neue PromptTemplate Entity
        """
        # Lade Source Template
        source = self.get_template(source_template_id)
        if not source:
            raise ValueError(f"Template mit ID {source_template_id} nicht gefunden")
        
        # Erstelle Kopie mit neuem Namen
        duplicate = PromptTemplate(
            name=new_name,
            description=f"Kopie von '{source.name}': {source.description}",
            prompt_text=source.prompt_text,
            system_instructions=source.system_instructions,
            document_type_id=source.document_type_id,
            ai_model=source.ai_model,
            temperature=source.temperature,
            max_tokens=source.max_tokens,
            top_p=source.top_p,
            detail_level=source.detail_level,
            status=PromptStatus.DRAFT,  # Always start as draft
            version="1.0",  # Reset version
            created_by=created_by or source.created_by,
            tags=source.tags.copy(),
            example_input=source.example_input,
            example_output=source.example_output
        )
        
        if not duplicate.is_valid():
            raise ValueError("Dupliziertes Template ist nicht valid")
        
        return self.repository.save(duplicate)

