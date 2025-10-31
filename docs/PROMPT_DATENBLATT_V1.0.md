# Prompt v1.0 — Datenblatt (technische Datenblätter, Produktspezifikationen) → JSON (strukturiert & konsistent)

## Aufgabe:
Extrahieren Sie aus diesem Datenblatt alle technischen Informationen, Spezifikationen und Anwendungshinweise objektiv in das JSON-Schema unten. Quellen: Text, Tabellen, Diagramme, Sicherheitshinweise. Keine Interpretation.

## Hard Rules (verbindlich):

### 1. **Nur Erkennbares**
- Fehlend/unklar/unleserlich ⇒ exakt `""`, `"unknown"` oder `"not_visible"`
- Keine Erfindung von Werten

### 2. **Normierung & Formatierung**
- **Einheiten konsistent:** Viskosität in mPa·s oder cSt, Temperaturen in °C, Drücke in bar, etc.
- **Artikelnummern:** Werte wie "ohne", "—", "-", "k.A." ⇒ `art_nr: "unknown"` + `notes: "raw_art_nr: <Original>"`
- **Zahlen:** Dezimalpunkte als `.`, Tausender-Trenner entfernen
- **Formate:** ISO-Datumsformat (YYYY-MM-DD), falls vorhanden

### 3. **Quellen (source) konsistent**
- Tabelle/Liste ⇒ `"table"`
- Fließtext ⇒ `"text"`
- Nur im Bild/Diagramm erkennbar ⇒ `"image"`
- Sicherheitsdatenblatt (SDS) ⇒ `"sds"`

### 4. **Technische Spezifikationen strukturiert**
- **Physikalische Eigenschaften:** Separater Abschnitt mit Einheiten
- **Chemische Eigenschaften:** Separater Abschnitt
- **Performance-Daten:** Separater Abschnitt (z.B. Zugfestigkeit, Scherfestigkeit)
- **Umgebungsbedingungen:** Temperaturbereich, Feuchtigkeit, etc.

### 5. **Sicherheitsdaten (SDS) Pflicht**
- Wenn Sicherheitshinweise vorhanden, MÜSSEN diese vollständig erfasst werden
- Gefahrstoff-Kennzeichnung (GHS-Symbole, H-Sätze, P-Sätze)
- Lagerungshinweise
- Entsorgungshinweise
- **Kritisch für RAG:** Ermöglicht Fragen wie "Welche Sicherheitshinweise gibt es zu Loctite 648?"

### 6. **Anwendungsgebiete & Verarbeitung**
- **Anwendungsbereiche:** Liste von Industriesektoren/Anwendungen
- **Verarbeitungshinweise:** Schritt-für-Schritt-Anleitung falls vorhanden
- **Vorbereitung:** Oberflächenvorbereitung, Temperaturen, etc.
- **Aushärtezeit:** Temperaturen und Zeiten strukturiert

### 7. **Vergleichsdaten & Varianten**
- Wenn mehrere Varianten/Größen existieren, als Array strukturieren
- Vergleichstabellen vollständig erfassen
- Produktvarianten klar unterscheiden

### 8. **Struktur der Felder**
- Arrays sind Listen von Strings oder Objekten (keine leeren Strings!)
- Wenn nichts vorhanden ⇒ leeres Array `[]`
- Keine verschachtelten Arrays ohne Grund

### 9. **Nur JSON ausgeben**
- Keine Erklärtexte außerhalb des JSON
- Keine Markdown-Formatierung außerhalb des JSON
- Valides JSON (prüfbar!)

---

## Ausgabeformat (Schema – exakt verwenden):

```json
{
  "page_metadata": {
    "page_number": 0,
    "file_name": "",
    "document_images": ["Diagramm 1", "Grafik 1"]
  },
  "document_metadata": {
    "product_name": "",
    "art_nr": "",
    "manufacturer": "",
    "product_type": "",
    "version": "",
    "issue_date": "",
    "valid_until": "",
    "language": "",
    "file_name": ""
  },
  "technical_specifications": {
    "physical_properties": [
      {
        "property": "",
        "value": "",
        "unit": "",
        "test_method": "",
        "conditions": "",
        "source": "text|table|image"
      }
    ],
    "chemical_properties": [
      {
        "property": "",
        "value": "",
        "unit": "",
        "test_method": "",
        "source": "text|table|image"
      }
    ],
    "performance_data": [
      {
        "test_type": "",
        "value": "",
        "unit": "",
        "conditions": "",
        "test_method": "",
        "source": "text|table|image"
      }
    ],
    "environmental_conditions": {
      "operating_temperature_min": "",
      "operating_temperature_max": "",
      "storage_temperature_min": "",
      "storage_temperature_max": "",
      "relative_humidity": "",
      "pressure_range": "",
      "source": "text|table"
    }
  },
  "application_info": {
    "application_areas": [],
    "industry_sectors": [],
    "material_compatibility": [],
    "surface_preparation": {
      "steps": [],
      "cleaning_agents": [],
      "surface_roughness": "",
      "temperature_requirements": "",
      "source": "text|table"
    },
    "processing_instructions": [
      {
        "step_number": 0,
        "instruction": "",
        "temperature": "",
        "time": "",
        "pressure": "",
        "notes": "",
        "source": "text|table|image"
      }
    ],
    "curing_information": {
      "room_temperature": {
        "time": "",
        "conditions": "",
        "full_cure_time": ""
      },
      "accelerated": [
        {
          "temperature": "",
          "time": "",
          "conditions": ""
        }
      ],
      "source": "text|table"
    }
  },
  "safety_data": {
    "ghs_symbols": [],
    "h_statements": [],
    "p_statements": [],
    "safety_warnings": [],
    "first_aid_measures": [],
    "storage_requirements": [],
    "disposal_instructions": [],
    "regulatory_info": [],
    "source": "text|table|sds"
  },
  "product_variants": [
    {
      "variant_name": "",
      "art_nr": "",
      "size": "",
      "packaging": "",
      "differences": [],
      "source": "text|table"
    }
  ],
  "additional_information": {
    "shelf_life": "",
    "storage_conditions": "",
    "packaging_info": "",
    "order_information": [],
    "references": [],
    "contact_information": {
      "manufacturer_contact": "",
      "technical_support": "",
      "sds_request": ""
    },
    "notes": []
  },
  "visual_elements": [
    {
      "ref": "Diagramm 1",
      "type": "Diagramm/Grafik/Tabelle",
      "description": "",
      "data_points": [],
      "source": "image"
    }
  ]
}
```

