# 📦 Archiv-System

> **User Manual:** Gelöschte Dokumente - Read-Only Historie  
> **Version:** 2.9.4  
> **Letzte Aktualisierung:** 2025-12-28

---

## 🎯 Übersicht

Das Archiv-System dient als **Read-Only Historie** für gelöschte Dokumente. Archivierte Dokumente können nur angezeigt, **nicht wiederhergestellt** werden.

### **Archiv-Features**

- 📋 **Read-Only Ansicht:** Alle gelöschten Dokumente (Soft Delete) zur Einsicht
- 🔍 **Filterung & Suche:** Nach Dokumenttyp, QM-Kapitel, Dateiname
- 🗑️ **Hard Delete:** Endgültige Löschung (nur Level 5 - für Tests/Cleanup)
- 📊 **Audit-Trail:** Vollständige Historie mit Löschgrund, Zeitstempel, Gelöscht-Von

### **Philosophie: "Gelöscht bleibt gelöscht"**

- ✅ **Einfach:** Keine komplexe Wiederherstellungs-Logik
- ✅ **Klar:** Archiv = Historie, keine aktive Verwaltung
- ✅ **Sauber:** Verhindert Inkonsistenzen mit RAG und Duplikaten
- ✅ **Audit-konform:** Vollständige Historie für Compliance

> **💡 Tipp:** Wenn Sie ein Dokument erneut benötigen, laden Sie es einfach neu hoch. Das ist einfacher und sauberer als Wiederherstellung.

---

## 👥 Berechtigungen (RBAC Multi-Level)

### **User-Level Matrix**

| Level | Rolle | Archiv sehen | Ansehen | Hard Delete |
|-------|-------|--------------|---------|-------------|
| **1** | Mitarbeiter | ❌ Kein Zugriff | ❌ | ❌ |
| **2** | Teamleiter | ❌ Kein Zugriff | ❌ | ❌ |
| **3** | Abteilungsleiter | ❌ Kein Zugriff | ❌ | ❌ |
| **4** | QM-Manager | ✅ Alle gelöschten Dokumente | ✅ Read-Only | ❌ |
| **5** | QMS Admin | ✅ Alle gelöschten Dokumente | ✅ Read-Only | ✅ Hard Delete |

---

## 📋 Schritt-für-Schritt Anleitung

### **Schritt 1: Archiv-Seite öffnen**

1. Melden Sie sich an: `http://localhost:3000/login`
2. Klicken Sie in der Navigation auf **"Archiv"** 📦
3. Sie gelangen zur Archiv-Seite: `/documents/archive`

> **Hinweis:** Nur Level 4+ (QM-Mitarbeiter) und QMS Admins können die Archiv-Seite sehen.

---

### **Schritt 2: Archivierte Dokumente anzeigen**

Die Archiv-Seite zeigt alle gelöschten Dokumente (Soft Delete) mit folgenden Informationen:

| Spalte | Beschreibung |
|--------|--------------|
| **Dokument** | Original-Filename + Dateigröße + Typ |
| **Typ** | Dokumenttyp (z.B. Arbeitsanweisung) |
| **QM-Kapitel** | QM-Kapitel (z.B. 7.3) |
| **Version** | Version (z.B. v1.0) |
| **Status** | Workflow-Status beim Löschen |
| **Gelöscht am** | Datum und Uhrzeit der Löschung |
| **Aktionen** | Ansehen (Read-Only) + Hard Delete (Level 5) |

---

### **Schritt 3: Dokumente filtern**

1. **Suche:**
   - Geben Sie einen Suchbegriff ein (Dokumentenname, Typ oder QM-Kapitel)
   - Die Liste wird in Echtzeit gefiltert

2. **Sortierung:**
   - Standardmäßig nach Löschdatum absteigend sortiert
   - Neueste Löschungen oben

---

### **Schritt 4: Archiviertes Dokument ansehen (Read-Only)**

