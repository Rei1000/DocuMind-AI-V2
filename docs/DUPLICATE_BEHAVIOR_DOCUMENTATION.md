# 📋 Duplikat-Verhalten: Dokumentation

> **Status:** ✅ Implementiert  
> **Datum:** 2025-11-03  
> **Kontext:** Document Upload & RAG Integration

---

## 🎯 Zusammenfassung

**Duplikate können hochgeladen werden, werden markiert, können gelöscht werden, werden aber NICHT indexiert.**

### ✅ Implementiertes Verhalten

1. **Upload:** ✅ Duplikate können hochgeladen werden (mit Warnung)
2. **Markierung:** ✅ Duplikate werden im System als `is_duplicate=true` markiert
3. **Original-Verweis:** ✅ `duplicate_of_document_id` zeigt auf das Original
4. **Löschung:** ✅ Duplikate können gelöscht werden (wie normale Dokumente)
5. **Indexierung:** ❌ Duplikate werden NICHT indexiert (Backend + Frontend prüfen)

---

## 🔍 Technische Details

### **Backend: Duplikat-Erkennung**

**Datei:** `contexts/documentupload/application/use_cases.py`

```python
# SHA-256 Hash wird berechnet
file_hash = calculate_sha256_hash(file_path)

# Prüfe auf Duplikat
existing_doc = await self.upload_repo.find_by_hash(file_hash)
if existing_doc:
    is_duplicate = True
    duplicate_of_document_id = existing_doc.id
    # WICHTIG: Für Duplikate setze file_hash auf None
    # (um UNIQUE Constraint zu vermeiden - nur Original behält Hash)
    file_hash = None
```

**Ergebnis:**
- Original-Dokument: `is_duplicate=False`, `file_hash=<SHA256>`, `duplicate_of_document_id=NULL`
- Duplikat: `is_duplicate=True`, `file_hash=NULL`, `duplicate_of_document_id=<Original-ID>`

---

### **Backend: RAG-Indexierung verhindert Duplikate**

**Datei:** `contexts/ragintegration/interface/router.py`

```python
# Prüfe ob Dokument ein Duplikat ist
if is_duplicate:
    return IndexDocumentResponse(
        success=False,
        message=f"Duplikate können nicht indexiert werden. Dieses Dokument ist eine Kopie (zeigt auf Dokument #{duplicate_of_id}). Bitte indexieren Sie das Original-Dokument."
    )
```

**Ergebnis:** Duplikate werden im Backend blockiert, bevor Indexierung startet.

---

### **Frontend: RAG-Indexierung verhindert Duplikate**

**Dateien:**
- `frontend/app/documents/[id]/page.tsx`
- `frontend/components/RAGIndexing.tsx`

```typescript
// Indexierung Button wird nur angezeigt wenn:
document.workflow_status === 'approved' 
  && !document.is_indexed 
  && !document.is_duplicate  // ← NEU

// RAGIndexing Component prüft:
const canIndex = permissions.canIndexDocuments && isApproved && !isDuplicate
```

**Ergebnis:** Duplikate zeigen keinen Indexierungs-Button und können nicht indexiert werden.

---

## 🎨 UX-Implementierung (Alle 5 Optionen)

### **Option 1: Warning-Modal nach Upload** ✅

**Datei:** `frontend/components/DuplicateWarningModal.tsx`

- Modal erscheint nach Duplikat-Upload
- Zeigt Original-Dokument-Info
- Aktionen: "Zum Original springen" oder "Als Duplikat behalten"

**Verwendung:** `frontend/app/document-upload/page.tsx`

---

### **Option 2: Warning-Banner in Success-Message** ✅

**Datei:** `frontend/app/document-upload/page.tsx`

- Gelbes Warning-Banner unter Success-Message
- Zeigt Link zum Original-Dokument
- Nicht zu aufdringlich, aber sichtbar

---

### **Option 3: Badge in Dokument-Detail-Seite** ✅

**Datei:** `frontend/app/documents/[id]/page.tsx`

- Orange Warning-Banner ganz oben auf Detail-Seite
- Immer sichtbar beim Betrachten des Dokuments
- Button zum Springen zum Original

**Zusätzlich:** Warnung in RAG-Indexierung-Sektion:
- "⚠️ Indexierung nicht möglich"
- Link zum Original-Dokument

---

### **Option 4: Icon in Dokumenten-Liste** ✅

**Dateien:** `frontend/app/documents/page.tsx`

**Kanban-Ansicht:**
- Orange Badge mit ⚠️-Icon in jeder Karte
- Zeigt "Duplikat" Label

**Tabellen-Ansicht:**
- Neue Spalte "Duplikat"
- ⚠️-Icon wenn `is_duplicate=true`
- Tooltip zeigt Original-Dokument-ID

---

### **Option 5: Kombiniert** ✅

Alle 4 Optionen sind implementiert und arbeiten zusammen:

1. **Nach Upload:** Modal (Option 1) + Banner (Option 2)
2. **In Detail-Ansicht:** Badge oben (Option 3)
3. **In Liste:** Icon/Badge (Option 4)

---

## 📊 Datenbank-Schema

