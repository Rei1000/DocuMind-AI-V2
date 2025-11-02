# 📋 Document Lifecycle Management - Feature Proposal

> **Status:** 💭 Diskussion & Konzept  
> **Erstellt:** 2025-11-02  
> **Branch:** `feature/document-lifecycle-optimization` (zu erstellen)

---

## 🎯 Zielsetzung

Entwicklung eines robusten, auditfähigen Document Lifecycle Management Systems für DocuMind-AI V2, das folgende Herausforderungen adressiert:

1. **Duplikat-Prävention:** Keine identischen Dokumente im System
2. **Versions-Tracking:** Vollständige Audit-Spur für Dokumenten-Versionen
3. **Rejection Handling:** Intelligenter Umgang mit zurückgewiesenen Dokumenten
4. **Archivierung:** Automatische Archivierung bei neuen Versionen
5. **Soft Delete:** Audit-konforme Löschung mit Wiederherstellungsmöglichkeit
6. **RAG-Integration:** Konsistenter Zustand zwischen Dokumenten- und RAG-System

---

## 📊 Analyse: Aktueller Stand

### ✅ **Was bereits existiert:**

- `UploadedDocument` Entity mit Metadaten (`version`, `qm_chapter`, `original_filename`)
- Workflow-Status System (`draft`, `reviewed`, `approved`, `rejected`)
- Interest Group Assignment
- Hard Delete Methode (`delete()` im Repository)

### ❌ **Was fehlt:**

- **File Hash/Checksum:** Keine Möglichkeit, identische Dateien zu erkennen
- **Versions-Link:** Keine Verknüpfung zwischen Dokument-Versionen
- **Soft Delete:** Nur Hard Delete vorhanden (Daten gehen verloren)
- **Archivierung:** Keine automatische Archivierung bei neuen Versionen
- **Rejection Workflow:** Zurückgewiesene Dokumente bleiben im System ohne klaren Status
- **RAG Cleanup:** Löschung/Archivierung berücksichtigt RAG-Index nicht

---

## 🔍 Feature-Übersicht & Best Practices

### 1. **Duplikat-Prüfung** 🔍

#### **Problem:**
- Identische Dateien können mehrfach hochgeladen werden
- Verschwendet Speicherplatz
- Erzeugt Duplikate im RAG-Index
- Erschwert Audit-Trail

#### **Lösungsansatz:**
**A) Content-Based Hashing (Empfohlen)**
- Berechne SHA-256 Hash des Datei-Inhalts beim Upload
- Vergleiche Hash mit existierenden Dokumenten
- **Vorteile:**
  - Erkennt identische Dateien unabhängig vom Dateinamen
  - Resistent gegen Umbenennungen
  - Performance: O(1) Lookup mit Index auf `file_hash`

**B) Metadata-Based Matching (Optional)**
- Kombiniere `document_type_id` + `qm_chapter` + `version` + `original_filename`
- Für Dokumente mit identischen Metadaten: Warnung anzeigen
- **Use Case:** User hat versehentlich gleiche Version nochmal hochgeladen

#### **Implementierung:**

```python
# Value Object: FileHash
@dataclass(frozen=True)
class FileHash:
    """SHA-256 Hash einer Datei."""
    value: str
    
    def __post_init__(self):
        if not re.match(r'^[a-f0-9]{64}$', self.value):
            raise ValueError("Invalid SHA-256 hash format")

# Entity Erweiterung:
@dataclass
class UploadedDocument:
    # ... existing fields ...
    file_hash: FileHash  # NEU: SHA-256 Hash
    is_duplicate: bool = False  # NEU: Flag für Duplikat-Warnung
    duplicate_of_document_id: Optional[int] = None  # NEU: Link zum Original
```

**Duplikat-Prüfung im Use Case:**

```python
async def execute(self, ...):
    # 1. Berechne Hash
    file_hash = calculate_sha256_hash(file_path)
    
    # 2. Prüfe auf Duplikat
    existing = await self.upload_repo.find_by_hash(file_hash)
    if existing:
        # Option A: Upload ablehnen (strikt)
        raise ValueError(f"Dokument bereits vorhanden: ID {existing.id}")
        
        # Option B: Warnung + Upload erlauben (flexibel)
        # → Setze is_duplicate=True, duplicate_of_document_id=existing.id
```

