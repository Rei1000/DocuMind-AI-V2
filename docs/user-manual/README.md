# 📚 DocuMind-AI V2 - User Manual

> **Version:** 2.5.0  
> **Stand:** 2025-11-11
> **Status:** ✅ **PRODUCTION READY**

---

## 🎯 Übersicht

DocuMind-AI V2 ist ein modernes Quality Management System (QMS) mit intelligenter Dokumentenverwaltung und RAG Chat-System.

### ✨ Hauptfunktionen

- 🏢 **Interest Groups Management** - Stakeholder-Gruppen verwalten
- 👥 **User Management** - Benutzer mit Rollen und Berechtigungen
- 🤖 **AI Playground** - AI-Modelle testen und vergleichen
- 📤 **Document Upload** - Dokumente hochladen und verwalten
- 🔄 **Workflow System** - 4-Status Workflow (Draft → Reviewed → Approved/Rejected)
- 📦 **Archiv-System** - Gelöschte Dokumente verwalten, wiederherstellen oder endgültig löschen
- 💬 **RAG Chat** - Intelligente Fragen zu Dokumenten stellen
- 🔍 **Vector Search** - Semantische Suche in Dokumenten
- 🎯 **Prompt Management** - AI-Prompts verwalten und versionieren

---

## 🆕 Neue Features in v2.5.0

### **✂️ Chunk-Editor (NEU)**
- **Chunk-Vorschau:** Alle Chunks eines Dokuments anzeigen (Level 1+)
- **Chunk bearbeiten:** Text direkt im Chunk ändern (Level 4+)
- **Chunk splitten:** Lange Chunks in zwei Teile aufteilen
  - ⭐ **Overlap-Funktion:** 0-10 Overlap-Sätze zwischen gesplitteten Chunks für bessere Kontext-Erhaltung
  - ⭐ **Intelligente Satz-Erkennung:** Automatische Satz-Trennung für Overlap
- **Chunks zusammenführen:** Zwei benachbarte Chunks zu einem zusammenführen
- **Chunk löschen:** Chunk aus Datenbank und Vector Store entfernen
- **Seitenweise AI-Verarbeitung:** Einzelne Seiten können neu mit AI verarbeitet werden
- **Re-Indexierung:** Dokumente können nach AI-Verarbeitung vollständig neu indexiert werden
- **Strukturiertes Chunking:** JSON wird in lesbaren Text konvertiert (Fachartikel)
- **Diagramm-Beschreibung:** Figuren und Tabellen werden in Chunks integriert

## 🆕 Neue Features in v2.2.0

### **📦 Archiv-System (NEU)**
- **Soft Delete:** Audit-taugliche Löschung mit Grund und Zeitstempel
- **Archiv-Ansicht:** Gelöschte Dokumente für Level 4+ (QM-Mitarbeiter) und QMS Admins
- **Wiederherstellung:** Dokumente aus Archiv wiederherstellen (mit Status-Option: Draft/Reviewed/Approved)
- **Hard Delete:** Endgültige Löschung nach Retention-Periode (nur Level 5 - QMS Admin)
- **RAG Cleanup:** Automatisches Entfernen aus Vector-DB bei Soft Delete
- **Filterung & Suche:** Nach Dokumenttyp, Löschdatum, QM-Kapitel filtern
- **RBAC-geschützt:** Nur Level 4+ (QM-Mitarbeiter) und QMS Admins können Archiv einsehen

### **🔐 RBAC Multi-Level System**
- **5-Stufen-Berechtigungssystem:** Level 1 (Mitarbeiter) bis Level 5 (QMS Admin)
- **Context-Specific Permissions:** Dokument-Aktionen basierend auf Interest Group-Level
- **Interest Group Filtering:** Level 1-3 sehen nur relevante Dokumente
- **Multi-Level Support:** User mit unterschiedlichen Levels pro Interest Group
- **Document Type Filtering:** Level 2-3 sehen nur Document Types mit Dokumenten in eigenen IGs

### **Neue Features in v2.1.0**

### **💬 RAG Chat System**
- **Intelligente Fragen:** Stellen Sie Fragen zu Ihren freigegebenen Dokumenten
- **Vector Search:** Semantische Suche mit Qdrant Vector Store
- **Multi-Model AI:** GPT-4o Mini, GPT-5 Mini, Gemini 2.5 Flash
- **Source Attribution:** Präzise Quellenangaben mit Relevanz-Scores
- **Session Management:** Persistente Chat-Sessions
- **Structured Data:** Automatische Erkennung von Tabellen, Listen, Sicherheitshinweisen

