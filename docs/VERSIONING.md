# 📋 DocuMind-AI V2 - Versionierung Best Practices

> **Version:** 2.1.0  
> **Stand:** 2025-10-27

---

## 🎯 Versionierungs-Strategie

### **Semantic Versioning (SemVer)**

```
MAJOR.MINOR.PATCH
2.1.0
```

- **MAJOR (2):** Breaking Changes, Architektur-Änderungen
- **MINOR (1):** Neue Features, neue Contexts, erweiterte Funktionalität
- **PATCH (0):** Bug Fixes, kleine Verbesserungen

---

## 📝 Dokumente die bei Versionierung aktualisiert werden

### **✅ IMMER aktualisieren:**

1. **README.md** - Hauptversion + Status
2. **frontend/package.json** - Frontend Version
3. **docs/user-manual/README.md** - User Manual Version
4. **docs/user-manual/02-workflow.md** - Workflow Manual Version
5. **docs/database-schema.md** - Schema Version + Stand
6. **ONBOARDING_PROMPT.md** - Aktuelle Contexts + Features
7. **PROJECT_RULES.md** - Stand-Datum (automatisch bei Änderungen)

### **✅ Context-spezifisch aktualisieren:**

8. **contexts/[name]/README.md** - Context Status + Version
9. **docs/ROADMAP_DOCUMENT_UPLOAD.md** - Roadmap Status

### **🔍 Optional prüfen:**

10. **docs/architecture.md** - Nur bei Architektur-Änderungen
11. **docs/user-manual/01-upload.md** - Nur bei Upload-Änderungen

---

## 🚀 Versionierungs-Workflow

### **Bei MINOR Version (z.B. 2.0.0 → 2.1.0):**

```bash
# 1. Alle Dokumente aktualisieren
# 2. Git Commit
git add .
git commit -m "Release: Version 2.1.0 - [Feature Name]

🎉 MINOR RELEASE: [Feature Description]

📚 Documentation Updates:
- Update all versions to 2.1.0
- Update PROJECT_RULES.md date
- Update ONBOARDING_PROMPT.md with new features
- Update Context READMEs

✨ New Features in v2.1:
- [Feature 1]
- [Feature 2]
- [Feature 3]

🏗️ Architecture:
- [Technical details]
- [New endpoints/contexts]

Status: ✅ PRODUCTION READY"
```

### **Bei MAJOR Version (z.B. 2.1.0 → 3.0.0):**

```bash
# 1. Alle Dokumente aktualisieren
# 2. Breaking Changes dokumentieren
# 3. Migration Guide erstellen
git add .
git commit -m "Release: Version 3.0.0 - [Major Feature]

🎉 MAJOR RELEASE: [Major Feature Description]

⚠️ BREAKING CHANGES:
- [Breaking Change 1]
- [Breaking Change 2]

📚 Documentation Updates:
- Update all versions to 3.0.0
- Create migration guide
- Update architecture documentation

✨ New Features in v3.0:
- [Major Feature 1]
- [Major Feature 2]

🏗️ Architecture Changes:
- [Architecture Change 1]
- [Architecture Change 2]

Status: ✅ PRODUCTION READY - Migration Required"
```

---

## 📋 Checkliste für Versionierung

### **Vor Release:**

- [ ] Alle relevanten Dokumente auf neue Version aktualisiert
- [ ] ONBOARDING_PROMPT.md mit neuen Features aktualisiert
- [ ] PROJECT_RULES.md Stand-Datum aktualisiert
- [ ] Context READMEs aktualisiert
- [ ] Frontend package.json Version aktualisiert
- [ ] User Manual Versionen aktualisiert
- [ ] Database Schema Version aktualisiert

### **Nach Release:**

- [ ] Git Tag erstellen: `git tag v2.1.0`
- [ ] Release Notes erstellen
- [ ] Deployment testen
- [ ] Dokumentation final prüfen

---

## 🎯 Versionierungs-Beispiele

### **v2.1.0 - Document Workflow System**
- ✅ Complete 4-Status Workflow
- ✅ Kanban Board mit Drag & Drop
- ✅ Audit Trail mit User Names
- ✅ Interest Groups Filtering
- ✅ Document Type Filter
- ✅ Status Change Modal
- ✅ Real-time Updates

### **v2.0.0 - Core System**
- ✅ Interest Groups Management
- ✅ User Management mit RBAC
- ✅ JWT Authentication
- ✅ AI Playground
- ✅ Document Types
- ✅ Prompt Templates

### **v1.0.0 - Initial Release**
- ✅ Basic DDD Architecture
- ✅ Docker Setup
- ✅ Database Schema
- ✅ Authentication System

---

## 🔧 Automatisierung

### **Script für Versionierung:**

```bash
#!/bin/bash
# scripts/version-update.sh

VERSION=$1
if [ -z "$VERSION" ]; then
    echo "Usage: ./version-update.sh 2.1.0"
    exit 1
fi

# Update package.json
sed -i "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" frontend/package.json

# Update README.md
sed -i "s/Version: .*/Version: $VERSION/" README.md

# Update user manual
sed -i "s/Version: .*/Version: $VERSION/" docs/user-manual/README.md

echo "✅ Version updated to $VERSION"
echo "📝 Please manually update:"
echo "   - ONBOARDING_PROMPT.md"
echo "   - PROJECT_RULES.md"
echo "   - Context READMEs"
echo "   - Database Schema"
```

---

## 📚 Weitere Informationen

- **Semantic Versioning:** https://semver.org/
- **Conventional Commits:** https://conventionalcommits.org/
- **Git Tags:** `git tag -a v2.1.0 -m "Release version 2.1.0"`
