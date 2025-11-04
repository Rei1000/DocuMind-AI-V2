# 📦 Archiv-System

> **User Manual:** Gelöschte Dokumente verwalten  
> **Version:** 2.2.0  
> **Letzte Aktualisierung:** 2025-11-04

---

## 🎯 Übersicht

Das Archiv-System ermöglicht es QM-Mitarbeitern (Level 4+) und QMS Admins, gelöschte Dokumente zu verwalten, wiederherzustellen oder endgültig zu löschen.

### **Archiv-Features**

- 📋 **Archiv-Ansicht:** Alle gelöschten Dokumente (Soft Delete)
- 🔄 **Wiederherstellung:** Dokumente aus Archiv wiederherstellen
- 🗑️ **Hard Delete:** Endgültige Löschung nach Retention-Periode (nur Level 5)
- 🔍 **Filterung & Suche:** Nach Dokumenttyp, Löschdatum, QM-Kapitel
- 📊 **Audit-Trail:** Vollständige Historie mit Löschgrund und Zeitstempel

---

## 👥 Berechtigungen (RBAC Multi-Level)

### **User-Level Matrix**

| Level | Rolle | Archiv sehen | Wiederherstellen | Hard Delete |
|-------|-------|--------------|------------------|-------------|
| **1** | Mitarbeiter | ❌ Kein Zugriff | ❌ Kein Zugriff | ❌ Kein Zugriff |
| **2** | Teamleiter | ❌ Kein Zugriff | ❌ Kein Zugriff | ❌ Kein Zugriff |
| **3** | Abteilungsleiter | ❌ Kein Zugriff | ❌ Kein Zugriff | ❌ Kein Zugriff |
| **4** | QM-Manager | ✅ Alle gelöschten Dokumente | ✅ Wiederherstellen | ❌ Kein Zugriff |
| **5** | QMS Admin | ✅ Alle gelöschten Dokumente | ✅ Wiederherstellen | ✅ Hard Delete |

---

## 📋 Schritt-für-Schritt Anleitung

### **Schritt 1: Archiv-Seite öffnen**

1. Melden Sie sich an: `http://localhost:3000/login`
2. Klicken Sie in der Navigation auf **"Archiv"**
3. Sie gelangen zur Archiv-Seite: `/documents/archive`

> **Hinweis:** Nur Level 4+ (QM-Mitarbeiter) und QMS Admins können die Archiv-Seite sehen.

---

### **Schritt 2: Archivierte Dokumente anzeigen**

Die Archiv-Seite zeigt alle gelöschten Dokumente (Soft Delete) mit folgenden Informationen:

- **Dokumentname** (Original-Filename)
- **Dokumenttyp**
- **QM-Kapitel**
- **Löschdatum** (deleted_at)
- **Gelöscht von** (User ID)
- **Löschgrund** (deletion_reason)
- **Workflow-Status** (zum Zeitpunkt der Löschung)

---

### **Schritt 3: Dokumente filtern**

1. **Nach Dokumenttyp filtern:**
   - Wählen Sie einen Dokumenttyp aus dem Dropdown
   - Nur Dokumente dieses Typs werden angezeigt

2. **Suche:**
   - Geben Sie einen Suchbegriff ein (Dokumentenname, Typ oder QM-Kapitel)
   - Die Liste wird in Echtzeit gefiltert

3. **Nach Löschdatum filtern:**
   - **deleted_before:** Dokumente gelöscht vor diesem Datum
   - **deleted_after:** Dokumente gelöscht nach diesem Datum

---

### **Schritt 4: Dokument wiederherstellen**

1. Klicken Sie auf **"Wiederherstellen"** bei einem Dokument
2. Wählen Sie den gewünschten Status für die Wiederherstellung:
   - **Draft** (Standard)
   - **Reviewed**
   - **Approved**
3. Klicken Sie auf **"Bestätigen"**
4. Das Dokument wird wiederhergestellt und erscheint wieder in der Dokumenten-Liste

> **Hinweis:** Wenn ein Dokument als "Approved" wiederhergestellt wird, kann es optional automatisch in RAG re-indexiert werden (falls implementiert).

---

### **Schritt 5: Dokument endgültig löschen (Hard Delete)**

> **⚠️ WICHTIG:** Nur Level 5 (QMS Admin) können Hard Delete durchführen!

1. Klicken Sie auf **"Endgültig löschen"** bei einem Dokument
2. Geben Sie zur Bestätigung **"LÖSCHEN"** ein
3. Klicken Sie auf **"Bestätigen"**
4. Das Dokument wird **permanent** gelöscht:
   - Physische Dateien werden entfernt
   - Preview-Bilder werden gelöscht
   - Datenbank-Eintrag wird gelöscht
   - RAG-Vektoren sind bereits bei Soft Delete entfernt worden

