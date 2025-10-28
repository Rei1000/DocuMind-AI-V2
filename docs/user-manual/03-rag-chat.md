# 💬 RAG Chat System - Benutzerhandbuch

> **User Manual:** Intelligente Fragen zu Dokumenten stellen  
> **Version:** 2.1.0  
> **Letzte Aktualisierung:** 2025-10-27

---

## 🎯 Übersicht

Das RAG (Retrieval Augmented Generation) Chat System ermöglicht es Ihnen, intelligente Fragen zu Ihren freigegebenen Dokumenten zu stellen und präzise Antworten mit Quellenangaben zu erhalten.

### **Was ist RAG?**

RAG kombiniert:
- **Vector Search:** Semantische Suche nach ähnlichen Inhalten
- **AI Generation:** Intelligente Antworten basierend auf gefundenen Dokumenten
- **Source Attribution:** Präzise Quellenangaben mit Relevanz-Scores

---

## 🚀 Erste Schritte

### **RAG Chat öffnen**

1. **Anmelden:** Loggen Sie sich als QMS Admin ein (`qms.admin@company.com` / `Admin432!`)
2. **Dashboard:** Navigieren Sie zur Hauptseite
3. **RAG Chat:** Der Chat ist zentral platziert (60% der Ansicht)

### **Erste Frage stellen**

```
Beispiel-Fragen:
- "Welche Schritte sind bei der Reparaturerfassung erforderlich?"
- "Welche Sicherheitshinweise gibt es für Maschinen?"
- "Wie viele Artikel sind in der Stückliste aufgeführt?"
- "Welche Dokumente enthalten Informationen über Qualitätsprüfungen?"
```

---

## 💬 Chat-Interface

### **Haupt-Chat-Bereich (60% der Ansicht)**

#### **Frage eingeben**
1. **Eingabefeld:** Geben Sie Ihre Frage ein
2. **AI-Modell wählen:**
   - **GPT-4o Mini** ⚡ (schnell, kostengünstig)
   - **GPT-5 Mini** 🧠 (hochwertig, teurer)
   - **Gemini 2.5 Flash** ⚖️ (ausgewogen)
3. **Senden:** Klicken Sie auf "Senden" oder drücken Sie Enter

#### **Antworten verstehen**
Die Antworten enthalten:

- **Hauptantwort:** Direkte Antwort auf Ihre Frage
- **Quellen:** Links zu den relevanten Dokumenten
- **Relevanz-Score:** Wie relevant ist die Quelle (0-100%)
- **Strukturierte Daten:** Tabellen, Listen, Sicherheitshinweise
- **Preview-Links:** Direkte Links zu Dokument-Seiten

### **Session Sidebar (links, 20% der Ansicht)**

#### **Session-Management**
1. **Alle Sessions:** Sehen Sie alle Ihre Chat-Sessions
2. **Neue Session:** Erstellen Sie eine neue Session
3. **Session wechseln:** Klicken Sie auf eine Session
4. **Session löschen:** Löschen Sie alte Sessions

#### **Session-Informationen**
- **Session-Name:** Automatisch generiert oder manuell benannt
- **Erstellungsdatum:** Wann wurde die Session erstellt
- **Letzte Nachricht:** Zeitpunkt der letzten Aktivität
- **Nachrichten-Anzahl:** Anzahl der Nachrichten in der Session

### **Filter Panel (rechts, 20% der Ansicht)**

#### **Erweiterte Suche**
1. **Quick Search:** Schnelle Textsuche in allen Dokumenten
2. **Document Type Filter:** Nach Dokumenttyp filtern
   - SOP (Standard Operating Procedures)
   - Arbeitsanweisungen
   - Flussdiagramme
   - Formulare
   - Prozess-Dokumente
   - Qualitätsmanagement
   - Compliance-Dokumente
3. **Interest Group Filter:** Nach Stakeholder-Gruppen filtern
4. **Date Range Filter:** Nach Zeitraum filtern

---

## 🔍 Quellen erkunden

### **Source Preview Modal**

#### **Modal öffnen**
1. Klicken Sie auf **"Preview"** bei einer Quelle
2. Das **Source Preview Modal** öffnet sich im Vollbild

#### **Modal-Funktionen**
- **Vollbild-Preview:** Das komplette Dokument wird angezeigt
- **Zoom-Funktionen:** 50% - 300% Zoom
- **Text-Auszug:** Der relevante Chunk wird hervorgehoben
- **Relevanz-Informationen:** Score und Metadaten
- **Aktionen:**
  - **Dokument öffnen:** Öffnet das Dokument im Detail-View
  - **Download:** Lädt das Dokument herunter
  - **Im Chat fragen:** Stellt eine Follow-up-Frage

### **Quellen-Informationen**

#### **Relevanz-Score**
- **90-100%:** Sehr relevant, direkte Antwort
- **70-89%:** Relevant, unterstützende Information
- **50-69%:** Teilweise relevant, zusätzlicher Kontext
- **<50%:** Wenig relevant, möglicherweise nicht hilfreich

