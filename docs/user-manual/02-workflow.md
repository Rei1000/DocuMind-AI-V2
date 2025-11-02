# 📋 Document Workflow System

> **User Manual:** Workflow-Management für Dokumente  
> **Version:** 2.2.0  
> **Letzte Aktualisierung:** 2025-11-02

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

## 👥 Berechtigungen (RBAC Multi-Level)

### **User-Level Matrix**

| Level | Rolle | Dokumente sehen | Status ändern |
|-------|-------|------------------|---------------|
| **1** | Mitarbeiter | ❌ Keine (nur RAG Chat) | ❌ Keine |
| **2** | Teamleiter | 👁️ Eigene Interest Groups (nur Tabelle) | ❌ Keine |
| **3** | Abteilungsleiter | 👁️ Eigene Interest Groups (Kanban) | ✅ Draft → Reviewed<br/>✅ Rejected → Draft<br/>(nur für eigene IGs mit Level ≥ 3) |
| **4** | QM-Manager | 👁️ Alle Dokumente | ✅ Reviewed → Approved<br/>✅ Reviewed → Rejected<br/>✅ Alle Transitions |
| **5** | QMS Admin | 👁️ Alle Dokumente | ✅ Alle Transitions |

### **Interest Groups Filter**

- **Level 1-3:** Sehen nur Dokumente ihrer zugewiesenen Interest Groups
- **Level 4-5:** Sehen alle Dokumente im System

### **Multi-Level Support**

Ein User kann unterschiedliche Approval Levels für verschiedene Interest Groups haben:

**Beispiel:**
```
User: max.mustermann@company.com
├── Produktion: Level 3 (Abteilungsleiter)
└── Service: Level 2 (Teamleiter)
```

**Konsequenzen:**
- **Global:** User wird als Level 3 behandelt (für Navigation)
- **Context-Specific:**
  - Dokument (Produktion): Kanban sichtbar, Draft → Reviewed möglich (Level 3 ✅)
  - Dokument (Service): Kein Kanban, nur Tabelle (Level 2 ❌)

### **Document Type Filtering**

Für Level 2-3 werden in der Dokumenten-Liste nur Document Types angezeigt, die Dokumente in den eigenen Interest Groups haben.

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
A: Level 1-3 sehen nur ihre Interest Groups, Level 4-5 sehen alle Dokumente.

### **Q: Was bedeutet Multi-Level RBAC?**
A: Ein User kann unterschiedliche Approval Levels für verschiedene Interest Groups haben. Das System prüft für jede Aktion (Kanban, Workflow) das entsprechende IG-Level des Dokuments.

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

---

## 💬 RAG Integration

### **RAG-Indexierung**

#### **Automatische Indexierung**
- **Status "Approved":** Dokumente werden automatisch für RAG indexiert
- **Chunking:** Intelligente Aufteilung in semantische Abschnitte
- **Vector Store:** Speicherung in Qdrant für semantische Suche
- **Embeddings:** Intelligente Provider-Auswahl (Auto)
  - OpenAI GPT-5 Mini Key (1536 Dimensionen) - Best wenn verfügbar
  - Google Gemini (768 Dimensionen) - Sehr gut, kostenlos
  - Sentence Transformers (768/384 Dimensionen) - Lokal, kostenlos

#### **RAG-Verfügbarkeit**
- **Nur Approved:** Nur freigegebene Dokumente sind im RAG verfügbar
- **Real-time:** Indexierung erfolgt sofort nach Status-Änderung
- **Chunking-Strategie:** Dokumenttyp-spezifische Chunking-Methoden
- **Metadata:** Vollständige Metadaten für präzise Suche

### **RAG Chat für Workflow**

#### **Dokument-spezifische Fragen**
```
Beispiele:
- "Welche Schritte sind in diesem SOP erforderlich?"
- "Welche Sicherheitshinweise gibt es in dieser Arbeitsanweisung?"
- "Wie wird dieser Prozess dokumentiert?"
```

#### **Workflow-Unterstützung**
- **Review-Hilfe:** Fragen zu Dokumenten während der Prüfung
- **Compliance-Check:** Sicherheits- und Qualitätsanforderungen prüfen
- **Prozess-Verständnis:** Komplexe Prozesse verstehen
- **Referenz-Suche:** Ähnliche Dokumente finden

### **RAG-Berechtigungen**

#### **Level 1 - RAG Chat**
- **Zugriff:** Nur auf freigegebene Dokumente
- **Funktionen:** Fragen stellen, Quellen anzeigen
- **Einschränkungen:** Keine Dokument-Verwaltung

#### **Level 2-5 - Vollzugriff**
- **Zugriff:** Alle freigegebenen Dokumente
- **Funktionen:** Vollständige RAG-Funktionalität
- **Erweiterte Suche:** Filter nach Dokumenttyp, Interest Groups

---

Bei Fragen oder Problemen:
- **Technischer Support:** IT-Abteilung
- **Workflow-Fragen:** QM-Abteilung
- **Berechtigungen:** System-Administrator
- **RAG-Support:** QMS Admin

---

**Letzte Aktualisierung:** 2025-11-02  
**Version:** 2.2.0  
**Status:** ✅ Vollständig implementiert mit RAG Integration + RBAC Multi-Level