---

### 2. **Versions-Tracking** 📚

#### **Problem:**
- Keine Verknüpfung zwischen Dokument-Versionen
- Unklar, welche Version die aktuelle ist
- Audit-Trail für Versions-Historie fehlt

#### **Lösungsansatz:**
**Hierarchisches Versions-Modell:**

```
Document (Logical)
├── Version 1.0 (v1.0.0) → archived
├── Version 1.1 (v1.1.0) → archived  
├── Version 2.0 (v2.0.0) → active (current)
└── Version 2.1 (v2.1.0) → draft
```

**Implementierung:**

```python
# Entity Erweiterung:
@dataclass
class UploadedDocument:
    # ... existing fields ...
    document_series_id: Optional[int] = None  # NEU: ID der logischen Dokument-Serie
    parent_document_id: Optional[int] = None  # NEU: Vorgänger-Version
    is_current_version: bool = False  # NEU: Aktuelle Version?
    version_sequence: int = 1  # NEU: Sequenz-Nummer (1, 2, 3, ...)
```

**Versionierung-Logik:**

```python
async def execute(self, document_type_id, qm_chapter, version, ...):
    # 1. Suche nach logischer Dokument-Serie
    series = await self.find_document_series(document_type_id, qm_chapter)
    
    if series:
        # Existierende Serie → Neue Version
        document.document_series_id = series.id
        document.parent_document_id = series.current_version_id
        document.version_sequence = series.latest_sequence + 1
        
        # Archiviere alte Version
        await self.archive_version(series.current_version_id)
        
        # Setze neue Version als aktuell
        document.is_current_version = True
    else:
        # Neue Serie → Erste Version
        document.document_series_id = await self.create_document_series(...)
        document.version_sequence = 1
        document.is_current_version = True
```

**Version History API:**

```python
GET /api/documents/{document_id}/versions
→ List[VersionInfo] mit:
   - version: "v1.0.0"
   - uploaded_at: datetime
   - uploaded_by: user_name
   - workflow_status: "approved"
   - is_current: bool
```

---

### 3. **Rejection Handling** ❌

#### **Problem:**
- Zurückgewiesene Dokumente bleiben im System ohne klaren Workflow
- Unklar, ob User Dokument korrigieren/erneut hochladen soll
- RAG-Index enthält ggf. zurückgewiesene Dokumente

#### **Lösungsansatz:**
**Rejection Workflow mit Optionen:**

**Option A: "Reject & Archive" (Empfohlen)**
- Status: `rejected` → Automatisch archiviert
- Kann nicht für Workflow verwendet werden
- RAG-Index: Entferne zurückgewiesene Dokumente
- **Neuer Upload:** Startet neuen Workflow (neue Document ID)

**Option B: "Reject & Allow Resubmission"**
- Status: `rejected` → `draft` (zurückgesetzt)
- User kann Kommentare korrigieren und erneut einreichen
- **Neuer Upload:** Link zu zurückgewiesenem Dokument

**Implementierung:**

```python
# Value Object Erweiterung:
class WorkflowStatus(Enum):
    DRAFT = "draft"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"  # NEU
    DELETED = "deleted"    # NEU (Soft Delete)

@dataclass
class RejectionInfo:
    """Informationen zu einer Zurückweisung."""
    rejected_at: datetime
    rejected_by_user_id: int
    rejection_reason: Optional[str]
    can_resubmit: bool = False
```

**Rejection Use Case:**

```python
async def reject_document(self, document_id, user_id, reason):
    document = await self.upload_repo.get_by_id(document_id)
    
    # 1. Setze Status
    document.workflow_status = WorkflowStatus.REJECTED
    document.rejection_info = RejectionInfo(
        rejected_at=datetime.utcnow(),
        rejected_by_user_id=user_id,
        rejection_reason=reason,
        can_resubmit=True  # Konfigurierbar
    )
    
    # 2. Entferne aus RAG-Index (falls indexiert)
    if document.is_rag_indexed:
        await self.rag_service.remove_document(document_id)
    
    # 3. Optional: Archiviere sofort
    if self.config.auto_archive_rejected:
        await self.archive_document(document_id)
    
    await self.upload_repo.update(document)
```

