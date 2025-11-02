# 🔐 RBAC Berechtigungssystem - Spezifikation

> **Status:** Entwurf - Zur Diskussion  
> **Stand:** 2025-01-XX  
> **Version:** 1.0

---

## 🎯 Übersicht

Das DocuMind-AI System verwendet ein 5-stufiges Berechtigungssystem basierend auf `UserGroupMembership.approval_level` und `User.is_qms_admin`.

---

## 📊 Permission Levels

### **Level 5: QMS Admin** (nur `qms.admin@company.com`)

**Backend:**
- `User.is_qms_admin = True`
- Alle API-Endpunkte zugänglich

**Frontend:**
- ✅ **Alle Seiten sichtbar** (vollständige Navigation)
- ✅ **Benutzerverwaltung** (`/users`) - **NUR Level 5**
- ✅ **Dokument Upload** (`/document-upload`)
- ✅ **Dokumenten-Workflow** (Kanban Board)
- ✅ **Prompt-Verwaltung**
- ✅ **AI Models** (AI Playground)
- ✅ **RAG Chat**

**Features:**
- Vollzugriff auf alle Funktionen
- Einziger Zugriff auf Benutzerverwaltung
- Kann alle Dokumente unabhängig von Interest Groups sehen/bearbeiten

---

### **Level 4: QM-Mitarbeiter**

**Backend:**
- `UserGroupMembership.approval_level = 4`
- Upload-Endpunkte erlaubt
- Workflow-Endpunkte erlaubt (Status-Änderungen)

**Frontend:**
- ✅ **Dokument Upload** (`/document-upload`) - **NUR Level 4+**
- ✅ **Dokumenten-Workflow** (Kanban Board) - **ALLE Dokumente**
- ✅ **Dokumenten-Detail** (Vollzugriff)
- ✅ **RAG Chat** (alle Dokumente)
- ❌ **Prompt-Verwaltung** - **AUSGEBLENDET (später Level 4+)**
- ❌ **AI Models** - **AUSGEBLENDET (später Level 4+)**
- ❌ **Benutzerverwaltung** - **AUSGEBLENDET**

**Features:**
- Dürfen als einzige Dokumente hochladen
- Können alle Dokumente unabhängig von Interest Groups sehen
- Können Dokumente im Workflow verschieben und freigeben (approved/rejected)
- Workflow: Draft → Reviewed → Approved/Rejected
- RAG Chat: alle dokumente (keine IG-Filterung)

---

### **Level 3: Abteilungsleiter**

**Backend:**
- `UserGroupMembership.approval_level = 3`
- Workflow-Endpunkte erlaubt (nur Draft → Reviewed)

**Frontend:**
- ✅ **Dokumenten-Workflow** (Kanban Board) - **EINGESCHRÄNKT (nur eigene IG)**
- ✅ **Dokumenten-Detail** (Lesen + Kommentieren)
- ✅ **RAG Chat** (nur Dokumente seiner IG)
- ❌ **Dokument Upload** - **AUSGEBLENDET**
- ❌ **Prompt-Verwaltung** - **AUSGEBLENDET**
- ❌ **AI Models** - **AUSGEBLENDET**
- ❌ **Benutzerverwaltung** - **AUSGEBLENDET**

**Features:**
- Sehen nur Dokumente in ihrer zugeordneten Interest Group
- Kanban Board sichtbar (nur für eigene Interest Group)
- Workflow: Draft → Reviewed (nur innerhalb ihrer Interest Group)
- Können nicht freigeben (kein Approved/Rejected)
- Detail-Karte: Lesen + Kommentieren

---

### **Level 2: Teamleiter**

**Backend:**
- `UserGroupMembership.approval_level = 2`
- Nur Leserechte (GET-Endpunkte)

**Frontend:**
- ✅ **Dokumenten-Übersicht** (Tabellen-Ansicht) - **NUR Tabelle, kein Kanban**
- ✅ **Dokumenten-Detail** (Lesen + Kommentieren)
- ✅ **RAG Chat** (nur Dokumente seiner IG)
- ❌ **Dokument Upload** - **AUSGEBLENDET**
- ❌ **Dokumenten-Workflow (Kanban)** - **AUSGEBLENDET**
- ❌ **Prompt-Verwaltung** - **AUSGEBLENDET**
- ❌ **AI Models** - **AUSGEBLENDET**
- ❌ **Benutzerverwaltung** - **AUSGEBLENDET**

**Features:**
- Sehen nur Dokumente in ihrer zugeordneten Interest Group
- Nur Tabellen-Ansicht (Kanban Board nicht sichtbar)
- Detail-Karte: Lesen + Kommentieren (keine Status-Änderungen)
- Keine Workflow-Funktionen

---

### **Level 1: Mitarbeiter**

**Backend:**
- `UserGroupMembership.approval_level = 1`
- Nur Leserechte (GET-Endpunkte)

