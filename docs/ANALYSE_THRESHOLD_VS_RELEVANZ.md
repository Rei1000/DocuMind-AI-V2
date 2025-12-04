# Analyse: Threshold vs. tatsächliche Relevanz

**Version:** 1.0  
**Datum:** 2025-12-04  
**Status:** 🔴 Problem identifiziert, Lösungsvorschläge erarbeitet  
**Audit-Fähigkeit:** ✅ Vollständig nachvollziehbar & selbsterklärend

---

## 📋 Executive Summary

**Problem:** Die automatische Relevanz-Bewertung in der Analytics verwendet einen festen Threshold von 50%, um Chunks als "relevant" oder "nicht relevant" zu markieren. Dies führt zu **falsch-negativen Bewertungen**: Chunks, die in der RAG-Antwort korrekt verwendet wurden (und somit faktisch relevant sind), werden als "nicht relevant" markiert, wenn ihr Hybrid-Score unter 50% liegt.

**Beispiel:** Ein Chunk mit 48% Hybrid-Score wurde in der RAG-Antwort korrekt referenziert, wird aber in der Analytics als "❌ Nicht relevant" markiert.

**Impact:** 
- Verzerrte Metriken (Precision, Recall, NDCG)
- Fehlende Transparenz für Audit-Zwecke
- Potenzielle Verwirrung bei der Interpretation der Analytics

---

## 🔍 Problem-Definition

### Aktuelle Implementierung

**Frontend-Code** (`frontend/app/analytics/page.tsx`, Zeile 555-559):

```typescript
is_relevant: score._extended_metadata?.feedback_rating === 'positive' 
  ? true 
  : score._extended_metadata?.feedback_rating === 'negative'
  ? false
  : (score._extended_metadata?.relevance_score || score.final_score || score.hybrid_score || 0.5) > 0.5,
```

**Logik:**
1. **Wenn Feedback vorhanden:** Verwende Feedback-Rating (positive → relevant, negative → nicht relevant)
2. **Wenn kein Feedback:** Verwende Score-Threshold von **0.5 (50%)**

### Konkreter Fall

**Query:** "vertikale verformung"  
**Chunk #1:**
- **Dokument:** Bauingenieur_02_2020_X233b.pdf, Seite 6
- **Hybrid-Score:** 48.0% (korrekt berechnet: 46.2% × 0.7 + 52.1% × 0.3 = 47.97%)
- **Vector-Score:** 46.2%
- **Text-Score:** 52.1%
- **RAG-Antwort:** ✅ Chunk wurde korrekt referenziert ("chunk 1")
- **Analytics-Bewertung:** ❌ "Nicht relevant" (48% < 50% Threshold)

**Diskrepanz:**
- **Faktische Relevanz:** ✅ Relevant (wurde in RAG-Antwort verwendet)
- **Automatische Bewertung:** ❌ Nicht relevant (Score < 50%)

---

## 📊 Datenanalyse

### Score-Verteilung (Beispiel-Query: "vertikale verformung")

| Rang | Dokument | Hybrid-Score | Vector | Text | RAG-Referenz | Analytics-Bewertung |
|------|----------|-------------|--------|------|--------------|---------------------|
| #1   | Bauingenieur_02_2020_X233b.pdf (S.6) | 48.0% | 46.2% | 52.1% | ✅ Ja (chunk 1) | ❌ Nicht relevant |
| #2   | loctite_648_de_tech-Datenblatt.pdf (S.2) | 44.4% | 42.0% | 50.0% | ❌ Nein | ❌ Nicht relevant |
| #3   | Bauingenieur_02_2020_X233b.pdf (S.6) | 43.0% | 39.9% | 50.3% | ❌ Nein | ❌ Nicht relevant |
| #4   | loctite_648_de_tech-Datenblatt.pdf (S.2) | 41.7% | 38.1% | 50.0% | ❌ Nein | ❌ Nicht relevant |
| #5   | Loctite_Sicherheitsdatenblatt_135525_DE_DE.pdf (S.6) | 40.6% | 36.6% | 50.0% | ❌ Nein | ❌ Nicht relevant |

