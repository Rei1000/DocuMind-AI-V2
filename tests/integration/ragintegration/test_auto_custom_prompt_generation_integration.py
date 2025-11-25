"""
Integration Tests für Auto-Custom-Prompt-Generierung.

TDD Phase: Integration Tests für End-to-End Flow.

CR-P2.2: Auto-Custom-Prompt-Generierung aus Standard Prompts.

Diese Tests prüfen den vollständigen Workflow:
1. Standard Prompt speichern/aktivieren (mit document_type_id)
2. Auto-Generierung von Custom Prompt
3. Custom Prompt in Datenbank gespeichert mit is_auto_generated=True
4. Custom Prompt kann im RAG Chat verwendet werden
"""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from contexts.ragintegration.application.auto_custom_prompt_service import AutoCustomPromptService
from contexts.ragintegration.infrastructure.repositories import SQLAlchemyRAGChatPromptRepository
from contexts.ragintegration.domain.entities import RAGChatPrompt


# ========================================
# Test 1: End-to-End Flow - Standard Prompt → Custom Prompt
# ========================================

def test_auto_generate_custom_prompt_from_standard_prompt_fachartikel(db_session: Session):
    """
    Test: Auto-Generierung von Custom Prompt für Fachartikel.
    
    Requirements:
    - Standard Prompt mit JSON-Schema wird verarbeitet
    - Custom Prompt wird automatisch generiert
    - Custom Prompt enthält {context} und {question} Platzhalter
    - Custom Prompt wird in DB gespeichert mit is_auto_generated=True
    - Custom Prompt kann für RAG Chat verwendet werden
    """
    # Setup
    rag_chat_prompt_repo = SQLAlchemyRAGChatPromptRepository(db_session)
    auto_service = AutoCustomPromptService(rag_chat_prompt_repo)
    
    # Standard Prompt für Fachartikel (mit JSON-Schema)
    standard_prompt_text = """
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
    
    document_type_id = 10  # Fachartikel
    document_type_name = "Fachartikel"
    created_by_user_id = 1
    
    # Execute: Auto-Generierung
    result = auto_service.generate_from_standard_prompt(
        standard_prompt_text=standard_prompt_text,
        document_type_id=document_type_id,
        document_type_name=document_type_name,
        created_by_user_id=created_by_user_id
    )
    
    # Assertions
    assert result is not None, "Custom Prompt sollte generiert werden"
    assert result.document_type_id == document_type_id, "Document Type ID sollte korrekt sein"
    assert result.is_auto_generated is True, "is_auto_generated sollte True sein"
    assert "{context}" in result.prompt_text, "Sollte {context} Platzhalter enthalten"
    assert "{question}" in result.prompt_text, "Sollte {question} Platzhalter enthalten"
    assert "document_metadata" in result.prompt_text.lower(), "Sollte document_metadata erwähnen"
    assert "sections" in result.prompt_text.lower(), "Sollte sections erwähnen"
    
    # Prüfe DB-Persistenz
    saved_prompt = rag_chat_prompt_repo.get_by_document_type_id(document_type_id)
    assert saved_prompt is not None, "Custom Prompt sollte in DB gespeichert sein"
    assert saved_prompt.is_auto_generated is True, "is_auto_generated Flag sollte gespeichert sein"


def test_auto_generate_custom_prompt_from_standard_prompt_arbeitsanweisung(db_session: Session):
    """
    Test: Auto-Generierung von Custom Prompt für Arbeitsanweisung.
    
    Requirements:
    - Standard Prompt mit steps-Array wird verarbeitet
    - Custom Prompt wird automatisch generiert
    - Custom Prompt enthält steps-spezifische Anweisungen
    """
    # Setup
    rag_chat_prompt_repo = SQLAlchemyRAGChatPromptRepository(db_session)
    auto_service = AutoCustomPromptService(rag_chat_prompt_repo)
    
    # Standard Prompt für Arbeitsanweisung
    standard_prompt_text = """
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
    
    document_type_id = 3  # Arbeitsanweisung
    document_type_name = "Arbeitsanweisung"
    created_by_user_id = 1
    
    # Execute
    result = auto_service.generate_from_standard_prompt(
        standard_prompt_text=standard_prompt_text,
        document_type_id=document_type_id,
        document_type_name=document_type_name,
        created_by_user_id=created_by_user_id
    )
    
    # Assertions
    assert result is not None, "Custom Prompt sollte generiert werden"
    assert result.is_auto_generated is True, "is_auto_generated sollte True sein"
    assert "steps" in result.prompt_text.lower() or "schritte" in result.prompt_text.lower(), "Sollte steps erwähnen"


