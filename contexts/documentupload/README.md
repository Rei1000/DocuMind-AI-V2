# 📤 Document Upload Context

> **Bounded Context:** documentupload  
> **Verantwortlichkeit:** File Upload, Page Splitting, Preview Generation, Metadata Management, Workflow System  
> **Status:** ✅ Vollständig implementiert (v2.3.0) - **Document Lifecycle Management**

**NEU (v2.3.0):**
- ✅ SHA-256 Hash Duplikat-Prüfung
- ✅ Dokument-Versionierung (Series + Parent-Child)
- ✅ Soft Delete (Audit-tauglich)
- ✅ Archivierung (Automatisch + Manuell)
- ✅ Event-Driven RAG Cleanup Integration

---

## 🎯 Verantwortlichkeit

Dieser Context ist verantwortlich für:
- **File Upload:** PDF, DOCX, PNG, JPG (max 50MB)
- **Page Splitting:** Automatische Aufteilung mehrseitiger Dokumente
- **Preview Generation:** Thumbnails + Full-Size Bilder
- **Metadata Management:** Dokumentname, QM-Kapitel, Version
- **Interest Groups Assignment:** Zuweisung zu Abteilungen
- **Processing Method Selection:** OCR oder Vision (aus Dokumenttyp)
- **Workflow Management:** 4-Status Workflow (Draft → Reviewed → Approved/Rejected)
  - ⭐ **Approved → Rejected:** Auch freigegebene Dokumente können zurückgewiesen werden
- **Document Lifecycle Management (NEU v2.3):**
  - **SHA-256 Hash Duplikat-Prüfung:** Automatische Erkennung identischer Dateien
  - **Versionierung:** Dokument-Serien mit automatischer Archivierung alter Versionen
  - **Soft Delete:** Audit-taugliche Löschung mit Grund und Benutzer-Tracking
  - **Archivierung:** Manuelle und automatische Archivierung von Dokumenten
  - **Event-Driven RAG Cleanup:** Automatisches Entfernen aus Vector-DB bei Lifecycle-Events
- **Permission-based Access:** Level-basierte Berechtigungen (Level 2-5)
- **Audit Trail:** Vollständige Workflow-Historie
- **Comments System:** Kommentare zu Dokumenten

---

## 📦 Entities

### **UploadedDocument**
```python
@dataclass
class UploadedDocument:
    """Hochgeladenes Dokument mit Metadaten"""
    id: int
    filename: str
    original_filename: str
    file_size_bytes: int
    file_type: FileType  # PDF, DOCX, PNG, JPG
    document_type_id: int
    qm_chapter: Optional[str]
    version: str
    page_count: int
    uploaded_by_user_id: int
    uploaded_at: datetime
    file_path: str
    processing_method: ProcessingMethod  # OCR oder Vision
    processing_status: ProcessingStatus  # pending, processing, completed, failed
    workflow_status: WorkflowStatus  # draft, reviewed, approved, rejected, archived, deleted
    # NEU v2.3: Document Lifecycle Management
    file_hash: Optional[str]  # SHA-256 Hash (64 hex) für Duplikat-Prüfung
    is_duplicate: bool  # Flag: Ist Duplikat?
    duplicate_of_document_id: Optional[int]  # Link zum Original
    document_series_id: Optional[int]  # ID der logischen Dokument-Serie
    parent_document_id: Optional[int]  # Vorgänger-Version
    is_current_version: bool  # Aktuelle Version? (True bei Upload)
    deleted_at: Optional[datetime]  # Soft Delete Zeitstempel
    deleted_by_user_id: Optional[int]  # User ID des Löschers
    deletion_reason: Optional[str]  # Grund für Löschung
    archived_at: Optional[datetime]  # Archivierungs-Zeitstempel
    archived_by_user_id: Optional[int]  # User ID des Archivierers
    archive_reason: Optional[str]  # Grund für Archivierung
```

