# 🔍 Datenbank-Schema Vergleich: rag_models.py vs. tatsächliche DB-Tabellen

**Erstellt:** 2025-10-28  
**Zweck:** Schema-Diskrepanz zwischen Code und Datenbank analysieren

---

## 📊 **Übersicht der Diskrepanzen**

| Tabelle | Status | Hauptprobleme |
|---------|--------|---------------|
| `rag_chat_sessions` | ❌ **KRITISCH** | Spalten-Namen + fehlende Spalten |
| `rag_chat_messages` | ❌ **KRITISCH** | Spalten-Namen + Struktur |
| `rag_indexed_documents` | ⚠️ **MITTEL** | Zusätzliche Spalten in DB |
| `rag_document_chunks` | ⚠️ **MITTEL** | Komplett andere Struktur |

---

## 🚨 **1. rag_chat_sessions - KRITISCH**

### **rag_models.py (erwartet):**
```sql
CREATE TABLE rag_chat_sessions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    session_name VARCHAR(200) NOT NULL,
    created_at DATETIME NOT NULL,
    last_activity DATETIME NOT NULL,    -- ❌ FEHLT
    message_count INTEGER NOT NULL     -- ❌ FEHLT
);
```

### **Tatsächliche DB:**
```sql
CREATE TABLE rag_chat_sessions (
    id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    session_name VARCHAR(255),         -- ⚠️ Länger als erwartet
    created_at DATETIME NOT NULL,
    last_message_at DATETIME,          -- ❌ ANDERER NAME
    is_active BOOLEAN NOT NULL         -- ❌ ZUSÄTZLICH
);
```

### **Probleme:**
- ❌ `last_activity` → `last_message_at` (Name unterschiedlich)
- ❌ `message_count` fehlt komplett
- ❌ `is_active` existiert nur in DB
- ⚠️ `session_name` Länge: 200 vs 255

---

## 🚨 **2. rag_chat_messages - KRITISCH**

### **rag_models.py (erwartet):**
```sql
CREATE TABLE rag_chat_messages (
    id INTEGER PRIMARY KEY,
    chat_session_id INTEGER NOT NULL,  -- ❌ ANDERER NAME
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    source_references JSON,             -- ❌ ANDERE STRUKTUR
    structured_data JSON,              -- ❌ FEHLT
    created_at DATETIME NOT NULL
);
```

### **Tatsächliche DB:**
```sql
CREATE TABLE rag_chat_messages (
    id INTEGER NOT NULL,
    session_id INTEGER NOT NULL,        -- ❌ ANDERER NAME
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    source_chunks TEXT,                 -- ❌ ANDERE STRUKTUR
    created_at DATETIME NOT NULL
);
```

### **Probleme:**
- ❌ `chat_session_id` → `session_id` (Name unterschiedlich)
- ❌ `source_references JSON` → `source_chunks TEXT` (Struktur unterschiedlich)
- ❌ `structured_data JSON` fehlt komplett

---

## ⚠️ **3. rag_indexed_documents - MITTEL**

### **rag_models.py (erwartet):**
```sql
CREATE TABLE rag_indexed_documents (
    id INTEGER PRIMARY KEY,
    upload_document_id INTEGER UNIQUE,
    document_title VARCHAR(500),       -- ❌ FEHLT
    document_type VARCHAR(100),         -- ❌ FEHLT
    status VARCHAR(50),                -- ❌ FEHLT
    indexed_at DATETIME,
    total_chunks INTEGER,
    last_updated DATETIME
);
```

### **Tatsächliche DB:**
```sql
CREATE TABLE rag_indexed_documents (
    id INTEGER NOT NULL,
    upload_document_id INTEGER NOT NULL,
    qdrant_collection_name VARCHAR(100) NOT NULL,  -- ❌ ZUSÄTZLICH
    total_chunks INTEGER NOT NULL,
    indexed_at DATETIME NOT NULL,
    last_updated_at DATETIME NOT NULL,              -- ❌ ANDERER NAME
    embedding_model VARCHAR(100) NOT NULL,         -- ❌ ZUSÄTZLICH
    last_updated DATETIME                           -- ❌ ZUSÄTZLICH
);
```

