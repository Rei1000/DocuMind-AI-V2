# AI Playground Context

> **Clean DDD Context für AI Model Testing**  
> **Version:** 2.7.3  
> **Stand:** 2025-11-17

## 🎯 Verantwortlichkeit

AI Playground ermöglicht das Testen und Vergleichen von AI-Modellen:
- ✅ **Connection Tests** - Prüfe API-Verbindungen zu Providern
- ✅ **Interactive Testing** - Teste Prompts mit einzelnen Modellen
- ✅ **Model Comparison** - Vergleiche mehrere Modelle parallel
- ✅ **Metrics** - Token Counts, Response Time

**Zugriff:** Nur für QMS Admin (`qms.admin@company.com`)

---

## 🏗️ Architektur

### DDD Layers

```
contexts/aiplayground/
├── domain/                  # Pure Business Logic (KEINE Dependencies!)
│   ├── entities.py         # TestResult, ConnectionTest
│   └── value_objects.py    # ModelConfig, Provider, ModelDefinition
│
├── application/            # Use Cases
│   └── services.py         # AIPlaygroundService
│
├── infrastructure/         # Technical Implementation
│   └── ai_providers/       # Provider Adapters
│       ├── base.py         # Abstract Base (Port)
│       ├── openai_adapter.py
│       └── google_adapter.py
│
└── interface/              # API Routes
    └── router.py           # FastAPI Router (mit Admin-Check)
```

### Dependency Flow

```
interface → application → domain
          ↘ infrastructure ↗
```

---

## 🤖 Unterstützte AI-Provider

### OpenAI
- GPT-4o Mini (Vision: High/Low Detail)
- GPT-5 Mini (Vision: High/Low Detail, separate API Key)
- **PDF Support:** PDF → PNG Conversion (pdf2image für erste Seite)

**Setup:** 
- `OPENAI_API_KEY` in `.env` (für GPT-4o Mini)
- `OPENAI_GPT5_MINI_API_KEY` in `.env` (für GPT-5 Mini)

### Google AI (Gemini)
- Gemini 2.5 Flash (Vision + Native PDF Support)
- **PDF Support:** Direkte PDF-Verarbeitung ohne Conversion

**Setup:** `GOOGLE_AI_API_KEY` in `.env`

---

## 📡 API Endpoints

### List Models
```
GET /api/ai-playground/models
```
Returns: Liste aller verfügbaren Modelle mit `is_configured` Flag

### Test Connection
```
POST /api/ai-playground/test-connection?model_id=gpt-4
```
Returns: Connection Test Result mit Latency

### Test Model
```
POST /api/ai-playground/test
{
  "model_id": "gpt-4",
  "prompt": "Explain quality management",
  "config": {
    "temperature": 0.7,
    "max_tokens": 1000
  },
  "image_data": "base64_encoded_image_or_pdf"  # Optional: Bild oder PDF
}
```
Returns: Test Result mit Response, Tokens, Response Time

**PDF Support:**
- Google Gemini: Native PDF-Unterstützung (direkte Verarbeitung)
- OpenAI: PDF → PNG Conversion (erste Seite wird konvertiert)
- Frontend: PDF Upload mit Dateiname-Anzeige (kein Preview)

### Compare Models
```
POST /api/ai-playground/compare
{
  "model_ids": ["gpt-4", "gemini-pro"],
  "prompt": "Explain quality management",
  "config": { ... }
}
```
Returns: Array von Test Results (eins pro Modell)

---

## 🎨 Frontend

**Location:** `/app/models/page.tsx`

**Features:**
- Model Selection (Single/Compare Mode)
- Interactive Prompt Input
- Configuration Panel (Temperature, Max Tokens, Top P)
- Connection Testing
- Live Results mit Metrics
- Side-by-Side Comparison

**Access:** http://localhost:3000/models

---

## 🔐 Permissions

**Requirement:** QMS Admin

Der Router prüft automatisch via `check_admin_permission()`:
- Email = `qms.admin@company.com`
- ODER `system_administration` in Permissions

Nicht-Admins bekommen `403 Forbidden`.

---

## 📊 Domain Model

### Entities (In-Memory, keine DB!)

#### TestResult
```python
@dataclass
class TestResult:
    model_name: str
    provider: str
    prompt: str
    response: str
    tokens_sent: int
    tokens_received: int
    response_time: float
    success: bool
    error_message: Optional[str]
```

#### ConnectionTest
```python
@dataclass
class ConnectionTest:
    provider: str
    model_name: str
    success: bool
    latency: Optional[float]
    error_message: Optional[str]
```

### Value Objects

#### ModelConfig
```python
@dataclass(frozen=True)
class ModelConfig:
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 1.0
    top_k: Optional[int] = None
```

#### Provider
```python
@dataclass(frozen=True)
class Provider:
    name: str
    display_name: str
    requires_api_key: bool
```

---

## 🛠️ Setup

### 1. Backend Dependencies

```bash
pip install openai==1.54.0 google-generativeai==0.8.3
```

### 2. Environment Variables

Erstelle `.env` im Project Root:

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Google AI
GOOGLE_AI_API_KEY=...

# JWT (existing)
SECRET_KEY=...
```

### 3. Start System

```bash
./start.sh local
```

### 4. Test API

```bash
# Login als QMS Admin
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"qms.admin@company.com","password":"Admin432!"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# Get Models
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/ai-playground/models

# Test Model
curl -X POST http://localhost:8000/api/ai-playground/test \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "gpt-3.5-turbo",
    "prompt": "What is quality management?",
    "config": {"temperature": 0.7, "max_tokens": 500}
  }'
```

---

## ✅ Status

- [x] Domain Model (Entities, Value Objects)
- [x] Provider Adapters (OpenAI, Google AI)
- [x] Application Service
- [x] API Routes (mit Admin-Check)
- [x] Frontend UI (Single + Compare Mode)
- [x] Token Metrics
- [x] Response Time Tracking
- [x] Error Handling

---

## 🔮 Future Enhancements

- [ ] Azure OpenAI Support
- [ ] Token Cost Calculation
- [ ] Usage History (optional persistence)
- [ ] Preset Prompts für QM-Szenarien
- [ ] Streaming Responses
- [ ] File Upload (für Vision Models)

---

## 📝 Entwickler-Notizen

**Design Decisions:**
- **In-Memory:** Keine DB-Persistierung (temporärer Playground)
- **Admin Only:** Schutz vor Kosten-Explosion
- **Synchron:** Einfacher als Streaming, ausreichend für Tests
- **DDD-First:** Strikte Layer-Trennung, testbar

**Port Pattern:**
- `AIProviderAdapter` ist das Port-Interface
- OpenAI/Google sind Adapter-Implementierungen
- Easy erweiterbar für neue Provider

**Testing:**
- Alle Provider-Calls sind async
- Error-Handling auf jedem Layer
- Graceful Degradation bei fehlenden API-Keys

---

**Version:** 2.7.3  
**Stand:** 2025-11-17  
**Author:** DocuMind-AI Team

