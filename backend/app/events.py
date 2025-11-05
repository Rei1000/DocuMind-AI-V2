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
        DocumentVersionArchivedEventHandler,
        DocumentRestoredEventHandler  # NEU: Archiv-System
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
        DocumentVersionArchivedEvent,
        DocumentRestoredEvent,  # NEU: Archiv-System
        DocumentHardDeletedEvent  # NEU: Archiv-System
    )
    from backend.app.database import SessionLocal
    
    # Erstelle Wrapper-Handler, die bei jedem Event eine neue Session erstellen
    class SessionBasedHandler:
        """Wrapper Handler, der bei jedem Event eine neue Session erstellt und schließt."""
        def __init__(self, handler_class, session_local):
            self.handler_class = handler_class
            self.session_local = session_local
        
        async def handle(self, event):
            """Erstelle Use Case mit neuer Session für dieses Event."""
            db_session = self.session_local()
            try:
                indexed_doc_repo = SQLAlchemyIndexedDocumentRepository(db_session)
                chunk_repo = SQLAlchemyDocumentChunkRepository(db_session)
                vector_store = QdrantVectorStoreAdapter(collection_name="rag_documents")
                
                use_case = RemoveDocumentFromRAGUseCase(
                    indexed_document_repository=indexed_doc_repo,
                    document_chunk_repository=chunk_repo,
                    vector_store=vector_store
                )
                
                handler = self.handler_class(use_case)
                await handler.handle(event)
            finally:
                db_session.close()  # WICHTIG: Session immer schließen
    
    try:
        # Registriere Handler mit Session Factory
        event_publisher.subscribe(
            DocumentRejectedEvent,
            SessionBasedHandler(DocumentRejectedEventHandler, SessionLocal)
        )
        event_publisher.subscribe(
            DocumentDeletedEvent,
            SessionBasedHandler(DocumentDeletedEventHandler, SessionLocal)
        )
        event_publisher.subscribe(
            DocumentArchivedEvent,
            SessionBasedHandler(DocumentArchivedEventHandler, SessionLocal)
        )
        event_publisher.subscribe(
            DocumentVersionArchivedEvent,
            SessionBasedHandler(DocumentVersionArchivedEventHandler, SessionLocal)
        )
        
        # NEU: Archiv-System Event Handler
        # DocumentRestoredEvent: Optional Re-Indexierung (wenn restored_to_status == APPROVED)
        # TODO: IndexApprovedDocumentUseCase für Re-Indexierung hinzufügen
        # Aktuell: Nur Logging (Re-Indexierung kann später implementiert werden)
        from contexts.ragintegration.application.use_cases import IndexApprovedDocumentUseCase
        # TODO: IndexApprovedDocumentUseCase initialisieren für DocumentRestoredEventHandler
        # Für jetzt: Handler ohne Re-Indexierung (nur Logging)
        # event_publisher.subscribe(
        #     DocumentRestoredEvent,
        #     SessionBasedHandler(DocumentRestoredEventHandler, SessionLocal)
        # )
        
        # DocumentHardDeletedEvent: Optional Audit/Backup (aktuell: kein Handler nötig)
        # Kann später für Compliance-Logging verwendet werden
        
        print("✅ Event Handler registriert: RAG Cleanup für Document Lifecycle Events")
        print("✅ Archiv-System Events: DocumentRestoredEvent, DocumentHardDeletedEvent (Handler optional)")
        
    except Exception as e:
        # Bei Fehler: Logge Warnung, aber breche nicht ab
        # System sollte auch ohne RAG Cleanup funktionieren
        print(f"WARNING: Event Handler Setup fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()

