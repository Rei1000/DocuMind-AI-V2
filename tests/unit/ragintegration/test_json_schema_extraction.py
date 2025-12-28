"""
Unit Tests für JSON-Schema-Extraktion aus Standard Prompts.

TDD Phase 1: RED - Tests für JSON-Schema-Extraktion.
Diese Tests schlagen zunächst fehl, da die Implementierung noch nicht existiert.

CR-P2.2: Auto-Custom-Prompt-Generierung
"""

import pytest
from typing import Optional, Dict, Any


# ========================================
# Test 1: JSON-Schema-Lokalisierung
# ========================================

def test_locate_json_schema_fachartikel():
    """
    Test: JSON-Schema-Lokalisierung für Fachartikel Standard Prompt.
    
    Requirements:
    - Findet Schema-Marker "JSON-Ausgabeformat" oder "🧩 JSON"
    - Gibt Start- und End-Zeile zurück
    """
    from contexts.ragintegration.infrastructure.json_schema_extractor import locate_json_schema
    
    prompt_text = """
Prompt: Fachartikel-Analyse für RAG-Systeme (TechArticle-to-JSON v2.0)
Sie sind ein KI-gestützter wissenschaftlich-technischer Analyst.

🧩 JSON-Ausgabeformat

{
  "document_metadata": {
    "title": "",
    "subtitle": "",
    "authors": []
  },
  "abstract": {
    "german": "",
    "english": ""
  },
  "sections": []
}
"""
    
    result = locate_json_schema(prompt_text)
    
    assert result is not None, "JSON-Schema sollte gefunden werden"
    start_line, end_line = result
    assert start_line >= 0, "Start-Zeile sollte >= 0 sein"
    assert end_line > start_line, "End-Zeile sollte > Start-Zeile sein"


def test_locate_json_schema_arbeitsanweisung():
    """
    Test: JSON-Schema-Lokalisierung für Arbeitsanweisung Standard Prompt.
    
    Requirements:
    - Findet Schema-Marker "Ausgabeformat" oder "```json"
    - Gibt Start- und End-Zeile zurück
    """
    from contexts.ragintegration.infrastructure.json_schema_extractor import locate_json_schema
    
    prompt_text = """
Extrahieren Sie aus genau dieser Seite der Arbeitsanweisung alle Inhalte.

## Ausgabeformat (Schema – exakt verwenden)

```json
{
  "page_metadata": {
    "page_number": 1
  },
  "document_metadata": {
    "title": ""
  },
  "steps": [
    {
      "step_number": 1,
      "title": "",
      "description": ""
    }
  ]
}
```
"""
    
    result = locate_json_schema(prompt_text)
    
    assert result is not None, "JSON-Schema sollte gefunden werden"
    start_line, end_line = result
    assert start_line >= 0, "Start-Zeile sollte >= 0 sein"
    assert end_line > start_line, "End-Zeile sollte > Start-Zeile sein"


def test_locate_json_schema_not_found():
    """
    Test: JSON-Schema-Lokalisierung schlägt fehl wenn kein Schema vorhanden.
    
    Requirements:
    - Gibt None zurück wenn kein Schema-Marker gefunden wird
    """
    from contexts.ragintegration.infrastructure.json_schema_extractor import locate_json_schema
    
    prompt_text = """
Dies ist ein Prompt ohne JSON-Schema.
Er enthält nur Text, aber keine strukturierten Daten.
"""
    
    result = locate_json_schema(prompt_text)
    
    assert result is None, "Sollte None zurückgeben wenn kein Schema gefunden wird"


# ========================================
# Test 2: JSON-Schema-Extraktion
# ========================================

def test_extract_json_schema_fachartikel():
    """
    Test: JSON-Schema-Extraktion für Fachartikel.
    
    Requirements:
    - Extrahiert vollständiges JSON-Schema
    - Entfernt Kommentare
    - Parst JSON erfolgreich
    - Identifiziert Top-Level-Keys: document_metadata, abstract, sections
    """
    from contexts.ragintegration.infrastructure.json_schema_extractor import extract_json_schema
    
    prompt_text = """
🧩 JSON-Ausgabeformat

{
  "document_metadata": {
    "title": "",
    "subtitle": "",
    "authors": []
  },
  "abstract": {
    "german": "",
    "english": ""
  },
  "sections": []
}
"""
    
    result = extract_json_schema(prompt_text)
    
    assert result is not None, "JSON-Schema sollte extrahiert werden"
    assert isinstance(result, dict), "Ergebnis sollte ein Dict sein"
    assert "document_metadata" in result, "document_metadata sollte vorhanden sein"
    assert "abstract" in result, "abstract sollte vorhanden sein"
    assert "sections" in result, "sections sollte vorhanden sein"


