# 📋 Document Workflow System

> **User Manual:** Workflow-Management für Dokumente  
> **Version:** 2.0.0  
> **Letzte Aktualisierung:** 2025-10-22

---

## 🎯 Übersicht

Das Document Workflow System ermöglicht es, Dokumente durch einen strukturierten 4-Status-Workflow zu führen:

```
📄 Draft → 🔍 Reviewed → ✅ Approved
  ↓           ↓
❌ Rejected ← ❌ Rejected
```

### **Workflow-Status**

| Status | Beschreibung | Wer kann ändern |
|--------|-------------|-----------------|
| **📄 Draft** | Entwurf - Neues Dokument | Level 3+ |
| **🔍 Reviewed** | Geprüft - Von Abteilungsleiter freigegeben | Level 4+ |
| **✅ Approved** | Freigegeben - Finale QM-Freigabe | Level 4+ |
| **❌ Rejected** | Abgelehnt - Zurückgewiesen | Level 3+ |

---

## 👥 Berechtigungen

### **User-Level Matrix**

| Level | Rolle | Dokumente sehen | Status ändern |
|-------|-------|------------------|---------------|
| **1** | RAG Chat | ❌ Keine | ❌ Keine |
| **2** | Teamleiter | 👁️ Eigene Interest Groups | ❌ Keine |
| **3** | Abteilungsleiter | 👁️ Eigene Interest Groups | ✅ Draft → Reviewed<br/>✅ Rejected → Draft |
| **4** | QM-Manager | 👁️ Alle Dokumente | ✅ Reviewed → Approved<br/>✅ Reviewed → Rejected |
| **5** | QMS Admin | 👁️ Alle Dokumente | ✅ Alle Transitions |

### **Interest Groups Filter**

- **Level 2-3:** Sehen nur Dokumente ihrer zugewiesenen Interest Groups
- **Level 4-5:** Sehen alle Dokumente im System

---

## 🚀 Workflow-Prozess

### **1. Dokument hochladen**
1. Gehe zu `/document-upload`
2. Wähle Datei (PDF, DOCX, PNG, JPG)
3. Fülle Metadaten aus:
   - **Dokumenttyp:** Wähle aus verfügbaren Typen
   - **QM-Kapitel:** z.B. "1.2.3"
   - **Version:** z.B. "v1.0"
   - **Interest Groups:** Wähle betroffene Abteilungen
4. Klicke "Hochladen"
5. **Status:** Dokument startet als "Draft"

### **2. Dokument prüfen (Level 3+)**
1. Gehe zu `/documents`
2. Dokument erscheint in "Entwurf"-Spalte
3. **Drag & Drop:** Ziehe Dokument zu "Geprüft"
4. **Modal öffnet sich:**
   - **Grund:** Pflichtfeld - Warum wird Status geändert?
   - **Kommentar:** Optional - Zusätzliche Anmerkungen
5. Klicke "Bestätigen"
6. **Status:** Dokument wird zu "Reviewed"

### **3. Dokument freigeben (Level 4+)**
1. Dokument erscheint in "Geprüft"-Spalte
2. **Drag & Drop:** Ziehe Dokument zu "Freigegeben"
3. **Modal öffnet sich:**
   - **Grund:** z.B. "QM-Freigabe nach Prüfung"
   - **Kommentar:** z.B. "Alle Anforderungen erfüllt"
4. Klicke "Bestätigen"
5. **Status:** Dokument wird zu "Approved"

### **4. Dokument zurückweisen (Level 3+)**
1. Dokument in "Geprüft"-Spalte
2. **Drag & Drop:** Ziehe Dokument zu "Zurückgewiesen"
3. **Modal öffnet sich:**
   - **Grund:** z.B. "Anforderungen nicht erfüllt"
   - **Kommentar:** z.B. "Fehlende Informationen in Abschnitt 3.2"
4. Klicke "Bestätigen"
5. **Status:** Dokument wird zu "Rejected"

### **5. Zurück zu Entwurf (Level 3+)**
1. Dokument in "Zurückgewiesen"-Spalte
2. **Drag & Drop:** Ziehe Dokument zu "Entwurf"
3. **Modal öffnet sich:**
   - **Grund:** z.B. "Überarbeitung nach Rückmeldung"
   - **Kommentar:** z.B. "Fehlende Informationen ergänzt"