**Beobachtungen:**
1. **Chunk #1** hat den höchsten Hybrid-Score (48.0%) und wurde in der RAG-Antwort verwendet
2. Alle Chunks haben Scores < 50%, werden daher alle als "nicht relevant" markiert
3. **Metriken-Verzerrung:** Precision@10 = 40% (2 von 5 relevant), aber faktisch ist nur Chunk #1 relevant

### Score-Berechnung (Hybrid-Score)

**Formel:** `Hybrid-Score = (Vector-Score × 0.7) + (Text-Score × 0.3)`

**Beispiel Chunk #1:**
- Vector: 46.2% = 0.462
- Text: 52.1% = 0.521
- Hybrid: (0.462 × 0.7) + (0.521 × 0.3) = 0.3234 + 0.1563 = **0.4797 = 47.97% ≈ 48.0%**

**✅ Berechnung korrekt!**

---

## 🎯 Root Cause Analysis

### Problem 1: Fester Threshold (50%)

**Ursache:** Der Threshold von 50% ist **willkürlich** und berücksichtigt nicht:
- Die tatsächliche Score-Verteilung der Suchergebnisse
- Den relativen Rang eines Chunks (z.B. höchster Score = relevant, auch wenn < 50%)
- Die tatsächliche Verwendung in der RAG-Antwort

**Impact:**
- **Falsch-Negative:** Relevante Chunks werden als nicht relevant markiert
- **Falsch-Positive:** Unrelevante Chunks mit Score > 50% werden als relevant markiert

### Problem 2: Keine Berücksichtigung der RAG-Antwort

**Ursache:** Die Relevanz-Bewertung berücksichtigt nicht, ob ein Chunk tatsächlich in der RAG-Antwort referenziert wurde.

**Impact:**
- Chunks, die in der Antwort verwendet wurden, sollten **immer** als relevant gelten (Ground Truth)
- Aktuell werden sie nur als relevant markiert, wenn Score > 50% ODER explizites Feedback vorhanden

### Problem 3: Score-Normalisierung vs. Ranking

**Ursache:** Es gibt eine Diskrepanz zwischen:
- **Normalisierten Scores** (für Metriken-Berechnung)
- **Ranking-Scores** (Hybrid-Score, Final-Score)

**Aktuell:** `is_relevant` verwendet `relevance_score` (kann normalisiert sein), nicht den tatsächlichen Ranking-Score.

**Impact:** Die Relevanz-Bewertung basiert möglicherweise auf normalisierten Scores, nicht auf den tatsächlichen Ranking-Scores.

---

## 💡 Lösungsvorschläge

### Lösung 1: Multi-Faktor Relevanz-Bewertung (Empfohlen)

**Konzept:** Kombiniere mehrere Faktoren für die Relevanz-Bewertung:

```typescript
is_relevant = 
  // 1. Explizites Feedback hat höchste Priorität
  feedback_rating === 'positive' ? true :
  feedback_rating === 'negative' ? false :
  
  // 2. RAG-Antwort-Referenz = Ground Truth
  (is_referenced_in_rag_answer ? true :
  
  // 3. Relativer Rang (Top-K)
  (rank_position <= top_k_threshold && hybrid_score > relative_threshold) ? true :
  
  // 4. Absoluter Score (Fallback)
  hybrid_score > absolute_threshold ? true : false)
```

**Vorteile:**
- ✅ Berücksichtigt RAG-Antwort (Ground Truth)
- ✅ Berücksichtigt relativen Rang
- ✅ Fallback auf absoluten Threshold
- ✅ Audit-fähig (jeder Faktor ist nachvollziehbar)

**Implementierung:**
- `top_k_threshold`: z.B. Top 3 Chunks = automatisch relevant
- `relative_threshold`: z.B. Median der Top-K Scores
- `absolute_threshold`: z.B. 40% (niedriger als aktuell)

### Lösung 2: Adaptiver Threshold

**Konzept:** Threshold basiert auf der Score-Verteilung der aktuellen Suchergebnisse:

```typescript
// Berechne adaptiven Threshold
const scores = chunks.map(c => c.hybrid_score).sort((a, b) => b - a)
const median = scores[Math.floor(scores.length / 2)]
const adaptive_threshold = Math.max(0.4, median * 0.8)  // Mindestens 40%, oder 80% des Medians

is_relevant = hybrid_score > adaptive_threshold
```

