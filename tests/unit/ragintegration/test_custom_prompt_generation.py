"""
Unit Tests für Custom-Prompt-Generierung basierend auf JSON-Struktur.

TDD Phase 1: RED - Tests für Custom-Prompt-Generierung.
Diese Tests schlagen zunächst fehl, da die Implementierung noch nicht existiert.

CR-P2.2: Auto-Custom-Prompt-Generierung
"""

import pytest
from typing import Dict, Any


# ========================================
# Test 1: Custom-Prompt-Generierung für Fachartikel
# ========================================

def test_generate_custom_prompt_fachartikel():
    """
    Test: Custom-Prompt-Generierung für Fachartikel.
    
    Requirements:
    - Generiert Custom Prompt mit JSON-Struktur-Informationen
    - Enthält {context} und {question} Platzhalter
    - Erwähnt wichtige JSON-Felder: document_metadata, abstract, sections
    - Betont präzise Detail-Wiedergabe (Zahlen, Statistiken, Diagramme, Tabellen)
    """
    from contexts.ragintegration.application.services import generate_custom_prompt_from_json_schema
    
    json_structure = {
        "top_level_keys": ["document_metadata", "abstract", "sections"],
        "field_types": {
            "document_metadata": "object",
            "abstract": "object",
            "sections": "array"
        },
        "nested_structures": [
            {
                "key": "sections",
                "item_structure": {
                    "top_level_keys": ["content_summary", "methods", "experiments"]
                }
            }
        ]
    }
    
    document_type_name = "Fachartikel"
    
    result = generate_custom_prompt_from_json_schema(
        json_structure=json_structure,
        document_type_name=document_type_name
    )
    
    assert result is not None, "Custom Prompt sollte generiert werden"
    assert isinstance(result, str), "Ergebnis sollte ein String sein"
    assert "{context}" in result, "Sollte {context} Platzhalter enthalten"
    assert "{question}" in result, "Sollte {question} Platzhalter enthalten"
    assert "document_metadata" in result.lower(), "Sollte document_metadata erwähnen"
    assert "sections" in result.lower(), "Sollte sections erwähnen"
    assert "zahlen" in result.lower() or "statistiken" in result.lower(), "Sollte präzise Detail-Wiedergabe betonen"


def test_generate_custom_prompt_arbeitsanweisung():
    """
    Test: Custom-Prompt-Generierung für Arbeitsanweisung.
    
    Requirements:
    - Generiert Custom Prompt mit steps-Informationen
    - Erwähnt wichtige JSON-Felder: steps, step_number, materials, safety_instructions
    - Betont präzise Schritt-für-Schritt-Wiedergabe
    """
    from contexts.ragintegration.application.services import generate_custom_prompt_from_json_schema
    
    json_structure = {
        "top_level_keys": ["page_metadata", "document_metadata", "process_overview", "steps"],
        "field_types": {
            "steps": "array"
        },
        "nested_structures": [
            {
                "key": "steps",
                "item_structure": {
                    "top_level_keys": ["step_number", "title", "description", "materials", "safety_instructions"]
                }
            }
        ]
    }
    
    document_type_name = "Arbeitsanweisung"
    
    result = generate_custom_prompt_from_json_schema(
        json_structure=json_structure,
        document_type_name=document_type_name
    )
    
    assert result is not None, "Custom Prompt sollte generiert werden"
    assert "{context}" in result, "Sollte {context} Platzhalter enthalten"
    assert "{question}" in result, "Sollte {question} Platzhalter enthalten"
    assert "steps" in result.lower() or "schritte" in result.lower(), "Sollte steps erwähnen"
    assert "step_number" in result.lower() or "schrittnummer" in result.lower(), "Sollte step_number erwähnen"


def test_generate_custom_prompt_datenblatt():
    """
    Test: Custom-Prompt-Generierung für Datenblatt.
    
    Requirements:
    - Generiert Custom Prompt mit technical_specifications-Informationen
    - Erwähnt wichtige JSON-Felder: technical_specifications, application_info, safety_data
    - Betont präzise technische Spezifikationen-Wiedergabe
    """
    from contexts.ragintegration.application.services import generate_custom_prompt_from_json_schema
    
    json_structure = {
        "top_level_keys": ["page_metadata", "document_metadata", "technical_specifications", "application_info", "safety_data"],
        "field_types": {
            "technical_specifications": "object",
            "application_info": "object",
            "safety_data": "object"
        }
    }
    
    document_type_name = "Datenblätter"
    
    result = generate_custom_prompt_from_json_schema(
        json_structure=json_structure,
        document_type_name=document_type_name
    )
    
    assert result is not None, "Custom Prompt sollte generiert werden"
    assert "{context}" in result, "Sollte {context} Platzhalter enthalten"
    assert "{question}" in result, "Sollte {question} Platzhalter enthalten"
    assert "technical_specifications" in result.lower() or "technische" in result.lower(), "Sollte technical_specifications erwähnen"
    assert "safety_data" in result.lower() or "sicherheit" in result.lower(), "Sollte safety_data erwähnen"


