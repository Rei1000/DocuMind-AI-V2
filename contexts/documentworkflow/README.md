# ✅ Document Workflow Context

> **Bounded Context:** documentworkflow  
> **Verantwortlichkeit:** Document Review, Approval, Rejection, Audit Trail  
> **Status:** 🚧 In Entwicklung (Phase 3)

---

## 🎯 Verantwortlichkeit

Dieser Context ist verantwortlich für:
- **Workflow-Management:** Uploaded → Reviewed → Approved/Rejected
- **Permission-basierte Actions:** Level 2 (ansehen), Level 3 (prüfen), Level 4 (freigeben)
- **Kommentar-System:** Kommentare zu Dokumenten hinzufügen
- **Audit-Trail:** Vollständige Nachverfolgbarkeit aller Aktionen (TÜV-tauglich)
- **Notification-System:** Email/Slack bei Status-Änderungen

---

## 📦 Entities

### **WorkflowDocument**
```python
@dataclass
class WorkflowDocument:
    """Dokument im Workflow-Prozess"""
    id: int
    upload_document_id: int  # 1:1 Beziehung zu documentupload
    status: DocumentStatus  # uploaded, reviewed, approved, rejected
    current_reviewer_user_id: Optional[int]
    reviewed_at: Optional[datetime]
    reviewed_by_user_id: Optional[int]
    review_comment: Optional[str]
    approved_at: Optional[datetime]
    approved_by_user_id: Optional[int]
    approval_comment: Optional[str]
    rejected_at: Optional[datetime]
    rejected_by_user_id: Optional[int]
    rejection_reason: Optional[str]
    created_at: datetime
    updated_at: datetime
```

### **AuditLogEntry**
```python
@dataclass
class AuditLogEntry:
    """Audit-Trail Entry für Compliance"""
    id: int
    workflow_document_id: int
    action: WorkflowAction  # uploaded, reviewed, approved, rejected, comment_added
    performed_by_user_id: int
    previous_status: Optional[DocumentStatus]
    new_status: Optional[DocumentStatus]
    comment: Optional[str]
    ip_address: str
    user_agent: str
    created_at: datetime
```

### **ReviewComment**
```python
@dataclass
class ReviewComment:
    """Kommentar zu einem Dokument"""
    id: int
    workflow_document_id: int
    user_id: int
    comment: str
    created_at: datetime
```

---

## 🎯 Use Cases

### **ReviewDocumentUseCase** (Level 3)
- **Input:** WorkflowDocumentId, Comment, ReviewerUserId
- **Output:** WorkflowDocument
- **Logic:**
  1. Prüfe Permission (Level 3 erforderlich)
  2. Lade WorkflowDocument
  3. Setze Status auf `reviewed`
  4. Speichere Kommentar
  5. Erstelle AuditLogEntry
  6. Publiziere `DocumentReviewedEvent`
  7. Sende Notification an QM (Level 4)

### **ApproveDocumentUseCase** (Level 4)
- **Input:** WorkflowDocumentId, Comment, ApproverUserId
- **Output:** WorkflowDocument
- **Logic:**
  1. Prüfe Permission (Level 4 erforderlich)
  2. Lade WorkflowDocument
  3. Setze Status auf `approved`
  4. Speichere Kommentar
  5. Erstelle AuditLogEntry
  6. Publiziere `DocumentApprovedEvent`
  7. Sende Notification an alle Beteiligten

### **RejectDocumentUseCase**
- **Input:** WorkflowDocumentId, Reason, RejectorUserId
- **Output:** WorkflowDocument
- **Logic:**
  1. Prüfe Permission (Level 3 oder 4)
  2. Lade WorkflowDocument
  3. Setze Status auf `rejected`
  4. Speichere Ablehnungsgrund
  5. Erstelle AuditLogEntry
  6. Publiziere `DocumentRejectedEvent`
  7. Sende Notification an Uploader

### **AddCommentUseCase**
- **Input:** WorkflowDocumentId, Comment, UserId
- **Output:** ReviewComment
- **Logic:**
  1. Prüfe Permission (Level 2-4)
  2. Erstelle ReviewComment
  3. Speichere in Datenbank
  4. Erstelle AuditLogEntry
  5. Publiziere `CommentAddedEvent`