### **DocumentPage**
```python
@dataclass
class DocumentPage:
    """Einzelne Seite eines Dokuments"""
    id: int
    upload_document_id: int
    page_number: int
    preview_image_path: str
    thumbnail_path: str
    width: int
    height: int
    created_at: datetime
```

### **InterestGroupAssignment**
```python
@dataclass
class InterestGroupAssignment:
    """Zuweisung eines Dokuments zu einer Interest Group"""
    id: int
    upload_document_id: int
    interest_group_id: int
    assigned_at: datetime
    assigned_by_user_id: int
```

---

## 🎯 Use Cases

### **UploadDocumentUseCase**
- **Input:** File, Metadata (name, qm_chapter, version, document_type_id)
- **Output:** UploadedDocument
- **Logic:**
  1. Validiere Datei (Größe, Typ)
  2. **Berechne SHA-256 Hash (chunk-basiert für große Dateien) - NEU v2.3**
  3. **Prüfe auf Duplikate (find_by_hash) - NEU v2.3**
  4. **Versionierung: Prüfe ob Version bereits existiert - NEU v2.3**
  5. **Setze Parent-Child Beziehungen - NEU v2.3**
  6. **Archiviere alte Version (is_current_version=False) - NEU v2.3**
  7. Speichere Datei im File Storage
  8. Erstelle UploadedDocument Entity
  9. Speichere in Datenbank
  10. **Publiziere `DocumentVersionArchivedEvent` (wenn Version archiviert) - NEU v2.3**
  11. Publiziere `DocumentUploadedEvent`

### **GeneratePreviewUseCase**
- **Input:** UploadedDocument
- **Output:** List[DocumentPage]
- **Logic:**
  1. Splitte Dokument in Einzelseiten
  2. Generiere Preview-Bilder (Full-Size)
  3. Generiere Thumbnails
  4. Speichere DocumentPage Entities
  5. Publiziere `PagesGeneratedEvent`

### **AssignInterestGroupsUseCase**
- **Input:** UploadedDocument, List[InterestGroupId]
- **Output:** List[InterestGroupAssignment]
- **Logic:**
  1. Validiere Interest Groups
  2. Erstelle Assignments
  3. Speichere in Datenbank
  4. Publiziere `InterestGroupsAssignedEvent`

### **GetUploadDetailsUseCase**
- **Input:** UploadDocumentId
- **Output:** UploadedDocument + List[DocumentPage] + List[InterestGroupAssignment]
- **Logic:**
  1. Lade UploadedDocument
  2. Lade zugehörige Pages
  3. Lade zugehörige Interest Groups
  4. Returniere aggregierte Daten

---

## 🔌 API Endpoints

| Method | Endpoint | Beschreibung | Permission |
|--------|----------|--------------|------------|
| `POST` | `/api/document-upload/upload` | Upload + Metadata | Level 4 (QM) |
| `GET` | `/api/document-upload/` | Liste aller Uploads | Level 4 (QM) |
| `GET` | `/api/document-upload/{id}` | Upload Details | Level 2+ |
| `GET` | `/api/document-upload/{id}/preview/{page}` | Preview-Bild | Level 2+ |
| `POST` | `/api/document-upload/{id}/assign-interest-groups` | Assign Groups | Level 4 (QM) |
| `POST` | `/api/document-upload/{id}/process-page/{page}` | AI-Verarbeitung | Level 4 (QM) |
| `DELETE` | `/api/document-upload/{id}` | Upload löschen | Level 4 (QM) |
| **Workflow Endpoints:** |
| `POST` | `/api/document-workflow/change-status` | Status ändern | Level 3-5 |
| `GET` | `/api/document-workflow/status/{status}` | Dokumente nach Status | Level 2+ |
| `GET` | `/api/document-workflow/history/{id}` | Workflow-Historie | Level 2+ |
| `POST` | `/api/document-workflow/reject` | Dokument zurückweisen | Level 4 (QM) |
| `POST` | `/api/document-workflow/soft-delete` | **Soft Delete - NEU v2.3** | Level 4 (QM) |
| `POST` | `/api/document-workflow/archive` | **Archivierung - NEU v2.3** | Level 4 (QM) |