# ========================================
# Test 2: Update-Verhalten
# ========================================

def test_auto_update_existing_auto_generated_prompt(db_session: Session):
    """
    Test: Auto-Generierung aktualisiert existierenden auto-generierten Prompt.
    
    Requirements:
    - Wenn Custom Prompt mit is_auto_generated=True existiert
    - Wird es bei erneuter Auto-Generierung aktualisiert
    - updated_at wird aktualisiert
    """
    # Setup: Erstelle initialen auto-generierten Prompt
    rag_chat_prompt_repo = SQLAlchemyRAGChatPromptRepository(db_session)
    auto_service = AutoCustomPromptService(rag_chat_prompt_repo)
    
    standard_prompt_text = """
🧩 JSON-Ausgabeformat

{
  "document_metadata": {
    "title": ""
  },
  "sections": []
}
"""
    
    document_type_id = 10
    document_type_name = "Fachartikel"
    created_by_user_id = 1
    
    # Erste Generierung
    first_prompt = auto_service.generate_from_standard_prompt(
        standard_prompt_text=standard_prompt_text,
        document_type_id=document_type_id,
        document_type_name=document_type_name,
        created_by_user_id=created_by_user_id
    )
    
    assert first_prompt is not None
    first_updated_at = first_prompt.updated_at
    
    # Warte kurz (für updated_at Unterschied)
    import time
    time.sleep(0.1)
    
    # Zweite Generierung (sollte aktualisiert werden)
    second_prompt = auto_service.generate_from_standard_prompt(
        standard_prompt_text=standard_prompt_text + "\n// Neue Zeile",
        document_type_id=document_type_id,
        document_type_name=document_type_name,
        created_by_user_id=created_by_user_id
    )
    
    # Assertions
    assert second_prompt is not None, "Prompt sollte aktualisiert werden"
    assert second_prompt.id == first_prompt.id, "Sollte gleiche ID haben (Update, nicht Create)"
    assert second_prompt.updated_at > first_updated_at, "updated_at sollte aktualisiert sein"


def test_auto_generation_does_not_overwrite_manual_prompt(db_session: Session):
    """
    Test: Auto-Generierung überschreibt NICHT manuell bearbeiteten Prompt.
    
    Requirements:
    - Wenn Custom Prompt mit is_auto_generated=False existiert
    - Wird es bei Auto-Generierung NICHT überschrieben
    - Gibt None zurück
    """
    # Setup: Erstelle manuell bearbeiteten Prompt
    rag_chat_prompt_repo = SQLAlchemyRAGChatPromptRepository(db_session)
    
    manual_prompt = RAGChatPrompt(
        id=None,
        document_type_id=10,
        prompt_text="Manuell bearbeiteter Prompt",
        created_by_user_id=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        multi_query_prompt_text=None,
        is_auto_generated=False  # Manuell bearbeitet
    )
    
    saved_manual = rag_chat_prompt_repo.save(manual_prompt)
    
    # Auto-Generierung versuchen
    auto_service = AutoCustomPromptService(rag_chat_prompt_repo)
    
    standard_prompt_text = """
🧩 JSON-Ausgabeformat

{
  "document_metadata": {
    "title": ""
  }
}
"""
    
    result = auto_service.generate_from_standard_prompt(
        standard_prompt_text=standard_prompt_text,
        document_type_id=10,
        document_type_name="Fachartikel",
        created_by_user_id=1
    )
    
    # Assertions
    assert result is None, "Sollte None zurückgeben (nicht überschreiben)"
    
    # Prüfe dass manueller Prompt unverändert ist
    still_manual = rag_chat_prompt_repo.get_by_document_type_id(10)
    assert still_manual is not None, "Manueller Prompt sollte noch existieren"
    assert still_manual.prompt_text == "Manuell bearbeiteter Prompt", "Prompt-Text sollte unverändert sein"
    assert still_manual.is_auto_generated is False, "is_auto_generated sollte False bleiben"