---

## Self-Check (vor Ausgabe strikt anwenden):

### ✅ Vollständigkeits-Checks:
- [ ] Alle erkennbaren technischen Spezifikationen erfasst
- [ ] Sicherheitsdaten vollständig (wenn vorhanden)
- [ ] Anwendungsgebiete nicht leer (wenn im Dokument vorhanden)
- [ ] Verarbeitungshinweise strukturiert (wenn vorhanden)
- [ ] Artikelnummern konsistent (unknown wenn nicht erkennbar)

### ✅ Struktur-Checks:
- [ ] Arrays enthalten keine leeren Strings
- [ ] Einheiten konsistent (keine Mischung von °C und °F, etc.)
- [ ] Source-Attribute konsistent (text, table, image, sds)
- [ ] JSON ist valide (parsbar)

### ✅ RAG-Optimierung:
- [ ] Technische Spezifikationen sind strukturiert (für Fragen wie "Welche Viskosität hat Loctite 648?")
- [ ] Sicherheitshinweise vollständig (für Fragen wie "Welche Gefahrstoffe enthält Loctite 648?")
- [ ] Anwendungsgebiete erfasst (für Fragen wie "Für welche Materialien ist Loctite 648 geeignet?")
- [ ] Verarbeitungshinweise schrittweise (für Fragen wie "Wie wird Loctite 648 verarbeitet?")

### ✅ Verbote:
- ❌ Regex drop bei fehlenden Informationen (stattdessen `"unknown"` oder `""`)
- ❌ Arrays: Entferne leere Strings aus Arrays
- ❌ Keine Erfindung von Werten
- ❌ Keine Markdown-Formatierung außerhalb des JSON

---

## Beispiel-Ausgabe (Loctite 648 Datenblatt):