#### **Metadaten**
- **Dokument-Typ:** SOP, Arbeitsanweisung, etc.
- **Seiten-Nummer:** Wo wurde die Information gefunden
- **Chunk-Typ:** Metadaten, Prozess-Schritte, Compliance, etc.
- **Token-Anzahl:** Größe des Text-Auszugs
- **Erstellungsdatum:** Wann wurde das Dokument indexiert

---

## 🎯 Best Practices

### **Effektive Fragen stellen**

#### **Gute Fragen**
```
✅ "Welche Schritte sind bei der Reparaturerfassung erforderlich?"
✅ "Welche Sicherheitshinweise gibt es für Maschinen?"
✅ "Wie viele Artikel sind in der Stückliste aufgeführt?"
✅ "Welche Dokumente enthalten Informationen über Qualitätsprüfungen?"
```

#### **Schlechte Fragen**
```
❌ "Was ist das?"
❌ "Hilfe!"
❌ "Zeig mir alles"
❌ "Wie geht das?"
```

### **Follow-up-Fragen**

#### **Kontextuelle Fragen**
- "Kannst du das genauer erklären?"
- "Welche anderen Dokumente behandeln dieses Thema?"
- "Gibt es ähnliche Prozesse in anderen Bereichen?"

#### **Spezifische Fragen**
- "Welche Sicherheitsausrüstung wird benötigt?"
- "Wie lange dauert dieser Prozess?"
- "Wer ist für diesen Schritt verantwortlich?"

### **AI-Modell-Auswahl**

#### **GPT-4o Mini** ⚡
- **Verwendung:** Schnelle, einfache Fragen
- **Vorteile:** Kostengünstig, schnell
- **Nachteile:** Weniger detailliert

#### **GPT-5 Mini** 🧠
- **Verwendung:** Komplexe, detaillierte Fragen
- **Vorteile:** Hochwertige Antworten, detailliert
- **Nachteile:** Teurer, langsamer

#### **Gemini 2.5 Flash** ⚖️
- **Verwendung:** Ausgewogene Fragen
- **Vorteile:** Gutes Preis-Leistungs-Verhältnis
- **Nachteile:** Weniger spezialisiert

---

## 🔧 Erweiterte Funktionen

### **Strukturierte Daten**

#### **Tabellen**
- Werden automatisch erkannt und formatiert
- Können direkt in Antworten eingebettet werden
- Unterstützen komplexe Datenstrukturen

#### **Listen**
- Nummerierte Listen für Prozess-Schritte
- Aufzählungslisten für Kriterien
- Checklisten für Prüfungen

#### **Sicherheitshinweise**
- Werden automatisch hervorgehoben
- Enthalten Warnsymbole und Farbkodierung
- Sind besonders sichtbar in Antworten

### **Suggested Questions**

#### **Automatische Vorschläge**
Das System schlägt automatisch Follow-up-Fragen vor:
- "Was sind die wichtigsten Schritte?"
- "Welche Sicherheitshinweise gibt es?"
- "Welche Dokumente sind ähnlich?"
- "Wie wird dieser Prozess dokumentiert?"

#### **Kontextuelle Vorschläge**
Basierend auf der aktuellen Antwort werden relevante Fragen vorgeschlagen.

---

## 🚨 Troubleshooting

### **Häufige Probleme**

#### **Keine Antworten**
- **Ursache:** Keine freigegebenen Dokumente verfügbar
- **Lösung:** Dokumente müssen den Status "Approved" haben

#### **Schlechte Relevanz-Scores**
- **Ursache:** Frage zu unspezifisch
- **Lösung:** Konkretere Fragen stellen

#### **Langsame Antworten**
- **Ursache:** Große Dokumente oder komplexe Fragen
- **Lösung:** GPT-4o Mini für schnellere Antworten verwenden

#### **Fehlende Quellen**
- **Ursache:** Dokumente noch nicht indexiert
- **Lösung:** Dokumente müssen für RAG indexiert werden

### **Support**

#### **Bei Problemen**
1. **Logs prüfen:** Schauen Sie in die Browser-Konsole
2. **Session neu starten:** Erstellen Sie eine neue Chat-Session
3. **Browser aktualisieren:** Laden Sie die Seite neu
4. **Admin kontaktieren:** Bei anhaltenden Problemen

---

## 📊 System-Status

### **RAG-System prüfen**

#### **Verfügbare Dokumente**
- **Indexierte Dokumente:** Anzahl der für RAG verfügbaren Dokumente
- **Chunks:** Anzahl der Text-Abschnitte
- **Vector Store:** Status der Qdrant-Datenbank

#### **Performance-Metriken**
- **Antwortzeit:** Durchschnittliche Antwortzeit
- **Relevanz-Score:** Durchschnittlicher Relevanz-Score
- **Model-Usage:** Verwendung der verschiedenen AI-Modelle

---

**Letzte Aktualisierung:** 2025-10-27  
**Version:** 2.1.0  
**Status:** ✅ Production Ready
