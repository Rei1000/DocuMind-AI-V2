# Prompt v2.9 — Arbeitsanweisung (mehrseitig, Fotos/Zeichnungen) → JSON (seitenweise, strikt & konsistent)

**OPTIMIERTE VERSION** - Basierend auf v2.8 mit folgenden Verbesserungen:
- Explizitere Artikelnummern-Format-Erkennung
- Erweiterte Mengen-Einheiten Liste
- Klarere Visual Elements Labels Struktur
- Verbesserte Konsistenz bei Quellenangaben

---

## Aufgabe:

Extrahieren Sie aus genau dieser Seite der Arbeitsanweisung alle Inhalte objektiv in das JSON-Schema unten. Quellen: Text, Tabellen, Fotos, Zeichnungen, Symbole. Keine Interpretation.

---

## Hard Rules (verbindlich)

### 1. Nur Erkennbares
Fehlend/unklar/unleserlich ⇒ exakt `""`, `"unknown"` oder `"not_visible"`.

### 2. Seitenweise Verarbeitung
Verarbeiten Sie nur diese Seite. Schritt-Nummern aus dem Dokument übernehmen (nicht neu nummerieren).

### 3. Normierung & Metadaten

**qty_number (Zahl) + qty_unit (Standard: "pcs")**
- `"4x"` ⇒ `4` + `"pcs"`
- `"2 Stück"` ⇒ `2` + `"pcs"`
- Andere Einheiten erlaubt: `"ml"`, `"g"`, `"kg"`, `"m"`, `"cm"`, `"mm"`, `"l"`, `"kg/m"`, etc. - Original übernehmen wenn explizit angegeben

**Artikelnummern-Format-Erkennung:**
- **Standard-Formate erkennen:**
  - `XX-XX-XXX` (z.B. `47-01-004`, `26-10-201`)
  - `XXX.XXX.XXX` (z.B. `123.456.789`)
  - Reine Zahlenfolgen (z.B. `123456789`, `471004`)
  - Mit Bindestrichen in anderer Struktur (z.B. `ABC-12345`, `471-004`)
- **Unbekannt/fehlend:** Werte wie `ohne`, `—`, `-`, `k. A.`, `n. a.`, `N/A`, `xx-xx-xxx` ⇒ `art_nr:"unknown"` und `notes:"raw_art_nr: <Original>"`

**valid_from:**
- Format: `YYYY-MM-DD` (z.B. `2024-01-15`)
- Sonst: `""`

**aa_id:**
- Nur Kennung übernehmen (z.B. `AA 006 [00] 130317`)
- `title` separat erfassen (ohne Präfix wie "Schritt X:")

### 4. Quellen (source) konsistent

- **Artikelliste/Tabelle** ⇒ `"table"`
- **Fließtext/Schritttext** ⇒ `"text"`
- **Nur im Bild erkennbar** ⇒ `"image"`
- **Konsistenz prüfen:** Gleiche Information sollte immer gleiche Quelle haben

### 5. Konsumgüter-Pflicht

Wenn Chemikalie/Kleber/Fett im Schritttext oder in Artikeln vorkommt, **muss** es einen `consumables[]`-Eintrag mit `application_area` geben:
- Quelle: `"text"` (wenn aus Text) oder `"table"` (wenn aus Tabelle)
- Beispiele: `Aceton`, `Loctite 648`, `Fett`, `Kleber`, `Öl`, `Lösungsmittel`
- **WICHTIG:** Wenn im Text Sicherheitshinweise zu Chemikalien/Klebern stehen (z.B. "Achtung! Sicherheitsvorschriften..."), MÜSSEN diese in `consumables[].hazard_notes` übertragen werden (nicht leer lassen!)

### 6. PSA ist kein Werkzeug

Handschuhe/Brille/PSA nie unter `tools`, sondern als `safety_instructions` mit `source:"text"` oder `"image"`.

### 7. Labels & Mapping

**Labels-Regeln:**
- Labels **nie erfinden**. Nur auflisten, wenn im Bild klar sichtbar
- **Buchstabenlabels:** `a, b, c, ...` (nur Kleinbuchstaben, kein Punkt)
- **Ziffernlabels:** `1, 2, 3, ...` (ohne Punkt, als String)
- **Beide gleichzeitig möglich** (z.B. `a` und `1` im selben Bild)