### **upload_documents Tabelle:**

```sql
-- Duplikat-Felder
file_hash VARCHAR(64)                    -- SHA-256 Hash (nur für Originale, NULL bei Duplikaten)
is_duplicate BOOLEAN DEFAULT FALSE       -- Flag: Ist Duplikat?
duplicate_of_document_id INTEGER         -- FK zum Original-Dokument (wenn Duplikat)
```

### **Indizes:**

```sql
CREATE UNIQUE INDEX idx_upload_documents_file_hash_unique 
  ON upload_documents(file_hash) 
  WHERE file_hash IS NOT NULL;

CREATE INDEX idx_upload_documents_is_duplicate 
  ON upload_documents(is_duplicate) 
  WHERE is_duplicate = TRUE;
```

---

## 🔄 Workflow-Beispiel

### **Szenario: Gleiche Datei wird zweimal hochgeladen**

1. **Erster Upload (Original):**
   - ✅ Upload erfolgreich
   - ✅ `file_hash = "14b45d5563..."` (SHA-256)
   - ✅ `is_duplicate = false`
   - ✅ `duplicate_of_document_id = NULL`
   - ✅ Kann indexiert werden (wenn freigegeben)

2. **Zweiter Upload (Duplikat):**
   - ✅ Upload erfolgreich (mit Warnung)
   - ⚠️ Modal erscheint: "Duplikat erkannt"
   - ⚠️ Warning-Banner in Success-Message
   - ✅ `file_hash = NULL` (vermeidet UNIQUE Constraint)
   - ✅ `is_duplicate = true`
   - ✅ `duplicate_of_document_id = 6` (zeigt auf Original)
   - ❌ Kann NICHT indexiert werden (Button fehlt, Backend blockiert)

3. **In Dokument-Liste:**
   - ⚠️ Duplikat zeigt ⚠️-Icon
   - Tooltip: "Duplikat - zeigt auf Dokument #6"

4. **In Dokument-Detail:**
   - ⚠️ Orange Badge oben: "Duplikat"
   - ⚠️ Warnung in RAG-Sektion: "Indexierung nicht möglich"
   - ✅ Button "Zum Original →"

---

## 🛡️ Sicherheit & Constraints

### **UNIQUE Constraint auf file_hash:**

- Nur Originale haben einen Hash (Duplikate: `file_hash=NULL`)
- Verhindert doppelte Hashes
- Ermöglicht schnelle Duplikat-Prüfung (O(1) Lookup)

### **Foreign Key auf duplicate_of_document_id:**

- Optional (kann NULL sein)
- Zeigt immer auf existierendes Original
- Cascade-Verhalten: Bei Löschung des Originals bleibt Duplikat (zeigt auf gelöschtes Dokument)

---

## 📝 API-Responses

### **Upload Response (Duplikat):**

```json
{
  "success": true,
  "message": "⚠️ Warning: Duplicate document detected! This document is identical to document ID 6. Upload continued anyway.",
  "document": {
    "id": 9,
    "is_duplicate": true,
    "duplicate_of_document_id": 6,
    "file_hash": null,
    // ... andere Felder
  }
}
```

### **Indexierung Response (Duplikat):**

```json
{
  "success": false,
  "message": "Duplikate können nicht indexiert werden. Dieses Dokument ist eine Kopie (zeigt auf Dokument #6). Bitte indexieren Sie das Original-Dokument.",
  "chunks_created": 0,
  "processing_time_ms": 0
}
```

---

## ✅ Tests

**Integration Tests:**
- `tests/integration/documentupload/test_duplicate_prevention.py`
  - ✅ Duplikat wird erkannt
  - ✅ Verschiedene Dokumente werden nicht als Duplikat markiert
  - ✅ Hash-Berechnung ist konsistent

**Manuelle Tests:**
- ✅ Upload gleicher Datei zweimal → Duplikat wird erkannt
- ✅ Duplikat zeigt Modal + Banner
- ✅ Duplikat zeigt Badge in Detail-Ansicht
- ✅ Duplikat zeigt Icon in Liste
- ✅ Indexierung wird blockiert (Frontend + Backend)

---

## 🎯 Zusammenfassung: Duplikat-Verhalten

| Aktion | Original | Duplikat |
|--------|----------|----------|
| **Upload möglich?** | ✅ Ja | ✅ Ja (mit Warnung) |
| **Markiert als Duplikat?** | ❌ Nein | ✅ Ja |
| **file_hash gesetzt?** | ✅ Ja (SHA-256) | ❌ Nein (NULL) |
| **Löschung möglich?** | ✅ Ja | ✅ Ja |
| **Indexierung möglich?** | ✅ Ja (wenn approved) | ❌ Nein |

---

## 📚 Weitere Dokumentation

- `docs/UX_DUPLICATE_WARNING_PROPOSALS.md` - UX-Vorschläge
- `docs/database-schema.md` - Datenbank-Schema
- `backend/migrations/add_file_hash_fields.sql` - Migration

---

**✅ Implementierung abgeschlossen: Alle 5 UX-Optionen sind implementiert und Duplikate werden korrekt behandelt!**