def test_extract_json_schema_with_comments():
    """
    Test: JSON-Schema-Extraktion mit Kommentaren.
    
    Requirements:
    - Entfernt JSON-Kommentare (// und /* */)
    - Parst JSON erfolgreich trotz Kommentaren
    """
    from contexts.ragintegration.infrastructure.json_schema_extractor import extract_json_schema
    
    prompt_text = """
```json
{
  "document_metadata": {
    "title": "", // Titel des Dokuments
    "subtitle": ""
  },
  /* Dies ist ein Kommentar */
  "sections": []
}
```
"""
    
    result = extract_json_schema(prompt_text)
    
    assert result is not None, "JSON-Schema sollte trotz Kommentaren extrahiert werden"
    assert isinstance(result, dict), "Ergebnis sollte ein Dict sein"
    assert "document_metadata" in result, "document_metadata sollte vorhanden sein"


def test_extract_json_schema_datenblatt():
    """
    Test: JSON-Schema-Extraktion für Datenblatt.
    
    Requirements:
    - Extrahiert komplexe verschachtelte Struktur
    - Identifiziert Top-Level-Keys: page_metadata, document_metadata, technical_specifications, application_info, safety_data
    """
    from contexts.ragintegration.infrastructure.json_schema_extractor import extract_json_schema
    
    prompt_text = """
## Ausgabeformat (Schema – exakt verwenden):

```json
{
  "page_metadata": {
    "page_number": 1
  },
  "document_metadata": {
    "title": "",
    "art_nr": ""
  },
  "technical_specifications": {
    "physical_properties": {},
    "chemical_properties": {}
  },
  "application_info": {
    "application_areas": []
  },
  "safety_data": {
    "ghs_symbols": []
  }
}
```
"""
    
    result = extract_json_schema(prompt_text)
    
    assert result is not None, "JSON-Schema sollte extrahiert werden"
    assert isinstance(result, dict), "Ergebnis sollte ein Dict sein"
    assert "page_metadata" in result, "page_metadata sollte vorhanden sein"
    assert "technical_specifications" in result, "technical_specifications sollte vorhanden sein"
    assert "application_info" in result, "application_info sollte vorhanden sein"
    assert "safety_data" in result, "safety_data sollte vorhanden sein"


# ========================================
# Test 3: Top-Level-Keys-Identifikation
# ========================================

def test_identify_top_level_keys_fachartikel():
    """
    Test: Top-Level-Keys-Identifikation für Fachartikel.
    
    Requirements:
    - Identifiziert alle Top-Level-Keys
    - Gibt Liste zurück: ["document_metadata", "abstract", "sections"]
    """
    from contexts.ragintegration.infrastructure.json_schema_extractor import identify_top_level_keys
    
    json_schema = {
        "document_metadata": {},
        "abstract": {},
        "sections": []
    }
    
    result = identify_top_level_keys(json_schema)
    
    assert isinstance(result, list), "Ergebnis sollte eine Liste sein"
    assert len(result) == 3, "Sollte 3 Top-Level-Keys identifizieren"
    assert "document_metadata" in result, "document_metadata sollte vorhanden sein"
    assert "abstract" in result, "abstract sollte vorhanden sein"
    assert "sections" in result, "sections sollte vorhanden sein"


def test_identify_top_level_keys_arbeitsanweisung():
    """
    Test: Top-Level-Keys-Identifikation für Arbeitsanweisung.
    
    Requirements:
    - Identifiziert alle Top-Level-Keys
    - Gibt Liste zurück: ["page_metadata", "document_metadata", "process_overview", "steps"]
    """
    from contexts.ragintegration.infrastructure.json_schema_extractor import identify_top_level_keys
    
    json_schema = {
        "page_metadata": {},
        "document_metadata": {},
        "process_overview": {},
        "steps": []
    }
    
    result = identify_top_level_keys(json_schema)
    
    assert isinstance(result, list), "Ergebnis sollte eine Liste sein"
    assert len(result) == 4, "Sollte 4 Top-Level-Keys identifizieren"
    assert "steps" in result, "steps sollte vorhanden sein"


# ========================================
# Test 4: Struktur-Beschreibung
# ========================================

