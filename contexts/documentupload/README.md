# 📤 Document Upload Context

> **Bounded Context:** documentupload  
> **Verantwortlichkeit:** File Upload, Page Splitting, Preview Generation, Metadata Management, Workflow Management  
> **Status:** ✅ Vollständig implementiert (inkl. Workflow)

---

## 🎯 Verantwortlichkeit

Dieser Context ist verantwortlich für:
- **File Upload:** PDF, DOCX, PNG, JPG (max 50MB)
- **Page Splitting:** Automatische Aufteilung mehrseitiger Dokumente
- **Preview Generation:** Thumbnails + Full-Size Bilder
- **Metadata Management:** Dokumentname, QM-Kapitel, Version
- **Interest Groups Assignment:** Zuweisung zu Abteilungen
- **Processing Method Selection:** OCR oder Vision (aus Dokumenttyp)
- **Workflow Management:** 4-Status-Workflow (draft → reviewed → approved/rejected)
- **Permission System:** Level-basierte Berechtigungen (2/3/4/5)
- **Audit Trail:** Vollständige Workflow-Historie mit Kommentaren

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
    workflow_status: WorkflowStatus  # draft, reviewed, approved, rejected
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

### **WorkflowStatusChange**
```python
@dataclass
class WorkflowStatusChange:
    """Audit Trail für Workflow-Status-Änderungen"""
    id: int
    upload_document_id: int
    from_status: Optional[WorkflowStatus]
    to_status: WorkflowStatus
    changed_by_user_id: int
    changed_at: datetime
    change_reason: str
    comment: Optional[str]
```

### **DocumentComment**
```python
@dataclass
class DocumentComment:
    """Kommentar zu einem Dokument"""
    id: int
    upload_document_id: int
    comment_text: str
    comment_type: str  # general, review, rejection, approval
    page_number: Optional[int]
    created_by_user_id: int
    created_at: datetime
    status_change_id: Optional[int]
```

---

## 🎯 Use Cases

### **UploadDocumentUseCase**
- **Input:** File, Metadata (name, qm_chapter, version, document_type_id)
- **Output:** UploadedDocument
- **Logic:**
  1. Validiere Datei (Größe, Typ)
  2. Speichere Datei im File Storage
  3. Erstelle UploadedDocument Entity
  4. Speichere in Datenbank
  5. Publiziere `DocumentUploadedEvent`

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

### **ChangeDocumentWorkflowStatusUseCase**
- **Input:** DocumentId, NewStatus, UserId, Reason, Comment
- **Output:** UpdatedDocument
- **Logic:**
  1. Lade Dokument
  2. Prüfe Permission (via WorkflowPermissionService)
  3. Validiere Status-Transition
  4. Ändere Status (Domain-Methode)
  5. Speichere Status-Änderung (Audit Trail)
  6. Speichere Kommentar (falls vorhanden)
  7. Publiziere DocumentWorkflowChangedEvent

### **GetWorkflowHistoryUseCase**
- **Input:** DocumentId, UserId
- **Output:** List[WorkflowStatusChange]
- **Logic:**
  1. Prüfe Permission (nur eigene Interest Groups für Level 2)
  2. Lade Workflow-Historie chronologisch
  3. Returniere Status-Änderungen

### **GetDocumentsByWorkflowStatusUseCase**
- **Input:** Status, UserId, InterestGroupIds
- **Output:** List[UploadedDocument]
- **Logic:**
  1. Prüfe Permission (Level 2: nur eigene Groups)
  2. Filter nach Status
  3. Filter nach Interest Groups (falls angegeben)
  4. Returniere Dokumente

---

## 🔌 API Endpoints

| Method | Endpoint | Beschreibung | Permission |
|--------|----------|--------------|------------|
| `POST` | `/api/document-upload/upload` | Upload + Metadata | Level 4 (QM) |
| `GET` | `/api/document-upload/` | Liste aller Uploads | Level 4 (QM) |
| `GET` | `/api/document-upload/{id}` | Upload Details | Level 4 (QM) |
| `GET` | `/api/document-upload/{id}/preview/{page}` | Preview-Bild | Level 2-4 |
| `POST` | `/api/document-upload/{id}/assign-interest-groups` | Assign Groups | Level 4 (QM) |
| `DELETE` | `/api/document-upload/{id}` | Upload löschen | Level 4 (QM) |
| `POST` | `/api/document-workflow/change-status` | Status ändern | Level 3+ (je nach Transition) |
| `GET` | `/api/document-workflow/status/{status}` | Dokumente nach Status | Level 2+ |
| `GET` | `/api/document-workflow/history/{id}` | Workflow-Historie | Level 2+ |
| `GET` | `/api/document-workflow/allowed-transitions/{id}` | Erlaubte Transitions | Level 2+ |

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

### **DocumentWorkflowChangedEvent**
```python
@dataclass
class DocumentWorkflowChangedEvent:
    """Event: Workflow-Status wurde geändert"""
    document_id: int
    from_status: Optional[WorkflowStatus]
    to_status: WorkflowStatus
    changed_by_user_id: int
    reason: str
    comment: Optional[str]
    timestamp: datetime
```

---

## 🔗 Dependencies

### **Domain Events:**
- `DocumentUploadedEvent` → `ragintegration` Context (wenn approved)

### **External Contexts:**
- **documenttypes:** Liest Dokumenttyp-Konfiguration (requires_ocr, requires_vision)
- **interestgroups:** Validiert Interest Group IDs
- **users:** Validiert User IDs

### **Infrastructure:**
- **File Storage:** Lokales Filesystem (`/data/uploads/`)
- **PDF Processing:** PyPDF2, pdf2image
- **Image Processing:** Pillow

---

## ✅ Status

- [x] Context-Struktur erstellt
- [x] README.md dokumentiert
- [x] Domain Model (Entities, Value Objects, Events)
- [x] Use Cases (Upload, Workflow, History)
- [x] Infrastructure (File Storage, PDF Splitter, Image Processor, Repositories)
- [x] API Routes (Upload + Workflow)
- [x] Tests (Unit, Integration, E2E)
- [x] Frontend Integration (Kanban Board, Modal, Toast)
- [x] Workflow Management (4-Status-System)
- [x] Permission System (Level 2/3/4/5)
- [x] Audit Trail (Status Changes, Comments)

---

## 📚 Weiterführende Links

- **Roadmap:** `docs/ROADMAP_DOCUMENT_UPLOAD.md` (Phase 2)
- **User Manual:** `docs/user-manual/01-upload.md`
- **Architecture:** `docs/architecture.md`

---

**Last Updated:** 2025-10-22  
**Phase:** 9 (Vollständig implementiert)

