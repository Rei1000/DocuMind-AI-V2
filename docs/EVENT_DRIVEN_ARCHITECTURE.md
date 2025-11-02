# 🎯 Event-Driven Architecture - Integration & Vorteile

> **Status:** 💭 Dokumentation & Konzept  
> **Erstellt:** 2025-11-02  
> **Phase:** 5.5 - RAG Cleanup Event-Driven Integration

---

## 📊 Aktueller Zustand

### ✅ **Was bereits implementiert ist:**

1. **Domain Events** (documentupload Context):
   - `DocumentRejectedEvent`
   - `DocumentDeletedEvent`
   - `DocumentArchivedEvent`
   - `DocumentVersionArchivedEvent`

2. **Event Publishing** (documentupload Use Cases):
   - Alle Use Cases können Events publizieren
   - EventPublisher als optionaler Parameter (Dependency Injection)

3. **Event Handler** (ragintegration Context):
   - `DocumentRejectedEventHandler`
   - `DocumentDeletedEventHandler`
   - `DocumentArchivedEventHandler`
   - `DocumentVersionArchivedEventHandler`
   - Alle rufen `RemoveDocumentFromRAGUseCase` auf

### ❌ **Was noch fehlt (Integration Layer):**

**Event Publisher Implementation** die Events weiterleitet + **Handler Registration**

---

## 🔗 Die Integration

### **Aktueller Flow (ohne Integration):**

```
┌─────────────────────────────────┐
│ RejectDocumentUseCase           │
│  ↓                               │
│  await event_publisher.publish( │
│    DocumentRejectedEvent(...)    │
│  )                               │
└─────────────────────────────────┘
          ↓
     [EventPublisher]
          ↓
     ❌ NOP (No Operation)
          ↓
     ❌ Event geht verloren!
```

### **Gewünschter Flow (mit Integration):**

```
┌─────────────────────────────────┐
│ RejectDocumentUseCase           │
│  ↓                               │
│  await event_publisher.publish( │
│    DocumentRejectedEvent(...)    │
│  )                               │
└─────────────────────────────────┘
          ↓
┌─────────────────────────────────┐
│ InMemoryEventPublisher           │
│  (Event Bus Implementation)      │
│  ↓                               │
│  - Event Queue                   │
│  - Handler Registry              │
│  - Event Routing                 │
└─────────────────────────────────┘
          ↓
┌─────────────────────────────────┐
│ DocumentRejectedEventHandler    │
│  (ragintegration Context)        │
│  ↓                               │
│  remove_document_use_case.       │
│    execute(document_id=1)        │
│  ↓                               │
│  ✅ RAG Cleanup erfolgt!         │
└─────────────────────────────────┘
```

---

## 🏗️ Integration Implementation

### **1. Event Publisher Implementation**

```python
# contexts/documentupload/infrastructure/event_publisher.py

class InMemoryEventPublisher:
    """
    In-Memory Event Publisher Implementation.
    
    WICHTIG: Für Production sollte Message Queue verwendet werden
    (z.B. RabbitMQ, Redis, Apache Kafka).
    """
    
    def __init__(self):
        self._handlers = {}  # event_type -> [handlers]
    
    def subscribe(self, event_type: type, handler):
        """Registriere Handler für Event-Typ."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    async def publish(self, event):
        """Publiziere Event an alle registrierten Handler."""
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])
        
        for handler in handlers:
            try:
                await handler.handle(event)
            except Exception as e:
                # Logge Fehler, aber breche nicht ab
                print(f"ERROR: Handler failed for {event_type.__name__}: {e}")
```

### **2. Handler Registration (Bootstrap)**

```python
# backend/app/main.py oder backend/app/events.py

def setup_event_handlers(event_publisher):
    """
    Registriere alle Event Handler.
    
    WICHTIG: Diese Funktion verbindet Events mit Handlern,
    ohne Cross-Context Imports zu benötigen!
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
    db_session = SessionLocal()
    indexed_doc_repo = SQLAlchemyIndexedDocumentRepository(db_session)
    chunk_repo = SQLAlchemyDocumentChunkRepository(db_session)
    vector_store = QdrantVectorStoreAdapter()
    
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
```

### **3. FastAPI Dependency Injection**

```python
# contexts/documentupload/interface/workflow_router.py

# Globale Event Publisher Instanz
_event_publisher = None

def get_event_publisher() -> EventPublisher:
    """Dependency für Event Publisher."""
    global _event_publisher
    if _event_publisher is None:
        from contexts.documentupload.infrastructure.event_publisher import (
            InMemoryEventPublisher
        )
        from backend.app.events import setup_event_handlers
        
        _event_publisher = InMemoryEventPublisher()
        setup_event_handlers(_event_publisher)
    
    return _event_publisher

@router.post("/reject", response_model=RejectDocumentResponse)
async def reject_document(
    request: RejectDocumentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    event_publisher: EventPublisher = Depends(get_event_publisher)  # NEU
):
    # ...
    use_case = RejectDocumentUseCase(
        upload_repository=upload_repo,
        comment_repository=comment_repo,
        event_publisher=event_publisher  # NEU: Event Publisher wird injiziert
    )
    # ...
```

---

## ✨ Vorteile der Event-Driven Architecture

