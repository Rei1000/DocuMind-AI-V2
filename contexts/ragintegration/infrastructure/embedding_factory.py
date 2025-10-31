"""
Embedding Service Factory

Wählt automatisch den besten verfügbaren Embedding-Provider basierend auf Konfiguration.
Best Practice: Sentence Transformers als Standard (lokal, kostenlos, sehr gut für RAG).
"""

import os
from typing import Optional
from contexts.ragintegration.domain.repositories import EmbeddingService
from contexts.ragintegration.domain.value_objects import EmbeddingVector


def create_embedding_service(
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    openai_api_key: Optional[str] = None,
    google_api_key: Optional[str] = None
) -> EmbeddingService:
    """
    Factory-Funktion für Embedding Services.
    
    Priorität (AUTO-Mode):
    1. OpenAI GPT-5 Mini Key (1536 dim, wenn verfügbar)
    2. Google Gemini (768 dim, wenn verfügbar)
    3. Sentence Transformers (lokal, kostenlos, sehr gut für RAG/Deutsch)
    4. OpenAI Standard Key (falls funktioniert)
    5. Fallback zu Mock Embeddings
    
    Args:
        provider: "openai" | "google" | "sentence-transformers" | "st" | "auto" (default: auto)
        model_name: Name des Modells (optional)
        openai_api_key: OpenAI API Key (optional, prüft auch OPENAI_GPT5_MINI_API_KEY)
        google_api_key: Google AI API Key (optional)
    
    Returns:
        EmbeddingService Instance
    """
    # Hole Provider aus ENV oder verwende Parameter
    provider = provider or os.getenv("EMBEDDING_PROVIDER", "auto")
    
    # Hole API Keys aus ENV falls nicht übergeben
    if not openai_api_key:
        # Prüfe zuerst GPT-5 Mini Key (hat Zugriff auf Embeddings!)
        openai_api_key = os.getenv("OPENAI_GPT5_MINI_API_KEY") or os.getenv("OPENAI_API_KEY")
    
    if not google_api_key:
        google_api_key = os.getenv("GOOGLE_AI_API_KEY")
    
    # AUTO-Mode: Versuche intelligente Auswahl
    if provider == "auto":
        provider = _select_best_provider(openai_api_key, google_api_key)
    
    # Erstelle entsprechenden Service
    if provider == "openai":
        return _create_openai_service(openai_api_key, model_name)
    elif provider == "google" or provider == "gemini":
        return _create_google_service(google_api_key, model_name)
    elif provider == "sentence-transformers" or provider == "st":
        return _create_sentence_transformers_service(model_name)
    else:
        # Fallback zu Sentence Transformers
        print(f"⚠️ Unbekannter Provider '{provider}', verwende Sentence Transformers")
        return _create_sentence_transformers_service(model_name)


def _select_best_provider(
    openai_api_key: Optional[str] = None,
    google_api_key: Optional[str] = None
) -> str:
    """
    Wählt automatisch den besten verfügbaren Provider.
    
    Priorität (nach Dimensionen und Qualität):
    1. OpenAI GPT-5 Mini Key (1536 dim, best wenn verfügbar)
    2. Google Gemini (768 dim, sehr gut, kostenlos)
    3. Sentence Transformers (768 dim, lokal, kostenlos)
    4. OpenAI Standard Key (1536 dim, falls funktioniert)
    5. Fallback zu Sentence Transformers
    """
    # Prüfe OpenAI GPT-5 Mini Key zuerst (1536 dim, best!)
    # WICHTIG: Prüfe zuerst OPENAI_GPT5_MINI_API_KEY aus ENV (hat Zugriff auf Embeddings!)
    gpt5_mini_key = os.getenv("OPENAI_GPT5_MINI_API_KEY")
    test_key = gpt5_mini_key or openai_api_key
    
    if test_key and test_key != "test-key":
        try:
            from openai import OpenAI
            client = OpenAI(api_key=test_key)
            try:
                response = client.embeddings.create(
                    model="text-embedding-3-small",
                    input="test"
                )
                print("✅ OpenAI Embeddings verfügbar (1536 Dimensionen)")
                if gpt5_mini_key:
                    print("   (Verwendet OPENAI_GPT5_MINI_API_KEY)")
                return "openai"
            except Exception as e:
                error_str = str(e)
                if "does not have access" not in error_str.lower():
                    # Anderer Fehler, wahrscheinlich temporär
                    print(f"⚠️ OpenAI API Fehler (temporär?): {error_str[:100]}")
                else:
                    # Key hat keinen Zugriff - prüfe nächstes Modell
                    pass
        except Exception:
            pass
    
    # Prüfe Google Gemini (768 dim, sehr gut, kostenlos)
    if google_api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=google_api_key)
            result = genai.embed_content(
                model="models/text-embedding-004",
                content="test"
            )
            if result and 'embedding' in result:
                print("✅ Google Gemini Embeddings verfügbar (768 Dimensionen)")
                return "google"
        except ImportError:
            pass
        except Exception as e:
            # Google API Fehler, aber nicht kritisch
            pass
    
    # Prüfe Sentence Transformers (immer verfügbar wenn installiert)
    try:
        import sentence_transformers
        print("✅ Sentence Transformers verfügbar (768 oder 384 Dimensionen)")
        return "sentence-transformers"
    except ImportError:
        pass
    
    # Fallback: Warnung und versuche trotzdem Sentence Transformers
    print("⚠️ Kein Embedding-Provider verfügbar, versuche Sentence Transformers")
    return "sentence-transformers"