**article_data[*].labels:**
- Enthält **nur** Buchstabenlabels aus der Artikelliste dieses Schritts
- Keine Ziffernlabels (diese nur in `visual_elements`)

**visual_elements[*].labels[] (Mapping):**
- Jedes Element hat die Form: `{"label":"a","refers_to":"<Objekt/Artikelbezeichnung>","source":"image"}`
- **Buchstabenlabels:** `"label":"a"`, `"label":"b"`, etc.
- **Ziffernlabels:** `"label":"1"`, `"label":"2"`, etc. (als String) - **WICHTIG:** Auch Ziffernlabels im Bild MÜSSEN erfasst werden!
- **refers_to:** Exakte Objektbezeichnung (z.B. `"Freilaufwelle"`, `"Passfeder"`), nicht `"unknown"`
- **KRITISCHE PFLICHT - Labels-Mapping für RAG:**
  1. **Systematischer Check:** Gehe durch JEDEN Artikel in `article_data[]` der ein Label hat (z.B. `["a", "b", "c", "d"]`)
  2. **Für JEDES Label:** Prüfe ob dieses Label im Bild sichtbar ist
  3. **Falls ja:** Füge zu `visual_elements[*].labels[]` hinzu: `{"label":"a","refers_to":"<Artikelname>","source":"image"}`
  4. **Vollständigkeitscheck:** Die Anzahl der Labels in `visual_elements[*].labels[]` MUSS mindestens gleich der Anzahl in `article_data[*].labels` sein
  5. **Beispiel:** Wenn `article_data` 4 Labels hat (`["a","b","c","d"]`), dann MUSS `visual_elements[*].labels[]` mindestens 4 Einträge haben!
- Wenn Zuordnung im Bild nicht eindeutig ist, Label **gar nicht** in `article_data[*].labels` aufnehmen (statt `refers_to:"unknown"`)
- **Hinweis:** Auch wenn viele Labels vorhanden sind (z.B. 4 Labels), MUSS jedes einzelne gemappt werden - das ist kritisch für RAG-System-Performance!

### 8. Titel & Beschreibung

- **title:** Ohne Präfix `"Schritt X:"` - nur der eigentliche Titel
- **description:** Enthält nur Arbeitsanweisungen, **keine** Liste "Benötigte Artikel"
- **Aufzählungszeichen entfernen:** Entferne Aufzählungszeichen (1., 2., a), b), etc.) aus `description` - nur reine Arbeitsanweisung ohne Nummerierung
- **Regex-Check:** Entferne jeden Text der mit `"Benötigte Artikel:"` beginnt aus `description`

### 9. Struktur der Felder

**Arrays von Strings (keine Objekte):**
- `orientation_details`: `["String 1", "String 2"]`
- `quality_checks`: `["Prüfung 1", "Prüfung 2"]`
- `notes`: `["Notiz 1", "Notiz 2"]`

**Arrays von Objekten:**
- `tools`: `[{"name": "Schraubendreher", "source": "text|image"}]`
- `safety_instructions`: `[{"topic":"Belüftung","instruction":"Offenes Fenster","source":"text|image"}]`
- **WICHTIG:** Jedes Topic in `safety_instructions` als separater Eintrag - nicht kombinieren (z.B. `"Belüftung"` und `"Handschutz"` getrennt, nicht `"Belüftung und PSA"`)

**Keine leeren Strings in Arrays:**
- Wenn nichts vorhanden ⇒ leeres Array `[]`
- Nicht: `["", "Wert"]` sondern: `["Wert"]`

### 10. Bilder & Referenzen

**page_images:**
- Ausschließlich normierte Platzhalter: `"Foto 1"`, `"Foto 2"`, `"Zeichnung 1"`, `"Zeichnung 2"` in Lesereihenfolge
- Format: `"Foto N"` oder `"Zeichnung N"` (N = fortlaufende Nummer)

**visual_elements[*].ref:**
- **Muss** einen der Platzhalter aus `page_images` verwenden
- Beispiel: Wenn `page_images: ["Foto 1", "Foto 2"]`, dann `ref: "Foto 1"` oder `ref: "Foto 2"`