1. Klicken Sie auf **"Ansehen"** (👁️ Icon) bei einem Dokument
2. Sie gelangen zur Dokumenten-Detail-Seite
3. **Read-Only Modus:**
   - Alle Metadaten sichtbar
   - Preview-Bilder verfügbar
   - Workflow-Historie einsehbar
   - **Keine Bearbeitung möglich** (nur ansehen)

---

### **Schritt 5: Dokument endgültig löschen (Hard Delete)**

> **⚠️ NUR FÜR LEVEL 5 (QMS ADMIN)!**

**Use Case:** Test-Cleanup, fehlerhafte Uploads entfernen

1. Klicken Sie auf **"Endgültig löschen"** (🗑️ Icon)
2. **Sicherheitsabfrage erscheint:**
   - Dokumentname wird angezeigt
   - Geben Sie zur Bestätigung **"LÖSCHEN"** ein
3. Klicken Sie auf **"Bestätigen"**
4. Das Dokument wird **permanent** gelöscht:
   - ✅ Physische Dateien werden entfernt
   - ✅ Preview-Bilder werden gelöscht
   - ✅ Alle Metadaten werden entfernt
   - ✅ Archiv-Eintrag wird gelöscht
   - ✅ RAG-Vektoren sind bereits bei Soft Delete entfernt

> **⚠️ WARNUNG:** Hard Delete ist **irreversibel**! Es gibt keine Wiederherstellung.

---

## 🔄 Workflow: Soft Delete → Archiv

### **1. Dokument löschen (Soft Delete)**

1. Gehen Sie zur Dokumenten-Liste oder Detail-Seite
2. Klicken Sie auf **"Löschen"**
3. **Löschgrund-Dialog erscheint:**
   - Geben Sie einen **Löschgrund** ein (z.B. "Veraltete Version", "Duplikat", "Fehlerhafte Datei")
   - Klicken Sie auf **"Bestätigen"**
4. Das Dokument wird **soft-deleted:**
   - ✅ `deleted_at` wird gesetzt
   - ✅ `deleted_by_user_id` wird gesetzt
   - ✅ `deletion_reason` wird gesetzt
   - ✅ **RAG-Cleanup:** Automatisches Entfernen aus Vector-DB (wenn indexiert)
   - ✅ Dokument verschwindet aus aktiver Liste
   - ✅ Dokument erscheint im Archiv

### **2. Dokument im Archiv einsehen**

1. Öffnen Sie die Archiv-Seite: `/documents/archive`
2. Verwenden Sie Filter oder Suche, um das Dokument zu finden
3. Klicken Sie auf **"Ansehen"** für Details:
   - Löschgrund einsehen
   - Gelöscht von: User-Name
   - Gelöscht am: Datum + Uhrzeit
   - Workflow-Status beim Löschen
   - Alle Metadaten (Read-Only)

### **3. Dokument erneut benötigt?**

**Empfohlener Workflow:**
1. Original-Datei erneut hochladen
2. Metadaten neu eingeben (falls nötig)
3. Workflow-Prozess durchlaufen (Draft → Reviewed → Approved)
4. In RAG indexieren

> **Hinweis:** Dieser Workflow ist **einfacher und sauberer** als Wiederherstellung, da er:
> - ✅ Keine Inkonsistenzen mit RAG verursacht
> - ✅ Klare Audit-Historie bewahrt
> - ✅ Duplikat-Erkennung korrekt funktioniert

---

## 🔍 Tipps und Tricks

### **Effektive Archiv-Nutzung**

1. **Aussagekräftige Löschgründe:** 
   - ✅ "Veraltete Version - ersetzt durch v2.0"
   - ✅ "Duplikat von PA 7.3 (ID: 42)"
   - ✅ "Fehlerhafte Datei - falscher Inhalt"
   - ❌ "Test", "Löschen", "Falsch"

