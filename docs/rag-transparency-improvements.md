# RAG Workflow Transparenz - Verbesserungsvorschläge

## 🎯 Ziel

Den RAG-Suchprozess transparenter gestalten, damit Benutzer verstehen:
- **Wie sich Treffer formen** (Embedding → Chunk-Auswahl → Ranking)
- **Warum bestimmte Chunks ausgewählt wurden** (Relevanz-Score, Hybrid-Scoring)
- **Welche Faktoren die beste Übereinstimmung beeinflussen** (Vektor-Ähnlichkeit, Text-Matching, RBAC-Filter)
- **Welche Wörter/Phrasen zur Relevanz beitragen** (Feature-Importance, SHAP-Werte)

---

## 📊 Aktueller Stand

### Bereits vorhanden:
- ✅ Relevanz-Score als Prozent (0-100%)
- ✅ Source References mit Dokument, Seite, Chunk-ID
- ✅ `RAGTransparencyLayer` Komponente
- ✅ Processing Time, Tokens Used, Model Used
- ✅ Query Parameters (top_k, score_threshold, use_hybrid_search)

### Fehlt noch:
- ❌ Detaillierte Anzeige des Suchprozesses (Schritt-für-Schritt)
- ❌ Visualisierung der Chunk-Rankings
- ❌ Vergleich zwischen verschiedenen Chunks
- ❌ Embedding-Ähnlichkeits-Details
- ❌ Hybrid-Score Aufschlüsselung (Vektor-Score vs. Text-Score)
- ❌ Feature-Importance (welche Wörter tragen zur Relevanz bei)

---

## 💡 Verbesserungsvorschläge

### 1. **Erweiterte Metadaten in Source References**

**Backend-Erweiterung:**
```python
class SourceReferenceResponse(BaseModel):
    # ... bestehende Felder ...
    
    # NEU: Detaillierte Score-Informationen
    vector_score: float  # Reine Vektor-Ähnlichkeit (0-1)
    text_score: float    # Text-Matching-Score (0-1)
    hybrid_score: float  # Kombinierter Score
    
    # NEU: Ranking-Informationen
    rank_position: int   # Position im Ranking (1 = bestes Ergebnis)
    total_candidates: int  # Anzahl der gefundenen Kandidaten vor Filtering
    
    # NEU: Filter-Informationen
    passed_rbac_filter: bool
    passed_score_threshold: bool
    
    # NEU: Chunk-Metadaten
    chunk_metadata: Dict[str, Any]
```

---

### 2. **SHAP-Integration für Feature-Importance**

#### **Was ist SHAP?**
SHAP (SHapley Additive exPlanations) ist ein Framework zur Erklärung von ML-Modell-Entscheidungen. Es zeigt, welche Features (Wörter/Phrasen) am meisten zur Vorhersage beitragen.

#### **Ist SHAP für RAG sinnvoll?**
**✅ Vorteile:**
- Zeigt welche Wörter im Chunk zur Relevanz beitragen
- Visualisiert Feature-Importance (Text-Highlighting)
- Erklärt warum ein Chunk ausgewählt wurde
- Wissenschaftlich fundiert (Shapley-Werte aus Spieltheorie)

**⚠️ Herausforderungen:**
- SHAP ist primär für klassische ML-Modelle (z.B. Random Forest, XGBoost)
- Embeddings sind hochdimensional (1536 dim bei OpenAI)
- Vector Search ist keine klassische ML-Vorhersage
- Berechnung kann rechenintensiv sein

#### **SHAP-Integration für RAG - Ansätze:**

**Ansatz 1: SHAP für Text-Matching-Score**
```python
# Erkläre Text-Matching-Score (nicht Embedding)
import shap
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# 1. Trainiere einfaches Modell auf Text-Matching
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform([chunk.text for chunk in chunks])
y = [chunk.text_score for chunk in chunks]

model = LogisticRegression()
model.fit(X, y)

# 2. Berechne SHAP-Werte
explainer = shap.LinearExplainer(model, X)
shap_values = explainer.shap_values(query_text)

# 3. Visualisiere welche Wörter wichtig sind
shap.plots.text(shap_values[0], query_text)
```

**Ansatz 2: SHAP für Hybrid-Score (Vektor + Text)**
```python
# Erkläre kombinierte Score-Berechnung
# Features: Vektor-Score, Text-Score, Chunk-Länge, etc.
features = [
    vector_score,
    text_score,
    len(chunk.text),
    chunk.metadata.confidence_score
]

# Trainiere Modell das Hybrid-Score vorhersagt
model = RandomForestRegressor()
model.fit(features, hybrid_scores)

# SHAP-Erklärung
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(features)
```

**Ansatz 3: Token-Level SHAP (für Embeddings)**
```python
# Erkläre Embedding-Ähnlichkeit auf Token-Ebene
# Zeige welche Tokens im Query-Embedding wichtig sind

# 1. Tokenisiere Query
tokens = tokenizer.tokenize(query)

# 2. Berechne Embedding für jeden Token
token_embeddings = [embedding_service.generate_embedding(token) for token in tokens]

# 3. Berechne SHAP-Werte für Token-Importance
# (vereinfachte Version: entferne Token und messe Score-Änderung)
shap_values = []
for token in tokens:
    query_without_token = query.replace(token, "")
    score_without = calculate_similarity(query_without_token, chunk)
    shap_value = original_score - score_without
    shap_values.append(shap_value)
```