**visual_elements[*].description:**
- Konkrete Bildbeschreibung (was ist zu sehen)
- **Keine** Prompt-Schablonen wie "Bild zeigt..." - direkt beschreiben
- Beispiel: `"Freilaufwelle liegend mit eingelegten Sicherungsringen; rote Beschriftungs-Pfeile markieren (a) links, (b) zwei mittlere Ringe, (c) rechte Nut/Passfederbereich."`

### 11. Feldbereinigung

- **Keine leeren Strings in Arrays:** Entferne alle `""` aus Arrays
- **Keine Platzhalter:** Entferne Texte wie `"..."`, `"-"`, `"N/A"` aus Arrays (außer wenn explizit im Dokument)
- **Null-Werte:** Nutze `""` für Strings, `0` für Zahlen, `[]` für leere Arrays

### 12. Nur JSON ausgeben

- **Keine Erklärtexte** außerhalb des JSON
- **Keine Kommentare** im JSON
- **Keine zusätzlichen Metadaten** über die Extraktion
- **Nur das reine JSON** gemäß Schema

---

## Ausgabeformat (Schema – exakt verwenden)

```json
{
  "page_metadata": {
    "page_number": 0,
    "file_name": "",
    "page_images": ["Foto 1", "Foto 2"]
  },
  "document_metadata": {
    "aa_id": "",
    "title": "",
    "version": "",
    "valid_from": "",
    "organization": "",
    "file_name": "",
    "created_by": "",
    "reviewed_by": "",
    "approved_by": "",
    "page_info": ""
  },
  "process_overview": {
    "goal": "",
    "scope": "",
    "general_safety": [
      {
        "topic": "",
        "instruction": "",
        "source": "text|image"
      }
    ],
    "general_tools": [],
    "general_materials": [],
    "reference_documents": []
  },
  "steps": [
    {
      "step_number": 0,
      "title": "",
      "description": "",
      "article_data": [
        {
          "name": "",
          "art_nr": "",
          "qty_number": 0,
          "qty_unit": "pcs",
          "notes": "",
          "labels": [],
          "source": "text|table"
        }
      ],
      "consumables": [
        {
          "name": "",
          "specification": "",
          "application_area": "",
          "hazard_notes": "",
          "source": "text|table"
        }
      ],
      "tools": [
        {
          "name": "",
          "source": "text|image"
        }
      ],
      "orientation_details": [],
      "safety_instructions": [
        {
          "topic": "",
          "instruction": "",
          "source": "text|image"
        }
      ],
      "quality_checks": [],
      "visual_elements": [
        {
          "ref": "Foto 1",
          "type": "Foto|Zeichnung|Symbol",
          "labels": [
            {
              "label": "a",
              "refers_to": "<Objekt/Artikelbezeichnung>",
              "source": "image"
            }
          ],
          "description": "",
          "source": "image"
        }
      ],
      "notes": [],
      "next_step_number": "",
      "return_to_step_number": ""
    }
  ],
  "critical_rules": [],
  "mini_flowchart_mermaid": "flowchart TD; Sx[Schritt x: …]-->Sy[Schritt y: …];"
}
```

---

## Self-Check (vor Ausgabe strikt anwenden)

### Struktur-Checks:
- [ ] `description` enthält keine "Benötigte Artikel"-Aufzählung
- [ ] `orientation_details`, `quality_checks`, `notes` sind Arrays aus Strings (keine Objekte, keine leeren Strings)
- [ ] `tools[]` und `safety_instructions[]` sind Arrays aus Objekten mit korrekter Struktur

### Content-Checks:
- [ ] Für jede Chemikalie/Kleber/Fett existiert mindestens ein `consumables`-Eintrag mit `application_area`
- [ ] `consumables[].source` ist immer `"text"` oder `"table"` (nie `"image"`)
- [ ] Wenn im Text Sicherheitshinweise zu Chemikalien stehen, MÜSSEN diese in `consumables[].hazard_notes` stehen (nicht leer!)