### **Probleme:**
- ❌ `document_title`, `document_type`, `status` fehlen komplett
- ❌ `last_updated` → `last_updated_at` (Name unterschiedlich)
- ❌ `qdrant_collection_name`, `embedding_model` existieren nur in DB

---

## ⚠️ **4. rag_document_chunks - MITTEL**

### **rag_models.py (erwartet):**
```sql
CREATE TABLE rag_document_chunks (
    id INTEGER PRIMARY KEY,
    indexed_document_id INTEGER,        -- ❌ ANDERER NAME
    chunk_text TEXT,
    chunk_index INTEGER,
    page_numbers JSON,                 -- ❌ ANDERE STRUKTUR
    heading_hierarchy JSON,            -- ❌ FEHLT
    document_type VARCHAR(100),         -- ❌ FEHLT
    confidence_score FLOAT,             -- ❌ FEHLT
    chunk_type VARCHAR(50),            -- ❌ FEHLT
    token_count INTEGER,
    created_at DATETIME
);
```

### **Tatsächliche DB:**
```sql
CREATE TABLE rag_document_chunks (
    id INTEGER NOT NULL,
    rag_indexed_document_id INTEGER NOT NULL,  -- ❌ ANDERER NAME
    chunk_id VARCHAR(100) NOT NULL,             -- ❌ ZUSÄTZLICH
    chunk_text TEXT NOT NULL,
    page_number INTEGER NOT NULL,               -- ❌ ANDERE STRUKTUR
    paragraph_index INTEGER,                    -- ❌ ZUSÄTZLICH
    chunk_index INTEGER NOT NULL,
    token_count INTEGER,
    sentence_count INTEGER,                     -- ❌ ZUSÄTZLICH
    has_overlap BOOLEAN NOT NULL,               -- ❌ ZUSÄTZLICH
    overlap_sentence_count INTEGER NOT NULL,    -- ❌ ZUSÄTZLICH
    qdrant_point_id VARCHAR(100),               -- ❌ ZUSÄTZLICH
    embedding_vector_preview TEXT,              -- ❌ ZUSÄTZLICH
    created_at DATETIME NOT NULL
);
```

### **Probleme:**
- ❌ `indexed_document_id` → `rag_indexed_document_id` (Name unterschiedlich)
- ❌ `page_numbers JSON` → `page_number INTEGER` (Struktur unterschiedlich)
- ❌ `heading_hierarchy`, `document_type`, `confidence_score`, `chunk_type` fehlen
- ❌ Viele zusätzliche Spalten in DB (`chunk_id`, `paragraph_index`, etc.)

---

## 🎯 **Empfohlene Lösungsansätze**

### **Option 1: Code anpassen (SICHERSTE)**
- ✅ Kein Datenverlust-Risiko
- ✅ Sofort funktionsfähig
- ❌ Code wird komplexer

### **Option 2: Schema-Migration (RISIKO)**
- ✅ Sauberer Code
- ❌ Datenverlust-Risiko
- ❌ Komplexe Migration

### **Option 3: Hybrid-Ansatz**
- ✅ Bestehende Daten bleiben erhalten
- ✅ Neue Features funktionieren
- ⚠️ Temporäre Komplexität

---

## 🚀 **Nächste Schritte**

1. **Entscheidung treffen:** Welcher Ansatz?
2. **Backup erstellen:** Falls Migration gewählt wird
3. **Schritt-für-Schritt:** Eine Tabelle nach der anderen
4. **Tests validieren:** Nach jeder Änderung

---

**⚠️ WICHTIG:** Die Datenbank enthält bereits wichtige Daten. Jede Änderung muss sorgfältig geplant werden!