---

### 4. **Archivierung** 📦

#### **Problem:**
- Keine klare Trennung zwischen aktiven und archivierten Dokumenten
- Alte Versionen bleiben im Haupt-View
- RAG-Index enthält möglicherweise veraltete Versionen

#### **Lösungsansatz:**
**Multi-Level Archivierung:**

1. **Automatische Archivierung:**
   - Neue Version ersetzt alte → Alte Version → `archived`
   - Zurückgewiesene Dokumente → `archived` (optional)

2. **Manuelle Archivierung:**
   - User (Level 4+) kann Dokumente manuell archivieren
   - Archivierte Dokumente bleiben sichtbar, aber markiert

3. **RAG-Integration:**
   - Archivierte Dokumente werden aus RAG-Index entfernt
   - Nur aktuelle, approved Versionen sind im RAG

**Implementierung:**

```python
@dataclass
class UploadedDocument:
    # ... existing fields ...
    archived_at: Optional[datetime] = None  # NEU
    archived_by_user_id: Optional[int] = None  # NEU
    archive_reason: Optional[str] = None  # NEU
    is_archived: bool = False  # NEU (Computed Property basierend auf workflow_status)

async def archive_document(self, document_id, user_id, reason):
    document = await self.upload_repo.get_by_id(document_id)
    
    # 1. Setze Status
    document.workflow_status = WorkflowStatus.ARCHIVED
    document.archived_at = datetime.utcnow()
    document.archived_by_user_id = user_id
    document.archive_reason = reason
    
    # 2. Entferne aus RAG-Index
    if document.is_rag_indexed:
        await self.rag_service.remove_document(document_id)
    
    # 3. Speichere
    await self.upload_repo.update(document)
    
    # 4. Publiziere Event
    await self.event_bus.publish(DocumentArchivedEvent(...))
```

**UI-Integration:**
- Filter: "Archivierte Dokumente anzeigen" (Toggle)
- Badge: "📦 Archiviert" auf archivierten Dokumenten
- Info-Tooltip: Grund der Archivierung

---

### 5. **Soft Delete** 🗑️

#### **Problem:**
- Hard Delete entfernt Daten unwiederbringlich
- Keine Audit-Spur nach Löschung
- RAG-Index-Referenzen bleiben möglicherweise bestehen

#### **Lösungsansatz:**
**Soft Delete mit Wiederherstellung:**

```python
@dataclass
class UploadedDocument:
    # ... existing fields ...
    deleted_at: Optional[datetime] = None  # NEU
    deleted_by_user_id: Optional[int] = None  # NEU
    deletion_reason: Optional[str] = None  # NEU
    is_deleted: bool = False  # NEU (Computed Property)

async def soft_delete_document(self, document_id, user_id, reason):
    document = await self.upload_repo.get_by_id(document_id)
    
    # 1. Setze Status
    document.workflow_status = WorkflowStatus.DELETED
    document.deleted_at = datetime.utcnow()
    document.deleted_by_user_id = user_id
    document.deletion_reason = reason
    document.is_deleted = True
    
    # 2. Entferne aus RAG-Index
    if document.is_rag_indexed:
        await self.rag_service.remove_document(document_id)
    
    # 3. Speichere
    await self.upload_repo.update(document)
    
    # 4. Publiziere Event
    await self.event_bus.publish(DocumentDeletedEvent(...))

async def restore_document(self, document_id, user_id):
    document = await self.upload_repo.get_by_id(document_id)
    
    if not document.is_deleted:
        raise ValueError("Document is not deleted")
    
    # 1. Wiederherstelle Status (zurück zum letzten validen Status)
    document.workflow_status = document.previous_workflow_status  # Oder: DRAFT
    document.deleted_at = None
    document.deleted_by_user_id = None
    document.deletion_reason = None
    document.is_deleted = False
    
    # 2. Speichere
    await self.upload_repo.update(document)
```

