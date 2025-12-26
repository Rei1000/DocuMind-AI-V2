# RAG Chat System - Benutzerhandbuch

> **Version:** 2.9.3  
> **Stand:** 2025-12-05

## Übersicht

Das RAG Chat System ermöglicht es Benutzern, Fragen zu indexierten Dokumenten zu stellen und intelligente Antworten basierend auf dem Dokumenteninhalt zu erhalten. Das System verwendet Machine Learning und SHAP-Analysen für optimale Suchergebnisse.

## 🆕 Neue Features in v2.9.3

### **🧩 Analytics Story Mode (NEU v2.9.3)**
- **Einfach erklärt:** Kindgerechte Erklärung, warum ein Chunk #1 ist (Finden → Mischen → Lernen → Final)
- **Pro / Details:** Umschalten auf technische Ansicht (Scores/SHAP/System)
- **Wichtig:** Das Analytics Dashboard zeigt automatisch die Analytics-Daten der **letzten** RAG-Chat-Anfrage

### **🧠 Robustere SHAP Analytics (NEU v2.9.3)**
- SHAP/Explainability nutzt bevorzugt die **gespeicherten Source-References** der letzten passenden Antwort
- Dadurch sind SHAP-Auswertungen stabiler als „nur Live-Search“

## 🆕 Neue Features in v2.9.2

### **🔧 Konfigurierbare Filter (NEU v2.9.2)**
- **Initialer Score-Filter:** Regelbarer Slider (0-5%) für Mindest-Hybrid-Score während der Suche
  - Filtert einzelne Chunks während der Suche heraus (pro Chunk)
  - Standard: 0% (keine Filterung)
  - Empfohlen: 1-2% für bessere Relevanz
- **Adaptive Filterung:** Zwei regelbare Slider für optimale Suchergebnisse
  - **Mindest-Durchschnitts-Score (0-50%):** Filtert Chunks wenn der durchschnittliche Score zu niedrig ist
  - **Mindest-Maximal-Score (0-50%):** Filtert Chunks wenn der beste Chunk zu unrelevant ist
  - **Filter-Reihenfolge:** Initialer Filter (während Suche) → Adaptive Filter (nach Suche)
  - **Info-Box:** Erklärt Filter-Reihenfolge und gibt Empfehlungen
- **Verbesserte Tooltips:** Standardisierte Tooltip-Darstellung mit vollständigen Metadaten
  - Zeigt alle Filter-Einstellungen (Initialer Score-Filter, Adaptive Filterung, AI-Modell-Einstellungen)
  - Positionierung: Linksbündig mit Überlauf-Schutz
- **Verwendung:** Öffnen Sie das Filter Panel im RAG Chat, um Filter-Einstellungen anzupassen

## 🆕 Neue Features in v2.9.1

### **🔧 Default-Prompts bearbeitbar (NEU v2.9.1)**
- **Default-Prompts anzeigen:** Default RAG Chat Prompts werden im FilterPanel angezeigt, auch wenn kein Dokumententyp ausgewählt ist
- **Default-Prompts bearbeiten:** Level 4+ können Default-Prompts bearbeiten (RAG Chat Prompt und Multi-Query Prompt)
- **Gleiche Darstellung:** Default-Prompts haben die gleiche Darstellung wie dokumenttyp-spezifische Prompts
- **Verwendung:** Öffnen Sie das "RAG Chat Prompt (Standard)" Panel im FilterPanel, um Default-Prompts zu bearbeiten

### **💬 Chunk-Level Feedback (NEU v2.9.1)**
- **Detailliertes Feedback:** Bewerten Sie einzelne Chunks in RAG-Antworten (positive, negative, neutral)
- **Präzisere Metriken:** Chunk-Level Feedback ermöglicht genauere Search Quality Metrics
- **Bessere ML-Training-Daten:** Ihr Feedback verbessert automatisch das ML-Ranking
- **Verwendung:** Klicken Sie auf "Relevant" oder "Nicht relevant" bei jedem Chunk im Analytics Dashboard

### **📈 Search Quality Metrics & Analytics (NEU v2.9.0)**
- **Automatisches Tracking:** Metriken (Precision@k, Recall@k, NDCG@k, MRR) für jede Query
- **Trend-Analyse:** Interaktive Charts zeigen Qualitätsentwicklung über Zeit
- **Alert-System:** Automatische Warnung bei Qualitätsverschlechterungen (>10%)
- **Analytics Dashboard:** Umfassende Analyse mit SHAP-Feature-Importance, Score-Charts, Chunk-Analyse

