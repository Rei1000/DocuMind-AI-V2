# 💬 RAG Integration Context

> **Bounded Context:** ragintegration  
> **Verantwortlichkeit:** RAG Chat, Vector Store, Document Indexing, Semantic Search, Chat Sessions, **RAG UX Transparency**, **ECHTE SHAP-Integration**, **Learning-to-Rank ML-Pipeline**, **Custom RAG Chat Prompts (CR-P2.2)**, **Einheitliches Embedding-Modell**  
> **Status:** ✅ Vollständig implementiert (v2.8.0) - **RAG UX Transparency PHASE 1-4 + ECHTE SHAP-Attribution + LTR ML-Ranking + GPT-5 Strict Mode + Custom RAG Chat Prompts + Einheitliches Embedding-Modell**  
> **Version:** 2.8.0  
> **Stand:** 2025-01-27

**NEU (v2.8.0 - 2025-01-27):**
- ✅ **Einheitliches Embedding-Modell:** text-embedding-3-small als Standard für alle Dokumente
  - **Standard-Modell:** `text-embedding-3-small` (1536 Dimensionen, beste Qualität, günstig)
  - **Re-Indexierung:** Alle Dokumente wurden mit einheitlichem Modell re-indexiert
  - **Dimension-Check:** Dokumente mit falschen Dimensionen werden automatisch übersprungen
  - **Mock Embeddings Erkennung:** Automatische Erkennung und Re-Indexierung von Mock Embeddings
  - **Keine Fallbacks:** Explizite Fehlermeldungen statt stillem Fallback zu inkompatiblen Modellen
  - **Re-Indexierung Script:** `scripts/reindex_all_documents.py` für automatische Re-Indexierung
  - **Embedding-Modell Speicherung:** `embedding_model` wird in `IndexedDocument` gespeichert
  - **Qualitätsprüfung:** Automatische Prüfung auf echte Embeddings (negative Werte, hohe Variation)
  - **Status:** Alle 9 freigegebenen Dokumente sind mit text-embedding-3-small indexiert (316 Chunks total)

**NEU (v2.7.3 - 2025-11-17):**
- ✅ **Custom RAG Chat Prompts (CR-P2.2):** Vollständige Implementierung abgeschlossen
  - **Custom Prompt Management:** Level 4+ User können RAG Chat Prompts pro Dokumenttyp anpassen
  - **Strikte Custom-Prompt-Enforcement:** Wenn `document_type_id` gesetzt → Custom Prompt MUSS existieren (HTTP 422 bei Fehlen)
  - **Prompt-Editor UI:** Vorschau, Edit-Modus, Speichern/Löschen von Custom Prompts
  - **3 Prompt-Quellen:** Custom Prompts (rag_chat_prompts), Hardcoded Prompts (Fallback), Generischer Prompt (Fallback)
  - **API Endpoints:** GET/POST/DELETE `/api/rag/chat/prompts/{document_type_id}`
  - **Dokumentation:** Vollständige Analyse aller Prompt-Quellen in `docs/technical/RAG_CHAT_PROMPT_SOURCES_ANALYSIS.md`
  - **Fix:** Backend akzeptiert jetzt sowohl document_type ID als auch Name für korrekte Prompt-Erkennung

**NEU (v2.7.1 - 2025-11-17):**
- ✅ **GPT-5 Mini Strict Mode:** Strikte API-Key-Validierung ohne Fallback
  - Dedizierter `OpenAIAdapter` für GPT-5 Mini mit `OPENAI_GPT5_MINI_API_KEY`
  - Adapter-Registry in `RAGAIService` für Multi-Key-Support
  - RuntimeError bei fehlendem Key (kein automatischer Fallback zu GPT-4o Mini)
  - Breaking Change: `OpenAIAdapter` erfordert jetzt ENV-Variable (kein `api_key` Parameter mehr)