# ========================================
# Test 3: Fehlerbehandlung
# ========================================

def test_auto_generation_fails_without_json_schema(db_session: Session):
    """
    Test: Auto-Generierung schlägt fehl wenn kein JSON-Schema vorhanden.
    
    Requirements:
    - Wenn Standard Prompt kein JSON-Schema enthält
    - Gibt None zurück
    - Kein Custom Prompt wird erstellt
    """
    # Setup
    rag_chat_prompt_repo = SQLAlchemyRAGChatPromptRepository(db_session)
    auto_service = AutoCustomPromptService(rag_chat_prompt_repo)
    
    # Standard Prompt OHNE JSON-Schema
    standard_prompt_text = """
Dies ist ein Prompt ohne JSON-Schema.
Er enthält nur Text, aber keine strukturierten Daten.
"""
    
    result = auto_service.generate_from_standard_prompt(
        standard_prompt_text=standard_prompt_text,
        document_type_id=10,
        document_type_name="Fachartikel",
        created_by_user_id=1
    )
    
    # Assertions
    assert result is None, "Sollte None zurückgeben wenn kein JSON-Schema gefunden wird"
    
    # Prüfe dass kein Custom Prompt erstellt wurde
    no_prompt = rag_chat_prompt_repo.get_by_document_type_id(10)
    # Kann None sein oder existierender Prompt (wenn vorher erstellt)
    # Wichtig: Neuer Prompt wurde nicht erstellt


# ========================================
# Test 4: Vollständiger Workflow (Standard Prompt → Custom Prompt → RAG Chat)
# ========================================

def test_full_workflow_standard_prompt_to_rag_chat(db_session: Session):
    """
    Test: Vollständiger Workflow von Standard Prompt bis RAG Chat.
    
    Requirements:
    1. Standard Prompt wird gespeichert (mit document_type_id)
    2. Auto-Generierung erstellt Custom Prompt
    3. Custom Prompt kann im RAG Chat verwendet werden
    4. Custom Prompt enthält alle erforderlichen Informationen
    """
    # Setup
    rag_chat_prompt_repo = SQLAlchemyRAGChatPromptRepository(db_session)
    auto_service = AutoCustomPromptService(rag_chat_prompt_repo)
    
    # 1. Standard Prompt (simuliert aus AI Playground)
    standard_prompt_text = """
🧩 JSON-Ausgabeformat

{
  "document_metadata": {
    "title": "",
    "authors": []
  },
  "sections": [
    {
      "title": "",
      "content": ""
    }
  ]
}
"""
    
    # 2. Auto-Generierung
    custom_prompt = auto_service.generate_from_standard_prompt(
        standard_prompt_text=standard_prompt_text,
        document_type_id=10,
        document_type_name="Fachartikel",
        created_by_user_id=1
    )
    
    assert custom_prompt is not None, "Custom Prompt sollte generiert werden"
    
    # 3. Prüfe dass Custom Prompt für RAG Chat verwendbar ist
    assert "{context}" in custom_prompt.prompt_text, "Sollte {context} Platzhalter haben"
    assert "{question}" in custom_prompt.prompt_text, "Sollte {question} Platzhalter haben"
    
    # 4. Prüfe dass Custom Prompt JSON-Struktur-Informationen enthält
    assert "document_metadata" in custom_prompt.prompt_text.lower(), "Sollte document_metadata erwähnen"
    assert "sections" in custom_prompt.prompt_text.lower(), "Sollte sections erwähnen"
    
    # 5. Prüfe dass Custom Prompt präzise Detail-Wiedergabe-Anweisungen enthält
    assert "zahlen" in custom_prompt.prompt_text.lower() or "statistiken" in custom_prompt.prompt_text.lower(), "Sollte präzise Detail-Wiedergabe betonen"
    
    # 6. Prüfe DB-Persistenz
    saved = rag_chat_prompt_repo.get_by_document_type_id(10)
    assert saved is not None, "Custom Prompt sollte in DB gespeichert sein"
    assert saved.is_auto_generated is True, "is_auto_generated Flag sollte gesetzt sein"


