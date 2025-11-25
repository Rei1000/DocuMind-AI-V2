"""
Auto-Custom-Prompt-Generierung Service.

CR-P2.2: Automatische Generierung von Custom RAG Chat Prompts aus Standard Prompts.

Dieser Service extrahiert JSON-Strukturen aus Standard Prompts (prompt_templates)
und generiert optimierte Custom Prompts für RAG Chat (rag_chat_prompts).

Workflow:
1. Extrahiert JSON-Schema aus Standard Prompt
2. Erstellt Struktur-Beschreibung
3. Generiert Custom Prompt mit JSON-Struktur-Informationen
4. Speichert Custom Prompt mit is_auto_generated=True Flag

Author: AI Assistant
Version: 2.7.3
Stand: 2025-11-17
"""

from typing import Optional
from datetime import datetime

from ..domain.entities import RAGChatPrompt
from ..domain.repositories import RAGChatPromptRepository
from ..infrastructure.json_schema_extractor import (
    extract_json_schema,
    identify_top_level_keys,
    describe_json_structure
)
from ..application.services import generate_custom_prompt_from_json_schema


class AutoCustomPromptService:
    """
    Service für automatische Custom-Prompt-Generierung.
    
    CR-P2.2: Generiert Custom Prompts basierend auf Standard Prompts.
    
    Dieser Service orchestriert den vollständigen Workflow der Auto-Generierung:
    - JSON-Schema-Extraktion aus Standard Prompts
    - Custom-Prompt-Generierung mit dokumenttyp-spezifischen Anpassungen
    - Persistierung mit is_auto_generated Flag
    
    Attributes:
        rag_chat_prompt_repo: Repository für RAG Chat Prompts (Dependency Injection)
    """
    
    def __init__(
        self,
        rag_chat_prompt_repo: RAGChatPromptRepository
    ):
        """
        Initialisiert den Auto-Custom-Prompt-Service.
        
        Args:
            rag_chat_prompt_repo: Repository für RAG Chat Prompts.
                Muss nicht None sein.
        """
        self.rag_chat_prompt_repo = rag_chat_prompt_repo
    
    def generate_from_standard_prompt(
        self,
        standard_prompt_text: str,
        document_type_id: int,
        document_type_name: str,
        created_by_user_id: int
    ) -> Optional[RAGChatPrompt]:
        """
        Generiert einen Custom Prompt aus einem Standard Prompt.
        
        CR-P2.2: Auto-Custom-Prompt-Generierung.
        
        Diese Methode führt den vollständigen Auto-Generierungs-Workflow durch:
        1. Extrahiert JSON-Schema aus Standard Prompt
        2. Erstellt Struktur-Beschreibung
        3. Generiert Custom Prompt mit dokumenttyp-spezifischen Anpassungen
        4. Speichert oder aktualisiert Custom Prompt
        
        Business Rules:
        - Wenn bereits ein Custom Prompt existiert und is_auto_generated=True:
          → Prompt wird aktualisiert
        - Wenn bereits ein Custom Prompt existiert und is_auto_generated=False:
          → Prompt wird NICHT überschrieben (User hat manuell bearbeitet)
        - Wenn kein Custom Prompt existiert:
          → Neues Custom Prompt wird erstellt mit is_auto_generated=True
        
        Args:
            standard_prompt_text: Text des Standard Prompts (aus prompt_templates).
                Muss nicht None oder leer sein.
            document_type_id: ID des Dokumenttyps. Muss > 0 sein.
            document_type_name: Name des Dokumenttyps (z.B. "Fachartikel", "Arbeitsanweisung").
                Wird für dokumenttyp-spezifische Prompt-Anpassungen verwendet.
            created_by_user_id: User ID des Erstellers. Muss > 0 sein.
        
        Returns:
            Optional[RAGChatPrompt]: Generierter oder aktualisierter RAGChatPrompt Entity
            oder None wenn:
            - JSON-Schema-Extraktion fehlschlägt
            - Bestehender Custom Prompt manuell bearbeitet wurde (is_auto_generated=False)
        
        Raises:
            Keine Exceptions - gibt None zurück bei Fehlern.
        
        Example:
            >>> service = AutoCustomPromptService(rag_chat_prompt_repo)
            >>> prompt = service.generate_from_standard_prompt(
            ...     standard_prompt_text="🧩 JSON-Ausgabeformat\\n{...}",
            ...     document_type_id=10,
            ...     document_type_name="Fachartikel",
            ...     created_by_user_id=1
            ... )
            >>> prompt.is_auto_generated
            True
        
        Note:
            - Custom Prompt enthält immer {context} und {question} Platzhalter
            - is_auto_generated Flag wird automatisch gesetzt
            - Timestamps (created_at, updated_at) werden automatisch generiert
        """
        # 1. Extrahiere JSON-Schema aus Standard Prompt
        json_schema = extract_json_schema(standard_prompt_text)
        if not json_schema:
            # Kein JSON-Schema gefunden - keine Auto-Generierung möglich
            return None
        
        # 2. Erstelle Struktur-Beschreibung
        json_structure = describe_json_structure(json_schema)
        
        # 3. Generiere Custom Prompt
        custom_prompt_text = generate_custom_prompt_from_json_schema(
            json_structure=json_structure,
            document_type_name=document_type_name
        )
        
        # 4. Prüfe ob bereits ein Custom Prompt existiert
        existing_prompt = self.rag_chat_prompt_repo.get_by_document_type_id(document_type_id)
        
        now = datetime.utcnow()
        
        if existing_prompt:
            # Update existierendes Prompt (nur wenn is_auto_generated=True)
            if existing_prompt.is_auto_generated:
                existing_prompt.prompt_text = custom_prompt_text
                existing_prompt.updated_at = now
                return self.rag_chat_prompt_repo.save(existing_prompt)
            else:
                # User hat Prompt manuell bearbeitet - nicht überschreiben
                return None
        else:
            # Neues Custom Prompt erstellen
            new_prompt = RAGChatPrompt(
                id=None,
                document_type_id=document_type_id,
                prompt_text=custom_prompt_text,
                created_by_user_id=created_by_user_id,
                created_at=now,
                updated_at=now,
                multi_query_prompt_text=None,
                is_auto_generated=True  # CR-P2.2: Markiere als auto-generiert
            )
            return self.rag_chat_prompt_repo.save(new_prompt)