### **🔍 Erweiterte Suche**
- **Hybrid Search:** Kombination aus Vector Search und Text-Suche
- **Filter Panel:** Nach Dokumenttyp, Interest Groups, Zeitraum filtern
- **Source Preview Modal:** Vollbild-Preview mit Zoom-Funktionen
- **Suggested Questions:** Automatische Vorschläge für Follow-up-Fragen

### **📊 Dokumenttyp-spezifische Chunking**
- **SOP-Dokumente:** Strukturierte Extraktion von Prozess-Schritten
- **Arbeitsanweisungen:** Sicherheitshinweise und Compliance-Anforderungen
- **Flussdiagramme:** Knoten und Verbindungen
- **Formulare:** Felder und Validierungsregeln
- **Prozess-Dokumente:** Workflow-Schritte und Verantwortlichkeiten

### **🎯 RAG Integration im Workflow**
- **Automatische Indexierung:** Dokumente werden bei Status "Approved" indexiert
- **Real-time Updates:** Sofortige Verfügbarkeit im RAG nach Freigabe
- **Workflow-Unterstützung:** Fragen zu Dokumenten während der Prüfung
- **Compliance-Check:** Sicherheits- und Qualitätsanforderungen prüfen

## 🔐 Anmeldung & Berechtigungen

### RBAC Multi-Level System

DocuMind-AI V2 verwendet ein **5-Stufen-Berechtigungssystem** mit Interest Group-spezifischen Berechtigungen:

- **Level 5 (QMS Admin):** Vollzugriff auf alle Funktionen
- **Level 4 (QM-Mitarbeiter):** Dokument Upload, Workflow, RAG Chat (alle Dokumente)
- **Level 3 (Abteilungsleiter):** Workflow (nur eigene Interest Groups), Kanban Board
- **Level 2 (Teamleiter):** Dokumenten-Tabelle (nur eigene Interest Groups), Kommentieren
- **Level 1 (Mitarbeiter):** RAG Chat (nur eigene Interest Groups)

### Standard-Benutzer (RBAC Multi-Level)

| Benutzer | E-Mail | Passwort | Level | Berechtigung |
|----------|--------|----------|-------|--------------|
| **QMS Admin** | `qms.admin@company.com` | `123` | L5 | Vollzugriff + AI Playground + RAG Chat |
| **QM Mitarbeiter** | `qm.mitarbeiter@company.com` | `123` | L4 | Dokument Upload, Workflow, RAG Chat |
| **Abteilungsleiter** | `abteilungsleiter.*@company.com` | `123` | L3 | Workflow (nur eigene Interest Groups) |
| **Teamleiter** | `teamleiter.*@company.com` | `123` | L2 | Dokumenten-Tabelle (nur eigene Interest Groups) |
| **Mitarbeiter** | `mitarbeiter.*@company.com` | `123` | L1 | RAG Chat (nur eigene Interest Groups) |

> **Hinweis:** Alle Test-User-Passwörter sind auf `123` gesetzt. Siehe `docs/RBAC_TEST_USERS.md` für Details.

### Anmelden

1. Öffnen Sie http://localhost:3000
2. Klicken Sie auf "Login"
3. Geben Sie E-Mail und Passwort ein
4. Klicken Sie auf "Anmelden"

---

## 🏢 Interest Groups Management

### Interest Groups anzeigen

1. Navigieren Sie zu **Interest Groups**
2. Sehen Sie alle verfügbaren Stakeholder-Gruppen
3. Verwenden Sie die Suchfunktion zum Filtern

### Neue Interest Group erstellen

1. Klicken Sie auf **"Neue Interest Group"**
2. Füllen Sie die Felder aus:
   - **Name:** Vollständiger Name der Gruppe
   - **Code:** Kurzer Code (z.B. "PROD")
   - **Beschreibung:** Detaillierte Beschreibung
3. Klicken Sie auf **"Erstellen"**

### Interest Group bearbeiten

1. Klicken Sie auf die **Bearbeiten**-Schaltfläche bei der gewünschten Gruppe
2. Ändern Sie die gewünschten Felder
3. Klicken Sie auf **"Speichern"**

