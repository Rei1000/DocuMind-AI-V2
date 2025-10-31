# Dokumenttyp-spezifische AI-Prompts für RAG-Chat

## Übersicht

Das System verwendet **zwei Arten von Prompts**:

1. **Standard-Prompts** (in Datenbank `prompt_templates`)
   - Werden für **Vision-AI Extraktion** verwendet
   - Definieren die JSON-Struktur für Dokumenttypen
   - Beispiel: "Extrahiere nodes für Flussdiagramm", "Extrahiere steps für Arbeitsanweisung"

2. **AI-Prompts für RAG-Chat** (dynamisch generiert)
   - Werden für **Chat-Antworten** verwendet
   - Werden automatisch aus Standard-Prompts abgeleitet
   - Werden im Code definiert, nicht in der Datenbank

## Wie funktioniert es?

### Schritt 1: Standard-Prompt wird geladen

Wenn eine Frage im RAG-Chat gestellt wird:

1. System extrahiert `document_type` aus den gefundenen Chunks
2. System lädt den **aktiven Standard-Prompt** für diesen Dokumenttyp aus `prompt_templates` Tabelle:
   ```sql
   SELECT pt.prompt_text
   FROM prompt_templates pt
   JOIN document_types dt ON pt.document_type_id = dt.id
   WHERE dt.name = 'Arbeitsanweisung' 
   AND pt.status = 'active'
   ```

### Schritt 2: Prompt-Struktur wird analysiert

Der `prompt_text` des Standard-Prompts wird analysiert:

```python
# In ai_service.py, _get_document_type_prompt_instructions()

if '"nodes"' in prompt_text:
    # Flussdiagramm-Detektion
    return "ANWEISUNGEN (Flussdiagramm): ..."

elif '"steps"' in prompt_text and '"step_number"' in prompt_text:
    # Arbeitsanweisung-Detektion
    return "ANWEISUNGEN (Arbeitsanweisung): ..."

elif '"process_steps"' in prompt_text:
    # SOP/Prozess-Detektion
    return "ANWEISUNGEN (SOP/Prozess): ..."
```

### Schritt 3: Dokumenttyp-spezifischer AI-Prompt wird erstellt

Basierend auf der erkannten Struktur wird ein spezifischer Prompt erstellt:

#### Arbeitsanweisung (wenn `"steps"` + `"step_number"` erkannt)
```
ANWEISUNGEN (Arbeitsanweisung):
1. Beantworte die Frage präzise basierend auf den konkreten Schritten und Anweisungen
2. Verwende die exakten Schrittnummern und Beschreibungen aus dem Dokument
3. Wenn nach spezifischen Informationen gefragt wird (z.B. Artikelnummern), gib diese EXAKT aus dem Dokument an
4. Fokussiere dich auf die relevanten Textpassagen - vermeide unnötige Erklärungen
5. Antworte auf Deutsch, kurz und präzise - nur die relevanten Informationen
6. Wenn die Antwort nicht im Kontext steht, sage das ehrlich
7. WICHTIG: Referenzen direkt im Text
```

#### Flussdiagramm (wenn `"nodes"` erkannt)
```
ANWEISUNGEN (Flussdiagramm):
1. Beantworte die Frage präzise basierend auf dem Prozessfluss und den Entscheidungspunkten
2. Fokussiere dich auf die relevanten Schritte und Entscheidungen im Prozess
3. Verwende konkrete Informationen aus den Nodes und Verbindungen
...
```

#### SOP/Prozess (wenn `"process_steps"` erkannt)
```
ANWEISUNGEN (SOP/Prozess):
1. Beantworte die Frage präzise basierend auf den Prozessschritten und Compliance-Anforderungen
2. Verwende die konkreten Prozessschritte und kritischen Regeln aus dem Dokument
...
```

## Wo werden die Prompts verwaltet?

