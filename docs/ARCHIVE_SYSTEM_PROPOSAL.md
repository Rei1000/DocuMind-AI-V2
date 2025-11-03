# 📦 Archiv-System: Best Practice Workflow & UX

## 🎯 Anforderungen

1. **Gelöschte Dokumente anzeigen** (Archiv-Ansicht)
2. **Wiederherstellung ermöglichen** (Undelete)
3. **Vollständige Löschung** (Hard Delete nach Retention-Periode)
4. **Überragende UX** - Intuitiv und effizient

---

## 🏗️ Konzept: 3-Ebenen Archiv-System

### Ebene 1: Aktive Dokumente (workflow_status != 'deleted')
- **Anzeige:** Normal in Kanban/Tabelle
- **Zugriff:** Vollzugriff, Bearbeitung möglich

### Ebene 2: Archiv (workflow_status == 'deleted', aber noch in DB)
- **Anzeige:** Separater Archiv-Bereich
- **Zugriff:** Nur lesen, Wiederherstellung möglich
- **Retention:** Konfigurierbar (z.B. 90 Tage)

### Ebene 3: Hard Delete (nach Retention)
- **Anzeige:** Nicht mehr sichtbar
- **Zugriff:** Kein Zugriff mehr möglich
- **DB:** Eintrag bleibt für Audit (nur Flag, keine Dateien)

---

## 📋 UX-Konzept

### 1. **Archiv-Navigation**

```
┌─────────────────────────────────────────┐
│ 📚 Dokumente  │  📦 Archiv (5)          │
└─────────────────────────────────────────┘
```

**Implementierung:**
- Tab/Navigation-Toggle zwischen "Aktive Dokumente" und "Archiv"
- Badge zeigt Anzahl gelöschter Dokumente
- Archiv-Tab nur für Level 4+ (QM-Mitarbeiter)

### 2. **Archiv-Ansicht (Table View)**

```
┌──────────────────────────────────────────────────────────────┐
│ 📦 Archiv │ Gelöschte Dokumente                              │
├──────────────────────────────────────────────────────────────┤
│ 🔍 Suche... │ 📅 Sortiert nach: Löschdatum (neueste zuerst)  │
├──────────────────────────────────────────────────────────────┤
│ 📄 PA 7.3 [00]... │ SOP │ 7.3 │ Gelöscht: 03.11.2025        │
│                   │ 📝 Wiederherstellen │ 🗑️ Endgültig löschen│
├──────────────────────────────────────────────────────────────┤
│ 📄 Dokument XY... │ ... │ Gelöscht: 02.11.2025              │
│                   │ 📝 Wiederherstellen │ 🗑️ Endgültig löschen│
└──────────────────────────────────────────────────────────────┘
```

**Features:**
- Nur Table View (kein Kanban für Archiv)
- Spalten: Name, Typ, QM-Kapitel, Gelöscht am, Gelöscht von, Grund
- Filter: Nach Datum, Dokumenttyp, User
- Aktionen: Wiederherstellen, Endgültig löschen

### 3. **Wiederherstellung**

**Workflow:**
1. User klickt "Wiederherstellen" im Archiv
2. Modal: "Dokument wiederherstellen?"
   - **Option:** Wiederherstellen als "Entwurf" (empfohlen)
   - **Option:** Wiederherstellen mit original Status (wenn berechtigt)
3. Nach Wiederherstellung:
   - `workflow_status` → `draft` (oder original Status)
   - `deleted_at` → `NULL`
   - `deleted_by_user_id` → `NULL`
   - `deletion_reason` → `NULL`
   - Dokument erscheint wieder in normaler Ansicht

**UX:**
- Toast-Benachrichtigung: "✅ Dokument wiederhergestellt"
- Automatischer Reload der Dokumenten-Liste
- Dokument erscheint in "Entwurf"-Spalte (oder original Status)

### 4. **Endgültige Löschung (Hard Delete)**

**Workflow:**
1. User klickt "Endgültig löschen" im Archiv
2. **Sicherheitsabfrage:**
   ```
   ⚠️ Endgültige Löschung
   
   Dieses Dokument wird permanent aus dem System entfernt:
   - Datei wird gelöscht
   - Preview-Bilder werden gelöscht
   - RAG-Index wird entfernt (falls indexiert)
   
   WICHTIG: Diese Aktion kann nicht rückgängig gemacht werden!
   
   Bitte geben Sie zur Bestätigung ein: "LÖSCHEN"
   [Textfeld für Bestätigung]
   
   [❌ Abbrechen] [🗑️ Endgültig löschen]
   ```
3. Nur Level 5 (Admin) darf endgültig löschen
4. Nach Bestätigung:
   - Physische Datei löschen
   - Preview-Bilder löschen
   - RAG-Index entfernen (falls vorhanden)
   - DB-Eintrag löschen (oder nur Flag setzen für Audit)

### 5. **Automatische Bereinigung**

**Background Job (täglich):**
- Prüfe alle gelöschten Dokumente (`deleted_at IS NOT NULL`)
- Wenn `deleted_at` älter als Retention-Periode (z.B. 90 Tage):
  - Optional: Warnung an QM-Admin (E-Mail/Notification)
  - Automatische Hard Delete nach zusätzlichen 30 Tagen
