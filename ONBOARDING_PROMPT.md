# 🚀 AI Agent Onboarding Prompt

Kopiere diesen Text und gib ihn dem AI-Agenten beim ersten Öffnen des Projekts:

---

## Prompt für neuen AI-Agenten:

```
Hallo! Ich arbeite an DocuMind-AI V2, einem Clean DDD-Projekt für Quality Management Systems.

Bitte führe folgendes Onboarding durch:

1. **Lies PROJECT_RULES.md komplett** und fasse zusammen:
   - Welche Architektur-Prinzipien gelten?
   - Welche Contexts sind implementiert?
   - Welche Contexts sind auf der Roadmap?
   - Welche Dokumentations-Regeln muss ich beachten?

2. **Lies README.md** und erkläre mir:
   - Wie starte ich das System?
   - Welche Features sind aktuell verfügbar?
   - Welcher Tech-Stack wird verwendet?

3. **Lies docs/architecture.md** und erkläre:
   - Wie ist die High-Level Architektur aufgebaut?
   - Wie funktioniert der Dependency Flow (Hexagonal Architecture)?
   - Welche Layer gibt es und was gehört wohin?

4. **Prüfe die aktuelle Code-Basis:**
   - Welche Contexts existieren unter `contexts/`?
   - Welche Backend-Routes sind unter `backend/app/main.py` registriert?
   - Welche Frontend-Pages existieren unter `frontend/app/`?

5. **Erstelle eine Status-Übersicht:**
   - Was ist vollständig implementiert?
   - Was fehlt noch (Frontend/Backend)?
   - Was sind sinnvolle nächste Schritte?

6. **Bestätige, dass du verstanden hast:**
   - Wie erstelle ich einen neuen Context (DDD-konform)?
   - Wie dokumentiere ich Änderungen automatisch?
   - Welche Regeln darf ich NIEMALS brechen?

Nachdem du alles gelesen und zusammengefasst hast, frage mich:
"Woran möchtest du als Nächstes arbeiten?"
```

---

## Alternative: Kürzerer Quick-Start Prompt

```
Hallo! Bitte lies zuerst `PROJECT_RULES.md` komplett durch und fasse in 5 Bullet Points zusammen:

1. Welche Architektur-Regeln gelten?
2. Welche Contexts existieren (Status)?
3. Was ist die Roadmap?
4. Wie dokumentiere ich Änderungen?
5. Was sind die wichtigsten "NIEMALS"-Regeln?

Danach: "Bereit für die Arbeit - was soll ich tun?"
```

---

## Was der Agent dann wissen sollte:

✅ DDD/Hexagonal Architecture
✅ Bounded Contexts Struktur
✅ 4 Layer-Prinzip (Domain → Application → Infrastructure → Interface)
✅ Dependency Rule (interface → application → domain ← infrastructure)
✅ Automatische Dokumentation (PROJECT_RULES.md, README.md, Context-README)
✅ Aktuelle Contexts + Roadmap
✅ Docker-Setup (docker-compose.yml)
✅ Git Workflow (Conventional Commits)

---

## 📊 Aktuelle Contexts (Stand: 2025-10-08)

### ✅ Vollständig implementiert:
1. **interestgroups** - 13 Stakeholder Groups Management
2. **users** - User Management mit RBAC
3. **accesscontrol** - JWT Auth & Permissions
4. **aiplayground** - AI Model Testing (OpenAI, Google AI, Vision, Parallel Processing)
5. **documenttypes** - Document Type Management
6. **prompttemplates** - Prompt Template Management & Versioning

### 🎯 Neue Features (2025-10-08):
- **Prompt-Verwaltung Page** (`/prompt-management`)
  - Split-View: Dokumenttypen Grid + Gestapelte Prompt-Karten
  - Drag & Drop für Standard-Prompt Zuweisung
  - AI Playground Integration ("Als Template speichern")
  - Edit-Workflow (Template im Playground bearbeiten)
  - Search & Filter, Preview Modal
  - Status Management (Draft/Active/Archived)
  - Dokumenttyp Aktivieren/Deaktivieren Toggle

### 🔜 Roadmap:
- **documents** Context (Document Upload & Storage)
- **uploads** Context (OCR, Vision AI Processing)
- **qmworkflow** Context (Review → Approval Workflow)

---

## 🎯 Wichtigste Regeln für neue Agents:

1. **IMMER zuerst `PROJECT_RULES.md` lesen!**
2. **NIEMALS** Domain-Layer von Infrastructure abhängig machen
3. **NIEMALS** Cross-Context Imports
4. **IMMER** Type Hints (Python) und Types (TypeScript)
5. **IMMER** Google-Style Docstrings
6. **IMMER** Dokumentation updaten bei Änderungen
7. **Für System-Start:** IMMER `./start.sh` verwenden, NIEMALS manuell starten!
