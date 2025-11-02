"""
Event Handler Registration & Setup.

NEU Phase 5: Bootstrap für Event-Driven Architecture.

Diese Datei verbindet Events aus documentupload Context mit Handlern
aus ragintegration Context, ohne Cross-Context Imports zu benötigen.
"""

from typing import Optional


def setup_event_handlers(event_publisher) -> None:
    """
    Registriere alle Event Handler für Document Lifecycle Events.
    
    Diese Funktion verbindet Events mit Handlern, ohne dass die Use Cases
    direkte Abhängigkeiten zu anderen Contexts haben müssen.
    
    Args:
        event_publisher: InMemoryEventPublisher Instanz
    
    WICHTIG: Cross-Context Imports sind hier OK, da dies der Integration Layer ist!
    Hier werden Contexts bewusst "gekoppelt" - das ist die Aufgabe dieser Schicht.
    """
    from contexts.ragintegration.application.event_handlers import (
        DocumentRejectedEventHandler,
        DocumentDeletedEventHandler,
        DocumentArchivedEventHandler,
        DocumentVersionArchivedEventHandler
    )
    from contexts.ragintegration.application.use_cases import (
        RemoveDocumentFromRAGUseCase
    )
    from contexts.ragintegration.infrastructure.repositories import (
        SQLAlchemyIndexedDocumentRepository,
        SQLAlchemyDocumentChunkRepository
    )
    from contexts.ragintegration.infrastructure.vector_store_adapter import (
        QdrantVectorStoreAdapter
    )
    from contexts.documentupload.domain.events import (
        DocumentRejectedEvent,
        DocumentDeletedEvent,
        DocumentArchivedEvent,
        DocumentVersionArchivedEvent
    )
    from backend.app.database import SessionLocal
    
    # Erstelle RAG Cleanup Use Case
    # WICHTIG: Session wird hier erstellt, aber könnte auch per Dependency Injection kommen
    db_session = SessionLocal()
    
    try:
        indexed_doc_repo = SQLAlchemyIndexedDocumentRepository(db_session)
        chunk_repo = SQLAlchemyDocumentChunkRepository(db_session)
        vector_store = QdrantVectorStoreAdapter(collection_name="rag_documents")
        
        remove_use_case = RemoveDocumentFromRAGUseCase(
            indexed_document_repository=indexed_doc_repo,
            document_chunk_repository=chunk_repo,
            vector_store=vector_store
        )
        
        # Registriere Handler
        event_publisher.subscribe(
            DocumentRejectedEvent,
            DocumentRejectedEventHandler(remove_use_case)
        )
        event_publisher.subscribe(
            DocumentDeletedEvent,
            DocumentDeletedEventHandler(remove_use_case)
        )
        event_publisher.subscribe(
            DocumentArchivedEvent,
            DocumentArchivedEventHandler(remove_use_case)
        )
        event_publisher.subscribe(
            DocumentVersionArchivedEvent,
            DocumentVersionArchivedEventHandler(remove_use_case)
        )
        
        print("✅ Event Handler registriert: RAG Cleanup für Document Lifecycle Events")
        
    except Exception as e:
        # Bei Fehler: Logge Warnung, aber breche nicht ab
        # System sollte auch ohne RAG Cleanup funktionieren
        print(f"WARNING: Event Handler Setup fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()

