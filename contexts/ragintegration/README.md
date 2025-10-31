# 💬 RAG Integration Context

> **Bounded Context:** ragintegration  
> **Verantwortlichkeit:** RAG Chat, Vector Store, Document Indexing, Semantic Search, Chat Sessions  
> **Status:** ✅ Vollständig implementiert (v2.1.0)

---

## 🎯 Verantwortlichkeit

Dieser Context ist verantwortlich für:
- **RAG Chat:** Intelligente Fragen zu QMS-Dokumenten beantworten
- **Vector Store:** Qdrant (in-memory, 1536-Dimension Embeddings)
- **Document Indexing:** Automatische Indexierung freigegebener Dokumente
- **Vision Processing:** GPT-4o Vision, Gemini für strukturierte Daten-Extraktion
- **Document Chunking:** Intelligente Chunking-Strategie (Vision-AI + Fallbacks)
- **Hybrid Search:** Vektor + Text-Suche mit Re-Ranking
- **Chat-Sessions:** Persistent, pro User mit Historie
- **Source-Links:** Präzise Quellenangaben mit Preview-Modal
- **Multi-Model Support:** GPT-4o Mini, GPT-5 Mini (Fallback zu GPT-4o Mini), Gemini 2.5 Flash

---

## 📦 Entities

### **IndexedDocument**
```python
@dataclass
class IndexedDocument:
    """Im RAG-System indexiertes Dokument"""
    id: int
    upload_document_id: int  # Nur freigegebene Dokumente
    document_title: str
    document_type: str
    qdrant_collection_name: str
    total_chunks: int
    status: str  # 'indexed', 'processing', 'failed'
    indexed_at: datetime
    last_updated: datetime
    embedding_model: str  # 'text-embedding-3-small'
    chunking_strategy: str  # 'vision_ai', 'page_boundary', 'plain_text'
```

### **DocumentChunk**
```python
@dataclass
class DocumentChunk:
    """Einzelner Chunk eines Dokuments mit Metadaten"""
    id: int
    indexed_document_id: int
    chunk_id: str  # z.B. '123_p1_c0'
    chunk_text: str
    metadata: ChunkMetadata  # Page-Numbers, Heading-Hierarchy, Confidence
    qdrant_point_id: str  # UUID in Qdrant
    embedding_vector_preview: str  # Erste 10 Dimensionen (Debug)
    created_at: datetime
```

### **ChatSession**
```python
@dataclass
class ChatSession:
    """Chat-Session eines Users"""
    id: int
    user_id: int
    session_name: str
    message_count: int
    created_at: datetime
    last_message_at: datetime
    is_active: bool
```

### **ChatMessage**
```python
@dataclass
class ChatMessage:
    """Einzelne Chat-Nachricht mit Source-References"""
    id: int
    session_id: int
    role: str  # 'user' oder 'assistant'
    content: str
    source_references: List[SourceReference]  # Quellen mit Relevanz-Score
    structured_data: List[dict]  # Strukturierte Daten (Tabellen, Listen)
    ai_model_used: str  # GPT-4o Mini, GPT-5 Mini, Gemini
    created_at: datetime
```

---

## 🎯 Use Cases

### **IndexApprovedDocumentUseCase**
- **Input:** UploadDocumentId
- **Output:** IndexedDocument + DocumentChunks
- **Logic:**
  1. Prüfe ob Dokument freigegeben ist
  2. **Lade Vision AI Processing Results** (bereits mit Standard-Prompt strukturiert)
  3. **Prompt-basierte Chunking-Strategie:** 
     - Analysiert den aktiven Standard-Prompt für den Dokumenttyp
     - Erkennt JSON-Struktur aus Prompt (steps, process_steps, nodes, etc.)
     - Wählt optimale Chunking-Strategie basierend auf Prompt-Struktur
     - **Game Changer:** Jeder Dokumenttyp hat individuelle Strukturierung
     - **Auto-Update:** Wenn Prompt geändert wird, wird Struktur automatisch aktualisiert
  4. Intelligentes Chunking (Vision-AI → Prompt-basiert → Page-Boundary → Plain-Text)
  5. Generiere Embeddings (OpenAI text-embedding-3-small)
  6. Speichere in Qdrant Vector Store
  7. Erstelle IndexedDocument + DocumentChunks
  8. Publiziere `DocumentIndexedEvent`
  
  **WICHTIG - Prompt-Integration Workflow:**
  - **Schritt 1 (Vision-Extraktion):** `ProcessDocumentPageUseCase` verwendet Standard-Prompt für Dokumenttyp
    → AI extrahiert strukturierte JSON gemäß Prompt-Vorgabe
  - **Schritt 2 (Chunking):** `DocumentTypeSpecificChunkingService` analysiert Standard-Prompt
    → Erkennt JSON-Struktur (z.B. `"steps"` für Arbeitsanweisung, `"nodes"` für Flussdiagramm)
    → Wählt optimale Chunking-Strategie
  - **Ergebnis:** Strukturierte, dokumenttyp-spezifische Chunks für optimale Vector-Search

