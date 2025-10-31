# 🔌 Embedding Provider Dokumentation

> **Status:** ✅ Vollständig implementiert  
> **Version:** 2.1.0  
> **Letzte Aktualisierung:** 2025-10-31

---

## 🎯 Übersicht

Das RAG-System unterstützt mehrere Embedding-Provider mit intelligenter Auto-Auswahl:

| Provider | Dimensionen | Kosten | Geschwindigkeit | Qualität | Verfügbarkeit |
|----------|-------------|--------|-----------------|----------|---------------|
| **OpenAI GPT-5 Mini Key** | 1536 | API-Kosten | Sehr schnell | ⭐⭐⭐⭐⭐ | Best wenn verfügbar |
| **Google Gemini** | 768 | Kostenlos | Schnell | ⭐⭐⭐⭐ | Sehr gut |
| **Sentence Transformers** | 768/384 | Kostenlos | Mittel | ⭐⭐⭐⭐ | Lokal, immer verfügbar |

---

## 🚀 Auto-Auswahl (Standard)

Das System wählt automatisch den besten verfügbaren Provider nach Priorität:

### **Priorität (Auto-Mode):**

1. **OpenAI GPT-5 Mini Key** (1536 Dimensionen)
   - ✅ Beste Qualität und Dimensionen
   - ✅ Sehr schnell
   - ⚠️ Benötigt `OPENAI_GPT5_MINI_API_KEY` mit Embedding-Zugriff
   - 💰 API-Kosten

2. **Google Gemini** (768 Dimensionen)
   - ✅ Sehr gut für multilingual (inkl. Deutsch)
   - ✅ Kostenlos mit Google AI API Key
   - ✅ 768 Dimensionen (gute Balance)
   - ⚠️ Benötigt `GOOGLE_AI_API_KEY`

3. **Sentence Transformers** (768/384 Dimensionen)
   - ✅ Lokal, keine API-Aufrufe
   - ✅ Kostenlos, keine Limits
   - ✅ Sehr gut für deutsche Dokumente
   - ⚠️ Benötigt Installation: `pip install sentence-transformers`

---

## 📋 Konfiguration

### **Environment Variables**

```bash
# Provider-Auswahl (optional, default: auto)
EMBEDDING_PROVIDER=auto|openai|google|sentence-transformers

# Modell-Spezifische Konfiguration (optional)
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-mpnet-base-v2
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
GOOGLE_EMBEDDING_MODEL=text-embedding-004

# API Keys (für OpenAI und Google)
OPENAI_GPT5_MINI_API_KEY=sk-...
GOOGLE_AI_API_KEY=AIzaSy...
```

### **Auto-Auswahl Logik**

Das System prüft automatisch:
1. **OpenAI GPT-5 Mini Key** → Testet Embedding-Zugriff
2. **Google Gemini** → Testet API-Verbindung
3. **Sentence Transformers** → Prüft Installation
4. **Fallback** → Verwendet bestes verfügbares Modell

---

## 🔧 Provider-Details

### **1. OpenAI GPT-5 Mini Key** (1536 Dimensionen)

**Modell:** `text-embedding-3-small`  
**Dimensionen:** 1536  
**Provider:** OpenAI  
**API Key:** `OPENAI_GPT5_MINI_API_KEY`

**Vorteile:**
- ✅ Beste Qualität für RAG-Systeme
- ✅ Höchste Dimensionen (1536)
- ✅ Sehr schnell
- ✅ Optimal für Qdrant Vector Store

**Nachteile:**
- ⚠️ API-Kosten
- ⚠️ Benötigt API Key mit Embedding-Zugriff

**Konfiguration:**
```bash
export EMBEDDING_PROVIDER=openai
export OPENAI_GPT5_MINI_API_KEY=sk-...
```

---

### **2. Google Gemini** (768 Dimensionen)

**Modell:** `text-embedding-004`  
**Dimensionen:** 768  
**Provider:** Google  
**API Key:** `GOOGLE_AI_API_KEY`

**Vorteile:**
- ✅ Kostenlos mit Google AI API Key
- ✅ Sehr gut für multilingual (inkl. Deutsch)
- ✅ 768 Dimensionen (gute Balance)
- ✅ Schnell

**Nachteile:**
- ⚠️ Benötigt Google AI API Key
- ⚠️ Weniger Dimensionen als OpenAI

**Konfiguration:**
```bash
export EMBEDDING_PROVIDER=google
export GOOGLE_AI_API_KEY=AIzaSy...
```

---

### **3. Sentence Transformers** (768/384 Dimensionen)

