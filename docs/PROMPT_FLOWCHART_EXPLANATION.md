# Warum "nodes" statt "process_steps" für Flussdiagramme?

## Der Unterschied

### `process_steps` (Prozess-Beschreibung)
```json
{
  "process_steps": [
    {
      "step_number": 1,
      "title": "Defektes Gerät angeliefert",
      "description": "Anlieferung eines defekten Geräts...",
      "responsible": "WE - Wareneingang"
    },
    {
      "step_number": 2,
      "title": "Reparatur durchführen",
      "description": "Der Service-Mitarbeiter führt die Reparatur durch..."
    }
  ]
}
```

**Problem:** Das ist eine **sequenzielle Beschreibung**, kein Flussdiagramm!
- Keine Entscheidungspunkte
- Keine Verzweigungen (Ja/Nein)
- Keine Verbindungen zwischen Nodes
- Flussdiagramm-Charakteristik geht verloren

**Ergebnis:** Chunks wie "Schritt 1, Schritt 2..." → **Ungenau für Flussdiagramme!**

---

### `nodes` + `connections` (Echtes Flussdiagramm)
```json
{
  "nodes": [
    {
      "id": "node_1",
      "type": "process",
      "label": "Defektes Gerät angeliefert",
      "responsible": "WE - Wareneingang"
    },
    {
      "id": "node_2",
      "type": "decision",
      "label": "Rücksendung?",
      "options": ["Ja", "Nein"]
    },
    {
      "id": "node_3",
      "type": "process",
      "label": "Gerät entsorgen",
      "responsible": "Service/Fertigung"
    }
  ],
  "connections": [
    {
      "from": "node_2",
      "to": "node_3",
      "condition": "Nein"
    }
  ]
}
```

**Vorteil:** Das ist ein **echtes Flussdiagramm**!
- Entscheidungspunkte werden erkannt
- Verzweigungen (Ja/Nein) werden erfasst
- Verbindungen zwischen Nodes werden dokumentiert
- Flussdiagramm-Struktur bleibt erhalten

**Ergebnis:** Chunks wie "Node: Gerät entsorgen, Verbindung von 'Rücksendung? (Nein)' → ..." → **Präzise für Flussdiagramme!**

---

## Warum ist das wichtig für RAG?

### Problem bei `process_steps`:
- **Frage:** "Wann wird ein Gerät entsorgt?"
- **Chunk findet:** "Schritt 15: Gerät entsorgen wenn Rücksendung nicht gewünscht"
- **Fehlt:** Der Entscheidungspunkt "Rücksendung? (Nein)" → **Ungenau!**

### Lösung mit `nodes`:
- **Frage:** "Wann wird ein Gerät entsorgt?"
- **Chunk findet:** "Node: Gerät entsorgen, Verbindung von 'Rücksendung? (Nein)'"
- **Vollständig:** Entscheidungspunkt + Bedingung → **Präzise!**

---

## Fazit

**Für Flussdiagramme:** Prompt sollte `"nodes"` und `"connections"` verwenden
**Für Prozess-Beschreibungen:** Prompt sollte `"process_steps"` verwenden

Das System erkennt automatisch die Struktur und wählt die passende Chunking-Strategie!