### **AskQuestionUseCase** (RAG Chat)
- **Input:** Question, SessionId, UserId, AIModel
- **Output:** ChatMessage (Assistant) mit Source-References
- **Logic:**
  1. **Frage-Normalisierung:** Entfernt Stop-Wörter ("und", "aber", "oder") am Anfang für konsistentere Vector-Search
  2. Prüfe Permission (filtere nach Interest Groups)
  3. Multi-Query Expansion für bessere Suche (verwendet normalisierte Frage)
  4. Hybrid Search (Qdrant + Text-Scoring) mit erweitertem Context (Top 10 Chunks)
  5. Re-Ranking der Ergebnisse
  6. Baue Prompt mit Kontext
  7. **Speichere User-Nachricht** (Frage) in Datenbank
  8. Sende an AI Model (GPT-4o Mini, GPT-5 Mini mit Fallback, Gemini)
  9. Extrahiere strukturierte Daten
  10. **Speichere Assistant-Message** mit `ai_model_used` Tracking
  11. Returniere Antwort mit Source-Links

### **CreateChatSessionUseCase**
- **Input:** UserId, SessionName
- **Output:** ChatSession
- **Logic:**
  1. Erstelle neue Session
  2. Speichere in Datenbank
  3. Returniere Session

### **GetChatHistoryUseCase**
- **Input:** SessionId, UserId
- **Output:** List[ChatMessage]
- **Logic:**
  1. Prüfe Permission (User ist Owner)
  2. Lade alle Messages der Session
  3. Returniere chronologisch sortiert

### **ReindexDocumentUseCase**
- **Input:** IndexedDocumentId, ForceReindex
- **Output:** Updated IndexedDocument
- **Logic:**
  1. Lösche alte Chunks aus Qdrant
  2. Führe neue Indexierung durch
  3. Aktualisiere IndexedDocument
  4. Returniere aktualisierte Daten

---

## 🔌 API Endpoints

| Method | Endpoint | Beschreibung | Permission |
|--------|----------|--------------|------------|
| `POST` | `/api/rag/documents/index` | Dokument indexieren | Level 2-4 |
| `POST` | `/api/rag/chat/ask` | Frage stellen | Level 1-4 |
| `POST` | `/api/rag/chat/sessions` | Neue Session erstellen | Level 1-4 |
| `GET` | `/api/rag/chat/sessions/{id}/history` | Chat-Historie | Level 1-4 |
| `POST` | `/api/rag/search` | Dokumente suchen | Level 2-4 |
| `POST` | `/api/rag/documents/{id}/reindex` | Re-indexieren | Level 2-4 |
| `GET` | `/api/rag/system/info` | System-Info | Level 1-4 |
| `GET` | `/api/rag/health` | Health Check | Level 1-4 |

---

## 📡 Domain Events

### **DocumentIndexedEvent**
```python
@dataclass
class DocumentIndexedEvent:
    """Event: Dokument wurde indexiert"""
    indexed_document_id: int
    upload_document_id: int
    total_chunks: int
    timestamp: datetime
```

**Subscribers:**
- `documentupload.DocumentIndexedEventHandler` → Aktualisiert Upload-Status

### **ChunkCreatedEvent**
```python
@dataclass
class ChunkCreatedEvent:
    """Event: Chunk wurde erstellt"""
    chunk_id: str
    indexed_document_id: int
    page_number: int
    paragraph_index: int
    timestamp: datetime
```

---

## 🔗 Dependencies

### **Domain Events:**
- **Incoming:** `documentupload.DocumentApprovedEvent` → Startet Indexierung

### **External Contexts:**
- **documentupload:** Liest freigegebene Dokumente
- **documentupload:** Liest Original-Dateien für OCR/Vision
- **users:** Validiert User IDs, prüft Permissions
- **interestgroups:** Filtert Dokumente nach Interest Groups (Level 1)

