# 🔍 RAG-Suche Verhalten: Warum funktionieren spezifische Fragen schlechter?

## 📋 Beobachtetes Verhalten

**Frage 1:** "wie ist die beständigkeit gegen medinen beim loctite kleber?"
- ❌ Antwort: "keine spezifischen Informationen" (keine Referenz)

**Frage 2:** "wie ist die beständigkeit gegen medinen beim loctite kleber?" (nochmal)
- ⚠️ Antwort: Bekommt Link zum Datenblatt, aber sagt trotzdem "keine Informationen"

**Frage 3:** "Beständigkeit gegen Medien" (ohne "loctite" und "kleber")
- ✅ Antwort: Super ausgewertete Tabelle mit allen Medien!

---

## 🎯 Ursachen-Analyse

### Problem 1: **Over-Specification (Über-Spezifizierung)**

**Warum passiert das?**

1. **Embedding-Semantik:**
   - Vector Embeddings (z.B. OpenAI `text-embedding-3-small`) sind semantisch orientiert
   - "loctite kleber" wird als **Kombination** zweier Begriffe interpretiert
   - Der Embedding-Vektor für "loctite kleber" ist **nicht gleich** "loctite" + "kleber"
   - Im Dokument steht vielleicht:
     - ✅ "Loctite 648" (Produktname)
     - ✅ "Kleber" (allgemein)
     - ✅ "Beständigkeit gegen Medien" (Überschrift)
     - ❌ Aber **NICHT** "loctite kleber" als Kombination zusammen

2. **Hybrid Search Problematik:**
   - **Vector Search**: Sucht nach semantischer Ähnlichkeit
     - "loctite kleber" → niedriger Score wenn beide Begriffe nicht nahe beieinander stehen
   - **Text Search**: Sucht nach exakten Begriffen
     - Findet "loctite" ODER "kleber", aber nicht die Kombination

3. **Chunking-Strategie:**
   - Das Dokument wird in **Chunks** aufgeteilt
   - "Loctite" steht möglicherweise in Chunk 1 (Titel, Produktinfo)
   - "Beständigkeit gegen Medien" steht in Chunk X (Seite 2)
   - "kleber" steht möglicherweise in einem anderen Chunk
   - **Die Kombination "loctite kleber" findet keinen Chunk, der beide Begriffe zusammen enthält**

### Problem 2: **Exakte Begriffe funktionieren besser**

**Warum funktioniert "Beständigkeit gegen Medien" so gut?**

1. **Exakte Überschrift:**
   - "Beständigkeit gegen Medien" ist die **exakte Überschrift** im Dokument
   - Diese Überschrift wird wahrscheinlich im Chunking besonders hervorgehoben (Heading Hierarchy)
   - Vector Embeddings für Überschriften haben hohe Relevanz

2. **Semantische Klarheit:**
   - "Beständigkeit gegen Medien" ist ein **klarer Fachbegriff**
   - Keine Ambiguität, keine Kombination mehrerer Konzepte
   - Perfekt für Vector Search

3. **Besserer Chunk-Match:**
   - Der Chunk mit "Beständigkeit gegen Medien" enthält **genau diese Tabelle**
   - Die AI bekommt den vollständigen Kontext mit allen Medien
   - Keine Filterung durch irrelevante Begriffe

---

## 🔧 Warum "loctite" und "kleber" nicht helfen

**Theoretisch sollten sie helfen, aber:**

### 1. **Hybrid Search Relevanz-Scoring:**

Das System verwendet **Hybrid Search** (Vector + Text):

```
final_score = α * vector_score + β * text_score
```

- **Vector Score**: Semantische Ähnlichkeit
  - "loctite kleber" → niedrig wenn Begriffe nicht zusammen vorkommen
- **Text Score**: Exakte Textübereinstimmung
  - Findet "loctite" (score: 0.5) ODER "kleber" (score: 0.3)
  - Aber nicht die Kombination → kombiniertes Score niedrig

### 2. **Score Threshold:**

Das System verwendet `score_threshold = 0.01` (sehr niedrig):
- Bei über-spezifischen Fragen wird der Threshold möglicherweise nicht erreicht
- Oder die Chunks werden gefunden, aber mit niedriger Relevanz
- Die AI interpretiert niedrige Relevanz als "keine Informationen"

### 3. **Prompt-Interpretation:**