2. **Archiv als Audit-Log:**
   - Nutzen Sie das Archiv für Compliance-Prüfungen
   - Filter nach Zeitraum: Welche Dokumente wurden im letzten Monat gelöscht?
   - Prüfen Sie Löschgründe für Audit-Zwecke

3. **Hard Delete mit Bedacht:**
   - Nur für Test-Dateien oder fehlerhafte Uploads
   - Nicht für reguläre Dokumente (Soft Delete ist ausreichend)
   - Behalten Sie Archiv für Audit-Historie

---

## 📊 FAQ

### Q: Warum kann ich gelöschte Dokumente nicht wiederherstellen?

A: Das Archiv ist als **Read-Only Historie** konzipiert, um Inkonsistenzen zu vermeiden:
- ✅ **Einfacher Workflow:** Kein komplexes Restore-Handling
- ✅ **Keine RAG-Konflikte:** Re-Indexierung ist nicht nötig
- ✅ **Keine Duplikat-Probleme:** Klare Trennung zwischen gelöscht und aktiv
- ✅ **Audit-konform:** Klare Historie ohne Änderungen

**Lösung:** Laden Sie das Dokument erneut hoch, wenn Sie es benötigen.

---

### Q: Was passiert mit RAG-Vektoren bei Soft Delete?

A: RAG-Vektoren werden **automatisch** aus Qdrant entfernt, wenn ein Dokument soft-deleted wird. Das verhindert veraltete oder doppelte Vektoren in der Vector-DB.

**Prozess:**
1. Dokument wird soft-deleted
2. `DocumentDeletedEvent` wird publiziert
3. RAG Event Handler löscht alle Chunks aus Qdrant
4. Dokument ist nicht mehr durchsuchbar im RAG Chat

---

### Q: Kann ich ein Dokument nach Hard Delete wiederherstellen?

A: **Nein**, Hard Delete ist **irreversibel**. Alle Dateien, Preview-Bilder und Datenbank-Einträge werden permanent entfernt.

---

### Q: Wie lange bleiben Dokumente im Archiv?

A: Dokumente bleiben **permanent** im Archiv, bis sie manuell hard-deleted werden (nur Level 5). Es gibt keine automatische Retention-Periode.

**Empfehlung:** Behalten Sie Archiv für Audit-Zwecke, nutzen Sie Hard Delete nur für Cleanup/Tests.

---

### Q: Wer kann das Archiv sehen?

A: Nur **Level 4+ (QM-Mitarbeiter)** und **QMS Admins (Level 5)** können das Archiv einsehen.

**Begründung:** Archiv-Zugriff erfordert erweiterte Berechtigungen für Audit und Compliance.

---

### Q: Was passiert wenn ich ein gelöschtes Dokument erneut hochlade?

A: Das neu hochgeladene Dokument wird als **eigenständiges Dokument** behandelt:
- ✅ Neue Upload-ID
- ✅ Duplikat-Prüfung erfolgt nur gegen **aktive** Dokumente
- ✅ Archivierte Dokumente werden bei Duplikat-Prüfung **ignoriert**

**Ergebnis:** Kein Duplikat, neuer Workflow-Prozess.

---

## 🚨 Wichtige Hinweise

- **Archiv = Read-Only:** Keine Wiederherstellung möglich
- **Soft Delete ≠ Hard Delete:** Soft Delete = Archiv, Hard Delete = Permanent
- **RAG Cleanup:** Automatisch bei Soft Delete
- **Audit-Trail:** Vollständige Dokumentation aller Löschungen
- **Hard Delete:** Nur für Tests/Cleanup (Level 5), nicht für reguläre Dokumente

---

**Weiterführende Dokumentation:**
- [Workflow System](02-workflow.md) - Dokument-Workflow
- [Document Upload](01-upload.md) - Dokumente hochladen
- [RAG Chat System](03-rag-chat.md) - RAG Chat verwenden