---

## 👥 User Management

### Benutzer anzeigen

1. Navigieren Sie zu **Users**
2. Sehen Sie alle Benutzer mit ihren Rollen
3. Verwenden Sie die Suchfunktion zum Filtern

### Neuen Benutzer erstellen

1. Klicken Sie auf **"Neuen Benutzer"**
2. Füllen Sie die Felder aus:
   - **E-Mail:** Gültige E-Mail-Adresse
   - **Passwort:** Sicheres Passwort
   - **Rolle:** Wählen Sie die entsprechende Rolle
   - **Abteilungen:** Wählen Sie zugehörige Abteilungen
3. Klicken Sie auf **"Erstellen"**

### Benutzer zu Interest Groups zuweisen

1. Öffnen Sie den Benutzer-Details
2. Klicken Sie auf **"Interest Groups zuweisen"**
3. Wählen Sie die gewünschten Gruppen aus
4. Klicken Sie auf **"Speichern"**

---

## 🤖 AI Playground

> **Hinweis:** Nur für QMS Admin verfügbar

### AI-Modell testen

1. Navigieren Sie zu **Models**
2. Wählen Sie ein AI-Modell aus:
   - **GPT-4o Mini** (OpenAI)
   - **GPT-5 Mini** (OpenAI)
   - **Gemini 2.5 Flash** (Google AI)
3. Geben Sie Ihren Prompt ein
4. Klicken Sie auf **"Testen"**

### Modelle vergleichen

1. Wählen Sie **"Modelle vergleichen"**
2. Wählen Sie 2-3 Modelle aus
3. Geben Sie den Test-Prompt ein
4. Klicken Sie auf **"Vergleichen"**
5. Sehen Sie die Ergebnisse in der Vergleichstabelle

### Modelle bewerten

1. Nach einem Vergleich können Sie die Modelle bewerten
2. Klicken Sie auf **"Evaluate First Model"** oder **"Evaluate Second Model"**
3. Das System bewertet das Modell nach 10 Kriterien
4. Sehen Sie die detaillierte Bewertung mit Stärken und Schwächen

### Bilder hochladen

1. Klicken Sie auf **"Bild hochladen"**
2. Ziehen Sie ein Bild in den Upload-Bereich oder klicken Sie zum Auswählen
3. Das Bild wird automatisch verarbeitet
4. Geben Sie Ihren Prompt ein und testen Sie das Modell

---

## 📤 Document Upload

### Dokument hochladen

1. Navigieren Sie zu **Document Upload**
2. Ziehen Sie ein Dokument in den Upload-Bereich oder klicken Sie zum Auswählen
3. **Unterstützte Formate:** PDF, DOCX, PNG, JPG (max. 50MB)
4. Füllen Sie die Metadaten aus:
   - **Document Type:** Wählen Sie den Dokumenttyp
   - **QM Chapter:** QM-Kapitel
   - **Version:** Dokumentversion
   - **Interest Groups:** Wählen Sie relevante Gruppen
5. Klicken Sie auf **"Upload starten"**

### Upload-Status verfolgen

- **10%** - Datei wird hochgeladen
- **30%** - Dokument wird verarbeitet
- **50%** - Seiten werden aufgeteilt
- **70%** - Previews werden generiert
- **100%** - Upload abgeschlossen

---

## 🔄 Workflow System

### Dokument-Status verwalten

1. Navigieren Sie zu **Documents**
2. Sehen Sie das **Kanban Board** mit 4 Spalten:
   - **Draft** - Entwurf
   - **Reviewed** - Geprüft
   - **Approved** - Freigegeben
   - **Rejected** - Zurückgewiesen

### Status ändern

1. **Drag & Drop:** Ziehen Sie Dokumente zwischen Spalten
2. **Status-Button:** Klicken Sie auf den Status-Button
3. **Kommentar hinzufügen:** Geben Sie einen Grund für die Änderung ein
4. Klicken Sie auf **"Status ändern"**

### Dokument-Details anzeigen

1. Klicken Sie auf ein Dokument
2. Sehen Sie:
   - **Preview:** Seitenvorschau
   - **Metadaten:** Dokumentinformationen
   - **Interest Groups:** Zugewiesene Gruppen
   - **Audit Trail:** Komplette Historie
   - **AI Processing:** Verarbeitungsergebnisse