### Label-Mapping-Checks:
- [ ] `visual_elements[*].labels[]` enthält bei vorhandenen Bildlabels stets ein konkretes `refers_to` (keine Platzhaltertexte/Leerwerte)
- [ ] **KRITISCHE PFLICHT:** Jede Buchstabenmarke in `article_data[*].labels` taucht auch in irgendeinem `visual_elements[*].labels[].label` auf - wenn `article_data` Labels hat, MUSS `visual_elements` diese enthalten!
- [ ] **Vollständigkeitscheck:** Anzahl Labels in `visual_elements[*].labels[]` ≥ Anzahl Labels in `article_data[*].labels` (z.B. 4 Labels in article_data → mindestens 4 Labels in visual_elements!)
- [ ] **Systematischer Check:** Jeder Artikel mit Label wurde einzeln geprüft und zu visual_elements hinzugefügt
- [ ] Ziffernlabels (1, 2, 3...) stehen nur in `visual_elements[*].labels`, nicht in `article_data[*].labels`
- [ ] Alle im Bild sichtbaren Ziffernlabels (1, 2, 3...) MÜSSEN in `visual_elements[*].labels` erfasst werden

### Format-Checks:
- [ ] `page_images` / `visual_elements[*].ref` nutzen nur `"Foto N"` oder `"Zeichnung N"` (normierte Platzhalter)
- [ ] `source` konsistent: Tabelle→`"table"`, Text→`"text"`, Bild→`"image"`
- [ ] `title` ohne `"Schritt X:"` Präfix
- [ ] `description` enthält keine Aufzählungszeichen (1., 2., a), b), etc.) - nur reine Arbeitsanweisung
- [ ] `qty_unit` ist Standard `"pcs"` oder eine erlaubte Einheit (`"ml"`, `"g"`, `"kg"`, etc.)
- [ ] Artikelnummern haben korrektes Format oder sind `"unknown"` mit `notes`
- [ ] `safety_instructions` haben jeweils nur ein Topic pro Eintrag (nicht kombiniert wie "Belüftung und PSA")

### Datenbereinigung:
- [ ] Arrays: Entferne alle leeren Strings (`""`) aus `orientation_details`, `quality_checks`, `notes`
- [ ] Labels: Wenn `article_data[*].labels` nicht leer und kein passendes `visual_elements[*].labels` existiert ⇒ entferne die Labels im Artikel
- [ ] Konsumgüter-Pflicht: Wenn `article_data.name` ∈ {`"Aceton"`, `"Loctite"`, `"Fett"`, `"Kleber"`, `"Öl"`, etc.} oder `description` enthält eines dieser Wörter ⇒ erzwinge mind. einen `consumables`-Eintrag

### Final-Check:
- [ ] **Nur JSON** - keine Erklärtexte außerhalb
- [ ] JSON ist **valide** (kann geparst werden)
- [ ] Alle Pflichtfelder vorhanden (auch wenn leer)

---

## Changelog v2.8 → v2.9

1. ✅ **Artikelnummern-Format-Erkennung expliziter:** Standard-Formate (XX-XX-XXX, XXX.XXX.XXX, Zahlenfolgen) jetzt klar definiert
2. ✅ **Mengen-Einheiten erweitert:** Zusätzlich zu "pcs" auch "ml", "g", "kg", "m", "cm", etc. erlaubt (Original übernehmen)
3. ✅ **Visual Elements Labels klarer:** 
   - Unterscheidung zwischen Buchstabenlabels (in article_data) und Ziffernlabels (nur in visual_elements) explizit
   - **Pflicht:** Wenn article_data Labels hat, MUSS visual_elements diese enthalten
   - Ziffernlabels im Bild MÜSSEN erfasst werden
4. ✅ **Quellen-Konsistenz betont:** Gleiche Information sollte immer gleiche Quelle haben
5. ✅ **Self-Check erweitert:** Zusätzliche Checks für Format-Validierung und Datenbereinigung
6. ✅ **Konsumgüter-Liste erweitert:** Explizite Liste von Beispielen (Aceton, Loctite, Fett, Kleber, Öl, Lösungsmittel)
7. ✅ **Consumables hazard_notes:** Sicherheitshinweise zu Chemikalien MÜSSEN in hazard_notes übertragen werden
8. ✅ **Description bereinigt:** Aufzählungszeichen (1., 2., etc.) müssen entfernt werden
9. ✅ **Safety Instructions:** Jedes Topic als separater Eintrag (nicht kombiniert)