**Frontend:**
- ✅ **RAG Chat** (`/`) - **HAUPTSEITE (nur Dokumente seiner IG)**
- ✅ **Dokumenten-Detail** (über Link aus RAG Chat, schreibgeschützt)
- ❌ **Dokument Upload** - **AUSGEBLENDET**
- ❌ **Dokumenten-Übersicht** (`/documents`) - **AUSGEBLENDET**
- ❌ **Prompt-Verwaltung** - **AUSGEBLENDET**
- ❌ **AI Models** - **AUSGEBLENDET**
- ❌ **Benutzerverwaltung** - **AUSGEBLENDET**

**Features:**
- Nur RAG Chat sichtbar
- RAG Chat: nur Dokumente aus ihrer zugeordneten Interest Group (Backend-Filter)
- Über Link (Source Reference) Detail-Karte öffnen (schreibgeschützt, nur Lesen)
- Minimale Navigation (nur Home/RAG Chat)

---

## 🔄 Workflow-Berechtigungen

| Level | Draft → Reviewed | Reviewed → Approved | Reviewed → Rejected | Rejected → Draft |
|-------|------------------|---------------------|----------------------|-------------------|
| **L1** | ❌ | ❌ | ❌ | ❌ |
| **L2** | ❌ | ❌ | ❌ | ❌ |
| **L3** | ✅ (nur eigene IG) | ❌ | ❌ | ❌ |
| **L4** | ✅ (alle) | ✅ (alle) | ✅ (alle) | ✅ (alle) |
| **L5** | ✅ (alle) | ✅ (alle) | ✅ (alle) | ✅ (alle) |

---

## 🎨 Frontend-Navigation (Sichtbarkeit)

| Navigation Link | L1 | L2 | L3 | L4 | L5 |
|----------------|----|----|----|----|----|
| **Home (RAG Chat)** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Dokument Upload** | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Dokumente** | ❌ | ✅ (nur Tabelle) | ✅ (Kanban) | ✅ (Kanban) | ✅ (Kanban) |
| **Prompt-Verwaltung** | ❌ | ❌ | ❌ | ❌ | ✅ |
| **AI Models** | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Benutzer** | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## 🔍 Interest Group Filterung (Backend-Filter)

- **Level 1:** RAG Chat - nur Dokumente seiner IG
- **Level 2:** RAG Chat + Dokumenten-Tabelle - nur Dokumente seiner IG
- **Level 3:** RAG Chat + Dokumenten-Kanban - nur Dokumente seiner IG (Workflow nur für diese)
- **Level 4:** RAG Chat + Dokumenten-Kanban - alle Dokumente (keine IG-Filterung)
- **Level 5:** Alle Dokumente (keine IG-Filterung)

---

## ✅ Klärungen (2025-01-XX)

1. ✅ **Level 3 Kanban:** Sichtbar, aber nur für eigene IG, Draft → Reviewed möglich
2. ✅ **Level 2 Detail-Karte:** Lesen + Kommentieren erlaubt
3. ✅ **Prompt-Verwaltung:** Nur Level 5 (später Level 4+)
4. ✅ **AI Models:** Nur Level 5 (später Level 4+)
5. ✅ **RAG Chat Filterung:** Backend-Filter (konsistenter)
6. ✅ **Navigation UX:** Ausgeblendete Links komplett entfernen (aufgeräumter)

---

## 📝 Implementierungs-Hinweise

### Backend:
- ✅ `SQLAlchemyWorkflowPermissionService.get_user_level()` - Ermittelt User Level
- ✅ `SQLAlchemyWorkflowPermissionService.can_change_status()` - Prüft Workflow-Berechtigung
- ✅ Permission-Checks in `router.py` (Upload, Delete, Assign)
- ❌ **RAG Chat Backend-Filter:** Interest Group-Filterung in `/api/rag/chat/ask` und `/api/rag/search`
- ❌ **Dokumenten-Liste Backend-Filter:** Interest Group-Filterung in `/api/document-upload/` (Level 1-3)

### Frontend:
- ❌ User-Level aus JWT Token extrahieren
- ❌ Navigation-Links basierend auf Level ausblenden
- ❌ Dokument Upload-Seite nur bei Level 4+ anzeigen
- ❌ Kanban Board nur bei Level 3+ anzeigen (Level 2 nur Tabelle)
- ❌ Workflow-Buttons basierend auf Level aktivieren/deaktivieren
- ❌ Level-Badge in Navigation anzeigen
- ❌ Kommentar-Funktion für Level 2+ aktivieren

---

## 🔄 Änderungen gegenüber aktuellem System

**Aktuell:**
- Alle User sehen alle Navigation-Links
- Upload ist für alle sichtbar (Backend blockiert bei Level < 4)
- Workflow ist für alle sichtbar
- Keine Interest Group-Filterung im Frontend

**Neu (nach dieser Spezifikation):**
- Navigation-Links werden basierend auf Level gefiltert
- Upload-Button nur bei Level 4+ sichtbar
- Kanban nur bei Level 3+ sichtbar (Level 2 nur Tabelle)
- Interest Group-Filterung im Frontend für Level 1-3