---

### **RejectDocumentUseCase (NEU v2.3)**
- **Input:** document_id, rejected_by_user_id, rejection_reason
- **Output:** UploadedDocument
- **Logic:**
  1. Validiere Dokument-Status (muss REVIEWED sein)
  2. Validiere Rejection-Comment (muss vorhanden sein oder wird automatisch erstellt)
  3. Setze workflow_status = REJECTED
  4. Erstelle/Comment-Kommentar für Audit-Trail
  5. Speichere in Datenbank
  6. **Publiziere `DocumentRejectedEvent` → RAG Cleanup - NEU v2.3**

### **SoftDeleteDocumentUseCase (NEU v2.3)**
- **Input:** document_id, deleted_by_user_id, deletion_reason
- **Output:** UploadedDocument
- **Logic:**
  1. Validiere document_id, user_id, reason
  2. Setze workflow_status = DELETED
  3. Setze deleted_at, deleted_by_user_id, deletion_reason
  4. Speichere in Datenbank
  5. **Publiziere `DocumentDeletedEvent` → RAG Cleanup - NEU v2.3**

### **ArchiveDocumentUseCase (NEU v2.3)**
- **Input:** document_id, archived_by_user_id, archive_reason (optional)
- **Output:** UploadedDocument
- **Logic:**
  1. Validiere document_id, user_id
  2. Setze workflow_status = ARCHIVED
  3. Setze archived_at, archived_by_user_id, archive_reason
  4. Speichere in Datenbank
  5. **Publiziere `DocumentArchivedEvent` → RAG Cleanup - NEU v2.3**

---

## 📡 Domain Events

### **DocumentUploadedEvent**
```python
@dataclass
class DocumentUploadedEvent:
    """Event: Dokument wurde hochgeladen"""
    document_id: int
    filename: str
    document_type_id: int
    uploaded_by_user_id: int
    page_count: int
    interest_group_ids: List[int]
    timestamp: datetime
```

**Subscribers:**
- `ragintegration.DocumentUploadedEventHandler` → Startet Indexierung (wenn approved)

### **DocumentRejectedEvent (NEU v2.3)**
```python
@dataclass
class DocumentRejectedEvent:
    """Event: Dokument wurde zurückgewiesen"""
    document_id: int
    rejected_by_user_id: int
    rejection_reason: str
    timestamp: datetime
```

**Subscribers:**
- `ragintegration.DocumentRejectedEventHandler` → **RAG Cleanup (entfernt Vektoren) - NEU v2.3**

### **DocumentDeletedEvent (NEU v2.3)**
```python
@dataclass
class DocumentDeletedEvent:
    """Event: Dokument wurde soft-deleted"""
    document_id: int
    deleted_by_user_id: int
    deletion_reason: str
    timestamp: datetime
```

**Subscribers:**
- `ragintegration.DocumentDeletedEventHandler` → **RAG Cleanup (entfernt Vektoren) - NEU v2.3**

### **DocumentArchivedEvent (NEU v2.3)**
```python
@dataclass
class DocumentArchivedEvent:
    """Event: Dokument wurde archiviert"""
    document_id: int
    archived_by_user_id: int
    archive_reason: Optional[str]
    timestamp: datetime
```

**Subscribers:**
- `ragintegration.DocumentArchivedEventHandler` → **RAG Cleanup (entfernt Vektoren) - NEU v2.3**

### **DocumentVersionArchivedEvent (NEU v2.3)**
```python
@dataclass
class DocumentVersionArchivedEvent:
    """Event: Alte Dokument-Version wurde archiviert (bei neuem Upload)"""
    old_version_id: int
    new_version_id: int
    document_series_id: int
    archived_by_user_id: int
    timestamp: datetime
```