### **🧠 SHAP-Integration (NEU v2.6.0)**
- **Feature Importance:** Verstehen Sie, welche Features zum Ranking-Score beitragen
- **Waterfall Charts:** Visuelle Darstellung der SHAP-Werte für jeden Chunk
- **Interactive Dashboard:** Analytics-Seite mit detaillierten SHAP-Analysen

### **🤖 Machine Learning Ranking (NEU v2.7.0)**
- **Learning-to-Rank:** ML-Modell optimiert Suchergebnisse automatisch
- **11 Features:** Vector-Score, Text-Score, BM25, Keyword-Matches, Chunk-Länge, etc.
- **Automatisches Training:** ML-Modell wird täglich mit neuen Feedback-Daten trainiert
- **Final Score:** Kombination aus Hybrid-Score (60%) und ML-Score (40%)

### **✂️ Chunk-Editor (Level 4+)**
- **Chunk-Vorschau:** Alle Chunks eines Dokuments anzeigen
- **Chunk bearbeiten:** Text direkt im Chunk ändern
- **Chunk splitten:** Lange Chunks in zwei Teile aufteilen
  - ⭐ **Overlap-Funktion:** 0-10 Overlap-Sätze zwischen gesplitteten Chunks
  - ⭐ **Intelligente Satz-Erkennung:** Automatische Satz-Trennung für Overlap
- **Chunks zusammenführen:** Zwei benachbarte Chunks zu einem zusammenführen
- **Chunk löschen:** Chunk aus Datenbank und Vector Store entfernen

### **📊 Strukturiertes Chunking**
- **Fachartikel:** JSON wird in lesbaren Text konvertiert
- **Diagramm-Beschreibung:** Figuren und Tabellen werden in Chunks integriert
- **Markdown-Rendering:** Tabellen, Info-Boxen, Code-Blöcke werden korrekt formatiert

## Grundfunktionen

### Chat-Sessions

- **Session-Verwaltung**: Chat-Sessions werden automatisch persistiert. Beim Wechsel zwischen Seiten bleibt die ausgewählte Session erhalten.
- **Neue Session erstellen**: Klicken Sie auf "Neue Session" im Sidebar
- **Session auswählen**: Klicken Sie auf eine Session in der Sidebar
- **Session löschen**: Klicken Sie auf das Löschen-Icon neben einer Session

### Chat-Messages

- **Nachricht senden**: Geben Sie Ihre Frage in das Eingabefeld ein und drücken Sie Enter oder klicken Sie auf "Senden"
- **LLM-Model wählen**: Wählen Sie ein AI-Modell aus dem Dropdown (z.B. GPT-4o Mini, Gemini 2.5 Flash)
- **Model pro Nachricht**: Jede Antwort wird mit dem zum Zeitpunkt der Erstellung verwendeten Model gespeichert und angezeigt

## ✂️ Chunk-Editor (Level 4+)

### **Chunk-Vorschau**

1. Öffnen Sie ein indexiertes Dokument in der Dokument-Detail-Ansicht
2. Scrollen Sie zum **"Chunk Preview Panel"**
3. Sehen Sie alle Chunks des Dokuments mit:
   - **Chunk-Text:** Vollständiger Text des Chunks
   - **Metadaten:** Seiten-Nummern, Token-Count, Satz-Count, Overlap-Status
   - **Overlap-Badge:** Grünes Badge mit "Overlap: X Sätze" für gesplittete Chunks
   - **3-Stufen-Expansion:**
     - **Zugeklappt:** Nur Header sichtbar
     - **Vorschau:** Erste 500 Zeichen + Gesamt-Zeichenanzahl
     - **Vollständig:** Kompletter Chunk-Text
   - **Erweitern/Verkleinern:** Klicken Sie auf einen Chunk, um Details zu sehen

### **Chunk bearbeiten**

1. Klicken Sie auf **"Bearbeiten"** bei einem Chunk
2. Ändern Sie den Text direkt im Editor
3. Klicken Sie auf **"Speichern"**
4. Der Chunk wird in der Datenbank und im Vector Store aktualisiert

### **Chunk splitten**

1. Klicken Sie auf **"Splitten"** bei einem Chunk
2. **Split-Modal öffnet sich** mit folgenden Optionen:
   - **Split-Position:** Wählen Sie nach welchem Satz gesplittet werden soll (Slider)
   - **Overlap-Sätze:** Wählen Sie 0-10 Overlap-Sätze (Slider)
   - **Live-Vorschau:** Beide resultierenden Chunks werden angezeigt
     - Chunk 1: Zeigt die ersten N Sätze (endet am Split-Punkt)
     - Chunk 2: Zeigt die Overlap-Sätze (grün markiert) + restliche Sätze