- ✅ **QDRANT_URL Environment-Variable Parsing:** Docker-Netzwerk-Support
  - Unterstützt `host:port`, `http://host:port`, `https://host:port` Formate
  - Default: `localhost:6333` wenn `QDRANT_URL` nicht gesetzt
  - Ermöglicht Docker-Compose Integration (`QDRANT_URL=http://qdrant:6333`)
- ✅ **Test-Fixes:** IndexError-Prävention und Mock-Handling
  - Defensive Checks für leere `context_chunks` Listen
  - Explizites Setzen von `source_references` für Test-Kompatibilität
  - 8/8 Tests grün (test_final_score_fallback.py, test_qdrant_url_resolution.py)
- ✅ **Custom RAG Chat Prompts (CR-P2.2):** Dokumenttyp-spezifische Prompt-Verwaltung
  - **Custom Prompt Management:** Level 4+ User können RAG Chat Prompts pro Dokumenttyp anpassen
  - **Strikte Custom-Prompt-Enforcement:** Wenn `document_type_id` gesetzt → Custom Prompt MUSS existieren (HTTP 422 bei Fehlen)
  - **Prompt-Editor UI:** Vorschau, Edit-Modus, Speichern/Löschen von Custom Prompts
  - **3 Prompt-Quellen:** Custom Prompts (rag_chat_prompts), Hardcoded Prompts (Fallback), Generischer Prompt (Fallback)
  - **API Endpoints:** GET/POST/DELETE `/api/rag/chat/prompts/{document_type_id}`
  - **Dokumentation:** Vollständige Analyse aller Prompt-Quellen in `docs/technical/RAG_CHAT_PROMPT_SOURCES_ANALYSIS.md`

**NEU (v2.7.0 - 2025-11-14):**
- ✅ **SQLite-Persistenz für ML/SHAP-Daten:** Migration von File/In-Memory zu SQLite
  - **3 neue Tabellen:** `training_samples`, `shap_background_data`, `shap_cache`
  - **TrainingDataRepositorySQLite:** Ersetzt FileBasedRepository (JSONL → SQLite)
    - Features als JSON in `features_json` (TEXT)
    - Format-Konvertierung für LTRTrainingPipeline-Kompatibilität
    - Statistik-Endpoint für Analytics
  - **SHAPBackgroundDataRepositorySQLite:** Ersetzt In-Memory Service
    - Rolling Window in SQLite (max 1000 Records)
    - Automatisches Löschen ältester Records
    - Export/Import zu JSON für Backup
  - **SHAPCacheRepositorySQLite:** Ersetzt In-Memory Cache
    - LRU Cache mit TTL (max 100 Einträge, 1 Stunde TTL)
    - UNIQUE Constraint auf `cache_key` (MD5 Hash)
    - Automatisches Cleanup abgelaufener Einträge
  - **Feature Flag:** `PERSIST_TO_DB=true` (default) für SQLite-Repositories
  - **Migration-Script:** `backend/app/migrations/add_ml_shap_tables.py` mit automatischem Backup
  - **Integration:** SubmitFeedbackUseCase, SHAPExplainerService, LTRTrainingPipeline
  - **34 neue Unit-Tests:** Alle SQLite-Repositories getestet (100% Coverage)
  - **Browser-Test:** System läuft, Repositories aktiv, Daten werden gespeichert

**NEU (v2.7.0 - 2025-11-13):**
- ✅ **Learning-to-Rank ML-Pipeline:** Echtes ML-Ranking für optimale Suchergebnisse
  - **11 ML-Features:** vector_score, text_score, bm25_score, jaccard_score, keyword_matches, chunk_length, document_type_encoded, heading_hierarchy_depth, confidence_score, user_level, hybrid_score
  - **LightGBM Ranker:** lambdarank objective für echtes Learning-to-Rank
  - **sklearn Fallback:** GradientBoostingRegressor (falls LightGBM nicht verfügbar)
  - **Training Pipeline:** Cross-Validation mit NDCG@k Metrics, Model Persistence
  - **Inference Service:** Model Serving, Auto-Loading, Feature-Extraction
  - **LTR Service Wrapper:** High-Level API für einfache Integration
  - **Final-Score Ranking:** 0.6 * hybrid_score + 0.4 * ml_score (konfigurierbar)
  - **UseCase Integration:** use_ml_ranking Parameter in AskQuestionUseCase
  - **ML kann Ranking ändern:** Chunks werden nach final_score sortiert (nicht nur hybrid)