#### **Empfehlung: Hybrid-Ansatz**

**Phase 1: Einfache Text-Highlighting (ohne SHAP)**
- Highlighte Wörter aus der Query im Chunk-Text
- Zeige TF-IDF-basierte Wichtigkeit
- Schnell umsetzbar, gute UX

**Phase 2: SHAP für Text-Matching (wenn nötig)**
- SHAP für Text-Score-Erklärung
- Zeigt welche Wörter zur Text-Ähnlichkeit beitragen
- Mittlerer Aufwand, gute Erklärbarkeit

**Phase 3: Erweiterte SHAP-Integration (optional)**
- Token-Level SHAP für Embeddings
- Feature-Importance für Hybrid-Score
- Höherer Aufwand, maximale Transparenz

---

### 3. **Suchprozess-Visualisierung (Step-by-Step)**

**Neue Komponente: `RAGSearchProcessVisualization`**

Zeigt den Suchprozess Schritt für Schritt:
- Query Embedding generiert
- Vector Search durchgeführt
- Hybrid Scoring angewendet
- RBAC-Filter angewendet
- Top-K Auswahl
- Chunks an LLM gesendet

---

### 4. **Chunk-Ranking-Visualisierung**

**Neue Komponente: `ChunkRankingChart`**

Balkendiagramm mit allen gefundenen Chunks:
- Score-Verteilung visualisiert
- Interaktive Hover-Tooltips
- Sortierbar nach verschiedenen Scores

---

### 5. **Text-Highlighting (Feature-Importance ohne SHAP)**

**Einfache Alternative zu SHAP:**

```tsx
// Highlighte Wörter aus Query im Chunk-Text
const highlightQueryWords = (chunkText: string, query: string) => {
  const queryWords = query.toLowerCase().split(/\s+/);
  const words = chunkText.split(/(\s+)/);
  
  return words.map((word, index) => {
    const wordLower = word.toLowerCase().replace(/[^\w]/g, '');
    if (queryWords.includes(wordLower)) {
      return <mark key={index} className="bg-yellow-200">{word}</mark>;
    }
    return word;
  });
};
```

**Erweiterte Version mit TF-IDF:**
```python
# Berechne TF-IDF für Chunk-Text
from sklearn.feature_extraction.text import TfidfVectorizer

vectorizer = TfidfVectorizer()
tfidf_scores = vectorizer.fit_transform([chunk.text])
feature_names = vectorizer.get_feature_names_out()

# Zeige Top-10 wichtigste Wörter
top_words = sorted(
    zip(feature_names, tfidf_scores[0].toarray()[0]),
    key=lambda x: x[1],
    reverse=True
)[:10]
```

---

## 🚀 Implementierungs-Priorität

### Phase 1 (Schnell umsetzbar):
1. ✅ **Erweiterte Metadaten in Source References** (Backend + Frontend)
2. ✅ **Score-Aufschlüsselung in Tooltip** (Vector-Score vs. Text-Score)
3. ✅ **Text-Highlighting** (Query-Wörter im Chunk-Text hervorheben)

### Phase 2 (Mittlerer Aufwand):
4. ✅ **Chunk-Ranking-Visualisierung** (Balkendiagramm)
5. ✅ **Erweiterte Source Reference Anzeige** (Chunk-Metadaten)
6. ✅ **TF-IDF-basierte Feature-Importance** (ohne SHAP)

### Phase 3 (Höherer Aufwand):
7. ✅ **Suchprozess-Visualisierung** (Step-by-Step)
8. ✅ **SHAP-Integration** (für Text-Matching-Score)
9. ✅ **Chunk-Vergleichsansicht** (Side-by-Side)

---

## 📊 SHAP vs. Einfache Alternativen

| Feature | SHAP | TF-IDF | Text-Highlighting |
|---------|------|--------|-------------------|
| **Aufwand** | Hoch | Mittel | Niedrig |
| **Genauigkeit** | Sehr hoch | Hoch | Mittel |
| **Performance** | Langsam | Schnell | Sehr schnell |
| **Erklärbarkeit** | Sehr gut | Gut | Gut |
| **Visualisierung** | Komplex | Einfach | Sehr einfach |

**Empfehlung:** Starte mit Text-Highlighting + TF-IDF, füge SHAP später hinzu wenn nötig.

---

## 📝 Nächste Schritte

1. **Backend-Erweiterung:**
   - `SourceReferenceResponse` Schema erweitern
   - Metadaten in `AskQuestionUseCase` sammeln
   - Text-Highlighting-Logik implementieren

2. **Frontend-Erweiterung:**
   - `RAGTransparencyLayer` erweitern
   - Text-Highlighting in Source References
   - Neue Komponenten: `ChunkRankingChart`, `RAGSearchProcessVisualization`

3. **SHAP-Integration (optional):**
   - SHAP-Bibliothek installieren (`pip install shap`)
   - SHAP-Explainer für Text-Matching implementieren
   - Visualisierung in Frontend

---

## 💬 Empfehlung

**Starte mit Phase 1 ohne SHAP:**
- Text-Highlighting ist schnell umsetzbar und gibt gute UX
- TF-IDF-basierte Feature-Importance ist ausreichend für die meisten Fälle
- SHAP kann später hinzugefügt werden wenn mehr Transparenz benötigt wird

**SHAP nur wenn:**
- Sehr detaillierte Erklärbarkeit benötigt wird
- Wissenschaftliche Validierung wichtig ist
- Performance keine Rolle spielt
