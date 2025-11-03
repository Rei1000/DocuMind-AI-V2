# Dokument-Löschung mit RAG Cleanup

## Übersicht

Wenn ein Dokument gelöscht wird (Soft Delete), wird automatisch auch die RAG-Indexierung und alle Vektoren entfernt.

## Ablauf

### 1. Soft Delete auslösen

**Frontend:** `frontend/app/documents/page.tsx`
```typescript
handleDelete() → softDeleteDocument() API-Call
```

**Backend Endpoint:** `contexts/documentupload/interface/workflow_router.py`
```
POST /api/document-workflow/soft-delete
```

### 2. Use Case: SoftDeleteDocumentUseCase

**Datei:** `contexts/documentupload/application/use_cases.py`

Führt aus:
1. Setzt `workflow_status = DELETED`
2. Setzt `deleted_at`, `deleted_by_user_id`, `deletion_reason`
3. **Publiziert `DocumentDeletedEvent`** (Phase 5 - Event-Driven Architecture)

### 3. Event Handler: DocumentDeletedEventHandler

**Datei:** `contexts/ragintegration/application/event_handlers.py`

Empfängt das Event und ruft auf:
```python
RemoveDocumentFromRAGUseCase.execute(upload_document_id)
```

### 4. RemoveDocumentFromRAGUseCase

**Datei:** `contexts/ragintegration/application/use_cases.py`

Führt aus:
1. **Prüft ob Dokument indexiert ist** (aus `rag_indexed_documents` Tabelle)
2. **Löscht Chunks aus Qdrant Vector Store:**
   ```python
   vector_store.delete_chunks_by_document_id(
       collection_name=indexed_doc.collection_name,
       document_id=upload_document_id
   )
   ```
3. **Löscht Chunks aus Datenbank:**
   ```python
   document_chunk_repository.delete_by_indexed_document_id(
       indexed_document_id=indexed_doc.id
   )
   ```
4. **Löscht IndexedDocument:**
   ```python
   indexed_document_repository.delete(indexed_document_id=indexed_doc.id)
   ```

## Was wird gelöscht?

✅ **Wird gelöscht:**
- RAG-Index Eintrag (`rag_indexed_documents`)
- Alle Chunks aus Datenbank (`rag_document_chunks`)
- **Alle Vektoren aus Qdrant** (über `delete_chunks_by_document_id`)
- Collection wird gelöscht wenn leer (optional)

❌ **Wird NICHT gelöscht:**
- Upload-Dokument selbst (Soft Delete - bleibt in DB)
- Physische Datei im Upload-Folder
- Preview-Bilder
- Dokument-Seiten

## Event-Flow

```
SoftDeleteDocumentUseCase
  ↓ (publiziert)
DocumentDeletedEvent
  ↓ (verarbeitet von)
DocumentDeletedEventHandler
  ↓ (ruft auf)
RemoveDocumentFromRAGUseCase
  ↓
1. vector_store.delete_chunks_by_document_id()  → Qdrant Vektoren gelöscht
2. chunk_repo.delete_by_indexed_document_id() → DB Chunks gelöscht  
3. indexed_doc_repo.delete()                   → DB IndexedDocument gelöscht
```

## Prüfung ob Cleanup funktioniert

Nach Soft Delete sollte geprüft werden:

1. **Datenbank:**
   ```sql
   SELECT * FROM rag_indexed_documents WHERE upload_document_id = ?;
   -- Sollte leer sein
   
   SELECT * FROM rag_document_chunks WHERE indexed_document_id IN (
     SELECT id FROM rag_indexed_documents WHERE upload_document_id = ?
   );
   -- Sollte leer sein
   ```

2. **Qdrant:**
   ```python
   # Über Qdrant API prüfen
   collection_info = client.get_collection(collection_name)
   # collection_info.points_count sollte 0 sein für dieses Dokument
   ```

## Wichtig

- **Idempotent:** Cleanup kann mehrfach aufgerufen werden ohne Fehler
- **Asynchron:** Event wird asynchron verarbeitet (kann kurz dauern)
- **Fehler-Tolerant:** Bei Fehler wird Warning geloggt, aber Soft Delete wird nicht rückgängig gemacht