- ✅ **Celery Background Jobs:** Asynchrone SHAP-Berechnungen
  - **Celery App:** Redis Broker/Backend (redis://localhost:6379/0 und /1)
  - **SHAP Background Task:** compute_shap_explanation mit Progress-Tracking (0-100%)
  - **Task-Status API:** GET /api/rag/shap-tasks/{task_id} für Polling
  - **Error Handling:** Retry mit Exponential Backoff (max 3 Retries)
  - **Timeout:** 120s Hard Limit, 100s Soft Limit
- ✅ **24/24 Tests GRÜN:**
  - 8 Tests: ML Feature Extractor
  - 5 Tests: Training Pipeline
  - 6 Tests: Inference Service  
  - 5 Tests: UseCase Integration
  - 100% Test-Coverage für LTR-Komponenten
- ✅ **TDD-basierte Entwicklung:**
  - RED → GREEN → REFACTOR
  - +4800 Zeilen Code (Backend + Tests)
  - 15 neue Commits

**NEU (v2.6.0 - 2025-11-13):**
- ✅ **ECHTE SHAP-Integration:** Mathematisch korrekte SHAP-Attribution für RAG-Rankings
  - **KernelExplainer** ersetzt heuristische Approximation
  - **7 Features:** vector_score, text_score, user_level, keyword_matches, chunk_length, heading_hierarchy_depth, confidence_score
  - **SHAP Property:** base_value + sum(shap_values) ≈ prediction (mathematisch korrekt)
- ✅ **Background Data Service:** Automatisches Sammeln historischer Search-Daten
  - Rolling Window (max 1000 Records)
  - Kontinuierliche Verbesserung der SHAP-Qualität
  - Export/Import zu JSON für Persistenz
- ✅ **Performance-Optimierung:** LRU Cache mit TTL
  - Cache Hit: ~0ms (instant)
  - Cache Miss: ~2000ms (SHAP-Berechnung)
  - 50-90% schneller bei wiederholten Queries
  - Max 100 Einträge, TTL: 1 Stunde
- ✅ **Interactive Analytics Dashboard:**
  - Feature Importance Bar Chart (sortiert nach Wichtigkeit)
  - SHAP Waterfall Visualisierung (Base Value → Prediction)
  - Background Data Statistics Grid
  - Cache Performance Monitoring
- ✅ **3 neue API Endpoints:**
  - `GET /api/rag/analytics/shap` - SHAP Analytics Dashboard
  - `GET /api/rag/analytics/shap/background-stats` - Background Data Stats
  - `GET /api/rag/analytics/shap/cache-stats` - Cache Performance Metrics
- ✅ **17/17 Tests GRÜN:**
  - 8 Unit Tests (test_shap_real_attribution.py)
  - 9 Integration Tests (test_shap_integration.py)
  - 100% Test-Coverage für SHAP-Komponenten
- ✅ **TDD-basierte Implementierung:**
  - RED → GREEN → REFACTOR
  - +2693 Zeilen Code (Backend + Frontend + Tests)
  - 5 neue Commits

**NEU (v2.5.1):**
- ✅ **RAG Chat Prompts:** Globale, dokumenttyp-spezifische Prompts (Level 4+ können anpassen)
  - `RAGChatPrompt` Entity - Prompt-Management für RAG Chat
  - `SaveRAGChatPromptUseCase` - Prompt speichern/aktualisieren
  - `GetRAGChatPromptUseCase` - Prompt abrufen (dokumenttyp-spezifisch)
  - `rag_chat_prompts` Tabelle - Persistente Speicherung
  - Multi-Query Prompt Support (`multi_query_prompt_text`)
- ✅ **Message Metadata:** JSON-Metadaten in Chat-Messages
  - `message_metadata` Feld in `rag_chat_messages` (JSON)
  - Enthält: `query_params`, `generated_queries`, `processing_time_ms`, `tokens_used`
  - Transparenz-Layer zeigt alle Metadaten an
- ✅ **Multi-Query Transparency:** Generierte Query-Varianten werden angezeigt
  - `generated_queries` in `message_metadata` gespeichert
  - RAG Transparency Layer zeigt alle generierten Queries an
- ✅ **Top-K Fix:** `top_k` Parameter wird korrekt angewendet (nach Deduplication und RBAC Filtering)
  - Problem: Bei mehreren indexierten Dokumenten wurden pro Dokument top_k Chunks geholt und zusammengeführt, aber nicht erneut auf top_k begrenzt
  - Lösung: Finale Begrenzung auf top_k nach allen Filtern (Deduplizierung + RBAC) hinzugefügt
  - Ergebnis: User erhält jetzt genau die gewünschte Anzahl an Chunks (z.B. 5 statt 24)

**NEU (v2.4.0):**
- ✅ **PHASE 1:** RAG Audit-Trail System
  - `RAGAuditLog` Entity - Vollständige Historie aller RAG-Operationen
  - `LogRAGActionUseCase` - Protokolliert Chunking, Indexing, Queries
  - `RAGAuditEventHandler` - Event-Driven Audit-Logging
  - 7 Domain Events: ChunkingStarted/Completed/Failed, IndexingStarted/Completed/Failed, QueryExecuted
- ✅ **PHASE 2:** Chunk-Vorschau & Editor
  - `ChunkPreviewResponse` - Read-Only Chunk-Vorschau
  - `EditChunkUseCase` - Chunk-Text bearbeiten
  - `SplitChunkUseCase` - Chunk in zwei Teile splitten
    - ⭐ **Overlap-Funktion:** 0-10 Overlap-Sätze zwischen gesplitteten Chunks
    - ⭐ **Intelligente Satz-Erkennung:** Automatische Satz-Trennung für Overlap
    - ⭐ **Metadaten:** `has_overlap` und `overlap_sentence_count` werden korrekt gespeichert
  - `MergeChunksUseCase` - Zwei Chunks zusammenführen
  - `DeleteChunkUseCase` - Chunk löschen (DB + Vector Store)
  - Chunking-Strategie Selector (OpenAI 1536, Gemini 768, Local 384)
  - ⭐ **Seitenweise AI-Verarbeitung:** `POST /api/document-upload/{id}/process-page/{page}` - Einzelne Seiten neu verarbeiten
  - ⭐ **Re-Indexierung:** Dokumente können nach AI-Verarbeitung vollständig neu indexiert werden
  - ⭐ **Strukturiertes Chunking:** JSON wird in lesbaren Text konvertiert (Fachartikel)
  - ⭐ **Diagramm-Beschreibung:** Figuren und Tabellen werden in Chunks integriert
- ✅ **PHASE 3:** RAG Chat Transparency
  - `PromptViewerResponse` - Vollständiger Prompt mit Kontext anzeigen
  - `RAGTransparencyLayer` - Sources, Metadata, Processing-Time, Tokens, Embedding-Info
- ✅ **PHASE 4.1:** User Feedback System
  - `RAGFeedback` Entity - User Feedback für Chat-Antworten
  - `SubmitFeedbackUseCase` - Feedback abgeben (Positive/Negative/Neutral)
  - `GetFeedbackStatisticsUseCase` - Feedback-Statistiken
  - `FeedbackSubmittedEvent` - Event-Driven Feedback-Logging
  - `RAGFeedbackButton` - Frontend-Komponente für Feedback
- ✅ **PHASE 4.2:** RAG Analytics Dashboard
  - `GetRAGAnalyticsUseCase` - Umfassende Analytics-Aggregation
  - Analytics Dashboard - Performance-Metriken, Quality-Score, Trends
  - Zeitbereich-Filterung (7d, 30d, 90d, all)

**NEU (v2.3.0):**
- ✅ Event-Driven RAG Cleanup Integration
  - `RemoveDocumentFromRAGUseCase` - Entfernt Vektoren aus Qdrant
  - 4 Event Handlers für Document Lifecycle Events
  - Idempotent (mehrfaches Aufrufen sicher)

---

## 🎯 Verantwortlichkeit

Dieser Context ist verantwortlich für:
- **RAG Chat:** Intelligente Fragen zu QMS-Dokumenten beantworten
- **Vector Store:** Qdrant (in-memory, dynamische Dimensionen: 1536/768/384)
- **Embedding Provider:** Intelligente Auto-Auswahl (OpenAI GPT-5 Mini Key > Google Gemini > Sentence Transformers)
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

### **RAG Audit Use Cases (PHASE 1)**
- `LogRAGActionUseCase` - Protokolliert RAG-Aktionen im Audit-Trail
- `GetAuditTrailUseCase` - Hole Audit-Trail für Dokument oder User

### **Chunk Editor Use Cases (PHASE 2)**
- `EditChunkUseCase` - Chunk-Text bearbeiten
- `DeleteChunkUseCase` - Chunk löschen (DB + Vector Store)
- `SplitChunkUseCase` - Chunk in zwei Teile splitten
  - **Overlap-Parameter:** `overlap_sentences` (0-10, Standard: 0)
  - **Funktionsweise:** Die letzten N Sätze von Chunk 1 werden am Anfang von Chunk 2 hinzugefügt und umgekehrt
  - **Metadaten:** Beide Chunks erhalten `has_overlap: true` und `overlap_sentence_count: N`
  - **Collection-Name:** Wird automatisch aus IndexedDocument geholt
- `MergeChunksUseCase` - Zwei Chunks zusammenführen

### **RAG Feedback Use Cases (PHASE 4.1)**
- `SubmitFeedbackUseCase` - User Feedback für Chat-Antwort abgeben
- `GetFeedbackStatisticsUseCase` - Hole Feedback-Statistiken

### **RAG Analytics Use Cases (PHASE 4.2)**
- `GetRAGAnalyticsUseCase` - Hole umfassende RAG Analytics (Feedback, Queries, Chunking, Indexing, Messages, Quality)

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
  5. Generiere Embeddings (Auto-Auswahl: OpenAI GPT-5 Mini Key > Google Gemini > Sentence Transformers)
  6. Speichere in Qdrant Vector Store
  7. Erstelle IndexedDocument + DocumentChunks
  8. Publiziere `DocumentIndexedEvent`

### **RemoveDocumentFromRAGUseCase (NEU v2.3)**
- **Input:** upload_document_id
- **Output:** Dict mit success, removed_chunks, message
- **Logic:**
  1. Lade IndexedDocument (by upload_document_id)
  2. **Falls nicht indexiert:** Return success (idempotent)
  3. **Lösche Vektoren aus Qdrant:** delete_chunks_by_document_id
  4. **Lösche Chunks aus DB:** delete_by_indexed_document_id
  5. **Lösche IndexedDocument Eintrag:** delete(indexed_document_id)
  6. Return Ergebnis mit Anzahl entfernter Chunks
- **Verwendung:** Event-Driven RAG Cleanup bei Document Lifecycle Events
  
  **WICHTIG - Prompt-Integration Workflow (Game Changer!):**
  - **Schritt 1 (Vision-Extraktion):** `ProcessDocumentPageUseCase` verwendet Standard-Prompt für Dokumenttyp
    → AI extrahiert strukturierte JSON gemäß Prompt-Vorgabe
  - **Schritt 2 (Chunking):** `DocumentTypeSpecificChunkingService` analysiert Standard-Prompt
    → Erkennt JSON-Struktur (z.B. `"steps"` für Arbeitsanweisung, `"nodes"` für Flussdiagramm)
    → Wählt optimale Chunking-Strategie
  - **Ergebnis:** Strukturierte, dokumenttyp-spezifische Chunks für optimale Vector-Search
  
  **⭐ Neue Features (v2.9):**
  - **Consumables in Chunks:** Chemikalien/Kleber werden als separater Abschnitt übernommen
    → Ermöglicht RAG-Suche nach "Welcher Kleber wird verwendet?" oder "Welche Sicherheitshinweise zu Aceton?"
  - **Labels-Mapping für Bild-zu-Text-Verknüpfung:**
    → Systematischer Check: Jeder Artikel mit Label wird zu visual_elements gemappt
    → Buchstabenlabels (a, b, c, d) + Ziffernlabels (1, 2, 3, 4) werden erfasst
    → Vollständigkeitscheck: Anzahl Labels in visual_elements ≥ Anzahl in article_data
    → **Kritisch für RAG-Performance:** Ermöglicht präzise Bild-zu-Text-Verknüpfung

### **AskQuestionUseCase** (RAG Chat)
- **Input:** Question, SessionId, UserId, AIModel
- **Output:** ChatMessage (Assistant) mit Source-References
- **Logic:**
  1. **Frage-Normalisierung:** Entfernt Stop-Wörter ("und", "aber", "oder") am Anfang für konsistentere Vector-Search
  2. Prüfe Permission (filtere nach Interest Groups)
  3. Multi-Query Expansion für bessere Suche (verwendet normalisierte Frage)
  4. Hybrid Search (Qdrant + Text-Scoring) mit erweitertem Context (Top 10 Chunks)
  5. Re-Ranking der Ergebnisse
  6. **Source References erstellen:** Extrahiert document_id, page_number, relevance_score aus Chunks
  7. **Document-Type für AI-Prompt:** Bestimmt document_type aus Chunks für dokumenttyp-spezifischen Prompt
  8. Baue Prompt mit Kontext (inkl. dokumenttyp-spezifischen Anweisungen)
  9. **Speichere User-Nachricht** (Frage) in Datenbank
  10. Sende an AI Model (GPT-4o Mini, GPT-5 Mini mit Fallback, Gemini)
  11. Extrahiere strukturierte Daten
  12. **Speichere Assistant-Message** mit `ai_model_used` Tracking und `source_references`
  13. Returniere Antwort mit Source-Links (inkl. in-text Referenzen)

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

### **ProcessDocumentPageUseCase** (Document Upload Context)
- **Input:** upload_document_id, page_number
- **Output:** AIProcessingResult
- **Logic:**
  1. Lädt die gewünschte Seite
  2. Verwendet den Standard-Prompt für den Dokumenttyp
  3. Verarbeitet die Seite mit AI-Modell
  4. Speichert JSON-Response in `document_ai_responses`
  5. **WICHTIG:** Aktualisiert existierende AI-Results statt neue zu erstellen (verhindert UNIQUE constraint Fehler)
- **Verwendung:** Seitenweise Neu-Verarbeitung für bessere AI-Ergebnisse
- **Re-Indexierung:** Nach seitenweiser Verarbeitung kann das Dokument mit `POST /api/rag/documents/index` neu indexiert werden

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
| **PHASE 1** | `GET /api/rag/audit-trail` | Audit-Trail abrufen | Level 1-4 |
| **PHASE 2** | `GET /api/rag/documents/{id}/chunks` | Chunk-Liste | Level 1-4 |
| **PHASE 2** | `GET /api/rag/chunks/{id}/preview` | Chunk-Vorschau | Level 1-4 |
| **PHASE 2** | `POST /api/rag/chunks/{id}/edit` | Chunk bearbeiten | Level 4+ |
| **PHASE 2** | `POST /api/rag/chunks/{id}/split` | Chunk splitten (mit Overlap) | Level 4+ |
| **Document Upload** | `POST /api/document-upload/{id}/process-page/{page}` | Seitenweise AI-Verarbeitung | Level 4+ |
| **RAG** | `POST /api/rag/documents/index` | Dokument neu indexieren | Level 2+ |
| **PHASE 2** | `POST /api/rag/chunks/merge` | Chunks zusammenführen | Level 4+ |
| **PHASE 2** | `GET /api/rag/chunking-strategies` | Verfügbare Strategien | Level 1-4 |
| **PHASE 3** | `GET /api/rag/chat/messages/{id}/prompt` | Prompt-Viewer | Level 1-4 |
| **PHASE 4.1** | `POST /api/rag/chat/feedback` | Feedback abgeben | Level 1+ |
| **PHASE 4.1** | `GET /api/rag/chat/feedback/statistics` | Feedback-Statistiken | Level 1+ (eigene), Level 4+ (alle) |
| **PHASE 4.1** | `GET /api/rag/chat/messages/{id}/feedback` | Feedback für Message | Level 1+ |
| **PHASE 4.2** | `GET /api/rag/analytics` | RAG Analytics Dashboard | Level 1+ (eigene), Level 4+ (alle) |

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

### **RAG Audit Events (PHASE 1)**
- `ChunkingStartedEvent` - Chunking-Prozess gestartet
- `ChunkingCompletedEvent` - Chunking erfolgreich abgeschlossen
- `ChunkingFailedEvent` - Chunking fehlgeschlagen
- `IndexingStartedEvent` - Indexierung gestartet
- `IndexingCompletedEvent` - Indexierung erfolgreich abgeschlossen
- `IndexingFailedEvent` - Indexierung fehlgeschlagen
- `QueryExecutedEvent` - RAG Query ausgeführt

**Subscribers:**
- `RAGAuditEventHandler` → Protokolliert alle Events im Audit-Trail

### **Feedback Events (PHASE 4.1)**
- `FeedbackSubmittedEvent` - User Feedback wurde abgegeben

**Subscribers:**
- `RAGAuditEventHandler` → Protokolliert Feedback im Audit-Trail

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
- **Embedding Providers (Einheitliches Modell):**
  - **OpenAI:** Embeddings (text-embedding-3-small, 1536 dim) - via OPENAI_GPT5_MINI_API_KEY
    - **NEU (v2.8.0):** Einheitliches Modell für alle Dokumente (text-embedding-3-small)
    - **NEU (v2.7.1):** GPT-5 Mini Strict Mode - Dedizierter Adapter, kein Fallback, strikte Validierung
    - **Keine Fallbacks:** Explizite Fehlermeldungen bei fehlendem API-Key oder fehlenden Berechtigungen
  - **Google Gemini:** Embeddings (text-embedding-004, 768 dim) - kostenlos, via GOOGLE_AI_API_KEY (nur als Fallback wenn OpenAI nicht verfügbar)
  - **Sentence Transformers:** Lokale Embeddings (768/384 dim) - kostenlos, lokal (nur als Fallback wenn OpenAI/Google nicht verfügbar)
  - **WICHTIG:** Alle neuen Dokumente werden mit text-embedding-3-small indexiert. Alte Dokumente müssen re-indexiert werden.
- **Chat Models:** OpenAI (GPT-4o Mini, GPT-5 Mini mit Strict Mode), Google (Gemini 2.5 Flash)
  - **NEU (v2.7.1):** GPT-5 Mini erfordert `OPENAI_GPT5_MINI_API_KEY`, kein Fallback zu GPT-4o Mini
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
- **Parameter:** Max 512 Tokens pro Chunk (ca. 2000 Zeichen)

#### **Level 2: Page-Boundary-aware (Fallback)**
- Respektiert Seiten-Grenzen
- Absatz-basiert mit Satz-Überlappung
- **Parameter:** Max 512 Tokens (ca. 2000 Zeichen), 2 Sätze Überlappung

#### **Level 3: Plain-Text (Notfall)**
- Einfache Text-Aufteilung
- **Parameter:** Max 512 Tokens pro Chunk (ca. 2000 Zeichen)

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

- [x] **Domain Layer:** 6 Entities, 4 Value Objects, 6 Repository Interfaces, 11 Domain Events
  - Entities: IndexedDocument, DocumentChunk, ChatSession, ChatMessage, RAGAuditLog, RAGFeedback
  - Events: DocumentIndexedEvent, ChunkCreatedEvent, 7 Audit Events, FeedbackSubmittedEvent
- [x] **Application Layer:** 12+ Use Cases, 3 Services
  - Use Cases: IndexDocument, AskQuestion, CreateSession, GetHistory, Reindex, RemoveDocument, LogRAGAction, GetAuditTrail, EditChunk, DeleteChunk, SplitChunk, MergeChunks, SubmitFeedback, GetFeedbackStatistics, GetRAGAnalytics
  - Services: HeadingAwareChunking, MultiQuery, StructuredDataExtractor
- [x] **Infrastructure Layer:** Qdrant Adapter, OpenAI Embedding Adapter, Vision Data Extractor, Hybrid Search Service, 6 SQLAlchemy Repositories
  - Repositories: IndexedDocument, DocumentChunk, ChatSession, ChatMessage, RAGAuditLog, RAGFeedback
- [x] **Interface Layer:** 15+ FastAPI Endpoints, Pydantic Schemas, Permission Checks
- [x] **Database:** 6 Tabellen mit Indizes und Triggers
  - Tabellen: rag_indexed_documents, rag_document_chunks, rag_chat_sessions, rag_chat_messages, rag_audit_logs, rag_feedback
- [x] **Frontend:** RAG Chat Dashboard, Session Sidebar, Filter Panel, Source Preview Modal, Document Integration
  - **PHASE 1:** RAG Audit-Trail UI
  - **PHASE 2:** Chunk-Vorschau & Editor UI
  - **PHASE 2:** Chunking-Strategie Selector Wizard
  - **PHASE 3:** RAG Chat Prompt Viewer Modal
  - **PHASE 3:** RAG Chat Transparency Layer Component
  - **PHASE 4.1:** RAG Feedback Button Component
  - **PHASE 4.2:** RAG Analytics Dashboard Page
- [x] **TDD Testing:** Domain + Application Layer Tests (100% Coverage)
- [x] **Chunking-Strategie:** Intelligente Multi-Level Fallback-Strategie + 3-Stage Embedding (OpenAI 1536, Gemini 768, Local 384)
- [x] **Multi-Model Support:** GPT-4o Mini, GPT-5 Mini, Gemini 2.5 Flash
- [x] **Document Integration:** RAG Indexierung Panel in Document Detail View
- [x] **Source Preview:** Vollbild-Preview mit Zoom-Funktionalität
- [x] **Structured Data:** Tabellen, Listen, Sicherheitshinweise Rendering
- [x] **Suggested Questions:** UX-Optimierung für bessere User Experience
- [x] **RAG UX Transparency:** Vollständige Transparenz für Compliance und Qualitätsverbesserung

---

## 📚 Weiterführende Links

- **Roadmap:** `docs/ROADMAP_DOCUMENT_UPLOAD.md` (Phase 4)
- **User Manual:** `docs/user-manual/03-rag-chat.md`
- **Architecture:** `docs/architecture.md`
- **Chunking-Strategie:** Siehe oben (TÜV-Audit-tauglich)

---

**Last Updated:** 2025-11-11  
**Version:** 2.5.1  
**Phase:** 4 (RAG Integration) - **VOLLSTÄNDIG IMPLEMENTIERT** ✅  
**NEU:** RAG UX Transparency PHASE 1-4 (Audit-Trail, Chunk-Editor, Prompt-Viewer, Feedback-System, Analytics Dashboard)  
**NEU (v2.5.1):** RAG Chat Prompts, Message Metadata, Multi-Query Transparency, Top-K Fix  
**NEU (v2.5.0):** Chunk-Editor mit Overlap-Funktion, Seitenweise AI-Verarbeitung, Re-Indexierung, Strukturiertes Chunking für Fachartikel