**UI-Integration:**
- Löschen-Button zeigt Bestätigungs-Dialog mit Grund
- Gelöschte Dokumente: Nur für QMS Admin sichtbar (Filter)
- "Wiederherstellen"-Button für gelöschte Dokumente
- Audit-Log zeigt Lösch-/Wiederherstellungs-Historie

---

### 6. **RAG-Integration & Konsistenz** 🤖

#### **Problem:**
- RAG-Index kann veraltete/archivierte/gelöschte Dokumente enthalten
- Inkonsistenz zwischen Dokumenten-DB und RAG-Index
- Keine automatische Bereinigung

#### **Lösungsansatz:**
**Event-Driven RAG Cleanup:**

```python
# Event Handler für Dokument-Änderungen
class DocumentLifecycleEventHandler:
    def __init__(self, rag_service: RAGService):
        self.rag_service = rag_service
    
    async def handle_document_archived(self, event: DocumentArchivedEvent):
        await self.rag_service.remove_document(event.document_id)
    
    async def handle_document_deleted(self, event: DocumentDeletedEvent):
        await self.rag_service.remove_document(event.document_id)
    
    async def handle_document_rejected(self, event: DocumentRejectedEvent):
        await self.rag_service.remove_document(event.document_id)
    
    async def handle_version_archived(self, event: DocumentVersionArchivedEvent):
        # Alte Version → Entferne aus RAG
        await self.rag_service.remove_document(event.old_version_id)
        
        # Neue Version → Indexiere (falls approved)
        if event.new_version_status == "approved":
            await self.rag_service.index_document(event.new_version_id)
```

**RAG Status Tracking:**

```python
@dataclass
class UploadedDocument:
    # ... existing fields ...
    rag_indexed_at: Optional[datetime] = None  # NEU
    rag_index_id: Optional[str] = None  # NEU (Qdrant Collection ID)
    is_rag_indexed: bool = False  # NEU (Computed Property)
```

**RAG Cleanup Job (Optional - Scheduled Task):**

```python
async def cleanup_rag_index():
    """Entferne nicht-existierende/archivierte Dokumente aus RAG-Index."""
    # 1. Hole alle RAG-indexierten Dokumente
    indexed_docs = await rag_service.list_all_indexed_documents()
    
    # 2. Prüfe Status in DB
    for rag_doc in indexed_docs:
        db_doc = await upload_repo.get_by_id(rag_doc.document_id)
        
        if not db_doc or db_doc.is_deleted or db_doc.is_archived:
            await rag_service.remove_document(rag_doc.document_id)
```

---

## 🎨 Zusätzliche Features (Empfehlungen)

### 7. **Audit Trail** 📜

**Vollständige Historie aller Änderungen:**

```python
@dataclass
class DocumentAuditLog:
    """Audit-Log Eintrag für Dokument-Änderungen."""
    id: int
    document_id: int
    action: str  # "created", "status_changed", "archived", "deleted", "restored"
    changed_by_user_id: int
    changed_at: datetime
    old_value: Optional[str]
    new_value: Optional[str]
    reason: Optional[str]
    metadata: Dict[str, Any]  # Zusätzliche Kontext-Informationen
```

**API:**
```
GET /api/documents/{document_id}/audit-log
→ List[DocumentAuditLog]
```

### 8. **Dokument-Vergleich** 🔍

**Side-by-Side Vergleich von Versionen:**

```python
GET /api/documents/{document_id}/compare?with_version={other_version_id}
→ ComparisonResult:
   - Differences: List[Difference]
   - Metadata changes: Dict
   - Visual diff (optional)
```

### 9. **Dokument-Statistiken** 📊

**Dashboard für Dokumenten-Metriken:**

```python
GET /api/documents/statistics
→ Statistics:
   - Total documents: int
   - By status: Dict[status, count]
   - By document type: Dict[type, count]
   - By version: Dict[series_id, latest_version]
   - Duplicates detected: int
   - Archived count: int
```

### 10. **Import/Export** 📥📤

**Mass-Import mit Duplikat-Prüfung:**

