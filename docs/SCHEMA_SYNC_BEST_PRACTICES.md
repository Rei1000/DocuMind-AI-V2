# 📋 Schema-Sync Best Practices

## 🎯 **Ziel:** Schema-Diskrepanzen vermeiden

**Problem:** Code und Datenbank-Schema driften auseinander → 500 Internal Server Errors

**Lösung:** Automatische Synchronisation bei jeder Änderung

---

## 🔄 **Schema-First Development Workflow**

### **1. Vor jeder Schema-Änderung:**

```bash
# 1. Aktuelles Schema dokumentieren
sqlite3 data/qms.db ".schema" > current_schema.sql

# 2. Backup erstellen
cp data/qms.db data/qms_backup_$(date +%Y%m%d_%H%M%S).db

# 3. Änderung planen
echo "Geplante Änderung: [Beschreibung]"
```

### **2. Schema-Änderung implementieren:**

```bash
# Schritt 1: Backend Models
# backend/app/models.py oder backend/app/rag_models.py

# Schritt 2: Domain Entities
# contexts/[name]/domain/entities.py

# Schritt 3: Pydantic Schemas
# contexts/[name]/interface/schemas.py

# Schritt 4: Tests
# tests/unit/[context]/test_entities.py
# tests/integration/[context]/test_repositories.py

# Schritt 5: Dokumentation
# docs/database-schema.md
# contexts/[name]/README.md
```

### **3. Validierung:**

```bash
# 1. Tests laufen lassen
pytest tests/ -v

# 2. Backend starten
./start.sh local

# 3. Health Check
curl http://localhost:8000/health

# 4. API-Endpoints testen
curl http://localhost:8000/api/[endpoint]
```

---

## 📋 **Schema-Sync Checklist**

### **Bei JEDER Schema-Änderung:**

- [ ] **DB-Schema geändert?**
  - [ ] SQLite Schema dokumentiert
  - [ ] Backup erstellt
  - [ ] Migration geplant

- [ ] **Backend Models angepasst?**
  - [ ] `backend/app/models.py` aktualisiert
  - [ ] `backend/app/rag_models.py` aktualisiert
  - [ ] Spalten-Namen korrekt
  - [ ] Datentypen korrekt

- [ ] **Domain Entities synchronisiert?**
  - [ ] `contexts/[name]/domain/entities.py` aktualisiert
  - [ ] Entity-Attribute korrekt
  - [ ] Relationships korrekt

- [ ] **Pydantic Schemas aktualisiert?**
  - [ ] `contexts/[name]/interface/schemas.py` aktualisiert
  - [ ] Request/Response Schemas korrekt
  - [ ] Validation Rules korrekt

- [ ] **Tests angepasst?**
  - [ ] Unit Tests für Entities
  - [ ] Integration Tests für Repositories
  - [ ] E2E Tests für API-Endpoints
  - [ ] Alle Tests grün

- [ ] **Dokumentation aktualisiert?**
  - [ ] `docs/database-schema.md` aktualisiert
  - [ ] `contexts/[name]/README.md` aktualisiert
  - [ ] `docs/PROJECT_RULES.md` aktualisiert
  - [ ] API-Dokumentation aktualisiert

- [ ] **Integration Tests grün?**
  - [ ] Backend startet ohne Fehler
  - [ ] API-Endpoints funktionieren
  - [ ] Frontend kann mit Backend kommunizieren

---

## 🚨 **Häufige Schema-Probleme**

### **1. Spalten-Namen unterschiedlich:**
```python
# ❌ PROBLEM: Code erwartet 'last_activity', DB hat 'last_message_at'
class RAGChatSession(Base):
    last_activity = Column(DateTime)  # ❌ Existiert nicht in DB

# ✅ LÖSUNG: Spalten-Namen anpassen
class RAGChatSession(Base):
    last_message_at = Column(DateTime)  # ✅ Stimmt mit DB überein
```

### **2. Fehlende Spalten:**
```python
# ❌ PROBLEM: Code erwartet 'message_count', DB hat es nicht
class RAGChatSession(Base):
    message_count = Column(Integer)  # ❌ Existiert nicht in DB

# ✅ LÖSUNG: Spalte berechnen oder hinzufügen
@property
def message_count(self):
    return len(self.messages)  # ✅ Berechnet aus Relationship
```

### **3. Datentyp-Unterschiede:**
```python
# ❌ PROBLEM: Code erwartet JSON, DB hat TEXT
source_references = Column(JSON)  # ❌ DB hat TEXT

# ✅ LÖSUNG: Datentyp anpassen
source_references = Column(Text)  # ✅ Stimmt mit DB überein
```

---

## 🛠️ **Schema-Debugging Tools**

### **1. Schema-Vergleich:**
```bash
# Aktuelles DB-Schema
sqlite3 data/qms.db ".schema rag_chat_sessions"

# Erwartetes Schema aus Code
grep -A 20 "class RAGChatSession" backend/app/rag_models.py
```

### **2. Schema-Validierung:**
```bash
# Backend starten und Fehler prüfen
./start.sh local
tail -f backend.log

# API-Endpoint testen
curl -v http://localhost:8000/api/rag/chat/sessions?user_id=123
```

### **3. Schema-Dokumentation:**
```bash
# Schema-Dokumentation aktualisieren
echo "## rag_chat_sessions" >> docs/database-schema.md
sqlite3 data/qms.db ".schema rag_chat_sessions" >> docs/database-schema.md
```

---

## 📚 **Referenz-Dateien**

- **Schema-Dokumentation:** `docs/database-schema.md`
- **Backend Models:** `backend/app/models.py`, `backend/app/rag_models.py`
- **Domain Entities:** `contexts/[name]/domain/entities.py`
- **API Schemas:** `contexts/[name]/interface/schemas.py`
- **Tests:** `tests/unit/[context]/`, `tests/integration/[context]/`

---

**⚠️ WICHTIG:** Schema-Diskrepanzen sind die häufigste Ursache für 500 Internal Server Errors!