> **⚠️ WARNUNG:** Hard Delete ist **irreversibel**! Stellen Sie sicher, dass Sie das Dokument wirklich nicht mehr benötigen.

---

## 🔄 Workflow: Soft Delete → Archiv → Wiederherstellung

### **1. Dokument löschen (Soft Delete)**

1. Gehen Sie zur Dokumenten-Liste oder Detail-Seite
2. Klicken Sie auf **"Löschen"**
3. Geben Sie einen **Löschgrund** ein (z.B. "Veraltete Version")
4. Das Dokument wird **soft-deleted**:
   - `deleted_at` wird gesetzt
   - `deleted_by_user_id` wird gesetzt
   - `deletion_reason` wird gesetzt
   - **RAG-Cleanup:** Automatisches Entfernen aus Vector-DB
   - Dokument verschwindet aus aktiver Liste
   - Dokument erscheint im Archiv

### **2. Dokument im Archiv finden**

1. Öffnen Sie die Archiv-Seite
2. Verwenden Sie Filter oder Suche, um das Dokument zu finden
3. Prüfen Sie Löschgrund und Löschdatum

### **3. Dokument wiederherstellen**

1. Klicken Sie auf **"Wiederherstellen"**
2. Wählen Sie Status (Draft/Reviewed/Approved)
3. Dokument wird wiederhergestellt:
   - `deleted_at` wird auf `NULL` gesetzt
   - `deleted_by_user_id` wird auf `NULL` gesetzt
   - `deletion_reason` wird auf `NULL` gesetzt
   - Workflow-Status wird auf gewählten Status gesetzt
   - Dokument erscheint wieder in aktiver Liste
   - Optional: Re-Indexierung in RAG (wenn Status = Approved)

### **4. Dokument endgültig löschen (Hard Delete)**

1. Nach Retention-Periode (konfigurierbar)
2. Nur Level 5 (QMS Admin)
3. Bestätigung: "LÖSCHEN" eingeben
4. Physische Löschung aller Dateien

---

## 🔍 Tipps und Tricks

### **Effektive Archiv-Verwaltung**

1. **Löschgrund dokumentieren:** Geben Sie immer einen aussagekräftigen Löschgrund ein
2. **Regelmäßige Prüfung:** Prüfen Sie das Archiv regelmäßig auf Dokumente, die wiederhergestellt werden sollten
3. **Retention-Policy:** Hard Delete nur nach Ablauf der Retention-Periode durchführen
4. **Audit-Compliance:** Nutzen Sie das Archiv für Audit-Zwecke (Löschgrund und Zeitstempel)

### **Wiederherstellung optimieren**

1. **Status wählen:** Wählen Sie den passenden Status für die Wiederherstellung
   - **Draft:** Für Überarbeitung
   - **Reviewed:** Wenn bereits geprüft
   - **Approved:** Wenn sofort freigegeben werden soll
2. **RAG-Re-Indexierung:** Wenn als "Approved" wiederhergestellt, kann automatisch re-indexiert werden

---

## 📊 FAQ

### Q: Kann ich ein Dokument mehrfach löschen und wiederherstellen?
A: Ja, Soft Delete und Wiederherstellung können mehrfach durchgeführt werden. Jede Löschung wird mit einem neuen `deleted_at` Zeitstempel dokumentiert.

### Q: Was passiert mit RAG-Vektoren bei Soft Delete?
A: RAG-Vektoren werden automatisch aus Qdrant entfernt, wenn ein Dokument soft-deleted wird. Das verhindert doppelte oder veraltete Vektoren in der Vector-DB.

### Q: Kann ich ein Dokument nach Hard Delete wiederherstellen?
A: Nein, Hard Delete ist irreversibel. Alle Dateien und Datenbank-Einträge werden permanent entfernt.

### Q: Wie lange bleiben Dokumente im Archiv?
A: Das hängt von der konfigurierten Retention-Periode ab. Standardmäßig bleiben Dokumente im Archiv, bis sie manuell hard-deleted werden (nur Level 5).

### Q: Wer kann das Archiv sehen?
A: Nur Level 4+ (QM-Mitarbeiter) und QMS Admins (Level 5) können das Archiv einsehen.

---

## 🚨 Wichtige Hinweise

- **Soft Delete ist nicht Hard Delete:** Dokumente bleiben im Archiv und können wiederhergestellt werden
- **Hard Delete ist irreversibel:** Stellen Sie sicher, dass Sie das Dokument wirklich nicht mehr benötigen
- **RAG Cleanup:** Automatisch bei Soft Delete - keine manuelle Aktion erforderlich
- **Audit-Trail:** Vollständige Dokumentation aller Löschungen und Wiederherstellungen

---

**Weiterführende Dokumentation:**
- [Workflow System](02-workflow.md) - Dokument-Workflow
- [Document Upload](01-upload.md) - Dokumente hochladen
- [RAG Chat System](03-rag-chat.md) - RAG Chat verwenden

