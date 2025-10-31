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
    openai_api_key: Optional[str] = None
) -> EmbeddingService:
    """
    Factory-Funktion für Embedding Services.
    
    Priorität:
    1. Sentence Transformers (lokal, kostenlos, sehr gut für RAG/Deutsch)
    2. OpenAI (wenn API Key verfügbar und funktioniert)
    3. Fallback zu Mock Embeddings
    
    Args:
        provider: "sentence-transformers" | "openai" | "auto" (default: auto)
        model_name: Name des Modells (optional)
        openai_api_key: OpenAI API Key (optional)
    
    Returns:
        EmbeddingService Instance
    """
    # Hole Provider aus ENV oder verwende Parameter
    provider = provider or os.getenv("EMBEDDING_PROVIDER", "auto")
    
    # AUTO-Mode: Versuche intelligente Auswahl
    if provider == "auto":
        provider = _select_best_provider(openai_api_key)
    
    # Erstelle entsprechenden Service
    if provider == "sentence-transformers" or provider == "st":
        return _create_sentence_transformers_service(model_name)
    elif provider == "openai":
        return _create_openai_service(openai_api_key, model_name)
    else:
        # Fallback zu Sentence Transformers
        print(f"⚠️ Unbekannter Provider '{provider}', verwende Sentence Transformers")
        return _create_sentence_transformers_service(model_name)


def _select_best_provider(openai_api_key: Optional[str] = None) -> str:
    """
    Wählt automatisch den besten verfügbaren Provider.
    
    Priorität:
    1. Sentence Transformers (immer verfügbar wenn installiert)
    2. OpenAI (nur wenn API Key verfügbar und funktioniert)
    """
    # Prüfe ob Sentence Transformers verfügbar ist
    try:
        import sentence_transformers
        print("✅ Sentence Transformers verfügbar")
        return "sentence-transformers"
    except ImportError:
        pass
    
    # Prüfe OpenAI
    if openai_api_key and openai_api_key != "test-key":
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_api_key)
            # Teste ob Embedding-Modell verfügbar ist
            try:
                response = client.embeddings.create(
                    model="text-embedding-3-small",
                    input="test"
                )
                print("✅ OpenAI Embeddings verfügbar")
                return "openai"
            except Exception:
                # OpenAI Key vorhanden, aber kein Zugriff auf Embeddings
                print("⚠️ OpenAI API Key vorhanden, aber kein Zugriff auf Embedding-Modelle")
                print("   Verwende Sentence Transformers als Fallback")
                # Versuche Sentence Transformers als Fallback
                try:
                    import sentence_transformers
                    return "sentence-transformers"
                except ImportError:
                    pass
        except Exception:
            pass
    
    # Default: Sentence Transformers
    print("⚠️ Kein Embedding-Provider verfügbar, verwende Sentence Transformers")
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
    
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "test-key":
        raise ValueError(
            "OpenAI API Key nicht verfügbar. "
            "Verwende Sentence Transformers stattdessen."
        )
    
    model = model_name or os.getenv(
        "OPENAI_EMBEDDING_MODEL",
        "text-embedding-3-small"
    )
    
    return OpenAIEmbeddingAdapter(api_key=api_key, model=model)