### **GetWorkflowDocumentsUseCase**
- **Input:** Filter (status, interest_group_id), UserId
- **Output:** List[WorkflowDocument]
- **Logic:**
  1. Prüfe Permission
  2. Filtere nach Interest Groups (basierend auf User)
  3. Filtere nach Status
  4. Returniere Liste

### **GetAuditLogUseCase**
- **Input:** WorkflowDocumentId
- **Output:** List[AuditLogEntry]
- **Logic:**
  1. Prüfe Permission (Level 3-4)
  2. Lade alle AuditLogEntries
  3. Returniere chronologisch sortiert

---

## 🔌 API Endpoints

| Method | Endpoint | Beschreibung | Permission |
|--------|----------|--------------|------------|
| `GET` | `/api/workflow/documents` | Liste (Filter) | Level 2-4 |
| `GET` | `/api/workflow/documents/{id}` | Details | Level 2-4 |
| `POST` | `/api/workflow/documents/{id}/review` | Prüfen | Level 3 |
| `POST` | `/api/workflow/documents/{id}/approve` | Freigeben | Level 4 |
| `POST` | `/api/workflow/documents/{id}/reject` | Ablehnen | Level 3-4 |
| `POST` | `/api/workflow/documents/{id}/comment` | Kommentar | Level 2-4 |
| `GET` | `/api/workflow/documents/{id}/audit-log` | Audit Trail | Level 3-4 |

---

## 📡 Domain Events

### **DocumentReviewedEvent**
```python
@dataclass
class DocumentReviewedEvent:
    """Event: Dokument wurde geprüft"""
    workflow_document_id: int
    reviewed_by_user_id: int
    comment: str
    timestamp: datetime
```

**Subscribers:**
- `NotificationService` → Sendet Email an QM (Level 4)

### **DocumentApprovedEvent**
```python
@dataclass
class DocumentApprovedEvent:
    """Event: Dokument wurde freigegeben"""
    workflow_document_id: int
    upload_document_id: int
    approved_by_user_id: int
    comment: str
    timestamp: datetime
```

**Subscribers:**
- `ragintegration.DocumentApprovedEventHandler` → Startet Indexierung
- `NotificationService` → Sendet Email an alle Beteiligten

### **DocumentRejectedEvent**
```python
@dataclass
class DocumentRejectedEvent:
    """Event: Dokument wurde abgelehnt"""
    workflow_document_id: int
    rejected_by_user_id: int
    reason: str
    timestamp: datetime
```

**Subscribers:**
- `NotificationService` → Sendet Email an Uploader

### **CommentAddedEvent**
```python
@dataclass
class CommentAddedEvent:
    """Event: Kommentar wurde hinzugefügt"""
    workflow_document_id: int
    user_id: int
    comment: str
    timestamp: datetime
```

---

## 🔗 Dependencies

### **Domain Events:**
- **Incoming:** `documentupload.DocumentUploadedEvent` → Erstellt Workflow-Entry
- **Outgoing:** `DocumentApprovedEvent` → `ragintegration` Context

### **External Contexts:**
- **documentupload:** Liest Upload-Details
- **users:** Validiert User IDs, prüft Permissions
- **interestgroups:** Filtert Dokumente nach Interest Groups

---

## 🔐 Permission Policy

| Level | Rolle | Dokumente ansehen | Prüfen | Freigeben | Kommentieren |
|-------|-------|-------------------|--------|-----------|--------------|
| **2** | Teamleiter | ✅ | ❌ | ❌ | ✅ |
| **3** | Abteilungsleiter | ✅ | ✅ | ❌ | ✅ |
| **4** | QM | ✅ | ✅ | ✅ | ✅ |

---

## ✅ Status

- [x] Context-Struktur erstellt
- [x] README.md dokumentiert
- [ ] Domain Model (Entities, Value Objects, Policies)
- [ ] Use Cases
- [ ] Event Handlers
- [ ] Infrastructure (Repositories, Notification Adapter)
- [ ] API Routes
- [ ] Tests
- [ ] Frontend Integration

---

## 📚 Weiterführende Links

- **Roadmap:** `docs/ROADMAP_DOCUMENT_UPLOAD.md` (Phase 3)
- **User Manual:** `docs/user-manual/02-workflow.md`
- **Architecture:** `docs/architecture.md`

---

**Last Updated:** 2025-10-13  
**Phase:** 1 (Foundation)