Die AI bekommt Chunks mit niedriger Relevanz:
```
Chunk 1: "Datenblatt: LOCTITE Produkt 648..." (Score: 0.02)
Chunk 2: "Beständigkeit gegen Medien: ..." (Score: 0.03)
```

Die AI sieht beide Chunks, aber:
- Chunk 1 hat niedrige Relevanz → AI denkt "nicht relevant"
- Chunk 2 hat bessere Relevanz, aber enthält nicht "loctite kleber" zusammen
- AI antwortet: "keine spezifischen Informationen"

**Bei "Beständigkeit gegen Medien":**
```
Chunk 1: "Beständigkeit gegen Medien: Motoröl 100%, Benzin 100%..." (Score: 0.9)
```

- Perfekter Match → Hohe Relevanz
- AI sieht komplette Tabelle → Perfekte Antwort

---

## 💡 Lösungsansätze

### Option 1: **Query Expansion** (Empfohlen)

Erweitere die Frage automatisch:

```
Original: "wie ist die beständigkeit gegen medinen beim loctite kleber?"

Expandiert:
- "Beständigkeit gegen Medien Loctite"
- "Beständigkeit gegen Medien Kleber"
- "Loctite 648 Beständigkeit"
- "Kleber Beständigkeit Medien"
```

**Status:** `MultiQueryService` ist im Code vorhanden, aber **nicht aktiviert** (Zeile 317 in `router.py`: `multi_query_service=None`)

### Option 2: **Query Normalization**

Normalisiere die Frage:
- Entferne redundante Begriffe ("loctite kleber" → "loctite" ODER "kleber")
- Erkenne Produktnamen ("loctite kleber" → "Loctite 648")
- Erkenne Fachbegriffe ("beständigkeit medien" → "Beständigkeit gegen Medien")

**Status:** Teilweise implementiert (`_normalize_question`), aber noch nicht optimal

### Option 3: **Hybrid Search Verbesserung**

Verbessere die Text-Search Komponente:
- **Boolean Search**: Finde Chunks mit "loctite" UND "kleber" (auch wenn nicht direkt zusammen)
- **Phrase Search**: Finde exakte Phrasen ("loctite kleber") mit höherem Score
- **Synonym-Erkennung**: "loctite" → "Loctite 648", "kleber" → "Klebstoff"

### Option 4: **Chunking-Strategie**

Verbessere das Chunking für Datenblätter:
- Erkenne Überschriften und behalte sie im Chunk
- Erkenne Produktnamen und verlinke sie mit relevanten Abschnitten
- Größere Chunks für zusammenhängende Informationen

---

## 🎯 Empfehlung

**Sofort umsetzbar:**

1. **MultiQueryService aktivieren** (Code bereits vorhanden!)
   ```python
   # In router.py Zeile 317:
   multi_query_service=rag_adapter.multi_query_service  # Statt None
   ```

2. **Query Normalization verbessern:**
   - Erkenne Produktnamen ("loctite kleber" → "Loctite 648")
   - Erkenne Fachbegriffe und normalisiere sie

3. **Debug-Logging erweitern:**
   - Zeige gefundene Chunks mit Scores
   - Zeige welche Query-Varianten verwendet wurden

**Mittelfristig:**

4. **Hybrid Search optimieren:**
   - Boolean-Search für Kombinationen
   - Phrase-Search für exakte Phrasen

5. **Chunking-Strategie für Datenblätter verbessern:**
   - Größere Chunks für zusammenhängende Informationen
   - Cross-Reference zwischen Chunks (Produktname → Tabellen)

---

## 📊 Zusammenfassung

**Warum "Beständigkeit gegen Medien" funktioniert:**
- ✅ Exakter Begriff (Überschrift im Dokument)
- ✅ Hoher Vector-Score (semantisch klar)
- ✅ Vollständiger Kontext im Chunk (Tabelle vorhanden)

**Warum "loctite kleber" nicht funktioniert:**
- ❌ Kombination zweier Begriffe (semantisch anders)
- ❌ Begriffe stehen nicht zusammen im Dokument
- ❌ Niedrige Vector-Scores durch Kombination
- ❌ Chunks enthalten nicht beide Begriffe zusammen

**Die JSON-Struktur funktioniert, weil:**
- Die AI bekommt strukturierte Daten aus dem Dokument
- Die Vision-AI extrahiert strukturierte Daten beim Indexieren
- Die AI kann diese Struktur perfekt nutzen für Tabellen-Formatierung

