"""
Event Handler für Document Lifecycle Events.

NEU Phase 5: RAG Cleanup Event Handler für Cross-Context Kommunikation.

Diese Handler konsumieren Events aus dem documentupload Context und führen
RAG Cleanup durch, ohne direkte Cross-Context Abhängigkeiten.
"""

from typing import Protocol


class DocumentRejectedEventHandler:
    """
    Event Handler: DocumentRejectedEvent → RAG Cleanup.
    
    NEU Phase 5: Entfernt rejected Dokumente aus RAG Index.
    
    Args:
        remove_document_use_case: RemoveDocumentFromRAGUseCase
    """
    
    def __init__(self, remove_document_use_case):
        self.remove_document_use_case = remove_document_use_case
    
    async def handle(self, event) -> None:
        """
        Verarbeite DocumentRejectedEvent.
        
        Args:
            event: DocumentRejectedEvent (aus documentupload Context)
        """
        # Entferne Dokument aus RAG
        result = self.remove_document_use_case.execute(
            upload_document_id=event.document_id
        )
        # Logge Ergebnis (optional)
        if not result.get("success"):
            print(f"WARNING: Failed to remove rejected document {event.document_id} from RAG")


class DocumentDeletedEventHandler:
    """
    Event Handler: DocumentDeletedEvent → RAG Cleanup.
    
    NEU Phase 5: Entfernt soft-deleted Dokumente aus RAG Index.
    
    Args:
        remove_document_use_case: RemoveDocumentFromRAGUseCase
    """
    
    def __init__(self, remove_document_use_case):
        self.remove_document_use_case = remove_document_use_case
    
    async def handle(self, event) -> None:
        """
        Verarbeite DocumentDeletedEvent.
        
        Args:
            event: DocumentDeletedEvent (aus documentupload Context)
        """
        # Entferne Dokument aus RAG
        result = self.remove_document_use_case.execute(
            upload_document_id=event.document_id
        )
        # Logge Ergebnis (optional)
        if not result.get("success"):
            print(f"WARNING: Failed to remove deleted document {event.document_id} from RAG")


class DocumentArchivedEventHandler:
    """
    Event Handler: DocumentArchivedEvent → RAG Cleanup.
    
    NEU Phase 5: Entfernt archived Dokumente aus RAG Index.
    
    Args:
        remove_document_use_case: RemoveDocumentFromRAGUseCase
    """
    
    def __init__(self, remove_document_use_case):
        self.remove_document_use_case = remove_document_use_case
    
    async def handle(self, event) -> None:
        """
        Verarbeite DocumentArchivedEvent.
        
        Args:
            event: DocumentArchivedEvent (aus documentupload Context)
        """
        # Entferne Dokument aus RAG
        result = self.remove_document_use_case.execute(
            upload_document_id=event.document_id
        )
        # Logge Ergebnis (optional)
        if not result.get("success"):
            print(f"WARNING: Failed to remove archived document {event.document_id} from RAG")


class DocumentVersionArchivedEventHandler:
    """
    Event Handler: DocumentVersionArchivedEvent → RAG Cleanup.
    
    NEU Phase 5: Entfernt alte Version aus RAG Index (bei neuer Version).
    
    Args:
        remove_document_use_case: RemoveDocumentFromRAGUseCase
    """
    
    def __init__(self, remove_document_use_case):
        self.remove_document_use_case = remove_document_use_case
    
    async def handle(self, event) -> None:
        """
        Verarbeite DocumentVersionArchivedEvent.
        
        Args:
            event: DocumentVersionArchivedEvent (aus documentupload Context)
        
        WICHTIG: Entfernt nur die alte Version (old_version_id), nicht die neue!
        """
        # Entferne alte Version aus RAG (nicht die neue!)
        result = self.remove_document_use_case.execute(
            upload_document_id=event.old_version_id
        )
        # Logge Ergebnis (optional)
        if not result.get("success"):
            print(f"WARNING: Failed to remove old version {event.old_version_id} from RAG")