4. Klicke "Bestätigen"
5. **Status:** Dokument wird zu "Draft"

---

## 📊 Kanban Board

### **Ansicht wechseln**
- **📋 Kanban:** Drag & Drop Ansicht (Standard)
- **📊 Tabelle:** Listen-Ansicht mit Sortierung

### **Filter verwenden**
- **Dokumenttyp:** Filtere nach Dokumenttyp
- **Interest Groups:** Filtere nach Abteilungen
- **Suche:** Volltext-Suche in Dateinamen

### **Dokument-Aktionen**
- **👁️ Ansehen:** Öffne Dokument-Detail
- **🗑️ Löschen:** Lösche Dokument (nur Draft-Status)
- **📋 Historie:** Zeige Workflow-Historie

---

## 📈 Workflow-Historie

### **Historie anzeigen**
1. Öffne Dokument-Detail (`/documents/{id}`)
2. Scrolle zu "Workflow-Historie"
3. **Timeline zeigt:**
   - **Status-Änderungen:** Wer, wann, warum
   - **Kommentare:** Zusätzliche Anmerkungen
   - **Zeitstempel:** Exakte Uhrzeit

### **Historie-Details**
- **Von/zu Status:** Welche Änderung
- **Geändert von:** Benutzername
- **Grund:** Warum wurde geändert
- **Kommentar:** Zusätzliche Informationen
- **Datum/Zeit:** Wann geändert

---

## 🔧 Technische Details

### **API-Endpoints**
- `POST /api/document-workflow/change-status` - Status ändern
- `GET /api/document-workflow/status/{status}` - Dokumente nach Status
- `GET /api/document-workflow/history/{document_id}` - Workflow-Historie
- `GET /api/document-workflow/allowed-transitions/{document_id}` - Erlaubte Transitions

### **Datenbank-Tabellen**
- **`upload_documents`:** Dokumente mit `workflow_status`
- **`document_status_changes`:** Workflow-Historie
- **`document_comments`:** Kommentare zu Dokumenten

### **Permission-Checks**
- **Backend:** Automatische Berechtigungsprüfung
- **Frontend:** UI-Elemente basierend auf User-Level
- **API:** JWT-Token-basierte Authentifizierung

---

## ❓ Häufige Fragen

### **Q: Kann ich ein Dokument überspringen?**
A: Nein, der Workflow muss sequenziell durchlaufen werden (Draft → Reviewed → Approved).

### **Q: Wer kann Dokumente sehen?**
A: Level 2-3 sehen nur ihre Interest Groups, Level 4-5 sehen alle Dokumente.

### **Q: Kann ich einen Status rückgängig machen?**
A: Ja, aber nur bestimmte Transitions:
- Rejected → Draft (Level 3+)
- Approved ist final (keine Rücknahme)

### **Q: Was passiert mit gelöschten Dokumenten?**
A: Nur Draft-Dokumente können gelöscht werden. Andere Status sind geschützt.

### **Q: Wie lange wird die Historie gespeichert?**
A: Alle Workflow-Änderungen werden permanent gespeichert (Audit Trail).

---

## 🎯 Best Practices

### **Für Abteilungsleiter (Level 3)**
- Prüfe Dokumente gründlich vor "Geprüft"
- Verwende aussagekräftige Gründe
- Kommentiere bei Problemen

### **Für QM-Manager (Level 4)**
- Prüfe Dokumente vor finaler Freigabe
- Dokumentiere Ablehnungen mit Begründung
- Nutze Kommentare für Team-Kommunikation

### **Für QMS Admin (Level 5)**
- Überwache Workflow-Performance
- Prüfe Audit Trail regelmäßig
- Schulung der Teams

---

## 📞 Support

Bei Fragen oder Problemen:
- **Technischer Support:** IT-Abteilung
- **Workflow-Fragen:** QM-Abteilung
- **Berechtigungen:** System-Administrator

---

**Letzte Aktualisierung:** 2025-10-22  
**Version:** 2.0.0  
**Status:** ✅ Vollständig implementiert