def test_describe_json_structure_fachartikel():
    """
    Test: Struktur-Beschreibung für Fachartikel.
    
    Requirements:
    - Erstellt strukturierte Beschreibung
    - Identifiziert Top-Level-Keys
    - Identifiziert Feld-Typen (object, array, string)
    - Identifiziert verschachtelte Strukturen
    """
    from contexts.ragintegration.infrastructure.json_schema_extractor import describe_json_structure
    
    json_schema = {
        "document_metadata": {
            "title": "",
            "authors": []
        },
        "abstract": {
            "german": "",
            "english": ""
        },
        "sections": []
    }
    
    result = describe_json_structure(json_schema)
    
    assert isinstance(result, dict), "Ergebnis sollte ein Dict sein"
    assert "top_level_keys" in result, "top_level_keys sollte vorhanden sein"
    assert "field_types" in result, "field_types sollte vorhanden sein"
    assert "nested_structures" in result, "nested_structures sollte vorhanden sein"
    
    assert len(result["top_level_keys"]) == 3, "Sollte 3 Top-Level-Keys haben"
    assert result["field_types"]["document_metadata"] == "object", "document_metadata sollte object sein"
    assert result["field_types"]["sections"] == "array", "sections sollte array sein"


def test_describe_json_structure_nested():
    """
    Test: Struktur-Beschreibung mit verschachtelten Strukturen.
    
    Requirements:
    - Identifiziert verschachtelte Objekte
    - Identifiziert Arrays von Objekten
    """
    from contexts.ragintegration.infrastructure.json_schema_extractor import describe_json_structure
    
    json_schema = {
        "steps": [
            {
                "step_number": 1,
                "title": "",
                "description": ""
            }
        ]
    }
    
    result = describe_json_structure(json_schema)
    
    assert isinstance(result, dict), "Ergebnis sollte ein Dict sein"
    assert "nested_structures" in result, "nested_structures sollte vorhanden sein"
    assert len(result["nested_structures"]) > 0, "Sollte verschachtelte Strukturen identifizieren"


# ========================================
# Test 5: Vollständige Extraktion (End-to-End)
# ========================================

def test_extract_complete_schema_fachartikel():
    """
    Test: Vollständige JSON-Schema-Extraktion für Fachartikel (End-to-End).
    
    Requirements:
    - Lokalisiert Schema
    - Extrahiert JSON
    - Identifiziert Top-Level-Keys
    - Erstellt Struktur-Beschreibung
    """
    from contexts.ragintegration.infrastructure.json_schema_extractor import (
        locate_json_schema,
        extract_json_schema,
        identify_top_level_keys,
        describe_json_structure
    )
    
    prompt_text = """
🧩 JSON-Ausgabeformat

{
  "document_metadata": {
    "title": "",
    "authors": []
  },
  "abstract": {
    "german": "",
    "english": ""
  },
  "sections": []
}
"""
    
    # 1. Lokalisiere Schema
    location = locate_json_schema(prompt_text)
    assert location is not None, "Schema sollte lokalisiert werden"
    
    # 2. Extrahiere JSON
    json_schema = extract_json_schema(prompt_text)
    assert json_schema is not None, "JSON sollte extrahiert werden"
    
    # 3. Identifiziere Top-Level-Keys
    top_level_keys = identify_top_level_keys(json_schema)
    assert len(top_level_keys) == 3, "Sollte 3 Top-Level-Keys identifizieren"
    
    # 4. Erstelle Struktur-Beschreibung
    description = describe_json_structure(json_schema)
    assert "top_level_keys" in description, "Struktur-Beschreibung sollte top_level_keys enthalten"


def test_extract_complete_schema_arbeitsanweisung():
    """
    Test: Vollständige JSON-Schema-Extraktion für Arbeitsanweisung (End-to-End).
    
    Requirements:
    - Funktioniert mit Code-Block-Markern (```json)
    - Extrahiert komplexe Struktur mit steps-Array
    """
    from contexts.ragintegration.infrastructure.json_schema_extractor import (
        extract_json_schema,
        identify_top_level_keys
    )
    
    prompt_text = """
## Ausgabeformat (Schema – exakt verwenden)

```json
{
  "page_metadata": {
    "page_number": 1
  },
  "document_metadata": {
    "title": ""
  },
  "steps": [
    {
      "step_number": 1,
      "title": "",
      "description": ""
    }
  ]
}
```
"""
    
    json_schema = extract_json_schema(prompt_text)
    assert json_schema is not None, "JSON sollte extrahiert werden"
    
    top_level_keys = identify_top_level_keys(json_schema)
    assert "steps" in top_level_keys, "steps sollte identifiziert werden"
    assert "page_metadata" in top_level_keys, "page_metadata sollte identifiziert werden"