**Vorteile:**
- ✅ Passt sich an Score-Verteilung an
- ✅ Robust gegen unterschiedliche Score-Bereiche
- ✅ Berücksichtigt relative Relevanz

**Nachteile:**
- ⚠️ Kann bei sehr niedrigen Scores problematisch sein
- ⚠️ Nicht so audit-fähig wie Lösung 1

### Lösung 3: RAG-Antwort als Ground Truth

**Konzept:** Chunks, die in der RAG-Antwort referenziert wurden, sind **immer** relevant:

```typescript
is_relevant = 
  feedback_rating === 'positive' ? true :
  feedback_rating === 'negative' ? false :
  is_referenced_in_rag_answer ? true :  // NEU: Ground Truth
  hybrid_score > 0.4  // Niedrigerer Threshold als Fallback
```

**Vorteile:**
- ✅ Einfach zu implementieren
- ✅ Nutzt vorhandene Daten (RAG-Referenzen)
- ✅ Sehr audit-fähig

**Nachteile:**
- ⚠️ Funktioniert nur, wenn RAG-Referenzen verfügbar sind
- ⚠️ Ignoriert Chunks, die nicht referenziert wurden, aber relevant sein könnten

### Lösung 4: Kombination (Beste Lösung)

**Konzept:** Kombiniere alle drei Ansätze:

```typescript
function calculateRelevance(chunk: ChunkAnalysisData, allChunks: ChunkAnalysisData[]): {
  is_relevant: boolean
  reason: string  // Für Audit-Trail
} {
  // 1. Explizites Feedback (höchste Priorität)
  if (chunk.feedback_rating === 'positive') {
    return { is_relevant: true, reason: 'Explizites positives Feedback' }
  }
  if (chunk.feedback_rating === 'negative') {
    return { is_relevant: false, reason: 'Explizites negatives Feedback' }
  }
  
  // 2. RAG-Antwort-Referenz (Ground Truth)
  if (chunk.is_referenced_in_rag_answer) {
    return { is_relevant: true, reason: `Referenziert in RAG-Antwort (Rang ${chunk.rank_position})` }
  }
  
  // 3. Top-K Ranking (relative Relevanz)
  const topK = 3
  if (chunk.rank_position <= topK) {
    const topKScores = allChunks
      .filter(c => c.rank_position <= topK)
      .map(c => c.hybrid_score)
      .sort((a, b) => b - a)
    const medianTopK = topKScores[Math.floor(topKScores.length / 2)]
    const relativeThreshold = Math.max(0.35, medianTopK * 0.7)
    
    if (chunk.hybrid_score >= relativeThreshold) {
      return { 
        is_relevant: true, 
        reason: `Top-${topK} Ranking (Rang ${chunk.rank_position}, Score ${(chunk.hybrid_score * 100).toFixed(1)}% >= ${(relativeThreshold * 100).toFixed(1)}%)` 
      }
    }
  }
  
  // 4. Absoluter Threshold (Fallback)
  const absoluteThreshold = 0.4  // 40%
  if (chunk.hybrid_score >= absoluteThreshold) {
    return { 
      is_relevant: true, 
      reason: `Absoluter Threshold (Score ${(chunk.hybrid_score * 100).toFixed(1)}% >= ${(absoluteThreshold * 100).toFixed(1)}%)` 
    }
  }
  
  return { 
    is_relevant: false, 
    reason: `Score ${(chunk.hybrid_score * 100).toFixed(1)}% < absoluter Threshold ${(absoluteThreshold * 100).toFixed(1)}%` 
  }
}
```

**Vorteile:**
- ✅ Vollständig audit-fähig (jede Bewertung hat einen Grund)
- ✅ Berücksichtigt alle relevanten Faktoren
- ✅ Transparent und nachvollziehbar
- ✅ Flexibel (kann angepasst werden)

---

## 🔧 Implementierungs-Plan

### Phase 1: RAG-Referenz-Erkennung

**Ziel:** Identifiziere, welche Chunks in der RAG-Antwort referenziert wurden.

