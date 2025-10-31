# Cleanup & Re-Indexierung nach Prompt-Änderung

## Warum Cleanup?

Wenn der Standard-Prompt für einen Dokumenttyp geändert wird, müssen alle bereits indexierten Dokumente **neu indexiert** werden, damit:
- ✅ Die neue JSON-Struktur verwendet wird (z.B. `nodes` statt `process_steps`)
- ✅ Die richtige Chunking-Strategie angewendet wird (`_chunk_flowchart` statt `_chunk_sop_document`)
- ✅ Die neuen Metadaten korrekt gesetzt werden (`document_id`, `document_type`, etc.)

---

## Cleanup-Schritte

### 1. **Indexierte Dokumente löschen** (aus RAG-System)

**Option A: Über API** (wenn verfügbar)
```bash
# TODO: API-Endpoint für Bulk-Delete prüfen
```

**Option B: Direkt in Datenbank**
```sql
-- Prüfe welche Dokumente indexiert sind
SELECT id, upload_document_id, qdrant_collection_name, total_chunks 
FROM rag_indexed_documents;

-- Lösche alle IndexedDocuments (Cascade löscht automatisch Chunks)
DELETE FROM rag_indexed_documents;
```

**Option C: Python Script** (sauberer, mit Qdrant-Cleanup)
```python
from backend.app.database import SessionLocal
from contexts.ragintegration.infrastructure.models import IndexedDocumentModel
from qdrant_client import QdrantClient
import os

db = SessionLocal()
try:
    # Hole alle indexierten Dokumente
    indexed_docs = db.query(IndexedDocumentModel).all()
    
    print(f"=== CLEANUP: {len(indexed_docs)} Dokumente gefunden ===")
    
    # Lösche Qdrant Collections
    qdrant_path = 'data/qdrant'
    if os.path.exists(qdrant_path):
        client = QdrantClient(path=qdrant_path)
        for doc in indexed_docs:
            try:
                client.delete_collection(doc.qdrant_collection_name)
                print(f"✓ Collection gelöscht: {doc.qdrant_collection_name}")
            except Exception as e:
                print(f"⚠ Collection bereits leer oder nicht gefunden: {doc.qdrant_collection_name}")
    
    # Lösche aus Datenbank (Cascade löscht Chunks automatisch)
    deleted_count = db.query(IndexedDocumentModel).delete()
    db.commit()
    print(f"✓ {deleted_count} IndexedDocuments gelöscht")
    
    print("=== CLEANUP ABGESCHLOSSEN ===")
finally:
    db.close()
```

---

### 2. **Upload-Dokumente behalten** (wichtig!)

❌ **NICHT löschen:**
- `upload_documents` Tabelle → Dokumente bleiben erhalten
- Dateien in `data/uploads/` → Dateien bleiben erhalten
- Vision-Extraktion Results → Bleiben erhalten (werden neu verwendet)

✅ **Wird gelöscht:**
- `rag_indexed_documents` → Wird neu erstellt
- `rag_document_chunks` → Wird neu erstellt
- Qdrant Collections → Wird neu erstellt

---

### 3. **Neue Indexierung starten**

Nach dem Cleanup:

1. **Dokumente neu indexieren:**
   - Über Frontend: `/documents` → "RAG indexieren" Button
   - Oder über API: `POST /api/rag/documents/index`

2. **System verwendet automatisch:**
   - ✅ Neuen Standard-Prompt (mit `nodes` + `connections`)
   - ✅ Richtige Chunking-Strategie (`_chunk_flowchart`)
   - ✅ Korrekte Metadaten (`document_id`, etc.)

---

## Vollständiger Workflow

```
1. ✅ Neuer Prompt in AI Playground getestet
2. ✅ Neuer Prompt als Standard-Prompt gespeichert (Status: active)
3. ✅ Cleanup ausführen (siehe oben)
4. ✅ Dokumente neu hochladen/indexieren
   → System verwendet automatisch neuen Prompt
5. ✅ Prüfe Logs: Sollte "_chunk_flowchart" verwenden (nicht "_chunk_sop_document")
6. ✅ Test im RAG-Chat: Sollte jetzt präzise Antworten geben!
```

---

## Wichtige Hinweise

### Foreign Key Constraints
Die Datenbank hat Cascade-Delete konfiguriert:
- `rag_indexed_documents` → `rag_document_chunks` (automatisch gelöscht)

### Qdrant Collections
- Collections werden manuell gelöscht (über Qdrant Client)
- Bei Re-Indexierung werden neue Collections erstellt

### Upload Documents
- **BLEIBEN ERHALTEN** → Keine Neu-Upload nötig!
- Vision-Extraktion Results werden neu verwendet
- Neue Indexierung läuft automatisch durch

---

## Prüfen ob Cleanup erfolgreich

```python
from backend.app.database import SessionLocal
from contexts.ragintegration.infrastructure.models import IndexedDocumentModel, DocumentChunkModel

db = SessionLocal()
try:
    indexed_count = db.query(IndexedDocumentModel).count()
    chunks_count = db.query(DocumentChunkModel).count()
    
    print(f"Indexierte Dokumente: {indexed_count} (sollte 0 sein)")
    print(f"Chunks: {chunks_count} (sollte 0 sein)")
    
    if indexed_count == 0 and chunks_count == 0:
        print("✅ Cleanup erfolgreich!")
    else:
        print("❌ Cleanup unvollständig!")
finally:
    db.close()
```