def test_generate_custom_prompt_flussdiagramm():
    """
    Test: Custom-Prompt-Generierung für Flussdiagramm.
    
    Requirements:
    - Generiert Custom Prompt mit nodes/connections-Informationen
    - Erwähnt wichtige JSON-Felder: nodes, connections, diagram_overview
    - Betont präzise Prozessfluss-Wiedergabe
    """
    from contexts.ragintegration.application.services import generate_custom_prompt_from_json_schema
    
    json_structure = {
        "top_level_keys": ["document_metadata", "diagram_overview", "nodes", "connections"],
        "field_types": {
            "nodes": "array",
            "connections": "array"
        }
    }
    
    document_type_name = "Flussdiagramm"
    
    result = generate_custom_prompt_from_json_schema(
        json_structure=json_structure,
        document_type_name=document_type_name
    )
    
    assert result is not None, "Custom Prompt sollte generiert werden"
    assert "{context}" in result, "Sollte {context} Platzhalter enthalten"
    assert "{question}" in result, "Sollte {question} Platzhalter enthalten"
    assert "nodes" in result.lower() or "knoten" in result.lower(), "Sollte nodes erwähnen"
    assert "connections" in result.lower() or "verbindungen" in result.lower(), "Sollte connections erwähnen"


# ========================================
# Test 2: Platzhalter-Validierung
# ========================================

def test_generated_prompt_has_required_placeholders():
    """
    Test: Generierter Custom Prompt hat erforderliche Platzhalter.
    
    Requirements:
    - {context} Platzhalter MUSS vorhanden sein
    - {question} Platzhalter MUSS vorhanden sein
    - Keine anderen Platzhalter erforderlich
    """
    from contexts.ragintegration.application.services import generate_custom_prompt_from_json_schema
    
    json_structure = {
        "top_level_keys": ["document_metadata", "sections"],
        "field_types": {}
    }
    
    result = generate_custom_prompt_from_json_schema(
        json_structure=json_structure,
        document_type_name="Test"
    )
    
    assert "{context}" in result, "Sollte {context} Platzhalter enthalten"
    assert "{question}" in result, "Sollte {question} Platzhalter enthalten"
    assert result.count("{context}") == 1, "Sollte genau einen {context} Platzhalter haben"
    assert result.count("{question}") == 1, "Sollte genau einen {question} Platzhalter haben"


# ========================================
# Test 3: Dokumenttyp-spezifische Anpassungen
# ========================================

def test_custom_prompt_document_type_specific():
    """
    Test: Custom Prompt ist dokumenttyp-spezifisch.
    
    Requirements:
    - Fachartikel: Betont wissenschaftliche Inhalte, Statistiken, Diagramme
    - Arbeitsanweisung: Betont Schritt-für-Schritt-Anleitungen
    - Datenblatt: Betont technische Spezifikationen, Sicherheitsdaten
    - Flussdiagramm: Betont Prozessfluss, Entscheidungspunkte
    """
    from contexts.ragintegration.application.services import generate_custom_prompt_from_json_schema
    
    json_structure = {
        "top_level_keys": ["document_metadata", "sections"],
        "field_types": {}
    }
    
    # Fachartikel
    fachartikel_prompt = generate_custom_prompt_from_json_schema(
        json_structure=json_structure,
        document_type_name="Fachartikel"
    )
    assert "fachartikel" in fachartikel_prompt.lower() or "wissenschaftlich" in fachartikel_prompt.lower(), "Sollte Fachartikel-spezifisch sein"
    
    # Arbeitsanweisung
    arbeitsanweisung_prompt = generate_custom_prompt_from_json_schema(
        json_structure=json_structure,
        document_type_name="Arbeitsanweisung"
    )
    assert "arbeitsanweisung" in arbeitsanweisung_prompt.lower() or "schritt" in arbeitsanweisung_prompt.lower(), "Sollte Arbeitsanweisung-spezifisch sein"


# ========================================
# Test 4: Fehlerbehandlung
# ========================================

def test_generate_custom_prompt_empty_structure():
    """
    Test: Custom-Prompt-Generierung mit leerer JSON-Struktur.
    
    Requirements:
    - Sollte trotzdem einen gültigen Custom Prompt generieren
    - Enthält {context} und {question} Platzhalter
    - Fallback auf generische Anweisungen
    """
    from contexts.ragintegration.application.services import generate_custom_prompt_from_json_schema
    
    json_structure = {
        "top_level_keys": [],
        "field_types": {}
    }
    
    result = generate_custom_prompt_from_json_schema(
        json_structure=json_structure,
        document_type_name="Test"
    )
    
    assert result is not None, "Sollte auch bei leerer Struktur einen Prompt generieren"
    assert "{context}" in result, "Sollte {context} Platzhalter enthalten"
    assert "{question}" in result, "Sollte {question} Platzhalter enthalten"


def test_generate_custom_prompt_missing_keys():
    """
    Test: Custom-Prompt-Generierung mit fehlenden Keys.
    
    Requirements:
    - Sollte trotzdem funktionieren
    - Verwendet verfügbare Informationen
    """
    from contexts.ragintegration.application.services import generate_custom_prompt_from_json_schema
    
    json_structure = {
        "top_level_keys": ["document_metadata"],
        # field_types fehlt
    }
    
    result = generate_custom_prompt_from_json_schema(
        json_structure=json_structure,
        document_type_name="Test"
    )
    
    assert result is not None, "Sollte auch bei fehlenden Keys funktionieren"
    assert "{context}" in result, "Sollte {context} Platzhalter enthalten"


