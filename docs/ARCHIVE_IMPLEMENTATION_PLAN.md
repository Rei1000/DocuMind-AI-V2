# 📦 Archiv-System: Implementierungsplan

## ✅ Was bereits existiert

### Backend (bereits implementiert):
- ✅ **Soft Delete:** `SoftDeleteDocumentUseCase` setzt `deleted_at`, `deleted_by_user_id`, `deletion_reason`
- ✅ **RAG Cleanup:** `DocumentDeletedEvent` → automatisches RAG-Cleanup
- ✅ **Database Schema:** `deleted_at`, `deleted_by_user_id`, `deletion_reason` Felder existieren
- ✅ **Workflow Status:** `WorkflowStatus.DELETED` existiert

### Frontend (teilweise):
- ✅ **Delete Button:** Soft Delete funktioniert bereits
- ❌ **Archiv-Ansicht:** Noch nicht implementiert
- ❌ **Wiederherstellung:** Noch nicht implementiert
- ❌ **Hard Delete:** Noch nicht implementiert

---

## 🎯 Implementierungsplan (schrittweise)

### Phase 1: Backend - Archiv-Endpoints (2-3h)

#### 1.1 Get Archived Documents Endpoint
```python
# contexts/documentupload/interface/workflow_router.py

@router.get("/archive", response_model=List[WorkflowDocumentSchema])
async def get_archived_documents(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    document_type_id: Optional[int] = Query(None),
    deleted_before: Optional[datetime] = Query(None),
    deleted_after: Optional[datetime] = Query(None),
    db_session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Hole alle gelöschten Dokumente (Archiv).
    
    Nur Level 4+ (QM-Mitarbeiter) dürfen Archiv sehen.
    """
    # RBAC: Nur Level 4+
    if current_user.user_level < 4:
        raise HTTPException(403, "Nur QM-Mitarbeiter können Archiv einsehen")
    
    # Use Case
    use_case = GetArchivedDocumentsUseCase(upload_repository)
    documents = await use_case.execute(
        limit=limit,
        offset=offset,
        document_type_id=document_type_id,
        deleted_before=deleted_before,
        deleted_after=deleted_after
    )
    
    return documents
```

#### 1.2 Restore Document Use Case
```python
# contexts/documentupload/application/use_cases.py

class RestoreDocumentUseCase:
    """Use Case: Stelle gelöschtes Dokument wieder her."""
    
    async def execute(
        self,
        document_id: int,
        restore_to_status: WorkflowStatus = WorkflowStatus.DRAFT,
        restored_by_user_id: int
    ) -> UploadedDocument:
        """
        Stelle Dokument wieder her.
        
        - Setze workflow_status zurück (default: draft)
        - Setze deleted_at, deleted_by_user_id, deletion_reason auf NULL
        - Publiziere DocumentRestoredEvent (für optionales Re-Indexing)
        """
```

#### 1.3 Restore Endpoint
```python
@router.post("/restore/{document_id}", response_model=RestoreDocumentResponse)
async def restore_document(
    document_id: int,
    restore_to_status: Optional[WorkflowStatus] = Query('draft'),
    db_session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Stelle gelöschtes Dokument wieder her."""
```

#### 1.4 Hard Delete Use Case (nur Level 5)
```python
class HardDeleteDocumentUseCase:
    """Use Case: Endgültige Löschung (nur Level 5)."""
    
    async def execute(
        self,
        document_id: int,
        deleted_by_user_id: int,
        confirmation: str  # Muss "LÖSCHEN" sein
    ) -> Dict[str, Any]:
        """
        Endgültige Löschung.
        
        - Prüfe confirmation == "LÖSCHEN"
        - Lösche physische Dateien (file_path)
        - Lösche Preview-Bilder
        - RAG ist bereits gelöscht (bei Soft Delete)
        - Lösche DB-Eintrag ODER setze hard_deleted Flag
        """
```

#### 1.5 Hard Delete Endpoint
```python
@router.delete("/hard-delete/{document_id}")
async def hard_delete_document(
    document_id: int,
    confirmation: str = Query(..., description="Zur Bestätigung: 'LÖSCHEN' eingeben"),
    db_session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Endgültige Löschung (nur Level 5)."""
    # RBAC: Nur Level 5
    if current_user.user_level < 5:
        raise HTTPException(403, "Nur Administratoren können endgültig löschen")
```