**Modell:** `paraphrase-multilingual-mpnet-base-v2` (default)  
**Dimensionen:** 768 oder 384 (je nach Modell)  
**Provider:** Local (Hugging Face)  
**API Key:** Nicht erforderlich

**Verfügbare Modelle:**
- `paraphrase-multilingual-mpnet-base-v2` (768 dim) - **Best für DE**
- `multilingual-e5-base` (768 dim) - Sehr gut für multilingual
- `all-MiniLM-L6-v2` (384 dim) - Schnell, gut

**Vorteile:**
- ✅ Lokal, keine API-Aufrufe
- ✅ Kostenlos, keine Limits
- ✅ Sehr gut für deutsche Dokumente
- ✅ Datenschutz (keine Datenübertragung)

**Nachteile:**
- ⚠️ Benötigt Installation: `pip install sentence-transformers`
- ⚠️ Erster Download kann lange dauern (Modelle sind groß)
- ⚠️ Weniger Dimensionen als OpenAI (768 vs 1536)

**Konfiguration:**
```bash
export EMBEDDING_PROVIDER=sentence-transformers
export EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-mpnet-base-v2
```

**Installation:**
```bash
pip install sentence-transformers
```

---

## 🔄 Migration & Re-Indexierung

### **Wichtiger Hinweis:**

**Wenn du den Embedding-Provider wechselst oder von Mock-Embeddings zu echten Embeddings migrierst:**

1. **Alte Collections löschen:**
   ```python
   # Alte Collections mit Mock-Embeddings sollten neu indexiert werden
   # Sie haben möglicherweise nur wenige non-zero Werte (Mock-Embeddings)
   ```

2. **Neue Indexierung durchführen:**
   - Dokument hochladen
   - Dokument freigeben
   - RAG-Indexierung starten
   - System verwendet automatisch den besten Provider

### **Qdrant Status prüfen:**

```python
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)
info = client.get_collection("collection_name")

# Prüfe ob Mock-Embeddings vorhanden sind
scroll_result = client.scroll(
    collection_name="collection_name",
    limit=1,
    with_vectors=True
)

if scroll_result[0]:
    point = scroll_result[0][0]
    if point.vector:
        non_zero = sum(1 for v in point.vector if abs(v) > 0.01)
        # Mock-Embeddings haben viele Nullwerte (< 50% non-zero)
        if non_zero < len(point.vector) * 0.5:
            print("⚠️ Mock-Embeddings erkannt - Re-Indexierung empfohlen")
```

---

## 📊 Best Practices

### **Für Production:**

1. **OpenAI GPT-5 Mini Key** (falls Budget vorhanden)
   - Beste Qualität (1536 Dimensionen)
   - Optimal für Qdrant Vector Store
   - Schnell und zuverlässig

2. **Google Gemini** (kostenlose Alternative)
   - Sehr gut für multilingual
   - 768 Dimensionen (gute Balance)
   - Kostenlos mit Google AI API Key

3. **Sentence Transformers** (lokale Alternative)
   - Keine API-Kosten
   - Sehr gut für deutsche Dokumente
   - Datenschutz-freundlich

### **Für Development:**

- **Sentence Transformers** empfohlen
  - Lokal, keine API-Kosten
  - Schnelles Iterieren
  - Keine API-Limits

### **Hybrid-Ansatz:**

- **Development:** Sentence Transformers (lokal, kostenlos)
- **Production:** OpenAI GPT-5 Mini Key (beste Qualität)
- **Fallback:** Google Gemini (kostenlos, sehr gut)

---

## 🔍 Troubleshooting

### **Problem: "No embedding provider available"**

**Lösung:**
1. Prüfe ob API Keys gesetzt sind:
   ```bash
   echo $OPENAI_GPT5_MINI_API_KEY
   echo $GOOGLE_AI_API_KEY
   ```

2. Installiere Sentence Transformers:
   ```bash
   pip install sentence-transformers
   ```

### **Problem: "OpenAI API Key has no access to embeddings"**

**Lösung:**
- Verwende `OPENAI_GPT5_MINI_API_KEY` (hat Zugriff auf Embeddings)
- Oder verwende Google Gemini oder Sentence Transformers

### **Problem: "Collection dimension mismatch"**

**Lösung:**
- Lösche alte Collections mit falschen Dimensionen
- Starte neue Indexierung mit korrektem Provider

---

## 📚 Weiterführende Links

- **RAG Integration README:** `contexts/ragintegration/README.md`
- **PROJECT_RULES:** `docs/PROJECT_RULES.md`
- **Roadmap:** `docs/ROADMAP_DOCUMENT_UPLOAD.md`

---

**Last Updated:** 2025-10-31  
**Status:** ✅ Vollständig implementiert und getestet

