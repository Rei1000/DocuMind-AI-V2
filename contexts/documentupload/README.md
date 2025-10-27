# 📤 Document Upload Context

> **Bounded Context:** documentupload  
> **Verantwortlichkeit:** File Upload, Page Splitting, Preview Generation, Metadata Management, Workflow System  
> **Status:** ✅ Vollständig implementiert (v2.1.0)

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

---

## 🔌 API Endpoints

| Method | Endpoint | Beschreibung | Permission |
|--------|----------|--------------|------------|
| `POST` | `/api/uploads` | Upload + Metadata | Level 4 (QM) |
| `GET` | `/api/uploads` | Liste aller Uploads | Level 4 (QM) |
| `GET` | `/api/uploads/{id}` | Upload Details | Level 4 (QM) |
| `GET` | `/api/uploads/{id}/preview/{page}` | Preview-Bild | Level 2-4 |
| `POST` | `/api/uploads/{id}/interest-groups` | Assign Groups | Level 4 (QM) |
| `DELETE` | `/api/uploads/{id}` | Upload löschen | Level 4 (QM) |

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