### Standard-Prompts (Vision-AI)
- **Speicherort:** Datenbank-Tabelle `prompt_templates`
- **Verwaltung:** Über `/prompt-management` Frontend
- **Status:** `active`, `draft`, `archived`
- **Zweck:** Definieren JSON-Struktur für Vision-AI Extraktion

### AI-Prompts für RAG-Chat
- **Speicherort:** Code in `contexts/ragintegration/infrastructure/ai_service.py`
- **Verwaltung:** Code-basiert, wird automatisch aus Standard-Prompts abgeleitet
- **Zweck:** Optimierte Chat-Antworten basierend auf Dokumenttyp

## Prompt v2.9 für Arbeitsanweisungen (PRODUKTIONSREIF)

**Version:** 2.9  
**Status:** ✅ Produktionsreif (Excellence Level: 9.0/10 mit GPT-5 Mini)  
**Standard-Prompt:** Aktiv für "Arbeitsanweisung" Dokumenttyp

### ⭐ Neue Features in v2.9:

#### 1. **Systematischer Labels-Mapping-Check**
- **Buchstabenlabels (a, b, c, d):** Werden in `visual_elements[*].labels[]` gemappt
- **Ziffernlabels (1, 2, 3, 4):** Werden ebenfalls erfasst und gemappt
- **Vollständigkeitscheck:** Anzahl Labels in `visual_elements[*].labels[]` ≥ Anzahl in `article_data[*].labels`
- **Kritisch für RAG:** Ermöglicht präzise Bild-zu-Text-Verknüpfung bei Fragen wie "Was ist bei Label a?"
- **Systematischer Prozess:** Iteriert durch jeden Artikel mit Label und prüft visuelle Sichtbarkeit

#### 2. **Consumables hazard_notes Pflicht**
- **Kritische Regel:** Wenn Sicherheitshinweise zu Chemikalien/Klebern im Text stehen, MÜSSEN diese in `consumables[].hazard_notes` übertragen werden (nicht leer lassen!)
- **Beispiel:** Text enthält "Achtung! Sicherheitsvorschriften z.B. offenes Fenster, Abzug und Handschuhe beachten" → `consumables[].hazard_notes` = "Offenes Fenster, Abzug und Handschuhe beachten"
- **RAG-Vorteil:** Ermöglicht Fragen wie "Welche Sicherheitshinweise gibt es zu Aceton?"

#### 3. **Description-Bereinigung**
- **Aufzählungszeichen entfernen:** Entfernt Aufzählungszeichen (1., 2., a), b), etc.) aus `description`
- **Ergebnis:** Nur reine Arbeitsanweisung ohne Nummerierung
- **Vorteil:** Saubere, lesbare Chunks ohne Redundanz

#### 4. **Safety Instructions Topics trennen**
- **WICHTIG:** Jedes Topic in `safety_instructions` als separater Eintrag - nicht kombinieren
- **Beispiel:** "Belüftung" und "Handschutz" getrennt, nicht "Belüftung und PSA"
- **Vorteil:** Präzisere RAG-Suche nach einzelnen Sicherheitsthemen

#### 5. **Erweiterte Artikelnummern-Format-Erkennung**
- Unterstützt: `XX-XX-XXX`, `XXX.XXX.XXX`, reine Zahlenfolgen, andere Bindestrich-Strukturen
- Normierung: Unbekannte Formate → `art_nr: "unknown"` + `notes: "raw_art_nr: <Original>"`

#### 6. **Erweiterte Mengeneinheiten**
- Unterstützt: `pcs`, `ml`, `g`, `kg`, `m`, `cm`, etc.
- Standard: `pcs` (Stück)

**Dokumentation:** Siehe `docs/PROMPT_ARBEITSANWEISUNG_V2.9.md` für vollständigen Prompt-Text

**Vergleichs-Prompt:** Siehe `docs/PROMPT_COMPARISON_OPTIMIZED.md` für Modell-Evaluierung

## Automatische Dokumenttyp-Erkennung

### Flow im `AskQuestionUseCase`:

