"""
Application Use Cases: PromptTemplates Context

Implementiert die Anwendungslogik (Use Cases).
Orchestriert Domain Entities und Repository.
"""

from typing import List, Optional

from ..domain.entities import PromptTemplate, PromptStatus
from ..domain.repositories import IPromptTemplateRepository


class CreatePromptTemplateUseCase:
    """
    Use Case: Erstelle neues Prompt Template
    
    Business Flow:
        1. Validiere Input-Daten
        2. Prüfe ob Name bereits existiert
        3. Erstelle Entity
        4. Speichere via Repository
        5. Return Entity
    """
    
    def __init__(self, repository: IPromptTemplateRepository):
        """
        Args:
            repository: PromptTemplate Repository (Dependency Injection)
        """
        self.repository = repository
    
    def execute(
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
        Execute Use Case
        
        Args:
            name: Template-Name (eindeutig)
            prompt_text: Der Prompt-Text
            description: Beschreibung
            document_type_id: Optional: Verknüpfung mit Dokumenttyp
            ai_model: AI-Modell ID
            temperature: Temperature (0-2)
            max_tokens: Max Output Tokens
            top_p: Nucleus Sampling
            detail_level: Vision Detail Level
            system_instructions: Optional System Instructions
            created_by: User ID des Erstellers
            tags: Optional: Liste von Tags
            
        Returns:
            Erstellte PromptTemplate Entity
            
        Raises:
            ValueError: Wenn Name bereits existiert oder Validation fehlschlägt
        """
        # Business Rule: Name muss eindeutig sein
        if self.repository.exists_by_name(name):
            raise ValueError(f"Template mit Name '{name}' existiert bereits")
        
        # Erstelle Entity
        template = PromptTemplate(
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
            status=PromptStatus.DRAFT,
            tags=tags or []
        )
        
        # Business Rule: Template muss valid sein
        if not template.is_valid():
            raise ValueError("Template Validation fehlgeschlagen")
        
        # Speichere
        return self.repository.save(template)


class CreateFromPlaygroundUseCase:
    """
    Use Case: Erstelle Template aus AI Playground Test
    
    Spezialisierter Use Case der ein erfolgreiches Playground-Ergebnis
    als Template speichert.
    """
    
    def __init__(self, repository: IPromptTemplateRepository):
        self.repository = repository
    
    def execute(
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
        Execute Use Case
        
        Args:
            name: Template-Name
            prompt_text: Der Prompt aus Playground
            ai_model: Verwendetes AI-Modell
            temperature, max_tokens, top_p, detail_level: AI Config
            tokens_sent, tokens_received, response_time_ms: Performance Metrics
            description: Optional Beschreibung
            document_type_id: Optional Dokumenttyp-Verknüpfung
            created_by: User ID
            example_output: Optional: Response aus Playground
            
        Returns:
            Erstellte PromptTemplate Entity (bereits als tested_successfully markiert)
        """
        # Business Rule: Name muss eindeutig sein
        if self.repository.exists_by_name(name):
            raise ValueError(f"Template mit Name '{name}' existiert bereits")
        
        # Erstelle Template mit Performance-Daten
        template = PromptTemplate(
            name=name,
            prompt_text=prompt_text,
            description=description or f"Erstellt aus AI Playground Test ({ai_model})",
            document_type_id=document_type_id,
            ai_model=ai_model,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            detail_level=detail_level,
            created_by=created_by,
            status=PromptStatus.DRAFT,
            tested_successfully=True,  # Wurde ja schon im Playground getestet
            success_count=1,
            example_output=example_output
        )
        
        if not template.is_valid():
            raise ValueError("Template Validation fehlgeschlagen")
        
        # Speichere
        return self.repository.save(template)


class UpdatePromptTemplateUseCase:
    """
    Use Case: Aktualisiere existierendes Template
    """
    
    def __init__(self, repository: IPromptTemplateRepository):
        self.repository = repository
    
    def execute(
        self,
        template_id: int,
        name: Optional[str] = None,
        prompt_text: Optional[str] = None,
        description: Optional[str] = None,
        document_type_id: Optional[int] = None,
        ai_model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        detail_level: Optional[str] = None,
        system_instructions: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> PromptTemplate:
        """
        Execute Use Case
        
        Returns:
            Aktualisierte PromptTemplate Entity
            
        Raises:
            ValueError: Wenn Template nicht gefunden oder Validation fehlschlägt
        """
        # Lade existierende Entity
        template = self.repository.get_by_id(template_id)
        if not template:
            raise ValueError(f"Template mit ID {template_id} nicht gefunden")
        
        # Update Fields (nur wenn angegeben)
        if name is not None:
            # Check uniqueness (exclude current template)
            if name != template.name and self.repository.exists_by_name(name, exclude_id=template_id):
                raise ValueError(f"Template mit Name '{name}' existiert bereits")
            template.name = name
        
        if prompt_text is not None:
            template.prompt_text = prompt_text
        if description is not None:
            template.description = description
        if document_type_id is not None:
            template.document_type_id = document_type_id
        if ai_model is not None:
            template.ai_model = ai_model
        if temperature is not None:
            template.temperature = temperature
        if max_tokens is not None:
            template.max_tokens = max_tokens
        if top_p is not None:
            template.top_p = top_p
        if detail_level is not None:
            template.detail_level = detail_level
        if system_instructions is not None:
            template.system_instructions = system_instructions
        if tags is not None:
            template.tags = tags
        
        # Mark as updated
        template.mark_as_updated()
        
        # Business Rule: Template muss valid sein
        if not template.is_valid():
            raise ValueError("Template Validation fehlgeschlagen")
        
        # Speichere
        return self.repository.save(template)


class GetPromptTemplateUseCase:
    """
    Use Case: Hole Template by ID
    """
    
    def __init__(self, repository: IPromptTemplateRepository):
        self.repository = repository
    
    def execute(self, template_id: int) -> Optional[PromptTemplate]:
        """Execute Use Case"""
        return self.repository.get_by_id(template_id)


class ListPromptTemplatesUseCase:
    """
    Use Case: Liste alle Templates (mit Filtern)
    """
    
    def __init__(self, repository: IPromptTemplateRepository):
        self.repository = repository
    
    def execute(
        self,
        status: Optional[PromptStatus] = None,
        document_type_id: Optional[int] = None,
        active_only: bool = False
    ) -> List[PromptTemplate]:
        """
        Execute Use Case
        
        Args:
            status: Optional Status-Filter
            document_type_id: Optional Dokumenttyp-Filter
            active_only: Nur aktive Templates?
            
        Returns:
            Liste von PromptTemplate Entities
        """
        if active_only:
            if document_type_id:
                return self.repository.get_active_for_document_type(document_type_id)
            else:
                return self.repository.get_all(status=PromptStatus.ACTIVE)
        else:
            return self.repository.get_all(status=status, document_type_id=document_type_id)


class ActivateTemplateUseCase:
    """
    Use Case: Aktiviere Template
    """
    
    def __init__(self, repository: IPromptTemplateRepository):
        self.repository = repository
    
    def execute(self, template_id: int) -> PromptTemplate:
        """
        Execute Use Case
        
        Returns:
            Aktivierte PromptTemplate Entity
            
        Raises:
            ValueError: Wenn Template nicht gefunden oder nicht valid
        """
        template = self.repository.get_by_id(template_id)
        if not template:
            raise ValueError(f"Template mit ID {template_id} nicht gefunden")
        
        # Business Rule: Template muss valid sein
        template.activate()  # Wirft ValueError wenn nicht valid
        
        return self.repository.save(template)


class ArchiveTemplateUseCase:
    """
    Use Case: Archiviere Template
    """
    
    def __init__(self, repository: IPromptTemplateRepository):
        self.repository = repository
    
    def execute(self, template_id: int) -> PromptTemplate:
        """Execute Use Case"""
        template = self.repository.get_by_id(template_id)
        if not template:
            raise ValueError(f"Template mit ID {template_id} nicht gefunden")
        
        template.archive()
        return self.repository.save(template)


class DeletePromptTemplateUseCase:
    """
    Use Case: Lösche Template (Hard Delete)
    """
    
    def __init__(self, repository: IPromptTemplateRepository):
        self.repository = repository
    
    def execute(self, template_id: int) -> bool:
        """
        Execute Use Case
        
        Returns:
            True wenn gelöscht, False wenn nicht gefunden
        """
        return self.repository.delete(template_id)

