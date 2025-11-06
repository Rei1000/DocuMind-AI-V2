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
    # WICHTIG: Document Lifecycle Event Handlers wurden entfernt/refactored
    # Die Handler werden direkt in den Use Cases aufgerufen, nicht mehr über Events
    # Diese Registrierung ist daher nicht mehr nötig
    
    from backend.app.database import SessionLocal
    
    try:
        # Document Lifecycle Events werden jetzt direkt in den Use Cases behandelt
        # Keine Event-basierte Handler-Registrierung mehr nötig
        print("✅ Document Lifecycle Events werden direkt in Use Cases behandelt (keine Handler-Registrierung nötig)")
        
        # ============================================================================
        # RAG AUDIT-TRAIL EVENT HANDLERS (PHASE 1.2)
        # ============================================================================
        
        from contexts.ragintegration.application.event_handlers import RAGAuditEventHandler
        from contexts.ragintegration.application.use_cases import LogRAGActionUseCase
        from contexts.ragintegration.infrastructure.repositories import SQLAlchemyRAGAuditLogRepository
        from contexts.ragintegration.domain.events import (
            ChunkingStartedEvent,
            ChunkingCompletedEvent,
            ChunkingFailedEvent,
            IndexingStartedEvent,
            IndexingCompletedEvent,
            IndexingFailedEvent,
            QueryExecutedEvent,
            FeedbackSubmittedEvent  # PHASE 4.1: Feedback Events
        )
        
        # Erstelle Audit Handler mit Session Factory
        class SessionBasedAuditHandler:
            """Wrapper Handler für Audit-Logging mit Session Management."""
            def __init__(self, session_local):
                self.session_local = session_local
            
            async def handle(self, event):
                """Erstelle Audit Handler mit neuer Session für dieses Event."""
                db_session = self.session_local()
                try:
                    audit_repo = SQLAlchemyRAGAuditLogRepository(db_session)
                    log_use_case = LogRAGActionUseCase(audit_repo)
                    audit_handler = RAGAuditEventHandler(log_use_case)
                    
                    # Route Event zu entsprechendem Handler
                    if isinstance(event, ChunkingStartedEvent):
                        await audit_handler.handle_chunking_started(event)
                    elif isinstance(event, ChunkingCompletedEvent):
                        await audit_handler.handle_chunking_completed(event)
                    elif isinstance(event, ChunkingFailedEvent):
                        await audit_handler.handle_chunking_failed(event)
                    elif isinstance(event, IndexingStartedEvent):
                        await audit_handler.handle_indexing_started(event)
                    elif isinstance(event, IndexingCompletedEvent):
                        await audit_handler.handle_indexing_completed(event)
                    elif isinstance(event, IndexingFailedEvent):
                        await audit_handler.handle_indexing_failed(event)
                    elif isinstance(event, QueryExecutedEvent):
                        await audit_handler.handle_query_executed(event)
                    elif isinstance(event, FeedbackSubmittedEvent):
                        await audit_handler.handle_feedback_submitted(event)
                finally:
                    db_session.close()
        
        # Registriere Audit Handler für alle RAG Events
        audit_handler_wrapper = SessionBasedAuditHandler(SessionLocal)
        
        event_publisher.subscribe(ChunkingStartedEvent, audit_handler_wrapper)
        event_publisher.subscribe(ChunkingCompletedEvent, audit_handler_wrapper)
        event_publisher.subscribe(ChunkingFailedEvent, audit_handler_wrapper)
        event_publisher.subscribe(IndexingStartedEvent, audit_handler_wrapper)
        event_publisher.subscribe(IndexingCompletedEvent, audit_handler_wrapper)
        event_publisher.subscribe(IndexingFailedEvent, audit_handler_wrapper)
        event_publisher.subscribe(QueryExecutedEvent, audit_handler_wrapper)
        event_publisher.subscribe(FeedbackSubmittedEvent, audit_handler_wrapper)  # PHASE 4.1: Feedback Events
        
        print("✅ RAG Audit-Trail Event Handler registriert: Chunking, Indexing, Query, Feedback Events")
        
    except Exception as e:
        # Bei Fehler: Logge Warnung, aber breche nicht ab
        # System sollte auch ohne RAG Cleanup funktionieren
        print(f"WARNING: Event Handler Setup fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()