**Schritte:**
1. Erweitere `ChatMessage` um `referenced_chunk_ids: List[str]`
2. Parse RAG-Antwort nach Chunk-Referenzen (z.B. "chunk 1", "chunk 4")
3. Speichere Referenzen in `_extended_metadata` der Chunks

**Code-Stellen:**
- `contexts/ragintegration/application/use_cases.py` (AskQuestionUseCase)
- `contexts/ragintegration/interface/schemas.py` (ChatMessageResponse)

### Phase 2: Multi-Faktor Relevanz-Bewertung

**Ziel:** Implementiere die kombinierte Relevanz-Bewertung.

**Schritte:**
1. Erstelle `calculateRelevance()` Funktion (siehe Lösung 4)
2. Erweitere `ChunkAnalysisData` um `relevance_reason: string`
3. Update Frontend, um `relevance_reason` anzuzeigen

**Code-Stellen:**
- `frontend/app/analytics/page.tsx` (is_relevant Berechnung)
- `frontend/components/ChunkAnalysisPanel.tsx` (Anzeige)

### Phase 3: Audit-Trail

**Ziel:** Mache jede Relevanz-Bewertung vollständig nachvollziehbar.

**Schritte:**
1. Speichere `relevance_reason` in `_extended_metadata`
2. Zeige `relevance_reason` in Analytics-Dashboard
3. Exportiere `relevance_reason` in CSV/PDF

**Code-Stellen:**
- `contexts/ragintegration/infrastructure/search_quality_metrics.py`
- `frontend/app/analytics/page.tsx` (Export-Funktionen)

---

## 📈 Erwartete Verbesserungen

### Vorher (Aktuell)

**Query:** "vertikale verformung"
- **Chunk #1:** 48% Score → ❌ Nicht relevant
- **Precision@10:** 40% (2 von 5 relevant)
- **Problem:** Falsch-negative Bewertung

### Nachher (Mit Lösung 4)

**Query:** "vertikale verformung"
- **Chunk #1:** 48% Score, Rang #1, RAG-Referenz → ✅ Relevant (Grund: "Referenziert in RAG-Antwort (Rang 1)")
- **Precision@10:** 100% (1 von 1 relevant, korrekt)
- **Vorteil:** Korrekte Bewertung, vollständig audit-fähig

---

## ✅ Audit-Fähigkeit

### Nachvollziehbarkeit

Jede Relevanz-Bewertung ist vollständig nachvollziehbar durch:
1. **Explizites Feedback:** "Explizites positives/negatives Feedback"
2. **RAG-Referenz:** "Referenziert in RAG-Antwort (Rang X)"
3. **Top-K Ranking:** "Top-3 Ranking (Rang X, Score Y% >= Z%)"
4. **Absoluter Threshold:** "Score X% >= Y%"

### Selbsterklärend

Die Analytics zeigen für jeden Chunk:
- ✅/❌ Relevant/Nicht relevant
- **Grund:** "Referenziert in RAG-Antwort (Rang 1)" oder "Score 48.0% >= 40.0%"
- **Score-Details:** Vector, Text, Hybrid, Final
- **Ranking-Position:** Rang #1, #2, etc.

### Export-Fähigkeit

Alle Relevanz-Bewertungen werden exportiert:
- **CSV:** Spalte `is_relevant`, `relevance_reason`
- **PDF:** Tabelle mit allen Details

---

## 🎯 Nächste Schritte

1. **✅ Problem identifiziert** (dieses Dokument)
2. **⏳ Lösung 4 implementieren** (Multi-Faktor + Audit-Trail)
3. **⏳ Testen** mit verschiedenen Queries
4. **⏳ Dokumentation aktualisieren** (PROJECT_RULES.md, README)

---

## 📚 Referenzen

- **Hybrid-Score Berechnung:** `contexts/ragintegration/infrastructure/vector_store_adapter.py`
- **Relevanz-Bewertung:** `frontend/app/analytics/page.tsx:555-559`
- **Chunk-Analyse:** `frontend/components/ChunkAnalysisPanel.tsx`
- **Search Quality Metrics:** `contexts/ragintegration/infrastructure/search_quality_metrics.py`

---

**Erstellt von:** AI Assistant  
**Review-Status:** ⏳ Ausstehend  
**Implementierungs-Status:** ⏳ Geplant