### **1. Lose Kopplung (Loose Coupling)**

**Ohne Events (Tight Coupling):**
```python
# ❌ SCHLECHT: Direkter Import
from contexts.ragintegration.application.use_cases import RemoveDocumentFromRAGUseCase

class RejectDocumentUseCase:
    def __init__(self, ..., rag_cleanup_use_case):  # ❌ Hard Dependency
        self.rag_cleanup_use_case = rag_cleanup_use_case
```

**Mit Events (Loose Coupling):**
```python
# ✅ GUT: Keine direkten Abhängigkeiten
class RejectDocumentUseCase:
    def __init__(self, ..., event_publisher=None):  # ✅ Optional
        self.event_publisher = event_publisher
    
    async def execute(...):
        # ...
        if self.event_publisher:  # ✅ Kann None sein (optional)
            await self.event_publisher.publish(DocumentRejectedEvent(...))
```

**Vorteil:** Contexts können unabhängig entwickelt/getestet werden!

---

### **2. Skalierbarkeit & Erweiterbarkeit**

**Neue Handler hinzufügen ohne Code-Änderung:**

```python
# Neuer Handler für Analytics
class DocumentRejectedAnalyticsHandler:
    async def handle(self, event):
        # Track rejection für Analytics Dashboard
        analytics.track_event("document_rejected", event.document_id)

# Registration (ohne RejectDocumentUseCase zu ändern!)
event_publisher.subscribe(
    DocumentRejectedEvent,
    DocumentRejectedAnalyticsHandler()
)
```

**Vorteil:** Neue Features ohne bestehende Use Cases zu ändern!

---

### **3. Asynchrone Verarbeitung**

```python
# Events können asynchron verarbeitet werden
async def publish(self, event):
    # Fire-and-Forget oder Queue für später
    await self._event_queue.put(event)  # Non-blocking
```

**Vorteil:** API Response bleibt schnell, langsame RAG Cleanup läuft im Hintergrund!

---

### **4. Testbarkeit**

**Unit Tests ohne echte Handler:**

```python
# Test: Event wird publiziert (Handler-Mock)
mock_publisher = Mock()
use_case = RejectDocumentUseCase(..., event_publisher=mock_publisher)
await use_case.execute(...)
assert mock_publisher.publish.called
```

**Integration Tests mit echten Handlern:**

```python
# Test: Vollständiger Flow
event_publisher = InMemoryEventPublisher()
setup_event_handlers(event_publisher)  # Echte Handler
# ...
# RAG Cleanup wird wirklich ausgeführt
```

**Vorteil:** Tests auf verschiedenen Ebenen möglich!

---

### **5. Fehler-Isolation**

```python
async def publish(self, event):
    handlers = self._handlers.get(type(event), [])
    for handler in handlers:
        try:
            await handler.handle(event)
        except Exception as e:
            # Handler-Fehler bremsen andere Handler nicht
            logger.error(f"Handler {handler} failed: {e}")
            # Andere Handler werden trotzdem ausgeführt!
```

**Vorteil:** Wenn RAG Cleanup fehlschlägt, ist die Rejection trotzdem erfolgreich!

---

### **6. DDD-Konformität**

✅ **Keine Cross-Context Imports**  
✅ **Bounded Contexts bleiben unabhängig**  
✅ **Domain Events als Kommunikations-Mittel**  
✅ **Application Services orchestrieren Events**  

---

## 🔄 Vergleich: Mit vs. Ohne Integration

### **OHNE Integration (aktuell):**

```
User → API → RejectDocumentUseCase
              ↓
         event_publisher = None
              ↓
         ❌ Event wird NICHT publiziert
              ↓
         ❌ RAG Cleanup erfolgt NICHT
```

**Problem:** Events werden publiziert, aber niemand hört zu!

### **MIT Integration:**

```
User → API → RejectDocumentUseCase
              ↓
         event_publisher.publish(DocumentRejectedEvent)
              ↓
         InMemoryEventPublisher
              ↓
         DocumentRejectedEventHandler.handle()
              ↓
         RemoveDocumentFromRAGUseCase.execute()
              ↓
         ✅ RAG Cleanup erfolgt!
```

**Ergebnis:** Vollständig automatisiertes RAG Cleanup!

---

## 📋 Zusammenfassung

### **Was implementiert werden muss:**

1. ✅ **Domain Events** - DONE
2. ✅ **Event Publishing** - DONE
3. ✅ **Event Handler** - DONE
4. ❌ **Event Publisher Implementation** - TODO
5. ❌ **Handler Registration** - TODO
6. ❌ **FastAPI Dependency Injection** - TODO

### **Vorteile im Überblick:**

| Aspekt | Vorteil |
|--------|---------|
| **Kopplung** | Lose Kopplung zwischen Contexts |
| **Skalierung** | Neue Handler ohne Code-Änderung |
| **Performance** | Asynchrone Verarbeitung möglich |
| **Tests** | Einfache Mocking & Integration Tests |
| **Fehler** | Isolation zwischen Handlern |
| **DDD** | 100% konform mit DDD-Regeln |

---

**Erstellt von:** AI Assistant  
**Datum:** 2025-11-02  
**Status:** Bereit für Implementation 🚀

