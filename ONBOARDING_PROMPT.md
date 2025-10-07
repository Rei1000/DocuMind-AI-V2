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
✅ 3 Layer-Prinzip (Domain → Application → Infrastructure)
✅ Dependency Rule
✅ Automatische Dokumentation
✅ Aktuelle Contexts + Roadmap
✅ Docker-Setup
✅ Git Workflow
