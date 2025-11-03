# 🔄 Verbesserter Duplikat-Workflow

## ✅ Behobene Probleme

### Problem 1: Gelöschte Dokumente werden noch als Duplikat erkannt

**Vorher:**
- `find_by_hash` fand auch gelöschte Dokumente
- Wenn Original gelöscht, aber Hash noch in DB → Duplikat-Warnung

**Lösung:**
- `find_by_hash` filtert jetzt gelöschte Dokumente heraus (`deleted_at IS NULL`)
- Wenn alle Dokumente (Original + Duplikate) gelöscht sind → Dokument kann NEU hochgeladen werden

**Code-Änderung:**
```python
# contexts/documentupload/infrastructure/repositories.py
query = self.db.query(UploadDocumentModel).filter(
    UploadDocumentModel.file_hash == file_hash.value
)

# NEU: Nur aktive (nicht-gelöschte) Dokumente berücksichtigen
if hasattr(UploadDocumentModel, 'deleted_at'):
    query = query.filter(
        UploadDocumentModel.deleted_at.is_(None)
    )
```

### Problem 2: RAG Cleanup funktioniert nicht korrekt

**Vorher:**
- Gelöschte Dokumente blieben in RAG indexiert
- Vektoren in Qdrant nicht entfernt

**Lösung:**
- Bug-Fix in `delete_by_indexed_document_id` (falsche Spalte)
- Event Handler für RAG Cleanup ist implementiert
- Manuelles Cleanup-Script für bestehende Daten

---

## 🎯 Verbesserter Workflow

### Szenario: Dokument löschen und wieder hochladen

**Vorher:**
1. User löscht Original + Duplikate
2. User lädt gleiches Dokument hoch
3. ❌ System erkennt noch als Duplikat (findet gelöschtes Original)

**Jetzt:**
1. User löscht Original + Duplikate (Soft Delete)
2. RAG Cleanup entfernt Vektoren automatisch
3. User lädt gleiches Dokument hoch
4. ✅ System behandelt als NEU (find_by_hash findet keine aktiven Dokumente)

### UX-Verbesserungen

**Beim Upload:**
```
Wenn Original gelöscht ist:
┌─────────────────────────────────────────────┐
│ ℹ️ Info                                     │
├─────────────────────────────────────────────┤
│ Ein ähnliches Dokument existierte bereits, │
│ wurde aber gelöscht (im Archiv).           │
│                                              │
│ Dieses Dokument wird als NEU behandelt.     │
│                                              │
│ [✅ Als NEU hochladen]                      │
└─────────────────────────────────────────────┘
```

**Nach Upload:**
- Kein Duplikat-Flag
- Normale Behandlung (wie jedes neue Dokument)
- Kann normal indexiert werden

---

## 📋 Nächste Schritte (Archiv-System)

Siehe: `docs/ARCHIVE_SYSTEM_PROPOSAL.md`

**Kern-Features:**
1. 📦 Archiv-Ansicht für gelöschte Dokumente
2. 📝 Wiederherstellung (Undelete)
3. 🗑️ Endgültige Löschung (Hard Delete)
4. ⏰ Automatische Bereinigung nach Retention-Periode

