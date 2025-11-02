# 🌿 RBAC Branch-Strategie

> **Zweck:** Saubere Git-Workflow für RBAC-Implementierung

---

## 📊 Aktuelle Situation

**Aktueller Branch:** `feature/frontend-design-ux-overhaul`

**Uncommitted Änderungen:**
- ✅ Bug-Fix: `contexts/documentupload/interface/router.py` (permission_level → approval_level)
- ✅ Neu: `backend/setup_test_users.py` (Test-User-Setup)
- ✅ Neu: `docs/RBAC_SPECIFICATION.md` (RBAC-Dokumentation)
- ✅ Neu: `docs/RBAC_TDD_PLAN.md` (TDD-Plan)
- ✅ Neu: `docs/RBAC_TEST_USERS.md` (Test-User-Dokumentation)

---

## 🎯 Empfohlene Strategie

### **Option 1: Saubere Trennung (EMPFOHLEN)**

1. **Commit RBAC-Vorbereitungen auf aktuellem Branch:**
   ```bash
   git add contexts/documentupload/interface/router.py
   git add backend/setup_test_users.py
   git add docs/RBAC_*.md
   git commit -m "fix(rbac): Kritischer Bug-Fix + RBAC-Vorbereitung
   
   - Fix: permission_level → approval_level in router.py
   - Add: Test-User-Setup-Script (alle Passwörter: 123)
   - Add: RBAC-Spezifikation (docs/RBAC_SPECIFICATION.md)
   - Add: TDD-Plan (docs/RBAC_TDD_PLAN.md)
   - Add: Test-User-Dokumentation (docs/RBAC_TEST_USERS.md)"
   ```

2. **Frontend-Design-Overhaul mergen (wenn fertig):**
   ```bash
   git checkout main
   git merge feature/frontend-design-ux-overhaul
   ```

3. **Neuen RBAC-Branch erstellen:**
   ```bash
   git checkout main
   git checkout -b feature/rbac-implementation
   ```

4. **RBAC-Vorbereitungen in RBAC-Branch übernehmen:**
   ```bash
   git cherry-pick <commit-hash-von-schritt-1>
   ```

### **Option 2: Direkt auf Design-Branch (SCHNELLER)**

1. **Commit RBAC-Vorbereitungen:**
   ```bash
   git add contexts/documentupload/interface/router.py
   git add backend/setup_test_users.py
   git add docs/RBAC_*.md
   git commit -m "fix(rbac): Kritischer Bug-Fix + RBAC-Vorbereitung"
   ```

2. **Neuen RBAC-Branch vom aktuellen Branch erstellen:**
   ```bash
   git checkout -b feature/rbac-implementation
   ```
   
   **Vorteil:** RBAC-Vorbereitungen sind bereits im Branch
   **Nachteil:** Branch enthält noch Design-Overhaul-Änderungen

3. **Später: Design-Branch in main mergen (ohne RBAC-Commits)**

### **Option 3: Separate Commits (SAUBERSTE)**

1. **Nur Bug-Fix committen:**
   ```bash
   git add contexts/documentupload/interface/router.py
   git commit -m "fix(rbac): permission_level → approval_level Bug-Fix"
   ```

2. **Design-Branch in main mergen**

3. **Neuen RBAC-Branch erstellen:**
   ```bash
   git checkout main
   git checkout -b feature/rbac-implementation
   ```

4. **RBAC-Dokumentation hinzufügen:**
   ```bash
   git add backend/setup_test_users.py
   git add docs/RBAC_*.md
   git commit -m "docs(rbac): RBAC-Spezifikation + TDD-Plan"
   ```

---

## ✅ Empfehlung: **Option 1**

**Warum?**
- Saubere Trennung zwischen Design-Overhaul und RBAC
- Bug-Fix ist kritisch und sollte nicht warten
- RBAC-Vorbereitungen bleiben zusammen
- Design-Overhaul kann unabhängig gemergt werden

**Nachteile:**
- Cherry-pick nötig (aber einfach)

---

## 📝 Ausführungs-Befehle (Option 1)

```bash
# 1. RBAC-Vorbereitungen committen (auf Design-Branch)
git add contexts/documentupload/interface/router.py
git add backend/setup_test_users.py
git add docs/RBAC_*.md
git commit -m "fix(rbac): Kritischer Bug-Fix + RBAC-Vorbereitung

- Fix: permission_level → approval_level in router.py (kritischer Bug)
- Add: Test-User-Setup-Script (Passwörter: 123)
- Add: RBAC-Spezifikation + TDD-Plan + Test-User-Doku"

# 2. Commit-Hash merken (für später)
COMMIT_HASH=$(git rev-parse HEAD)
echo "RBAC-Prep Commit: $COMMIT_HASH"

# 3. Design-Branch in main mergen (wenn fertig)
git checkout main
git merge feature/frontend-design-ux-overhaul

# 4. Neuen RBAC-Branch erstellen
git checkout -b feature/rbac-implementation

# 5. RBAC-Vorbereitungen übernehmen
git cherry-pick $COMMIT_HASH
```

---

## ⚠️ Alternative: Design-Overhaul erst MERGEN

Wenn der Design-Overhaul noch nicht fertig ist, können wir:

1. **RBAC-Vorbereitungen jetzt committen**
2. **Neuen RBAC-Branch erstellen**
3. **Design-Overhaul später mergen**

**Nachteil:** Design-Overhaul-Branch hat dann schon RBAC-Commits

---

## 🎯 Entscheidung

Welche Option bevorzugst du?

1. **Option 1:** Saubere Trennung (empfohlen)
2. **Option 2:** Direkt vom Design-Branch
3. **Option 3:** Separate Commits
4. **Oder:** Design-Overhaul erst fertigstellen und mergen?

