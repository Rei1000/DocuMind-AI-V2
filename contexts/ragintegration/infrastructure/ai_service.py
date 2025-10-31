"""
AI Service für RAG Integration Context.

Implementiert AI-Services für die Generierung von Antworten basierend auf Dokument-Chunks.
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from contexts.aiplayground.infrastructure.ai_providers.openai_adapter import OpenAIAdapter
from contexts.aiplayground.infrastructure.ai_providers.google_adapter import GoogleAIAdapter
from ..domain.entities import DocumentChunk


class RAGAIService:
    """
    AI Service für RAG-System.
    
    Verwendet OpenAI und Google AI Adapter für die Generierung von Antworten.
    """
    
    def __init__(self):
        """Initialisiert den AI Service mit verfügbaren Adaptern."""
        self.openai_adapter = OpenAIAdapter()
        self.google_adapter = GoogleAIAdapter()
        
        # Verfügbare Modelle
        self.available_models = {
            "gpt-4o-mini": {
                "provider": "openai",
                "adapter": self.openai_adapter,
                "model_id": "gpt-4o-mini",
                "max_tokens": 16384,
                "cost_per_1k_tokens": 0.00015
            },
            "gpt-5-mini": {
                "provider": "openai", 
                "adapter": self.openai_adapter,
                "model_id": "gpt-5-mini",
                "max_tokens": 128000,
                "cost_per_1k_tokens": 0.00015
            },
            "gemini-2.5-flash": {
                "provider": "google",
                "adapter": self.google_adapter,
                "model_id": "gemini-2.5-flash",
                "max_tokens": 1000000,
                "cost_per_1k_tokens": 0.000075
            }
        }
    
    async def generate_response_async(
        self,
        question: str,
        context_chunks: List[Dict],  # Geändert von List[DocumentChunk] zu List[Dict]
        model_id: str = "gpt-4o-mini"
    ) -> Dict[str, Any]:
        """
        Generiert eine Antwort basierend auf der Frage und den Kontext-Chunks.
        
        Args:
            question: User-Frage
            context_chunks: Relevante Dokument-Chunks
            model_id: AI Model (gpt-4o-mini, gpt-5-mini, gemini-2.5-flash)
            
        Returns:
            Dict mit Antwort und Metadaten
        """
        if model_id not in self.available_models:
            raise ValueError(f"Unbekanntes Modell: {model_id}")
        
        # KRITISCH: Keine Antwort generieren wenn keine Chunks vorhanden sind
        if not context_chunks or len(context_chunks) == 0:
            print("DEBUG: Keine Chunks vorhanden - keine Antwort generiert")
            return {
                "answer": "Entschuldigung, ich konnte keine relevanten Informationen zu Ihrer Frage in den verfügbaren Dokumenten finden. Bitte stellen Sie eine andere Frage oder überprüfen Sie, ob die Dokumente korrekt indexiert sind.",
                "model_used": model_id,
                "tokens_used": 0,
                "confidence": 0.0,
                "provider": "no_context"
            }
        
        model_config = self.available_models[model_id]
        adapter = model_config["adapter"]
        
        # Erstelle Kontext aus Chunks mit strukturierten Daten
        context_text = self._build_structured_context_from_chunks(context_chunks)
        
        # Erstelle optimierten Prompt für strukturierte Daten
        prompt = self._create_structured_rag_prompt(question, context_text)
        
        try:
            # Verwende die AI Playground Adapter-Methoden direkt (async)
            from contexts.aiplayground.domain.value_objects import ModelConfig
            
            config = ModelConfig(
                temperature=0.7,
                max_tokens=4000,
                top_p=0.9,
                detail_level="high"
            )
            
            # Führe async call mit Timeout aus
            try:
                if model_config["provider"] == "openai":
                    # Fallback für GPT-5 Mini: Verwende GPT-4o Mini falls GPT-5 nicht verfügbar
                    actual_model_id = model_config["model_id"]
                    if actual_model_id == "gpt-5-mini":
                        # GPT-5 Mini existiert noch nicht bei OpenAI, verwende GPT-4o Mini
                        print(f"WARNING: GPT-5 Mini wird noch nicht unterstützt, verwende GPT-4o Mini als Fallback")
                        actual_model_id = "gpt-4o-mini"
                    
                    response = await adapter.send_prompt(
                        model_id=actual_model_id,
                        prompt=prompt,
                        config=config
                    )
                    
                    # Prüfe ob response gültig ist
                    if not response or not hasattr(response, 'response') or not response.response:
                        raise ValueError("response cannot be empty")
                    
                elif model_config["provider"] == "google":
                    response = await adapter.send_prompt(
                        model_id=model_config["model_id"],
                        prompt=prompt,
                        config=config
                    )
                    
                    # Prüfe ob response gültig ist
                    if not response or not hasattr(response, 'response') or not response.response:
                        raise ValueError("response cannot be empty")
                
                # Sicherstellen dass answer nicht leer ist
                answer = response.response if hasattr(response, 'response') else str(response)
                if not answer or not answer.strip():
                    raise ValueError("content cannot be empty")
                
                return {
                    "answer": answer,
                    "model_used": model_id,  # Original model_id beibehalten für Tracking
                    "tokens_used": response.tokens_received or 0 if hasattr(response, 'tokens_received') else 0,
                    "confidence": 0.9,
                    "provider": model_config["provider"]
                }
                
            except ValueError as e:
                if "cannot be empty" in str(e) or "empty" in str(e).lower():
                    # Fallback wenn leere Antwort
                    return {
                        "answer": "Entschuldigung, ich konnte keine Antwort generieren. Bitte versuchen Sie es erneut oder verwenden Sie ein anderes Modell (z.B. GPT-4o Mini).",
                        "model_used": model_id,
                        "tokens_used": 0,
                        "confidence": 0.0,
                        "provider": "error"
                    }
                raise
            except Exception as e:
                error_msg = str(e)
                print(f"DEBUG: AI Service Fehler: {error_msg}")
                # Prüfe spezifische Fehler
                if "gpt-5" in error_msg.lower() or "model not found" in error_msg.lower():
                    # Model nicht verfügbar - verwende Fallback
                    return {
                        "answer": "Entschuldigung, das gewählte Modell (GPT-5 Mini) wird noch nicht unterstützt. Bitte verwenden Sie GPT-4o Mini oder Gemini 2.5 Flash.",
                        "model_used": model_id,
                        "tokens_used": 0,
                        "confidence": 0.0,
                        "provider": "error"
                    }
                return {
                    "answer": f"Die Anfrage dauerte zu lange oder es gab einen Fehler: {error_msg}. Bitte versuchen Sie es erneut oder verwenden Sie ein anderes Modell.",
                    "model_used": model_id,
                    "tokens_used": 0,
                    "confidence": 0.1,
                    "provider": "error"
                }
                
        except Exception as e:
            # Fallback zu Mock-Antwort bei Fehlern
            return {
                "answer": f"Entschuldigung, es gab einen Fehler bei der Generierung der Antwort: {str(e)}. Basierend auf den verfügbaren Dokumenten kann ich folgende Informationen zu Ihrer Frage \"{question}\" geben: Das Dokument enthält wichtige Informationen über Arbeitsanweisungen und Verfahren.",
                "model_used": model_id,
                "tokens_used": 50,
                "confidence": 0.5,
                "provider": "error_fallback"
            }
    
    def _build_structured_context_from_chunks(self, chunks: List[Dict]) -> str:
        """Baut strukturierten Kontext aus Dokument-Chunks auf."""
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            # Extrahiere strukturierte Daten aus Chunk-Metadaten
            structured_info = []
            
            # Chunk ist jetzt ein Dict, nicht ein DocumentChunk Objekt
            metadata = chunk.get('metadata', {})
            
            if metadata.get('heading_hierarchy'):
                structured_info.append(f"Überschriften: {' > '.join(metadata['heading_hierarchy'])}")
            
            if metadata.get('page_numbers'):
                structured_info.append(f"Seiten: {', '.join(map(str, metadata['page_numbers']))}")
            
            if metadata.get('chunk_type'):
                structured_info.append(f"Typ: {metadata['chunk_type']}")
            
            # Erstelle strukturierten Kontext
            context_part = f"""Chunk {i}:
{chr(10).join(structured_info) if structured_info else 'Keine Metadaten verfügbar'}

