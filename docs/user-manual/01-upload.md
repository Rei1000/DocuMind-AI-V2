# 📤 Dokument hochladen

> **Für:** QM-Mitarbeiter (Level 4)  
> **Dauer:** ~5 Minuten  
> **Voraussetzungen:** Anmeldung als QM-Mitarbeiter

---

## 🎯 Übersicht

Als QM-Mitarbeiter können Sie QMS-Dokumente (SOPs, Arbeitsanweisungen, Formulare, etc.) hochladen und für verschiedene Abteilungen freigeben.

---

## 📋 Schritt-für-Schritt Anleitung

### **Schritt 1: Upload-Seite öffnen**

1. Melden Sie sich an: `http://localhost:3000/login`
2. Klicken Sie in der Navigation auf **"Dokument hochladen"**
3. Sie gelangen zur Upload-Seite: `/document-upload`

---

### **Schritt 2: Datei auswählen (Drag & Drop)**

1. **Ziehen Sie eine Datei** in die Drag & Drop Zone
   - **Unterstützte Formate:** PDF, DOCX, PNG, JPG
   - **Maximale Größe:** 50 MB
   - **Mehrseitige Dokumente:** Werden automatisch gesplittet

2. **Alternative:** Klicken Sie auf die Zone und wählen Sie eine Datei

3. **Validierung:**
   - ✅ Grüner Haken: Datei akzeptiert
   - ❌ Rotes Kreuz: Datei abgelehnt (falsches Format oder zu groß)

---

### **Schritt 3: Dokumenttyp zuweisen (Drag & Drop)**

1. **Dokumenttyp-Karten** werden angezeigt:
   - SOP (Standard Operating Procedure)
   - Arbeitsanweisung
   - Formular
   - Flussdiagramm
   - Checkliste
   - Prüfprotokoll
   - Schulungsunterlage

2. **Ziehen Sie eine Karte** in die "Drop Zone"
   - Der Dokumenttyp wird automatisch zugewiesen
   - Die Processing-Methode (OCR oder Vision) wird aus dem Dokumenttyp übernommen

3. **Wichtig:** Der Dokumenttyp bestimmt, welcher AI-Prompt zur Verarbeitung verwendet wird!

---

### **Schritt 4: Metadaten eingeben**

1. **Dokumentname:**
   - Geben Sie einen aussagekräftigen Namen ein
   - Beispiel: "Montage Antriebseinheit SB3"

2. **QM-Kapitel:**
   - Wählen Sie das zugehörige QM-Kapitel aus dem Dropdown
   - Beispiel: "5.2 Arbeitsanweisungen"

3. **Version:**
   - Geben Sie die Versionsnummer ein
   - Format: `vX.Y.Z` (z.B. `v1.0.0`)
   - Das System schlägt automatisch die nächste Version vor

4. **Klicken Sie auf "Weiter"**

---

### **Schritt 5: Interest Groups zuweisen (Drag & Drop)**

1. **QM Interest Group wird automatisch zugewiesen:**
   - ✅ QM (Qualitätsmanagement) ist bereits im "Zugewiesene Gruppen" Bereich
   - ⚠️ **Wichtig:** QM ist erforderlich und kann nicht entfernt werden
   - Jedes Dokument muss QM zugewiesen haben

2. **Weitere Interest Groups hinzufügen:**
   - **Interest Group Karten** werden links angezeigt:
     - Produktion PR
     - Service SV
     - Einkauf EK
     - Vertrieb VT
     - etc.
   - **Ziehen Sie Karten von links** in die "Zugewiesene Gruppen" Zone
   - Mehrfachauswahl möglich
   - Nur zugewiesene Gruppen können das Dokument später sehen

3. **Entfernen:** 
   - Klicken Sie auf das **[×]** neben einer Gruppe
   - ⚠️ **Hinweis:** QM kann nicht entfernt werden (Schaltfläche nicht sichtbar)

4. **Klicken Sie auf "Weiter"**

---

### **Schritt 6: Vorschau & Upload**

1. **Seiten-Vorschau:**
   - Das System zeigt Thumbnails aller Seiten
   - Klicken Sie auf eine Seite für Vollansicht

2. **Verarbeitungs-Info:**
   - ✅ Seiten gesplittet (z.B. "3 Seiten erkannt")
   - ✅ Vorschaubilder generiert
   - ⏳ OCR/Vision wird beim Upload gestartet

3. **Upload starten:**
   - Klicken Sie auf **"🚀 Upload starten"**
   - Progress Bar zeigt Fortschritt
   - Nach Abschluss: Weiterleitung zur Dokumenten-Verwaltung

---

## ✅ Nach dem Upload

### **Was passiert jetzt?**

1. **Dokument ist hochgeladen** (Status: "Uploaded")
2. **OCR/Vision Processing** läuft im Hintergrund
3. **Workflow-Entry** wird erstellt
4. **Benachrichtigung** an zugewiesene Abteilungsleiter

### **Nächste Schritte:**

- **Abteilungsleiter (Level 3)** prüft das Dokument
- **Sie (Level 4)** geben das Dokument frei
- **Freigegebenes Dokument** kommt ins RAG-System

---

## ❓ Häufige Fragen

### **Q: Kann ich mehrere Dateien gleichzeitig hochladen?**
A: Aktuell nur eine Datei pro Upload. Batch-Upload kommt in Phase 5.

### **Q: Was passiert, wenn die Datei zu groß ist?**
A: Sie erhalten eine Fehlermeldung. Maximale Größe: 50 MB.

### **Q: Kann ich ein Dokument nach dem Upload ändern?**
A: Nein, aber Sie können eine neue Version hochladen (Version Management kommt in Phase 5).

### **Q: Wie lange dauert die OCR/Vision-Verarbeitung?**
A: Je nach Dokumentgröße: 30 Sekunden bis 5 Minuten.

### **Q: Kann ich den Upload abbrechen?**
A: Ja, klicken Sie auf "Abbrechen" während des Uploads.

---

## 🔗 Weiterführende Links

- **[Dokumente freigeben](02-workflow.md)** - Wie gebe ich geprüfte Dokumente frei?
- **[RAG Chat nutzen](03-rag-chat.md)** - Wie stelle ich Fragen zu Dokumenten?

---

**Zurück zur [Übersicht](README.md)**