- Logge alle Löschungen für Audit

---

## 🔄 Verbesserter Duplikat-Workflow

### Problem gelöst:
✅ **Wenn alle Dokumente (Original + Duplikate) gelöscht sind:**
- `find_by_hash` findet keine aktiven Dokumente mehr
- Dokument kann wieder als NEU hochgeladen werden
- Keine Duplikat-Warnung mehr

### UX-Verbesserung:

**Beim Upload:**
```
┌─────────────────────────────────────────────┐
│ ⚠️ Duplikat erkannt                          │
├─────────────────────────────────────────────┤
│ Dieses Dokument existiert bereits als:      │
│ 📄 PA 7.3 [00]... (ID: 6)                    │
│                                              │
│ Status: ✅ Freigegeben                      │
│                                              │
│ ⚠️ Hinweis: Das Original ist bereits         │
│    gelöscht (Archiv). Wenn Sie fortfahren,   │
│    wird dieses Dokument als NEU behandelt.   │
│                                              │
│ [❌ Abbrechen] [✅ Als Neu hochladen]        │
└─────────────────────────────────────────────┘
```

**Wenn Original gelöscht:**
- Zeige Info: "Original ist gelöscht (im Archiv)"
- Upload-Button: "Als NEU hochladen" (statt "Duplikat trotzdem hochladen")
- Nach Upload: Normal behandelt (kein Duplikat-Flag)

---

## 🛠️ Implementierung

### Backend

**1. Archiv-Endpoint**
```python
@router.get("/archive", response_model=GetArchivedDocumentsResponse)
async def get_archived_documents(
    limit: int = Query(100),
    offset: int = Query(0),
    document_type_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Hole alle gelöschten Dokumente (Archiv)."""
    # Filter: workflow_status == 'deleted' AND deleted_at IS NOT NULL
    # Sortierung: deleted_at DESC (neueste zuerst)
```

**2. Wiederherstellung-Endpoint**
```python
@router.post("/restore/{document_id}", response_model=RestoreDocumentResponse)
async def restore_document(
    document_id: int,
    restore_to_status: Optional[WorkflowStatus] = Query('draft'),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Stelle gelöschtes Dokument wieder her."""
    # Setze workflow_status zurück
    # Setze deleted_at, deleted_by_user_id, deletion_reason auf NULL
    # Publiziere DocumentRestoredEvent
```

**3. Hard Delete Endpoint**
```python
@router.delete("/hard-delete/{document_id}")
async def hard_delete_document(
    document_id: int,
    confirmation: str = Query(..., description="Zur Bestätigung: 'LÖSCHEN' eingeben"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Endgültige Löschung (nur Level 5)."""
    # Prüfe confirmation == "LÖSCHEN"
    # Lösche physische Dateien
    # Entferne aus RAG
    # Lösche DB-Eintrag (oder setze hard_deleted Flag)
```

### Frontend

**1. Archiv-Tab in Navigation**
```typescript
// In Navigation.tsx
<Link href="/documents/archive">
  📦 Archiv {archivedCount > 0 && `(${archivedCount})`}
</Link>
```

**2. Archiv-Seite**
```
/app/documents/archive/page.tsx
- Table View mit gelöschten Dokumenten
- Filter & Suche
- Aktionen: Wiederherstellen, Hard Delete
```

**3. Verbesserter Upload-Flow**
- Prüfe ob Original gelöscht ist
- Zeige entsprechende Meldung
- Behandle als NEU wenn alle gelöscht sind

---

## 📊 Datenmodell-Erweiterungen

### Optional: Hard Delete Flag
```sql
ALTER TABLE upload_documents ADD COLUMN hard_deleted BOOLEAN DEFAULT FALSE;
ALTER TABLE upload_documents ADD COLUMN hard_deleted_at DATETIME;
ALTER TABLE upload_documents ADD COLUMN hard_deleted_by_user_id INTEGER;
```

**Vorteil:**
- Vollständige Audit-Trail
- Dokument bleibt in DB (nur Flag)
- Historische Daten bleiben erhalten

---

## ✅ Best Practices

1. **Soft Delete immer zuerst** (für Wiederherstellung)
2. **Retention-Periode** konfigurierbar (default: 90 Tage)
3. **Hard Delete nur für Admin** (Level 5)
4. **Audit-Trail** für alle Löschungen
5. **Automatische Bereinigung** nach Retention
6. **RAG Cleanup** bei Soft Delete (automatisch via Event)
7. **Physische Löschung** nur bei Hard Delete

---

## 🎨 UX-Highlights

✅ **Klare Trennung:** Aktive Dokumente vs. Archiv
✅ **Einfache Wiederherstellung:** Ein Klick
✅ **Sichere Hard Delete:** Doppelte Bestätigung
✅ **Transparenz:** Zeige Status, Datum, User, Grund
✅ **Automatisierung:** Retention-Management
✅ **Intelligente Duplikat-Erkennung:** Berücksichtigt gelöschte Dokumente