```python
POST /api/documents/bulk-upload
→ BulkUploadResult:
   - Successfully uploaded: List[document_id]
   - Duplicates skipped: List[duplicate_info]
   - Errors: List[error_info]
```

---

## 📐 Datenbank-Schema-Erweiterungen

### **Neue Spalten in `upload_documents`:**

```sql
ALTER TABLE upload_documents ADD COLUMN file_hash TEXT UNIQUE;  -- SHA-256 Hash
ALTER TABLE upload_documents ADD COLUMN document_series_id INTEGER;  -- FK zu document_series
ALTER TABLE upload_documents ADD COLUMN parent_document_id INTEGER;  -- FK zu upload_documents (selbe Tabelle)
ALTER TABLE upload_documents ADD COLUMN is_current_version BOOLEAN DEFAULT FALSE;
ALTER TABLE upload_documents ADD COLUMN version_sequence INTEGER DEFAULT 1;
ALTER TABLE upload_documents ADD COLUMN archived_at TIMESTAMP;
ALTER TABLE upload_documents ADD COLUMN archived_by_user_id INTEGER;
ALTER TABLE upload_documents ADD COLUMN archive_reason TEXT;
ALTER TABLE upload_documents ADD COLUMN deleted_at TIMESTAMP;
ALTER TABLE upload_documents ADD COLUMN deleted_by_user_id INTEGER;
ALTER TABLE upload_documents ADD COLUMN deletion_reason TEXT;
ALTER TABLE upload_documents ADD COLUMN rag_indexed_at TIMESTAMP;
ALTER TABLE upload_documents ADD COLUMN rag_index_id TEXT;

-- Indizes
CREATE INDEX idx_upload_documents_file_hash ON upload_documents(file_hash);
CREATE INDEX idx_upload_documents_series_id ON upload_documents(document_series_id);
CREATE INDEX idx_upload_documents_parent_id ON upload_documents(parent_document_id);
CREATE INDEX idx_upload_documents_current_version ON upload_documents(document_series_id, is_current_version) WHERE is_current_version = TRUE;
```

### **Neue Tabelle: `document_series`:**

```sql
CREATE TABLE document_series (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_type_id INTEGER NOT NULL,
    qm_chapter TEXT NOT NULL,
    series_name TEXT,  -- Automatisch generiert: "{document_type_name} - {qm_chapter}"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(document_type_id, qm_chapter)
);

CREATE INDEX idx_document_series_type_chapter ON document_series(document_type_id, qm_chapter);
```

### **Neue Tabelle: `document_audit_log`:**

```sql
CREATE TABLE document_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    action TEXT NOT NULL,  -- "created", "status_changed", "archived", "deleted", "restored"
    changed_by_user_id INTEGER NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    old_value TEXT,
    new_value TEXT,
    reason TEXT,
    metadata TEXT,  -- JSON
    FOREIGN KEY (document_id) REFERENCES upload_documents(id),
    FOREIGN KEY (changed_by_user_id) REFERENCES users(id)
);

CREATE INDEX idx_document_audit_log_document_id ON document_audit_log(document_id);
CREATE INDEX idx_document_audit_log_changed_at ON document_audit_log(changed_at);
```

---

## 🔄 Workflow-Integration

### **Workflow-Status Erweiterung:**

```python
class WorkflowStatus(Enum):
    DRAFT = "draft"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"    # NEU
    DELETED = "deleted"      # NEU (Soft Delete)
```

### **Status-Transitions:**

```
draft → reviewed → approved → archived (bei neuer Version)
                    ↓
                 rejected → archived (optional)
                 
approved → deleted (Soft Delete)
archived → restored (optional, nur für QMS Admin)
deleted → restored (nur für QMS Admin)
```

---

## 🎯 Priorisierung & Roadmap

### **Phase 1: Foundation (Kritisch)**
1. ✅ File Hash Implementation (SHA-256)
2. ✅ Duplikat-Prüfung im Upload-Use Case
3. ✅ Soft Delete Implementation
4. ✅ Workflow-Status Erweiterung (`archived`, `deleted`)