def _create_sentence_transformers_service(model_name: Optional[str] = None) -> EmbeddingService:
    """Erstellt Sentence Transformers Embedding Service."""
    try:
        from contexts.ragintegration.infrastructure.embedding_sentence_transformers import SentenceTransformersEmbeddingAdapter
    except ImportError:
        raise ImportError(
            "sentence-transformers ist nicht installiert. "
            "Installiere mit: pip install sentence-transformers"
        )
    
    # Best Practice Modelle für deutsche Dokumente (nach Priorität):
    default_models = [
        "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",  # Best für DE (768 dim)
        "sentence-transformers/multilingual-e5-base",  # Sehr gut für multilingual (768 dim)
        "sentence-transformers/all-MiniLM-L6-v2",  # Schnell, gut (384 dim)
    ]
    
    # Verwende ENV oder Parameter
    model = model_name or os.getenv(
        "EMBEDDING_MODEL",
        default_models[0]  # Best für deutsche Dokumente
    )
    
    return SentenceTransformersEmbeddingAdapter(model_name=model)


def _create_openai_service(
    api_key: Optional[str] = None,
    model_name: Optional[str] = None
) -> EmbeddingService:
    """Erstellt OpenAI Embedding Service."""
    from contexts.ragintegration.infrastructure.embedding_adapter import OpenAIEmbeddingAdapter
    
    # Prüfe zuerst GPT-5 Mini Key (hat Zugriff auf Embeddings!)
    if not api_key or api_key == "test-key":
        api_key = os.getenv("OPENAI_GPT5_MINI_API_KEY") or os.getenv("OPENAI_API_KEY")
    
    if not api_key or api_key == "test-key":
        raise ValueError(
            "OpenAI API Key nicht verfügbar. "
            "Verwende Sentence Transformers oder Google Gemini stattdessen."
        )
    
    model = model_name or os.getenv(
        "OPENAI_EMBEDDING_MODEL",
        "text-embedding-3-small"
    )
    
    return OpenAIEmbeddingAdapter(api_key=api_key, model=model)


def _create_google_service(
    api_key: Optional[str] = None,
    model_name: Optional[str] = None
) -> EmbeddingService:
    """Erstellt Google Gemini Embedding Service."""
    try:
        from contexts.ragintegration.infrastructure.embedding_google_gemini import GoogleGeminiEmbeddingAdapter
    except ImportError:
        raise ImportError(
            "Google Gemini Embedding Adapter nicht gefunden. "
            "Stelle sicher, dass google-generativeai installiert ist."
        )
    
    api_key = api_key or os.getenv("GOOGLE_AI_API_KEY")
    if not api_key:
        raise ValueError(
            "Google AI API Key nicht verfügbar. "
            "Setze GOOGLE_AI_API_KEY in der .env Datei."
        )
    
    model = model_name or os.getenv(
        "GOOGLE_EMBEDDING_MODEL",
        "text-embedding-004"
    )
    
    return GoogleGeminiEmbeddingAdapter(api_key=api_key, model=model)