3. **Overlap-Funktionsweise:**
   - Die letzten N Sätze von Chunk 1 werden am **Anfang** von Chunk 2 hinzugefügt
   - Chunk 1 bleibt unverändert (endet am Split-Punkt)
   - **Vorteil:** Bessere Kontext-Erhaltung für Vector Search
4. Klicken Sie auf **"Chunk splitten"**
5. Der Chunk wird in zwei Chunks aufgeteilt
6. Beide Chunks erhalten `has_overlap: true` und `overlap_sentence_count: N` in den Metadaten
7. Das Overlap-Badge wird in der Chunk-Vorschau angezeigt

### **Chunks zusammenführen**

1. Wählen Sie zwei benachbarte Chunks aus
2. Klicken Sie auf **"Zusammenführen"**
3. Die beiden Chunks werden zu einem Chunk zusammengeführt
4. Der neue Chunk wird in der Datenbank und im Vector Store aktualisiert

### **Chunk löschen**

1. Klicken Sie auf **"Löschen"** bei einem Chunk
2. Bestätigen Sie die Löschung
3. Der Chunk wird aus der Datenbank und dem Vector Store entfernt

**Hinweis:** Chunk-Editor-Funktionen sind nur für Level 4+ (QM-Mitarbeiter) verfügbar.

---

## Erweiterte Suche

### Schnellsuche

Die **Schnellsuche** ermöglicht es, einen Suchbegriff einzugeben, der als zusätzlicher Kontext zu Ihrer Frage verwendet wird.

**Verwendung:**
1. Geben Sie einen Suchbegriff in das "Schnellsuche..." Feld ein (z.B. "Sicherheitshinweise")
2. Stellen Sie Ihre Frage wie gewohnt
3. Die Schnellsuche wird automatisch als Kontext zur Frage hinzugefügt

**Beispiel:**
- Schnellsuche: "Sicherheitshinweise"
- Frage: "Was muss ich beachten?"
- Effektive Frage an das System: "Sicherheitshinweise. Was muss ich beachten?"

### Filter-Optionen

#### Dokumenttyp-Filter

- **Auswahl**: Wählen Sie einen Dokumenttyp aus dem Dropdown
- **Counts**: Die Anzahl zeigt, wie viele indexierte Dokumente dieses Typs vorhanden sind
- **Verwendung**: Filtert die Suche auf Dokumente des gewählten Typs

#### Datumsbereich-Filter

- **Von/Bis**: Wählen Sie einen Datumsbereich aus
- **Verwendung**: Filtert die Suche auf Dokumente innerhalb des gewählten Zeitraums

#### Seitenzahlen-Filter

- **Hinzufügen**: Geben Sie eine Seitenzahl ein und drücken Sie Enter
- **Entfernen**: Klicken Sie auf das X-Icon neben einer Seitenzahl
- **Verwendung**: Sucht nur in den angegebenen Seiten

#### Confidence-Threshold

- **Einstellung**: Schieberegler für Mindest-Relevanz-Score (0.0 - 1.0)
- **Standard**: 0.7
- **Verwendung**: Nur Suchergebnisse mit mindestens diesem Score werden verwendet

#### Hybrid Search

- **Aktivieren/Deaktivieren**: Toggle für Hybrid Search
- **Was ist Hybrid Search?**: Kombiniert semantische Vektor-Suche (Bedeutung) mit Text-basierter Suche (exakte Begriffe) für bessere Ergebnisse

#### RAG Chat Prompts (Level 4+)

- **Default-Prompts**: Standard-Prompts werden im FilterPanel angezeigt, auch wenn kein Dokumententyp ausgewählt ist
- **Dokumenttyp-spezifische Prompts**: Wenn ein Dokumententyp ausgewählt ist, werden die spezifischen Prompts angezeigt
- **Bearbeiten**: Level 4+ können Prompts bearbeiten (RAG Chat Prompt und Multi-Query Prompt)
- **Verwendung**: 
  - Öffnen Sie das "RAG Chat Prompt (Standard)" Panel im FilterPanel für Default-Prompts
  - Wählen Sie einen Dokumententyp aus, um dokumenttyp-spezifische Prompts zu bearbeiten
  - Klicken Sie auf "Bearbeiten", um den Prompt-Text zu ändern
  - Speichern Sie Ihre Änderungen