**Subscribers:**
- `ragintegration.DocumentVersionArchivedEventHandler` → **RAG Cleanup (entfernt Vektoren der alten Version) - NEU v2.3**

### **PagesGeneratedEvent**
```python
@dataclass
class PagesGeneratedEvent:
    """Event: Seiten wurden generiert"""
    document_id: int
    page_count: int
    timestamp: datetime
```

### **InterestGroupsAssignedEvent**
```python
@dataclass
class InterestGroupsAssignedEvent:
    """Event: Interest Groups wurden zugewiesen"""
    document_id: int
    interest_group_ids: List[int]
    assigned_by_user_id: int
    timestamp: datetime
```

---

## 🔗 Dependencies

### **Domain Events (Event-Driven RAG Cleanup - NEU v2.3):**
- `DocumentUploadedEvent` → `ragintegration` Context (wenn approved)
- `DocumentRejectedEvent` → `ragintegration` Context (**RAG Cleanup**)
- `DocumentDeletedEvent` → `ragintegration` Context (**RAG Cleanup**)
- `DocumentArchivedEvent` → `ragintegration` Context (**RAG Cleanup**)
- `DocumentVersionArchivedEvent` → `ragintegration` Context (**RAG Cleanup alter Versionen**)

### **External Contexts:**
- **documenttypes:** Liest Dokumenttyp-Konfiguration (requires_ocr, requires_vision)
- **interestgroups:** Validiert Interest Group IDs
- **users:** Validiert User IDs
- **ragintegration:** Event-Driven RAG Cleanup via Domain Events (keine direkten Imports!)

### **Infrastructure:**
- **File Storage:** Lokales Filesystem (`/data/uploads/`)
- **PDF Processing:** PyPDF2, pdf2image
- **Image Processing:** Pillow

---

## ✅ Status

- [x] Context-Struktur erstellt
- [x] README.md dokumentiert
- [ ] Domain Model (Entities, Value Objects)
- [ ] Use Cases
- [ ] Infrastructure (File Storage, PDF Splitter, Image Processor)
- [ ] API Routes
- [ ] Tests
- [x] Frontend Integration
- [x] Workflow System
- [x] Permission System
- [x] Audit Trail
- [x] Comments System

---

## 🔄 Workflow Features

### **4-Status Workflow**
```
Draft → Reviewed → Approved
  ↓         ↓
Rejected ← Rejected
```

### **Permission Matrix**
| Level | Beschreibung | Draft | Reviewed | Approved | Rejected |
|-------|-------------|-------|-----------|----------|----------|
| 1 | RAG Chat | ❌ | ❌ | ❌ | ❌ |
| 2 | Teamleiter | 👁️ | 👁️ | 👁️ | 👁️ |
| 3 | Abteilungsleiter | 👁️ | ✅ | ❌ | ✅ |
| 4 | QM-Manager | 👁️ | ✅ | ✅ | ✅ |
| 5 | QMS Admin | 👁️ | ✅ | ✅ | ✅ |

### **API Endpoints**
- `POST /api/document-workflow/change-status` - Status ändern
- `GET /api/document-workflow/status/{status}` - Dokumente nach Status
- `GET /api/document-workflow/history/{document_id}` - Workflow-Historie
- `GET /api/document-workflow/allowed-transitions/{document_id}` - Erlaubte Transitions

### **Use Cases**
- `ChangeDocumentWorkflowStatusUseCase` - Status-Änderung orchestrieren
- `GetWorkflowHistoryUseCase` - Historie abrufen
- `GetDocumentsByWorkflowStatusUseCase` - Dokumente filtern

---

## 📚 Weiterführende Links

- **Roadmap:** `docs/ROADMAP_DOCUMENT_UPLOAD.md` (Phase 2)
- **User Manual:** `docs/user-manual/01-upload.md`
- **Architecture:** `docs/architecture.md`

---

**Last Updated:** 2025-10-13  
**Phase:** 1 (Foundation)

