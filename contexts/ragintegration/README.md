# 💬 RAG Integration Context

> **Bounded Context:** ragintegration  
> **Verantwortlichkeit:** RAG Chat, Vector Store, OCR/Vision Processing, Document Chunking  
> **Status:** 🚧 In Entwicklung (v2.1.0)

---

## 🎯 Verantwortlichkeit

Dieser Context ist verantwortlich für:
- **RAG Chat:** Fragen zu QMS-Dokumenten beantworten
- **Vector Store:** Qdrant (lokal, in-memory)
- **OCR Processing:** Tesseract (lokal)
- **Vision Processing:** GPT-4o Vision, Gemini
- **Document Chunking:** TÜV-Audit-taugliche Strategie (Absatz + Satz-Überlappung)
- **Hybrid Search:** Keyword + Semantic Search
- **Chat-Sessions:** Persistent, pro User
- **Source-Links:** Präzise Quellenangaben (Seite + Absatz)

---

## 📦 Entities

### **IndexedDocument**
```python
@dataclass
class IndexedDocument:
    """Im RAG-System indexiertes Dokument"""
    id: int
    upload_document_id: int  # Nur freigegebene Dokumente
    qdrant_collection_name: str
    total_chunks: int
    indexed_at: datetime
    last_updated_at: datetime
    embedding_model: str  # z.B. 'text-embedding-3-small'
```

### **DocumentChunk**
```python
@dataclass
class DocumentChunk:
    """Einzelner Chunk eines Dokuments (TÜV-Audit-tauglich)"""
    id: int
    rag_indexed_document_id: int
    chunk_id: str  # z.B. '123_p1_c0'
    chunk_text: str
    page_number: int
    paragraph_index: int
    chunk_index: int
    token_count: int
    sentence_count: int
    has_overlap: bool
    overlap_sentence_count: int
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
    created_at: datetime
    last_message_at: datetime
    is_active: bool
```

### **ChatMessage**
```python
@dataclass
class ChatMessage:
    """Einzelne Chat-Nachricht"""
    id: int
    session_id: int
    role: str  # 'user' oder 'assistant'
    content: str
    source_chunks: List[str]  # JSON Array von chunk_ids
    created_at: datetime
```

---

## 🎯 Use Cases

### **IndexDocumentUseCase**
- **Input:** WorkflowDocumentId
- **Output:** IndexedDocument
- **Logic:**
  1. Lade freigegebenes Dokument
  2. Führe OCR/Vision Processing aus
  3. Chunking (Audit-Compliant Strategy)
  4. Generiere Embeddings (OpenAI)
  5. Speichere in Qdrant
  6. Erstelle IndexedDocument + DocumentChunks
  7. Publiziere `DocumentIndexedEvent`

### **SearchDocumentsUseCase**
- **Input:** SearchQuery, UserId
- **Output:** List[DocumentChunk] (mit Relevanz-Score)
- **Logic:**
  1. Prüfe Permission (filtere nach Interest Groups)
  2. Hybrid Search:
     - Semantic Search (Qdrant)
     - Keyword Search (SQLite FTS)
  3. Merge Results
  4. Returniere Top-K Chunks

### **AskQuestionUseCase** (RAG Chat)
- **Input:** Question, SessionId, UserId
- **Output:** ChatMessage (Assistant)
- **Logic:**
  1. Prüfe Permission
  2. Suche relevante Chunks (SearchDocumentsUseCase)
  3. Baue Prompt mit Kontext
  4. Sende an AI Model (GPT-4o oder Gemini)
  5. Parse Antwort
  6. Speichere User + Assistant Messages
  7. Returniere Antwort mit Source-Links

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

---

## 🔌 API Endpoints

| Method | Endpoint | Beschreibung | Permission |
|--------|----------|--------------|------------|
| `POST` | `/api/rag/chat` | Chat-Nachricht senden | Level 1-4 |
| `GET` | `/api/rag/sessions` | Chat-Sessions | Level 1-4 |
| `GET` | `/api/rag/sessions/{id}` | Chat-History | Level 1-4 |
| `POST` | `/api/rag/sessions` | Neue Session | Level 1-4 |
| `DELETE` | `/api/rag/sessions/{id}` | Session löschen | Level 1-4 |
| `GET` | `/api/rag/search` | Direkte Suche | Level 2-4 |

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

## 🧩 Chunking-Strategie (TÜV-Audit-tauglich)

### **AuditCompliantChunkingStrategy**

**Prinzipien:**
1. **Semantische Einheiten:** Absätze respektieren
2. **Satz-Grenzen:** NIEMALS brechen
3. **Überlappung:** 2 Sätze für Kontext-Erhaltung
4. **Präzise Metadaten:** Seite, Absatz, Chunk-ID, Token-Count

**Parameter:**
- **Max Tokens:** 512 (Balance zwischen Kontext und Präzision)
- **Überlappung:** 2 Sätze (ca. 50-100 Tokens)
- **Min Chunk Size:** 50 Tokens (verhindert zu kleine Chunks)

**Beispiel:**
```
Chunk 1 (Seite 1, Absatz 1):
"1. Klebeflächen an Bauteilen mit Aceton entfetten. 
Achtung! Sicherheitsvorschriften z.B. offenes Fenster, 
Abzug und Handschuhe beachten."

Chunk 2 (Seite 1, Absatz 2, mit Überlappung):
"Achtung! Sicherheitsvorschriften z.B. offenes Fenster, 
Abzug und Handschuhe beachten. 2. Sicherungsringe (b) 
in die beiden mittleren Einstiche von Freilaufwelle setzen."
```

**Metadaten pro Chunk:**
```json
{
  "chunk_id": "123_p1_c0",
  "document_id": 123,
  "document_title": "AA 006 [00] 130317 - Montage Antriebseinheit SB3",
  "page_number": 1,
  "paragraph_index": 1,
  "chunk_index": 0,
  "token_count": 45,
  "sentence_count": 2,
  "has_overlap": false,
  "overlap_sentence_count": 0
}
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

- [x] Context-Struktur erstellt
- [x] README.md dokumentiert
- [ ] Qdrant Setup (Docker Container, später)
- [ ] Domain Model (Entities, Value Objects, Services)
- [ ] Use Cases
- [ ] Event Handlers
- [ ] Infrastructure (OCR, Vision, Chunking, Embeddings, Qdrant)
- [ ] Job Queue (Celery, später)
- [ ] API Routes
- [ ] Tests
- [ ] Frontend Integration

---

## 📚 Weiterführende Links

- **Roadmap:** `docs/ROADMAP_DOCUMENT_UPLOAD.md` (Phase 4)
- **User Manual:** `docs/user-manual/03-rag-chat.md`
- **Architecture:** `docs/architecture.md`
- **Chunking-Strategie:** Siehe oben (TÜV-Audit-tauglich)

---

**Last Updated:** 2025-10-13  
**Phase:** 1 (Foundation)