### **Infrastructure:**
- **Qdrant:** Vector Database (Docker Container, später)
- **OpenAI:** Embeddings (text-embedding-3-small), Chat (GPT-4o)
- **Google AI:** Gemini (alternative)
- **Tesseract:** OCR (lokal)
- **Celery:** Job Queue für async Processing (später)

---

## 🧩 Chunking-Strategie (Intelligente Multi-Level)

### **HeadingAwareChunkingService**

**3-Level Fallback-Strategie:**

#### **Level 1: Vision-AI-basiert (Primär)**
- Nutzt strukturierte JSON-Response aus Vision AI Processing
- Respektiert natürliche Absätze und Überschriften
- Maximale semantische Kohärenz
- **Parameter:** Max 1000 Zeichen pro Chunk

#### **Level 2: Page-Boundary-aware (Fallback)**
- Respektiert Seiten-Grenzen
- Absatz-basiert mit Satz-Überlappung
- **Parameter:** Max 1000 Zeichen, 2 Sätze Überlappung

#### **Level 3: Plain-Text (Notfall)**
- Einfache Text-Aufteilung
- **Parameter:** Max 1000 Zeichen pro Chunk

**Metadaten pro Chunk:**
```json
{
  "chunk_id": "123_p1_c0",
  "page_numbers": [1],
  "heading_hierarchy": ["1. Montage", "1.1 Vorbereitung"],
  "document_type": "Arbeitsanweisung",
  "confidence_score": 0.95,
  "chunk_type": "instruction",
  "token_count": 45
}
```

**Beispiel Vision-AI Chunking:**
```
Chunk 1 (Vision-AI strukturiert):
"1. Klebeflächen an Bauteilen mit Aceton entfetten.
Achtung! Sicherheitsvorschriften z.B. offenes Fenster, 
Abzug und Handschuhe beachten."

Chunk 2 (Vision-AI strukturiert):
"2. Sicherungsringe (b) in die beiden mittleren Einstiche 
von Freilaufwelle setzen. 3. Lager (c) auf Freilaufwelle 
schieben bis Anschlag."
```

---

## 🔐 Permission Policy

| Level | Rolle | RAG Chat | Sichtbare Dokumente |
|-------|-------|----------|---------------------|
| **1** | Angestellte | ✅ | Nur eigene Interest Groups |
| **2** | Teamleiter | ✅ | Alle freigegebenen Dokumente |
| **3** | Abteilungsleiter | ✅ | Alle freigegebenen Dokumente |
| **4** | QM | ✅ | Alle freigegebenen Dokumente |

---

## ✅ Status

- [x] **Domain Layer:** 4 Entities, 4 Value Objects, 4 Repository Interfaces, 3 Domain Events
- [x] **Application Layer:** 5 Use Cases, 3 Services (HeadingAwareChunking, MultiQuery, StructuredDataExtractor)
- [x] **Infrastructure Layer:** Qdrant Adapter, OpenAI Embedding Adapter, Vision Data Extractor, Hybrid Search Service, 4 SQLAlchemy Repositories
- [x] **Interface Layer:** 8 FastAPI Endpoints, Pydantic Schemas, Permission Checks
- [x] **Database:** 4 neue Tabellen mit Indizes und Triggers
- [x] **Frontend:** RAG Chat Dashboard, Session Sidebar, Filter Panel, Source Preview Modal, Document Integration
- [x] **TDD Testing:** Domain + Application Layer Tests (100% Coverage)
- [x] **Chunking-Strategie:** Intelligente Multi-Level Fallback-Strategie
- [x] **Multi-Model Support:** GPT-4o Mini, GPT-5 Mini, Gemini 2.5 Flash
- [x] **Document Integration:** RAG Indexierung Panel in Document Detail View
- [x] **Source Preview:** Vollbild-Preview mit Zoom-Funktionalität
- [x] **Structured Data:** Tabellen, Listen, Sicherheitshinweise Rendering
- [x] **Suggested Questions:** UX-Optimierung für bessere User Experience

---

## 📚 Weiterführende Links

- **Roadmap:** `docs/ROADMAP_DOCUMENT_UPLOAD.md` (Phase 4)
- **User Manual:** `docs/user-manual/03-rag-chat.md`
- **Architecture:** `docs/architecture.md`
- **Chunking-Strategie:** Siehe oben (TÜV-Audit-tauglich)

---

**Last Updated:** 2025-10-27  
**Phase:** 4 (RAG Integration) - **VOLLSTÄNDIG IMPLEMENTIERT** ✅