```python
# 1. Chunks werden gefunden (mit Metadaten)
context_chunks = self._manage_context_window(unique_results)

# 2. Dokumenttyp wird aus Chunk-Metadaten extrahiert
first_chunk = context_chunks[0]
metadata = first_chunk.get('metadata', {})
document_type = metadata.get('document_type')  # z.B. "Arbeitsanweisung"

# 3. Dokumenttyp wird an AI-Service übergeben
ai_response = await self.ai_service.generate_response_async(
    question=question,
    context_chunks=context_chunks,
    model_id=model_id,
    document_type=document_type  # <-- Wichtig!
)

# 4. AI-Service lädt Standard-Prompt und erstellt spezifischen Prompt
prompt = self._create_structured_rag_prompt(
    question, 
    context_text, 
    document_type  # <-- Wird analysiert
)
```

## Vorteile dieses Systems

1. **Konsistenz:** Nutzt dieselbe Prompt-Struktur wie Vision-AI
2. **Automatisch:** Keine manuelle Konfiguration nötig
3. **Skalierbar:** Neue Dokumenttypen funktionieren automatisch (wenn Standard-Prompt existiert)
4. **Präzise:** Jeder Dokumenttyp bekommt optimierte Anweisungen

## Beispiel

### Szenario: Frage zu Arbeitsanweisung

1. **User fragt:** "Welche Artikelnummer hat die Passfeder?"
2. **System findet Chunks** mit `document_type: "Arbeitsanweisung"`
3. **System lädt Standard-Prompt** für "Arbeitsanweisung"
4. **System analysiert:** Findet `"steps"` + `"step_number"` → erkennt Arbeitsanweisung
5. **System erstellt Prompt:** "ANWEISUNGEN (Arbeitsanweisung): Kurz, präzise, EXAKT..."
6. **AI antwortet:** "Die Artikelnummer der Passfeder ist 123.456.789. **Referenz**: chunk 1"

### Szenario: Frage zu Flussdiagramm

1. **User fragt:** "Wann ist es ein wiederkehrender Fehler?"
2. **System findet Chunks** mit `document_type: "Flussdiagramm"`
3. **System lädt Standard-Prompt** für "Flussdiagramm"
4. **System analysiert:** Findet `"nodes"` → erkennt Flussdiagramm
5. **System erstellt Prompt:** "ANWEISUNGEN (Flussdiagramm): Prozessfluss, Entscheidungspunkte..."
6. **AI antwortet:** "Ein Fehler ist wiederkehrend wenn ≥ 3 mal pro Quartal. **Referenz**: chunk 1"

## Probleme die gelöst werden

### Vorher (Probleme):
- ❌ Ein generischer Prompt für alle Dokumenttypen
- ❌ Zu viel "Gelaber" in Antworten
- ❌ Unpräzise Antworten für Arbeitsanweisungen
- ❌ Prompt für Flussdiagramm funktioniert nicht für Arbeitsanweisungen

### Jetzt (Lösung):
- ✅ Dokumenttyp-spezifische Prompts
- ✅ Präzise, kurze Antworten für Arbeitsanweisungen
- ✅ Fokus auf Prozessfluss für Flussdiagramme
- ✅ Automatische Anpassung basierend auf Standard-Prompt-Struktur

## Technische Details

### Dateien:

1. **`contexts/ragintegration/infrastructure/ai_service.py`**
   - `_get_document_type_prompt_instructions()` - Analysiert Standard-Prompt
   - `_get_active_standard_prompt()` - Lädt aus Datenbank
   - `_create_structured_rag_prompt()` - Erstellt finalen Prompt

2. **`contexts/ragintegration/application/use_cases.py`**
   - `AskQuestionUseCase.execute()` - Extrahiert document_type und übergibt an AI-Service

3. **Datenbank:**
   - `prompt_templates` - Speichert Standard-Prompts
   - `document_types` - Dokumenttypen