```json
{
  "page_metadata": {
    "page_number": 1,
    "file_name": "Loctite_648_DE.pdf",
    "document_images": ["Anwendungsbeispiel", "Technische Daten Tabelle"]
  },
  "document_metadata": {
    "product_name": "Loctite 648",
    "art_nr": "648",
    "manufacturer": "Henkel",
    "product_type": "Schnellkleber (Cyanacrylat)",
    "version": "2024-01",
    "issue_date": "2024-01-15",
    "valid_until": "",
    "language": "DE",
    "file_name": "Loctite_648_DE.pdf"
  },
  "technical_specifications": {
    "physical_properties": [
      {
        "property": "Viskosität",
        "value": "20",
        "unit": "mPa·s",
        "test_method": "Brookfield",
        "conditions": "25°C",
        "source": "table"
      },
      {
        "property": "Dichte",
        "value": "1.09",
        "unit": "g/cm³",
        "test_method": "DIN EN ISO 2811",
        "conditions": "20°C",
        "source": "table"
      }
    ],
    "chemical_properties": [
      {
        "property": "Basis",
        "value": "Ethyl-2-Cyanacrylat",
        "unit": "",
        "test_method": "",
        "source": "text"
      }
    ],
    "performance_data": [
      {
        "test_type": "Zugscherfestigkeit",
        "value": "25",
        "unit": "N/mm²",
        "conditions": "Stahl/Stahl, 24h Aushärtung, RT",
        "test_method": "DIN EN 1465",
        "source": "table"
      }
    ],
    "environmental_conditions": {
      "operating_temperature_min": "-54",
      "operating_temperature_max": "82",
      "storage_temperature_min": "5",
      "storage_temperature_max": "25",
      "relative_humidity": "<70%",
      "pressure_range": "",
      "source": "table"
    }
  },
  "application_info": {
    "application_areas": [
      "Metallklebung",
      "Gummi-Metall-Klebung",
      "Kunststoff-Metall-Klebung"
    ],
    "industry_sectors": [
      "Automotive",
      "Elektronik",
      "Maschinenbau"
    ],
    "material_compatibility": [
      "Stahl",
      "Aluminium",
      "Kunststoffe (ABS, PC, PBT)",
      "Gummi"
    ],
    "surface_preparation": {
      "steps": [
        "Oberfläche entfetten",
        "Trocken wischen",
        "Saubere, trockene Oberfläche sicherstellen"
      ],
      "cleaning_agents": [
        "Aceton",
        "Isopropanol"
      ],
      "surface_roughness": "",
      "temperature_requirements": "Raumtemperatur (15-25°C)",
      "source": "text"
    },
    "processing_instructions": [
      {
        "step_number": 1,
        "instruction": "Oberfläche vorbereiten und entfetten",
        "temperature": "RT",
        "time": "",
        "pressure": "",
        "notes": "Sauber und trocken",
        "source": "text"
      },
      {
        "step_number": 2,
        "instruction": "Klebstoff auftragen",
        "temperature": "RT",
        "time": "",
        "pressure": "Leichter Andruck",
        "notes": "Dünner Film, eine Oberfläche",
        "source": "text"
      },
      {
        "step_number": 3,
        "instruction": "Fügeteile zusammenführen",
        "temperature": "RT",
        "time": "10-30 Sekunden",
        "pressure": "Leichter Andruck",
        "notes": "Sofort kleben",
        "source": "text"
      }
    ],
    "curing_information": {
      "room_temperature": {
        "time": "10-30 Sekunden",
        "conditions": "Anfangshaftung, 15-25°C",
        "full_cure_time": "24 Stunden"
      },
      "accelerated": [],
      "source": "table"
    }
  },
  "safety_data": {
    "ghs_symbols": [
      "GHS05",
      "GHS07"
    ],
    "h_statements": [
      "H315",
      "H317",
      "H319",
      "H335"
    ],
    "p_statements": [
      "P261",
      "P264",
      "P272",
      "P280",
      "P302+P352",
      "P305+P351+P338"
    ],
    "safety_warnings": [
      "Verursacht Hautreizungen",
      "Verursacht schwere Augenschäden",
      "Kann die Atemwege reizen",
      "Gefahr bei Hautkontakt"
    ],
    "first_aid_measures": [
      "Bei Hautkontakt: Sofort mit Wasser abspülen",
      "Bei Augenkontakt: Sofort mit Wasser spülen, Arzt aufsuchen",
      "Bei Verschlucken: Sofort ärztlichen Rat einholen"
    ],
    "storage_requirements": [
      "Trocken lagern",
      "Kühl lagern (5-25°C)",
      "Vor Licht schützen",
      "Originalverpackung verschlossen"
    ],
    "disposal_instructions": [
      "Nach geltenden Abfallbestimmungen entsorgen",
      "Nicht in Abwasser oder Boden gelangen lassen"
    ],
    "regulatory_info": [
      "REACH-konform",
      "RoHS-konform"
    ],
    "source": "sds"
  },
  "product_variants": [
    {
      "variant_name": "Loctite 648",
      "art_nr": "648",
      "size": "20g",
      "packaging": "Tube",
      "differences": [],
      "source": "table"
    }
  ],
  "additional_information": {
    "shelf_life": "12 Monate",
    "storage_conditions": "Trocken, kühl (5-25°C), vor Licht schützen",
    "packaging_info": "Tube 20g, Tube 50g",
    "order_information": [
      "Bestell-Nr. 648 (20g)",
      "Bestell-Nr. 648-50 (50g)"
    ],
    "references": [],
    "contact_information": {
      "manufacturer_contact": "Henkel AG & Co. KGaA",
      "technical_support": "",
      "sds_request": ""
    },
    "notes": []
  },
  "visual_elements": [
    {
      "ref": "Technische Daten Tabelle",
      "type": "Tabelle",
      "description": "Übersichtstabelle mit physikalischen Eigenschaften",
      "data_points": ["Viskosität", "Dichte", "Aushärtezeit"],
      "source": "image"
    }
  ]
}
```

---

## RAG-Optimierung für Chat-Fragen:

Dieser Prompt ist optimiert für Fragen wie:
- **"Welche Viskosität hat Loctite 648?"** → `technical_specifications.physical_properties[property="Viskosität"]`
- **"Wie wird Loctite 648 verarbeitet?"** → `application_info.processing_instructions[]`
- **"Welche Sicherheitshinweise gibt es zu Loctite 648?"** → `safety_data.safety_warnings[]` + `h_statements[]` + `p_statements[]`
- **"Für welche Materialien ist Loctite 648 geeignet?"** → `application_info.material_compatibility[]`
- **"Wie lange dauert die Aushärtung?"** → `application_info.curing_information.room_temperature.time`
- **"Welche Temperaturbereiche sind zulässig?"** → `technical_specifications.environmental_conditions`

---

**Version:** 1.0  
**Erstellt:** 2025-10-31  
**Status:** Draft (zum Testen im AI Playground)