---

### Phase 2: Frontend - Archiv-Seite (3-4h)

#### 2.1 Archiv-Navigation
```typescript
// frontend/app/components/Navigation.tsx
// NEU: Archiv-Link (nur Level 4+)
{userLevel >= 4 && (
  <Link href="/documents/archive">
    📦 Archiv {archivedCount > 0 && `(${archivedCount})`}
  </Link>
)}
```

#### 2.2 Archiv-Seite
```typescript
// frontend/app/documents/archive/page.tsx

export default function ArchivePage() {
  // State
  const [archivedDocuments, setArchivedDocuments] = useState<WorkflowDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDocument, setSelectedDocument] = useState<WorkflowDocument | null>(null);
  const [showRestoreModal, setShowRestoreModal] = useState(false);
  const [showHardDeleteModal, setShowHardDeleteModal] = useState(false);
  
  // Features:
  // - Table View (nur Table, kein Kanban)
  // - Spalten: Name, Typ, QM-Kapitel, Gelöscht am, Gelöscht von, Grund
  // - Filter: Datum, Dokumenttyp, User
  // - Aktionen: Wiederherstellen, Hard Delete (nur Level 5)
}
```

#### 2.3 Restore Modal
```typescript
// Modal für Wiederherstellung
<RestoreDocumentModal
  document={selectedDocument}
  isOpen={showRestoreModal}
  onClose={() => setShowRestoreModal(false)}
  onRestore={handleRestore}
  // Optionen: Als "Entwurf" oder original Status wiederherstellen
/>
```

#### 2.4 Hard Delete Modal
```typescript
// Sicherheits-Modal für Hard Delete
<HardDeleteModal
  document={selectedDocument}
  isOpen={showHardDeleteModal}
  onClose={() => setShowHardDeleteModal(false)}
  onConfirm={handleHardDelete}
  // Bestätigung: User muss "LÖSCHEN" eingeben
/>
```

---

### Phase 3: API Client (1h)

```typescript
// frontend/lib/api/documentWorkflow.ts

// NEU: Archiv-Endpoints
export async function getArchivedDocuments(params?: {
  limit?: number;
  offset?: number;
  document_type_id?: number;
}): Promise<ApiResponse<WorkflowDocument[]>> {
  // GET /api/document-workflow/archive
}

export async function restoreDocument(
  documentId: number,
  restoreToStatus?: 'draft' | 'reviewed' | 'approved'
): Promise<ApiResponse<WorkflowDocument>> {
  // POST /api/document-workflow/restore/{documentId}
}

export async function hardDeleteDocument(
  documentId: number,
  confirmation: string  // Muss "LÖSCHEN" sein
): Promise<ApiResponse<void>> {
  // DELETE /api/document-workflow/hard-delete/{documentId}
}
```

---

### Phase 4: Repository - Get Archived (1h)

```python
# contexts/documentupload/domain/repositories.py

class UploadRepository(ABC):
    # NEU
    @abstractmethod
    async def find_archived(
        self,
        limit: int = 100,
        offset: int = 0,
        document_type_id: Optional[int] = None,
        deleted_before: Optional[datetime] = None,
        deleted_after: Optional[datetime] = None
    ) -> List[UploadedDocument]:
        """
        Hole alle gelöschten Dokumente (Archiv).
        
        Filter: deleted_at IS NOT NULL AND workflow_status == 'deleted'
        Sortierung: deleted_at DESC (neueste zuerst)
        """
```

---

### Phase 5: Use Cases (2h)

```python
# contexts/documentupload/application/use_cases.py

class GetArchivedDocumentsUseCase:
    """Use Case: Hole archivierte Dokumente."""
    
    async def execute(...) -> List[UploadedDocument]:
        # Repository.find_archived aufrufen
        # Filter & Sortierung
        # Return Liste

class RestoreDocumentUseCase:
    """Use Case: Stelle Dokument wieder her."""
    
    async def execute(...) -> UploadedDocument:
        # 1. Lade Dokument (muss deleted sein)
        # 2. Setze workflow_status zurück
        # 3. Setze deleted_at, deleted_by_user_id, deletion_reason auf NULL
        # 4. Speichere
        # 5. Publiziere DocumentRestoredEvent (optional: für Re-Indexing)

class HardDeleteDocumentUseCase:
    """Use Case: Endgültige Löschung."""
    
    async def execute(...) -> Dict[str, Any]:
        # 1. Prüfe confirmation == "LÖSCHEN"
        # 2. Lade Dokument
        # 3. Lösche physische Datei (os.remove)
        # 4. Lösche Preview-Bilder (os.remove)
        # 5. RAG ist bereits gelöscht (bei Soft Delete)
        # 6. Lösche DB-Eintrag ODER setze hard_deleted Flag
```

