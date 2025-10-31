# Neuer Standard-Prompt für Flussdiagramme (Nodes & Connections)

## Für AI Playground Test

**Dokumenttyp:** Flussdiagramm  
**Zweck:** Extraktion von Flussdiagrammen als `nodes` + `connections` Struktur (statt `process_steps`)

---

## PROMPT TEXT:

```
Analysieren Sie das vorliegende Flussdiagramm vollständig und strukturieren Sie den gesamten erkennbaren Inhalt in valider, maschinenlesbarer JSON-Struktur nach folgendem Schema.

Ziel ist es, das gesamte Flussdiagramm mit allen Nodes (Knoten), Entscheidungspunkten, Verbindungen, beteiligten Rollen, Dokumentverweisen und kritischen Regeln exakt wiederzugeben.

Ziele:

• Alle Nodes eindeutig erfassen (Start, Prozess, Entscheidung, Ende)
• Entscheidungspunkte vollständig abbilden (jede Entscheidung mit Ja/Nein-Verbindungen)
• Verbindungen zwischen Nodes vollständig dokumentieren (von → zu, mit Bedingungen)
• Inputs, Outputs und Notes möglichst vollständig und konkret wiedergeben
• Rollenbezeichnungen („short" und „long") vollständig übernehmen oder aus dem Kontext ableiten
• Externe Verweise (z. B. auf andere SOPs, Formulare, ISO-Normen) in referenced_documents erfassen
• Kritische Regeln, Grenzwerte oder Bedingungen (z. B. „≥ 3 Fehler / Quartal") in critical_rules aufführen
• Rückverzweigungen oder Schleifen mit return_to_node_id markieren
• Unleserliche oder nicht erkennbare Angaben mit "unknown" markieren

Geben Sie nur gültiges JSON aus (kein erklärender Text davor oder danach).

JSON-Struktur:

{
  "document_metadata": {
    "title": "",
    "document_type": "flowchart",
    "version": "",
    "chapter": "",
    "valid_from": "",
    "organization": "",
    "page": "",
    "file_name": "",
    "created_by": {"name": "", "date": ""},
    "reviewed_by": {"name": "", "date": ""},
    "approved_by": {"name": "", "date": ""}
  },
  
  "diagram_overview": {
    "title": "",
    "description": "",
    "purpose": "",
    "scope": "",
    "swimlanes": []
  },
  
  "nodes": [
    {
      "node_id": "",
      "node_type": "start | process | decision | end | document | connector",
      "label": "",
      "description": "",
      "responsible_department": {"short": "", "long": ""},
      "swimlane": "",
      "inputs": [],
      "outputs": [],
      "notes": [],
      "position": {"x": 0, "y": 0}
    }
  ],
  
  "decision_points": [
    {
      "node_id": "",
      "question": "",
      "options": [
        {"label": "Ja", "value": "yes"},
        {"label": "Nein", "value": "no"}
      ],
      "default_option": ""
    }
  ],
  
  "connections": [
    {
      "connection_id": "",
      "from_node_id": "",
      "to_node_id": "",
      "condition": "",
      "label": "",
      "connection_type": "sequence | yes | no | parallel | loop | unknown"
    }
  ],
  
  "referenced_documents": [
    {"type": "", "reference": "", "title": "", "version": ""}
  ],
  
  "definitions": [
    {"term": "", "definition": ""}
  ],
  
  "compliance_requirements": [
    {"standard": "", "section": "", "requirement": ""}
  ],
  
  "critical_rules": [
    {"rule": "", "consequence": "", "linked_node_id": ""}
  ]
}

Zusätzliche Vorgaben für die Analyse:

1. Jeder Entscheidungsknoten (decision) muss mindestens zwei Verbindungen haben (Ja/Nein).
2. Start-Node: Verwenden Sie node_type "start" für den Beginn des Prozesses.
3. End-Node: Verwenden Sie node_type "end" für das Ende des Prozesses.
4. Prozess-Node: Verwenden Sie node_type "process" für alle normalen Prozessschritte.
5. Entscheidungs-Node: Verwenden Sie node_type "decision" für alle Entscheidungspunkte (Rauten).
6. Connections: Jede Verbindung sollte eine eindeutige connection_id haben und klar definieren:
   - Von welchem Node sie kommt (from_node_id)
   - Zu welchem Node sie führt (to_node_id)
   - Unter welcher Bedingung (condition) - z.B. "Ja", "Nein", "≥ 3 Fehler"
7. Wenn ein Node in einen vorherigen Pfad zurückführt, nutzen Sie die Felder return_to_node_id im Connection.
8. Wenn in Text oder Diagramm Bedingungen, Schwellenwerte oder Prüfgrenzen vorkommen, diese in critical_rules aufführen.
9. Wenn Abkürzungen vorkommen (z. B. WE, QMB, KVA), Bedeutung in definitions ergänzen.
10. Beschreibungen sollen kurz, aber vollständig sein – nicht nur Wiederholungen des Labels.
11. Swimlanes: Wenn das Diagramm Swimlanes hat (z.B. "Service", "Vertrieb/Service"), erfassen Sie diese in diagram_overview.swimlanes und bei jedem Node im Feld "swimlane".

WICHTIG: Dies ist ein Flussdiagramm, nicht eine sequenzielle Prozess-Beschreibung. Verwenden Sie die nodes/connections Struktur, nicht process_steps!
```

---

## Unterschiede zum alten Prompt:

### ❌ Alte Struktur (`process_steps`):
```json
{
  "process_steps": [
    {
      "step_number": 1,
      "label": "...",
      "next_steps": [...]
    }
  ]
}
```
→ **Sequenzielle Beschreibung** (Schritt 1, Schritt 2...)

### ✅ Neue Struktur (`nodes` + `connections`):
```json
{
  "nodes": [
    {
      "node_id": "node_1",
      "node_type": "decision",
      "label": "Rücksendung?",
      ...
    },
    {
      "node_id": "node_2",
      "node_type": "process",
      "label": "Gerät entsorgen",
      ...
    }
  ],
  "connections": [
    {
      "from_node_id": "node_1",
      "to_node_id": "node_2",
      "condition": "Nein",
      "connection_type": "no"
    }
  ]
}
```
→ **Echtes Flussdiagramm** mit Entscheidungspunkten und Verzweigungen

---

## Vorteile:

1. ✅ **Entscheidungspunkte werden erkannt** → "Rücksendung? (Ja/Nein)"
2. ✅ **Verzweigungen werden erfasst** → "Wenn Nein → Gerät entsorgen"
3. ✅ **Flussdiagramm-Struktur bleibt erhalten** → Nodes + Connections
4. ✅ **Bessere RAG-Chat Antworten** → Präzise Bezüge zu Entscheidungspunkten
5. ✅ **Keine "Phantasie"-Antworten** → Basierend auf echter Flussdiagramm-Struktur

---

## Nächste Schritte:

1. ✅ Kopiere diesen Prompt in AI Playground
2. ✅ Teste mit deinem Flussdiagramm-Dokument
3. ✅ Prüfe ob die JSON-Struktur passt (nodes + connections)
4. ✅ Wenn gut → Speichere als neuen Standard-Prompt (Status: active)
5. ✅ Alte Dokumente löschen (gemäß DB-Regel)
6. ✅ Dokumente neu hochladen → System verwendet neuen Prompt automatisch
7. ✅ Neue Indexierung mit korrekter Chunking-Strategie (_chunk_flowchart)
8. ✅ Test im RAG-Chat → Sollte jetzt präzise Antworten geben!