## 📊 Analytics Dashboard

Das Analytics Dashboard bietet umfassende Einblicke in die Qualität Ihrer RAG-Suche.

### **Zugriff auf Analytics**

1. Stellen Sie eine Frage im RAG Chat
2. Klicken Sie auf **"Analytics"** in der Navigation
3. Das Dashboard zeigt automatisch die Analytics-Daten Ihrer letzten Anfrage

### **Analytics-Features**

#### **Quick Summary**
- **Query:** Die bewertete Frage wird prominent angezeigt
- **Top 3 Metrics:** NDCG@10, Precision@10, MRR
- **Status:** Exzellent, Gut, Akzeptabel oder Verbesserung nötig

#### **Search Quality Metrics**
- **Precision@k:** Anteil relevanter Ergebnisse in Top-k
- **Recall@k:** Anteil gefundener relevanter Ergebnisse
- **NDCG@k:** Ranking-Qualität (berücksichtigt Position)
- **MRR:** Position des ersten relevanten Ergebnisses

#### **SHAP Analyse**
- **Feature Importance:** Welche Features tragen zum Score bei?
- **Waterfall Charts:** Visuelle Darstellung der SHAP-Werte
- **Hybrid vs ML:** Vergleich zwischen Hybrid- und ML-Ranking

#### **Chunk-Analyse**
- **Detaillierte Chunk-Informationen:** Rank, Dokument, Seitenzahl, Relevanz-Score
- **Alle Scores:** Vector, Text, Hybrid, ML, Final Score
- **Chunk-Level Feedback:** Bewerten Sie einzelne Chunks direkt im Dashboard
- **Multi-Page Warning:** Warnung wenn Chunk mehrere Seiten umfasst

#### **Score Charts**
- **Bar Chart:** Durchschnittliche Scores über alle Chunks
- **Line Chart:** Score-Verlauf über Rank-Position (Top 10)
- **Radar Chart:** Multi-dimensionaler Score-Vergleich (Top 5)

#### **Trend-Analyse**
- **Zeitreihen-Charts:** Entwicklung der Metriken über Zeit
- **Vorher/Nachher Vergleich:** Vergleich zwischen zwei Zeitpunkten
- **Quality Alerts:** Automatische Warnungen bei Verschlechterungen

### **Chunk-Level Feedback geben**

1. Öffnen Sie das Analytics Dashboard nach einer RAG-Anfrage
2. Scrollen Sie zur **"Chunk-Analyse"** Sektion
3. Klicken Sie auf einen Chunk, um Details zu sehen
4. Bewerten Sie den Chunk:
   - **"Relevant"** (✅): Chunk ist relevant für die Frage
   - **"Nicht relevant"** (❌): Chunk ist nicht relevant
   - **"Neutral"** (ℹ️): Neutrales Feedback
5. Ihr Feedback wird automatisch für ML-Training verwendet

## Best Practices

1. **Spezifische Fragen**: Stellen Sie spezifische Fragen statt sehr allgemeine
2. **Filter verwenden**: Nutzen Sie Filter um den Suchbereich einzuschränken
3. **Model-Auswahl**: Experimentieren Sie mit verschiedenen Modellen für verschiedene Fragentypen
   - **GPT-4o Mini**: Beste Balance aus Qualität und Geschwindigkeit (empfohlen)
   - **GPT-5 Mini**: Sehr detaillierte Antworten, kann zu ausführlich sein
   - **Gemini 2.5 Flash**: Schnell, gut für einfache Fragen
4. **Source References**: Klicken Sie auf Source References um die Quelle einer Antwort zu sehen
5. **Feedback geben**: Bewerten Sie Chunks im Analytics Dashboard für bessere Ergebnisse
6. **Analytics nutzen**: Prüfen Sie regelmäßig das Analytics Dashboard um Qualität zu überwachen

## Troubleshooting

- **Keine Antworten**: Prüfen Sie ob indexierte Dokumente vorhanden sind
- **Falsche Antworten**: Versuchen Sie eine spezifischere Frage oder andere Filter
- **Session verschwunden**: Sessions werden persistiert - Seite neu laden sollte helfen
- **Analytics leer**: Stellen Sie eine neue Frage im Chat, um Analytics-Daten zu generieren
- **Text Score 0%**: Prüfen Sie ob BM25-Service aktiviert ist (sollte automatisch funktionieren)
