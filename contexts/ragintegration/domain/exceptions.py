"""
Domain Exceptions für RAG Integration Context.

Domain-spezifische Fehler, die Geschäftsregeln verletzen.
"""

from typing import Optional


class MissingCustomPromptError(Exception):
    """
    Domain-Fehler: Custom Prompt fehlt für gewählten Dokumenttyp.
    
    Wird geworfen, wenn ein Dokumenttyp gewählt wurde (document_type_id gesetzt),
    aber kein Custom Prompt für diesen Dokumenttyp existiert.
    
    Gemäß CR-P2.2 Custom-Prompt-Enforcement: Keine Fallbacks, kein generischer Prompt.
    Die API muss mit HTTP 422 Unprocessable Entity abbrechen.
    
    Attributes:
        document_type_id: ID des Dokumenttyps, für den kein Custom Prompt existiert.
        document_type_name: Optionaler Name des Dokumenttyps (für bessere Fehlermeldungen).
    
    Example:
        >>> raise MissingCustomPromptError(
        ...     document_type_id=1,
        ...     document_type_name="SOP"
        ... )
        MissingCustomPromptError: Custom Prompt fehlt für Dokumenttyp ID 1 (SOP). 
        Bitte erstellen Sie einen Custom Prompt für diesen Dokumenttyp.
    """
    
    def __init__(self, document_type_id: int, document_type_name: Optional[str] = None):
        self.document_type_id = document_type_id
        self.document_type_name = document_type_name
        
        message = f"Custom Prompt fehlt für Dokumenttyp ID {document_type_id}"
        if document_type_name:
            message += f" ({document_type_name})"
        message += ". Bitte erstellen Sie einen Custom Prompt für diesen Dokumenttyp."
        
        super().__init__(message)


class InvalidCustomPromptError(Exception):
    """
    Domain-Fehler: Custom Prompt ist ungültig (fehlende Platzhalter).
    
    Wird geworfen, wenn ein Custom Prompt für einen Dokumenttyp existiert,
    aber die erforderlichen Platzhalter {context} und/oder {question} fehlen.
    
    Gemäß CR-P2.2 Custom-Prompt-Enforcement: Custom Prompts MÜSSEN beide Platzhalter
    enthalten. Keine automatische Reparatur, keine Fallbacks.
    Die API muss mit HTTP 422 Unprocessable Entity abbrechen.
    
    Attributes:
        document_type_id: ID des Dokumenttyps mit ungültigem Custom Prompt.
        missing_placeholders: Liste der fehlenden Platzhalter (z.B. ["{context}", "{question}"]).
        document_type_name: Optionaler Name des Dokumenttyps (für bessere Fehlermeldungen).
    
    Example:
        >>> raise InvalidCustomPromptError(
        ...     document_type_id=10,
        ...     missing_placeholders=["{context}"],
        ...     document_type_name="Fachartikel"
        ... )
        InvalidCustomPromptError: Custom Prompt für Dokumenttyp ID 10 (Fachartikel) 
        ist ungültig: Fehlende Platzhalter {context}. 
        Bitte ergänzen Sie die fehlenden Platzhalter im Custom Prompt.
    """
    
    def __init__(
        self, 
        document_type_id: int, 
        missing_placeholders: list[str],
        document_type_name: Optional[str] = None
    ):
        self.document_type_id = document_type_id
        self.document_type_name = document_type_name
        self.missing_placeholders = missing_placeholders
        
        placeholders_str = ", ".join(missing_placeholders)
        message = f"Custom Prompt für Dokumenttyp ID {document_type_id}"
        if document_type_name:
            message += f" ({document_type_name})"
        message += f" ist ungültig: Fehlende Platzhalter {placeholders_str}. "
        message += "Bitte ergänzen Sie die fehlenden Platzhalter im Custom Prompt."
        
        super().__init__(message)