### **Phase 2: Versions-Tracking (Wichtig)**
5. ✅ Document Series & Parent-Child Relationships
6. ✅ Automatische Archivierung bei neuen Versionen
7. ✅ Version History API

### **Phase 3: Rejection & Archivierung (Wichtig)**
8. ✅ Rejection Handling mit Archivierung
9. ✅ Manuelle Archivierung (Level 4+)
10. ✅ RAG Cleanup bei Archivierung/Rejection

### **Phase 4: Audit & Advanced Features (Nice-to-Have)**
11. ✅ Audit Log Implementation
12. ✅ Dokument-Vergleich
13. ✅ Statistik-Dashboard
14. ✅ Bulk Import/Export

---

## ✅ Entscheidungen (2025-11-02)

1. **Duplikat-Strategie:** ✅ **Option B (Flexibel)**
   - Warnung anzeigen wenn identisches Dokument gefunden
   - Upload erlauben (mit Flag `is_duplicate=True`)
   - User kann entscheiden ob er trotzdem hochladen möchte

2. **Versionierung:** ✅ **Manuell mit Hinweis**
   - User gibt Version selbst an
   - System warnt wenn Version bereits existiert
   - Vorschlag für nächste Version optional (z.B. v1.0.1 → v1.0.2)

3. **Rejection:** ✅ **Mit Kommentar + Kanban-Ausschluss**
   - Zurückgewiesene Dokumente MÜSSEN mit Kommentar versehen werden (Grund)
   - Nach Kommentierung: Dokument verschwindet aus Kanban (ohne Indexierung)
   - Bleibt in Dokumenten-Tabelle sichtbar
   - Kann manuell gelöscht werden (Soft Delete)

4. **Soft Delete:** ✅ **Permanente Aufbewahrung**
   - Nur Soft Delete (kein Hard Delete)
   - Gelöschte Dokumente bleiben permanent erhalten (für Audit)
   - Optional: Wiederherstellung möglich

5. **RAG Cleanup:** ✅ **Sofortig + Versionierung**
   - **Sofortige Entfernung** bei Archivierung/Rejection/Löschung
   - **Alte Version automatisch entfernen** wenn neue Version indexiert wird
   - **Begründung:** Verhindert Vektor-Duplikate bei 90% identischem Inhalt
   - Zusätzlich: Täglicher Cleanup-Job als Backup (prüft Inkonsistenzen)

### 📊 RAG-Vektoren bei Versionierung

**Problem:**
- Wenn Dokument v1.0 und v2.0 indexiert werden (90% identischer Inhalt)
- Werden ähnliche Vektoren doppelt gespeichert → Vector Store wächst unnötig
- Suche könnte beide Versionen finden (meist ungewollt)
- **Aktuell:** Jeder Chunk = separater Vektor (auch bei identischem Inhalt)

**Lösung:**
- **Beim Indexieren einer neuen Version:** 
  1. Prüfe ob es eine alte Version gibt (`parent_document_id` oder `document_series_id`)
  2. Wenn ja: Entferne alte Version aus RAG (Vector Store + `rag_indexed_documents` Tabelle)
  3. Indexiere neue Version
  4. **Ergebnis:** Nur aktuelle Version ist im RAG durchsuchbar (sauberer Vector Store)
- **Alte Versionen:** Bleiben in DB für Audit, aber nicht mehr im RAG

**Implementierung:**
- Erweitere `IndexApprovedDocumentUseCase`:
  - Vor Indexierung: Prüfe `parent_document_id` → Finde alte Version → Entferne aus RAG
  - Dann: Indexiere neue Version normal
- **Metadaten in RAG:** `document_version` Feld für Tracking (optional, für zukünftige Features)

---

## 📝 Nächste Schritte

1. **Diskussion:** Dieses Proposal durchgehen, offene Fragen klären
2. **Branch erstellen:** `feature/document-lifecycle-optimization`
3. **TDD Plan:** Test-Driven Development Plan für Phase 1
4. **Implementation:** Schrittweise Umsetzung nach Priorisierung

---

**Erstellt von:** AI Assistant  
**Datum:** 2025-11-02  
**Version:** 1.0