### Dokument verarbeiten

1. Öffnen Sie ein Dokument
2. Navigieren Sie zu einer Seite
3. Klicken Sie auf **"Mit AI Verarbeiten"**
4. Das System verarbeitet die Seite mit dem Standard-Prompt
5. Sehen Sie die Ergebnisse in der AI-Analyse-Sektion

---

## 💬 RAG Chat System

### RAG Chat öffnen

1. Navigieren Sie zur **Hauptseite** (Dashboard)
2. Der **RAG Chat** ist zentral platziert (60% der Ansicht)
3. Beginnen Sie mit einer Frage zu Ihren Dokumenten

### Chat-Session verwalten

1. **Session Sidebar** (links, 20% der Ansicht):
   - Sehen Sie alle Ihre Chat-Sessions
   - Erstellen Sie neue Sessions
   - Wechseln Sie zwischen Sessions
   - Löschen Sie alte Sessions

### Fragen stellen

1. Geben Sie Ihre Frage in das Eingabefeld ein
2. Wählen Sie das AI-Modell:
   - **GPT-4o Mini** (schnell, kostengünstig)
   - **GPT-5 Mini** (hochwertig, teurer)
   - **Gemini 2.5 Flash** (ausgewogen)
3. Klicken Sie auf **"Senden"** oder drücken Sie Enter

### Antworten verstehen

Die Antworten enthalten:

- **Hauptantwort:** Direkte Antwort auf Ihre Frage
- **Quellen:** Links zu den relevanten Dokumenten
- **Relevanz-Score:** Wie relevant ist die Quelle (0-100%)
- **Strukturierte Daten:** Tabellen, Listen, Sicherheitshinweise
- **Preview-Links:** Direkte Links zu Dokument-Seiten

### Quellen erkunden

1. Klicken Sie auf **"Preview"** bei einer Quelle
2. Das **Source Preview Modal** öffnet sich:
   - **Vollbild-Preview** des Dokuments
   - **Zoom-Funktionen** (50% - 300%)
   - **Text-Auszug** des relevanten Chunks
   - **Relevanz-Informationen**
   - **Aktionen:** Dokument öffnen, Download, Im Chat fragen

### Erweiterte Suche

1. **Filter Panel** (rechts, 20% der Ansicht):
   - **Quick Search:** Schnelle Textsuche
   - **Document Type Filter:** Nach Dokumenttyp filtern
   - **Date Range Filter:** Nach Datum filtern
   - **Advanced Filters:** Erweiterte Suchoptionen

### Suggested Questions

Das System schlägt automatisch Fragen vor:
- "Welche Sicherheitshinweise gibt es für die Montage?"
- "Welche Teile werden für die Installation benötigt?"
- "Wie lautet die Artikelnummer für das Hauptteil?"
- "Welche Schritte sind bei der Wartung zu beachten?"

---

## 🎯 Prompt Management

### Prompt-Templates anzeigen

1. Navigieren Sie zu **Prompt Management**
2. **Split-View Layout:**
   - **Links:** Dokumenttypen-Grid
   - **Rechts:** Gestapelte Prompt-Karten

### Neues Prompt-Template erstellen

1. Klicken Sie auf **"Neues Template"**
2. Füllen Sie die Felder aus:
   - **Name:** Template-Name
   - **Beschreibung:** Detaillierte Beschreibung
   - **Document Type:** Zugehöriger Dokumenttyp
   - **AI Model:** Verwendetes Modell
   - **Prompt Text:** Der eigentliche Prompt
   - **System Instructions:** System-Anweisungen
   - **Example Output:** Beispiel-Ausgabe
3. Klicken Sie auf **"Erstellen"**

### Standard-Prompt zuweisen

1. **Drag & Drop:** Ziehen Sie ein Prompt-Template auf einen Dokumenttyp
2. Das Template wird als Standard gesetzt
3. **Visueller Hinweis:** Grüner Gradient und "AKTIV" Badge

### Prompt aus AI Playground speichern

1. Testen Sie einen Prompt im AI Playground
2. Klicken Sie auf **"💾 Als Template speichern"**
3. Wählen Sie den Dokumenttyp aus
4. Das Template wird automatisch erstellt

### Prompt bearbeiten