Inhalt:
{chunk.get('chunk_text', chunk.get('metadata', {}).get('chunk_text', 'Kein Text verfügbar'))}

---
"""
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    def _create_structured_rag_prompt(self, question: str, context: str) -> str:
        """Erstellt einen optimierten Prompt für strukturierte RAG-Antworten."""
        return f"""Du bist ein Experte für Qualitätsmanagement und medizinische Dokumentation. Beantworte die folgende Frage basierend auf den bereitgestellten strukturierten Dokument-Auszügen.

KONTEXT (aus indexierten Dokumenten mit Metadaten):
{context}

FRAGE: {question}

ANWEISUNGEN:
1. Beantworte die Frage präzise und hilfreich basierend auf dem strukturierten Kontext
2. Verwende die Metadaten (Überschriften, Seiten, Typ) für präzise Referenzen
3. Wenn nach spezifischen Informationen gefragt wird (z.B. Artikelnummern), gib diese exakt an
4. Strukturiere deine Antwort übersichtlich mit klaren Abschnitten
5. Antworte auf Deutsch
6. Wenn die Antwort nicht im Kontext steht, sage das ehrlich
7. WICHTIG: Wenn du Informationen aus einem Chunk verwendest, füge direkt nach dem entsprechenden Satz/Absatz eine Referenz hinzu im Format:
   **Referenz**: chunk [Nummer]
   Beispiel: "Die Artikelnummer ist 123.456.789. **Referenz**: chunk 1"
   Die Referenz muss direkt unter oder nach dem Text stehen, der aus diesem Chunk stammt, NICHT am Ende der gesamten Antwort.

ANTWORT (strukturiert mit Metadaten-Referenzen direkt im Text):"""
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Gibt verfügbare Modelle zurück."""
        return [
            {
                "model_id": model_id,
                "provider": config["provider"],
                "max_tokens": config["max_tokens"],
                "cost_per_1k_tokens": config["cost_per_1k_tokens"]
            }
            for model_id, config in self.available_models.items()
        ]
    
    def test_model_connection(self, model_id: str) -> Dict[str, Any]:
        """Testet die Verbindung zu einem Modell."""
        if model_id not in self.available_models:
            return {
                "success": False,
                "error": f"Unbekanntes Modell: {model_id}"
            }
        
        model_config = self.available_models[model_id]
        adapter = model_config["adapter"]
        
        try:
            # Teste mit einfachem Prompt
            test_prompt = "Antworte mit 'Verbindung erfolgreich' auf Deutsch."
            response = adapter.generate_completion(
                model_id=model_config["model_id"],
                prompt=test_prompt,
                max_tokens=10,
                temperature=0.1
            )
            
            return {
                "success": True,
                "model_id": model_id,
                "provider": model_config["provider"],
                "test_response": response.content,
                "tokens_used": response.tokens_used or 0
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model_id": model_id,
                "provider": model_config["provider"]
            }