---

### Phase 6: Events (optional, 1h)

```python
# contexts/documentupload/domain/events.py

class DocumentRestoredEvent:
    """Event: Dokument wurde wiederhergestellt."""
    document_id: int
    restored_by_user_id: int
    restored_to_status: WorkflowStatus
    timestamp: datetime

# Optional: Event Handler für Re-Indexing
# contexts/ragintegration/application/event_handlers.py
class DocumentRestoredEventHandler:
    """Optional: Re-Indexiere wiederhergestelltes Dokument in RAG."""
```

---

## 📊 Datenmodell

### Bereits vorhanden:
- ✅ `deleted_at` (TIMESTAMP)
- ✅ `deleted_by_user_id` (INTEGER)
- ✅ `deletion_reason` (TEXT)
- ✅ `workflow_status` (VARCHAR) - 'deleted' Status

### Optional (für Hard Delete Audit):
```sql
ALTER TABLE upload_documents ADD COLUMN hard_deleted BOOLEAN DEFAULT FALSE;
ALTER TABLE upload_documents ADD COLUMN hard_deleted_at DATETIME;
ALTER TABLE upload_deleted_by_user_id INTEGER;
```

**Vorteil:** Vollständige Audit-Trail, Dokument bleibt in DB

---

## 🔄 Workflow

### 1. Soft Delete (bereits implementiert)
- User klickt "Löschen" → Soft Delete
- `workflow_status` → `deleted`
- `deleted_at` gesetzt
- **RAG Cleanup automatisch** ✅

### 2. Archiv-Ansicht
- User klickt "Archiv" Tab
- Zeigt alle Dokumente mit `deleted_at IS NOT NULL`
- Sortiert nach `deleted_at DESC`

### 3. Wiederherstellung
- User klickt "Wiederherstellen"
- Modal: Als "Entwurf" oder original Status?
- Backend: `deleted_at` → NULL, `workflow_status` → `draft` (oder original)
- Dokument erscheint wieder in normaler Ansicht
- **Optional:** Re-Indexierung in RAG (wenn vorher indexiert war)

### 4. Hard Delete (nur Level 5)
- User klickt "Endgültig löschen"
- Sicherheits-Modal: "LÖSCHEN" eingeben
- Backend: Lösche Dateien, DB-Eintrag (oder Flag)
- **RAG ist bereits gelöscht** ✅

---

## ✅ RAG-Status

**WICHTIG:** Archivierte Dokumente sind automatisch aus RAG entfernt!

- ✅ Soft Delete → `DocumentDeletedEvent` → RAG Cleanup (bereits implementiert)
- ✅ Wiederherstellung → Optional: Re-Indexierung (kann implementiert werden)
- ✅ Hard Delete → RAG ist bereits gelöscht (bei Soft Delete passiert)

---

## 🎨 UX-Features

1. **Archiv-Badge:** Zeigt Anzahl gelöschter Dokumente
2. **Filter:** Nach Datum, Dokumenttyp, User
3. **Sortierung:** Neueste zuerst (deleted_at DESC)
4. **Wiederherstellung:** Ein Klick, Modal für Status-Auswahl
5. **Hard Delete:** Doppelte Bestätigung ("LÖSCHEN" eingeben)
6. **Toast-Notifications:** "✅ Dokument wiederhergestellt", "🗑️ Dokument endgültig gelöscht"

---

## 📝 Nächste Schritte

1. **Phase 1 starten:** Backend-Endpoints (Get Archived, Restore, Hard Delete)
2. **TDD:** Tests ZUERST (RED → GREEN → REFACTOR)
3. **Phase 2:** Frontend-Archiv-Seite
4. **Phase 3:** API Client
5. **Phase 4:** Repository-Implementierung
6. **Phase 5:** Use Cases
7. **Phase 6:** Optional: Events für Re-Indexing

---

**Geschätzte Zeit:** 8-12 Stunden
**Priorität:** Hoch (löst Duplikat-Workflow-Problem)