1. Klicken Sie auf **"Bearbeiten"** bei einem Template
2. Das AI Playground öffnet sich mit vorausgefüllten Daten
3. Bearbeiten Sie den Prompt
4. Speichern Sie das Template

---

## 🔍 Tipps und Tricks

### Effektive RAG-Chat-Nutzung

1. **Spezifische Fragen:** Stellen Sie konkrete Fragen statt allgemeine
2. **Kontext nutzen:** Referenzieren Sie vorherige Antworten
3. **Quellen prüfen:** Klicken Sie auf Preview-Links für Details
4. **Sessions nutzen:** Organisieren Sie verwandte Fragen in Sessions

### Dokument-Workflow optimieren

1. **Metadaten vollständig:** Füllen Sie alle Felder beim Upload aus
2. **Interest Groups:** Weisen Sie relevante Gruppen zu
3. **AI Processing:** Verarbeiten Sie Seiten für bessere RAG-Ergebnisse
4. **Status-Management:** Nutzen Sie Kommentare für Audit-Trail

### AI Playground effektiv nutzen

1. **Modelle vergleichen:** Testen Sie verschiedene Modelle
2. **Evaluation nutzen:** Bewerten Sie Modell-Performance
3. **Prompts speichern:** Speichern Sie erfolgreiche Prompts als Templates
4. **Bilder testen:** Nutzen Sie Vision-Funktionen für Dokumente

---

## 📚 Detaillierte Anleitungen

### **Spezifische Handbücher**
- **[Document Upload](01-upload.md)** - Dokumente hochladen und verwalten
- **[Workflow System](02-workflow.md)** - 4-Status Workflow mit RAG Integration
- **[Archiv-System](04-archive.md)** - Gelöschte Dokumente verwalten, wiederherstellen oder endgültig löschen
- **[RAG Chat System](03-rag-chat.md)** - Intelligente Fragen zu Dokumenten stellen

### **Schnellstart**
1. **Anmelden:** Verwenden Sie `qms.admin@company.com` / `Admin432!`
2. **Dokument hochladen:** Siehe [Document Upload](01-upload.md)
3. **Workflow durchlaufen:** Siehe [Workflow System](02-workflow.md)
4. **RAG Chat nutzen:** Siehe [RAG Chat System](03-rag-chat.md)

### Q: Wie kann ich ein Dokument für RAG-Chat verfügbar machen?
A: Das Dokument muss den Status "Approved" haben. Dann können Sie es über das RAG Indexierung Panel in der Dokument-Detail-Ansicht indexieren.

### Q: Welche AI-Modelle stehen zur Verfügung?
A: GPT-4o Mini, GPT-5 Mini (OpenAI) und Gemini 2.5 Flash (Google AI). Die Verfügbarkeit hängt von Ihren API-Keys ab.

### Q: Wie funktioniert die Berechtigung für RAG-Chat?
A: Level 1 (Mitarbeiter) sehen nur Dokumente ihrer Interest Groups. Level 2-3 sehen nur Dokumente ihrer Interest Groups. Level 4-5 sehen alle freigegebenen Dokumente.

### Q: Was ist RBAC Multi-Level?
A: Ein User kann unterschiedliche Approval Levels für verschiedene Interest Groups haben. Beispiel: Level 3 für "Produktion" und Level 2 für "Service". Das System prüft für jede Aktion das entsprechende IG-Level.

### Q: Kann ich alte Chat-Sessions wiederherstellen?
A: Ja, alle Chat-Sessions werden persistent gespeichert. Sie können zwischen Sessions wechseln und die Historie einsehen.

### Q: Wie werden Dokumente für die Suche aufbereitet?
A: Das System nutzt eine intelligente Chunking-Strategie: Vision-AI-basiert → Page-Boundary-aware → Plain-Text Fallback.

---

## 🆘 Support

### Technische Probleme

1. **Browser-Konsole prüfen:** F12 → Console für Fehlermeldungen
2. **Datenbank zurücksetzen:** `docker-compose down -v && docker-compose up -d`
3. **Logs anzeigen:** `docker-compose logs -f`

### Kontakt

- **E-Mail:** support@documind.ai
- **Dokumentation:** Siehe `docs/` Verzeichnis
- **Architektur:** Siehe `docs/architecture.md`

---

**Last Updated:** 2025-11-11  
**Version:** 2.5.0  
**Status:** ✅ **PRODUCTION READY**