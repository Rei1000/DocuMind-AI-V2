# RAG Chat System - Benutzerhandbuch

> **Version:** 2.5.0  
> **Stand:** 2025-11-11

## Übersicht

Das RAG Chat System ermöglicht es Benutzern, Fragen zu indexierten Dokumenten zu stellen und intelligente Antworten basierend auf dem Dokumenteninhalt zu erhalten.

## 🆕 Neue Features in v2.5.0

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
   - **Erweitern/Verkleinern:** Klicken Sie auf einen Chunk, um Details zu sehen

### **Chunk bearbeiten**

1. Klicken Sie auf **"Bearbeiten"** bei einem Chunk
2. Ändern Sie den Text direkt im Editor
3. Klicken Sie auf **"Speichern"**
4. Der Chunk wird in der Datenbank und im Vector Store aktualisiert

### **Chunk splitten**

1. Klicken Sie auf **"Splitten"** bei einem Chunk
2. Wählen Sie die **Split-Position** (Zeichen-Position im Text)
3. **Overlap-Sätze (NEU):** Wählen Sie 0-10 Overlap-Sätze
   - **Funktionsweise:** Die letzten N Sätze von Chunk 1 werden am Anfang von Chunk 2 hinzugefügt und umgekehrt
   - **Vorteil:** Bessere Kontext-Erhaltung für Vector Search
4. Klicken Sie auf **"Splitten"**
5. Der Chunk wird in zwei Chunks aufgeteilt
6. Beide Chunks erhalten `has_overlap: true` und `overlap_sentence_count: N` in den Metadaten

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

## Best Practices

1. **Spezifische Fragen**: Stellen Sie spezifische Fragen statt sehr allgemeine
2. **Filter verwenden**: Nutzen Sie Filter um den Suchbereich einzuschränken
3. **Model-Auswahl**: Experimentieren Sie mit verschiedenen Modellen für verschiedene Fragentypen
4. **Source References**: Klicken Sie auf Source References um die Quelle einer Antwort zu sehen

## Troubleshooting

- **Keine Antworten**: Prüfen Sie ob indexierte Dokumente vorhanden sind
- **Falsche Antworten**: Versuchen Sie eine spezifischere Frage oder andere Filter
- **Session verschwunden**: Sessions werden persistiert - Seite neu laden sollte helfen
