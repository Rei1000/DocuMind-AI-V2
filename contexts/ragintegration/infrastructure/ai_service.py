"""
AI Service für RAG Integration Context.

Implementiert AI-Services für die Generierung von Antworten basierend auf Dokument-Chunks.
"""

import os
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from contexts.aiplayground.infrastructure.ai_providers.openai_adapter import OpenAIAdapter
from contexts.aiplayground.infrastructure.ai_providers.google_adapter import GoogleAIAdapter
from ..domain.entities import DocumentChunk
from ..domain.exceptions import MissingCustomPromptError, InvalidCustomPromptError
from .prompt_structure_detector import detect_prompt_structure_type


class RAGAIService:
    """
    AI Service für RAG-System.
    
    Verwendet OpenAI und Google AI Adapter für die Generierung von Antworten.
    """
    
    def __init__(self, rag_chat_prompt_repo=None):
        """
        Initialisiert den AI Service mit verfügbaren Adaptern.
        
        Args:
            rag_chat_prompt_repo: Optional RAGChatPromptRepository für Custom Prompts (PHASE 1)
        """
        self.openai_adapters = {
            "default": OpenAIAdapter(),
            "gpt-5-mini": OpenAIAdapter(api_key_env_var="OPENAI_GPT5_MINI_API_KEY"),
        }
        self.openai_adapter = self.openai_adapters["default"]
        self.google_adapter = GoogleAIAdapter()
        self.rag_chat_prompt_repo = rag_chat_prompt_repo  # PHASE 1: Für Custom Prompts
        
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
                "adapter": self.openai_adapters["gpt-5-mini"],
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
        model_id: str = "gpt-4o-mini",
        document_type: Optional[str] = None,  # Dokumenttyp für spezifische Prompts
        document_type_id: Optional[int] = None,  # PHASE 1: Document Type ID für Custom Prompt Lookup
        temperature: Optional[float] = None,  # NEU v2.10.3: AI Temperature (optional)
        max_tokens: Optional[int] = None,  # NEU v2.10.3: Max Tokens (optional)
        top_p: Optional[float] = None  # NEU v2.10.3: Top P (optional)
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
        
        # Query-Expansion Detection (Dummy-Chunk mit query_expansion Flag)
        is_query_expansion = (
            context_chunks and 
            len(context_chunks) > 0 and 
            context_chunks[0].get('metadata', {}).get('query_expansion', False)
        )
        
        # Prompt wird IMMER generiert, auch wenn keine Chunks vorhanden sind
        # Dies stellt sicher, dass der Prompt audit-sicher gespeichert werden kann
        has_chunks = context_chunks and len(context_chunks) > 0
        
        # Initialisiere Variable für Custom Prompt Platzhalter-Warnung
        custom_prompt_missing_placeholders = False
        
        model_config = self.available_models[model_id]
        adapter = model_config["adapter"]
        
        # Für Query-Expansion: Frage direkt als Prompt verwenden, kein Chunk-Kontext
        if is_query_expansion:
            # Frage ist bereits der Prompt für Query-Expansion
            prompt_text = question
            document_type = None  # Kein dokumenttyp-spezifischer Prompt für Query-Expansion
        else:
            # Erstelle Kontext aus Chunks (leer wenn keine Chunks vorhanden)
            if has_chunks:
                context_text = self._build_structured_context_from_chunks(context_chunks)
            else:
                context_text = ""  # Leerer Context wenn keine Chunks
            
            # Bestimme document_type aus Chunks falls nicht übergeben
            if not document_type and has_chunks:
                # Versuche document_type aus Metadaten zu extrahieren
                first_chunk = context_chunks[0]
                metadata = first_chunk.get('metadata', {})
                document_type = metadata.get('document_type') or metadata.get('document_type_name')
            
            # Erstelle dokumenttyp-spezifischen Prompt IMMER (auch bei No-Chunks)
            # document_type kann None sein (generischer Prompt), aber Prompt wird trotzdem generiert
            prompt_text, custom_prompt_missing_placeholders = self._create_structured_rag_prompt(question, context_text, document_type, document_type_id)
        
        # Wenn keine Chunks vorhanden und keine Query-Expansion, generiere trotzdem Antwort mit Prompt
        # Dies stellt sicher, dass der Prompt audit-sicher gespeichert werden kann
        if not has_chunks and not is_query_expansion:
            pass
        
        try:
            # Verwende die AI Playground Adapter-Methoden direkt (async)
            from contexts.aiplayground.domain.value_objects import ModelConfig
            
            # Für Query-Expansion: Andere Config (kürzer, direkter)
            if is_query_expansion:
                config = ModelConfig(
                    temperature=0.8,  # Kreativer für Varianten
                    max_tokens=200,  # Kurz, nur Varianten
                    top_p=0.9
                )
            else:
                # NEU v2.10.3: Verwende übergebene Einstellungen oder Defaults
                # Default Temperature auf 0.0 für konsistente Antworten
                # Default Max Tokens auf 8000 (max für GPT-4o Mini Schema)
                config = ModelConfig(
                    temperature=temperature if temperature is not None else 0.0,
                    max_tokens=max_tokens if max_tokens is not None else 8000,
                    top_p=top_p if top_p is not None else 0.9,
                    detail_level="high"
                )
            
            # Führe async call mit Timeout aus
            try:
                if model_config["provider"] == "openai":
                    actual_model_id = model_config["model_id"]
                    
                    # Strikte GPT-5 Mini Logik: Kein Fallback, eigener Adapter
                    if actual_model_id == "gpt-5-mini":
                        if not os.getenv("OPENAI_GPT5_MINI_API_KEY"):
                            raise RuntimeError("❌ GPT-5 Mini angefordert, aber OPENAI_GPT5_MINI_API_KEY ist nicht gesetzt.")
                        adapter = self.openai_adapters["gpt-5-mini"]
                    
                    response = await adapter.send_prompt(
                        model_id=actual_model_id,
                        prompt=prompt_text,
                        config=config
                    )
                    
                    # Prüfe ob response gültig ist
                    if not response or not hasattr(response, 'response') or not response.response:
                        raise ValueError("response cannot be empty")
                    
                elif model_config["provider"] == "google":
                    response = await adapter.send_prompt(
                        model_id=model_config["model_id"],
                        prompt=prompt_text,
                        config=config
                    )
                    
                    # Prüfe ob response gültig ist
                    if not response or not hasattr(response, 'response') or not response.response:
                        raise ValueError("response cannot be empty")
                
                # Sicherstellen dass answer nicht leer ist
                answer = response.response if hasattr(response, 'response') else str(response)
                if not answer or not answer.strip():
                    raise ValueError("content cannot be empty")
                
                # NEU v2.10.8: Parse JSON-Antwort falls vorhanden (für Custom Prompts mit JSON-Format)
                # Wenn die Antwort mit "{" beginnt und "answer" enthält, versuche JSON zu parsen
                answer_cleaned = answer.strip()
                if answer_cleaned.startswith('{') and '"answer"' in answer_cleaned:
                    try:
                        # Entferne mögliche Markdown-Code-Blöcke (```json ... ```)
                        if answer_cleaned.startswith('```json'):
                            answer_cleaned = answer_cleaned[7:].strip()
                        elif answer_cleaned.startswith('```'):
                            answer_cleaned = answer_cleaned[3:].strip()
                        if answer_cleaned.endswith('```'):
                            answer_cleaned = answer_cleaned[:-3].strip()
                        
                        # Parse JSON
                        parsed_json = json.loads(answer_cleaned)
                        if isinstance(parsed_json, dict) and 'answer' in parsed_json:
                            # Extrahiere nur den answer-Teil
                            answer = parsed_json['answer']
                            print(f"DEBUG: JSON-Antwort geparst, answer extrahiert: {answer[:100]}...")
                    except (json.JSONDecodeError, KeyError) as e:
                        # Wenn JSON-Parsing fehlschlägt, verwende Original-Antwort
                        print(f"DEBUG: JSON-Parsing fehlgeschlagen, verwende Original-Antwort: {e}")
                        pass
                
                result = {
                    "answer": answer,
                    "model_used": model_id,  # Original model_id beibehalten für Tracking
                    "tokens_used": response.tokens_received or 0 if hasattr(response, 'tokens_received') else 0,
                    "confidence": 0.9,
                    "provider": model_config["provider"],
                    "prompt_text": prompt_text  # PHASE 3: Prompt für Prompt Viewer speichern
                }
                # Füge Warnung hinzu wenn Custom Prompt Platzhalter fehlen
                if custom_prompt_missing_placeholders:
                    result["custom_prompt_missing_placeholders"] = True
                return result
                
            except ValueError as e:
                if "cannot be empty" in str(e) or "empty" in str(e).lower():
                    # Fallback wenn leere Antwort - Prompt muss trotzdem gespeichert werden
                    fallback_prompt_text = prompt_text if 'prompt_text' in locals() else self._create_structured_rag_prompt(question, "", document_type, document_type_id)[0]
                    result = {
                        "answer": "Entschuldigung, ich konnte keine Antwort generieren. Bitte versuchen Sie es erneut oder verwenden Sie ein anderes Modell (z.B. GPT-4o Mini).",
                        "model_used": model_id,
                        "tokens_used": 0,
                        "confidence": 0.0,
                        "provider": "error",
                        "prompt_text": fallback_prompt_text
                    }
                    if custom_prompt_missing_placeholders:
                        result["custom_prompt_missing_placeholders"] = True
                    return result
                raise
            except Exception as e:
                error_msg = str(e)
                # Prüfe spezifische Fehler
                if "gpt-5" in error_msg.lower() or "model not found" in error_msg.lower():
                    # GPT-5 Mini Fehler - kein Fallback, Fehler weiterwerfen
                    raise RuntimeError(f"❌ GPT-5 Mini API-Fehler: {error_msg}")
                # Prompt muss auch bei Fehlern gespeichert werden
                if 'prompt_text' not in locals():
                    fallback_prompt_text, fallback_missing_placeholders = self._create_structured_rag_prompt(question, "", document_type, document_type_id)
                else:
                    fallback_prompt_text = prompt_text
                    fallback_missing_placeholders = custom_prompt_missing_placeholders
                result = {
                    "answer": f"Die Anfrage dauerte zu lange oder es gab einen Fehler: {error_msg}. Bitte versuchen Sie es erneut oder verwenden Sie ein anderes Modell.",
                    "model_used": model_id,
                    "tokens_used": 0,
                    "confidence": 0.1,
                    "provider": "error",
                    "prompt_text": fallback_prompt_text
                }
                if fallback_missing_placeholders:
                    result["custom_prompt_missing_placeholders"] = True
                return result
                
        except Exception as e:
            # Fallback zu Mock-Antwort bei Fehlern - Prompt muss trotzdem generiert werden
            if 'prompt_text' not in locals():
                fallback_prompt_text, fallback_missing_placeholders = self._create_structured_rag_prompt(question, "", document_type, document_type_id)
            else:
                fallback_prompt_text = prompt_text
                fallback_missing_placeholders = custom_prompt_missing_placeholders
            result = {
                "answer": f"Entschuldigung, es gab einen Fehler bei der Generierung der Antwort: {str(e)}. Basierend auf den verfügbaren Dokumenten kann ich folgende Informationen zu Ihrer Frage \"{question}\" geben: Das Dokument enthält wichtige Informationen über Arbeitsanweisungen und Verfahren.",
                "model_used": model_id,
                "tokens_used": 50,
                "confidence": 0.5,
                "provider": "error_fallback",
                "prompt_text": fallback_prompt_text
            }
            if fallback_missing_placeholders:
                result["custom_prompt_missing_placeholders"] = True
            return result
    
    def _build_structured_context_from_chunks(self, chunks: List[Dict]) -> str:
        """Baut strukturierten Kontext aus Dokument-Chunks auf."""
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            # Extrahiere strukturierte Daten aus Chunk-Metadaten
            structured_info = []
            
            # Chunk ist jetzt ein Dict, nicht ein DocumentChunk Objekt
            metadata = chunk.get('metadata', {})
            
            # WICHTIG: document_title und document_id für detaillierte Referenzen
            if metadata.get('document_title'):
                structured_info.append(f"Dokument: {metadata['document_title']}")
            
            if metadata.get('document_id') or metadata.get('upload_document_id'):
                document_id = metadata.get('document_id') or metadata.get('upload_document_id')
                structured_info.append(f"Dokument-ID: {document_id}")
            
            if metadata.get('heading_hierarchy'):
                structured_info.append(f"Überschriften: {' > '.join(metadata['heading_hierarchy'])}")
            
            if metadata.get('page_numbers'):
                structured_info.append(f"Seiten: {', '.join(map(str, metadata['page_numbers']))}")
            
            if metadata.get('chunk_type'):
                structured_info.append(f"Typ: {metadata['chunk_type']}")
            
            # Erstelle strukturierten Kontext
            # WICHTIG: Verwende vollständigen Chunk-Text für bessere Antwortqualität
            # Keine Kürzung mehr - verwende vollständige Chunks für ausführliche, präzise Antworten
            chunk_text = chunk.get('chunk_text', chunk.get('metadata', {}).get('chunk_text', 'Kein Text verfügbar'))
            
            context_part = f"""Chunk {i}:
{chr(10).join(structured_info) if structured_info else 'Keine Metadaten verfügbar'}

Inhalt:
{chunk_text}

---
"""
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    def _create_structured_rag_prompt(
        self, 
        question: str, 
        context: str, 
        document_type: Optional[str] = None,
        document_type_id: Optional[int] = None
    ) -> tuple[str, bool]:
        """
        Erstellt einen dokumenttyp-spezifischen Prompt für strukturierte RAG-Antworten.
        
        Implementiert strikte Custom-Prompt-Enforcement-Regeln:
        
        1. Wenn document_type_id gesetzt ist, MUSS ein Custom Prompt existieren.
           Falls nicht, wird MissingCustomPromptError geworfen.
        
        2. Custom Prompt MUSS die Platzhalter {context} und {question} enthalten.
           Falls nicht, wird InvalidCustomPromptError geworfen.
        
        3. Wenn beide Platzhalter vorhanden sind, werden sie durch die tatsächlichen
           Werte ersetzt und der vollständige Prompt zurückgegeben.
        
        4. Keine System-Prompts, Hardcoded-Prefixe oder Fallbacks werden verwendet,
           wenn document_type_id gesetzt ist.
        
        Args:
            question: Die vom Benutzer gestellte Frage.
            context: Formatierter Kontext aus den gefundenen Dokument-Chunks.
            document_type: Optionaler Dokumenttyp-Name (nur für Fehlermeldungen).
            document_type_id: Optionaler Dokumenttyp-ID für Custom Prompt Lookup.
        
        Returns:
            Tuple (prompt_text, missing_placeholders):
            - prompt_text: Der vollständig zusammengesetzte Prompt (exakt wie verwendet).
            - missing_placeholders: Immer False (Platzhalter-Validierung erfolgt vorher).
        
        Raises:
            MissingCustomPromptError: Wenn document_type_id gesetzt ist, aber kein
                Custom Prompt für diesen Dokumenttyp existiert.
            InvalidCustomPromptError: Wenn ein Custom Prompt existiert, aber die
                erforderlichen Platzhalter {context} und/oder {question} fehlen.
        
        Note:
            Diese Methode implementiert die strikte Custom-Prompt-Enforcement-Logik
            gemäß CR-P2.2. Keine Fallbacks, keine automatischen Reparaturen.
        """
        # STRICTE REGEL 1: Wenn document_type_id gesetzt → Custom Prompt MUSS existieren
        if document_type_id:
            if not self.rag_chat_prompt_repo:
                raise MissingCustomPromptError(
                    document_type_id=document_type_id,
                    document_type_name=document_type
                )
            
            custom_prompt = self.rag_chat_prompt_repo.get_by_document_type_id(document_type_id)
            if not custom_prompt:
                raise MissingCustomPromptError(
                    document_type_id=document_type_id,
                    document_type_name=document_type
                )
            
            # STRICTE REGEL 2: Custom Prompt MUSS {context} und {question} enthalten
            custom_prompt_text = custom_prompt.prompt_text
            has_context_placeholder = "{context}" in custom_prompt_text
            has_question_placeholder = "{question}" in custom_prompt_text
            
            missing_placeholders = []
            if not has_context_placeholder:
                missing_placeholders.append("{context}")
            if not has_question_placeholder:
                missing_placeholders.append("{question}")
            
            if missing_placeholders:
                raise InvalidCustomPromptError(
                    document_type_id=document_type_id,
                    missing_placeholders=missing_placeholders,
                    document_type_name=document_type
                )
            
            # STRICTE REGEL 3: Platzhalter ersetzen und vollständigen Prompt zurückgeben
            prompt_text = custom_prompt_text.replace("{context}", context).replace("{question}", question)
            return (prompt_text, False)
        
        # Fallback: Nur wenn KEIN document_type_id gesetzt (z.B. "Alle Typen" Filter)
        # Dann darf generischer Prompt verwendet werden
        base_instructions = self._get_document_type_prompt_instructions(document_type, document_type_id)
        
        prompt_text = f"""Du bist ein Experte für Qualitätsmanagement und medizinische Dokumentation. Beantworte die folgende Frage basierend auf den bereitgestellten strukturierten Dokument-Auszügen.

KONTEXT (aus indexierten Dokumenten mit Metadaten):
{context}

FRAGE: {question}

{base_instructions}

ANTWORT (strukturiert mit Metadaten-Referenzen direkt im Text):"""
        
        return (prompt_text, False)
    
    def _get_document_type_prompt_instructions(
        self, 
        document_type: Optional[str],
        document_type_id: Optional[int] = None  # PHASE 1: Für Custom Prompt Lookup
    ) -> str:
        """
        Erstellt dokumenttyp-spezifische Prompt-Anweisungen.
        
        Basierend auf dem Standard-Prompt für den Dokumenttyp. Priorität:
        1. Custom RAG Chat Prompt (aus rag_chat_prompts)
        2. Standard Prompt (aus prompt_templates + Analyse)
        3. Generischer Prompt (Fallback)
        
        Args:
            document_type: Dokumenttyp-Name (optional)
            document_type_id: Dokumenttyp-ID für Custom Prompt Lookup (optional)
            
        Returns:
            Prompt-Anweisungen als String
        """
        # Prüfe Custom Prompt zuerst
        if document_type_id and self.rag_chat_prompt_repo:
            custom_prompt = self.rag_chat_prompt_repo.get_by_document_type_id(document_type_id)
            if custom_prompt:
                return custom_prompt.prompt_text
        
        if not document_type:
            # Generischer Prompt als Fallback
            return self._get_generic_prompt_instructions()
        
        doc_type_upper = document_type.upper()
        
        # Hole den aktiven Standard-Prompt für diesen Dokumenttyp
        active_prompt = self._get_active_standard_prompt(doc_type_upper)
        
        if active_prompt and active_prompt.get('prompt_text'):
            prompt_text = active_prompt['prompt_text']
            
            detected_type = detect_prompt_structure_type(prompt_text)
            
            if detected_type == "flowchart":
                return """ANWEISUNGEN (Flussdiagramm):
1. Beantworte die Frage präzise basierend auf dem Prozessfluss und den Entscheidungspunkten
2. Fokussiere dich auf die relevanten Schritte und Entscheidungen im Prozess
3. Verwende konkrete Informationen aus den Nodes und Verbindungen
4. Wenn nach spezifischen Informationen gefragt wird (z.B. Artikelnummern, Schritte), gib diese exakt an
5. Antworte auf Deutsch, kurz und präzise
6. Wenn die Antwort nicht im Kontext steht, sage das ehrlich
7. WICHTIG: Wenn du Informationen aus einem Chunk verwendest, füge direkt nach dem entsprechenden Satz eine Referenz hinzu:
   **Referenz**: chunk [Nummer]
   Beispiel: "Im Schritt 6 wird der Fehler geprüft. **Referenz**: chunk 1"
   Die Referenz muss direkt nach dem verwendeten Text stehen, NICHT am Ende."""
            
            elif detected_type == "work_instruction":
                return """ANWEISUNGEN (Arbeitsanweisung):
1. Beantworte die Frage präzise basierend auf den konkreten Schritten und Anweisungen
2. Verwende die exakten Schrittnummern und Beschreibungen aus dem Dokument
3. Wenn nach spezifischen Informationen gefragt wird (z.B. Artikelnummern, Teilenummern), gib diese EXAKT aus dem Dokument an
4. Fokussiere dich auf die relevanten Textpassagen - vermeide unnötige Erklärungen
5. Antworte auf Deutsch, kurz und präzise - nur die relevanten Informationen
6. Wenn die Antwort nicht im Kontext steht, sage das ehrlich
7. WICHTIG: Wenn du Informationen aus einem Chunk verwendest, füge direkt nach dem entsprechenden Satz eine Referenz hinzu:
   **Referenz**: chunk [Nummer]
   Beispiel: "Die Artikelnummer der Passfeder ist 123.456.789. **Referenz**: chunk 1"
   Die Referenz muss direkt nach dem verwendeten Text stehen, NICHT am Ende."""
            
            elif detected_type == "sop":
                return """ANWEISUNGEN (SOP/Prozess):
1. Beantworte die Frage präzise basierend auf den Prozessschritten und Compliance-Anforderungen
2. Verwende die konkreten Prozessschritte und kritischen Regeln aus dem Dokument
3. Wenn nach spezifischen Informationen gefragt wird, gib diese exakt an
4. Strukturiere deine Antwort nach Prozessschritten wenn relevant
5. Antworte auf Deutsch, präzise und fokussiert
6. Wenn die Antwort nicht im Kontext steht, sage das ehrlich
7. WICHTIG: Wenn du Informationen aus einem Chunk verwendest, füge direkt nach dem entsprechenden Satz eine Referenz hinzu:
   **Referenz**: chunk [Nummer]
   Beispiel: "Im Prozessschritt 6 wird der Fehler geprüft. **Referenz**: chunk 1"
   Die Referenz muss direkt nach dem verwendeten Text stehen, NICHT am Ende."""
            
            elif detected_type == "research_article":
                return """ANWEISUNGEN (Fachartikel - Wissenschaftlicher Brandschutz):
Du bist ein erfahrener Wissenschaftler im Bereich Brandschutz und Brandschutztechnik mit Expertise in wissenschaftlicher Methodik und Literaturanalyse.

1. **Wissenschaftlicher Ansatz:**
   - Beantworte die Frage basierend auf wissenschaftlichen Erkenntnissen aus dem Fachartikel
   - Nutze die strukturierten Informationen aus document_metadata (Autoren, Journal, Jahr, Keywords)
   - Berücksichtige die Methoden, Experimente und Ergebnisse aus den sections
   - Stelle Verbindungen zwischen verschiedenen Abschnitten her, wenn relevant

2. **Detaillierte Wiedergabe:**
   - Nutze die vollständige JSON-Struktur (document_metadata, abstract, sections mit content_summary, methods, experiments)
   - Gib konkrete Zahlen, Werte, Formeln und technische Details exakt wieder
   - Verwende die Fachterminologie aus dem Dokument (z.B. "Verbunddeckensysteme", "Membranwirkung", "ETK")
   - Erkläre komplexe Konzepte wissenschaftlich präzise, aber verständlich

3. **Quellen und Verweise:**
   - Zitiere immer die Quelle: [Autoren] (Jahr) - "Titel", Journal, Band/Heft
   - Beispiel: "Müller et al. (2020) - 'Methode zur effizienten Modellierung von Verbunddeckensystemen im Brandfall', BAUINGENIEUR, Band 95, Heft 2"
   - Verweise auf normative_references aus den sections (z.B. "Eurocode 1 Teil 1-2 [4]")
   - Erwähne experimentelle Validierungen und deren Quellen (z.B. "Brandversuche der TU München [2]")

4. **Strukturierung:**
   - Beginne mit einer kurzen Einordnung in den wissenschaftlichen Kontext
   - Strukturiere die Antwort nach den relevanten sections (section_number, title)
   - Nutze die heading_hierarchy aus den Chunk-Metadaten für präzise Referenzen
   - Schließe mit einer wissenschaftlichen Zusammenfassung, wenn relevant

5. **Präzision und Vollständigkeit:**
   - Antworte auf Deutsch, wissenschaftlich präzise und vollständig
   - Gib alle relevanten technischen Details an (Temperaturkurven, Materialeigenschaften, Berechnungsmethoden)
   - Erwähne Einschränkungen oder Annahmen, wenn im Dokument beschrieben
   - Wenn die Antwort nicht im Kontext steht, sage das ehrlich und wissenschaftlich fundiert

6. **Quellenangaben im Text:**
   - WICHTIG: Wenn du Informationen aus einem Chunk verwendest, füge direkt nach dem entsprechenden Satz/Absatz eine Quellenangabe hinzu:
     **Quelle**: [Autoren] (Jahr), chunk [Nummer], Seite [X]
   - Beispiel: "Die Membranwirkung wird durch geometrisch nicht-lineare Berechnung berücksichtigt. **Quelle**: Müller et al. (2020), chunk 1, Seite 48"
   - Die Quellenangabe muss direkt nach dem verwendeten Text stehen, NICHT am Ende der gesamten Antwort
   - Bei mehreren Quellen: **Quellen**: [Autoren1] (Jahr), chunk [X], Seite [Y]; [Autoren2] (Jahr), chunk [Z], Seite [W]"""
        
        # Fallback: Generischer Prompt
        return self._get_generic_prompt_instructions()
    
    def _get_generic_prompt_instructions(self) -> str:
        """Generischer Prompt als Fallback."""
        return """ANWEISUNGEN:
1. Beantworte die Frage präzise und hilfreich basierend auf dem strukturierten Kontext
2. Verwende die Metadaten (Überschriften, Seiten, Typ) für präzise Referenzen
3. Wenn nach spezifischen Informationen gefragt wird (z.B. Artikelnummern), gib diese exakt an
4. Strukturiere deine Antwort übersichtlich mit klaren Abschnitten
5. Antworte auf Deutsch
6. Wenn die Antwort nicht im Kontext steht, sage das ehrlich
7. WICHTIG: Wenn du Informationen aus einem Chunk verwendest, füge direkt nach dem entsprechenden Satz/Absatz eine Referenz hinzu im Format:
   **Referenz**: chunk [Nummer]
   Beispiel: "Die Artikelnummer ist 123.456.789. **Referenz**: chunk 1"
   Die Referenz muss direkt unter oder nach dem Text stehen, der aus diesem Chunk stammt, NICHT am Ende der gesamten Antwort."""
    
    def _get_active_standard_prompt(self, document_type: str) -> Optional[Dict[str, Any]]:
        """
        Hole den aktiven Standardprompt für einen Dokumenttyp.
        """
        try:
            from backend.app.database import get_db
            from sqlalchemy import text
            
            db_session = next(get_db())
            result = db_session.execute(text('''
                SELECT pt.id, pt.name, pt.prompt_text, pt.status
                FROM prompt_templates pt
                JOIN document_types dt ON pt.document_type_id = dt.id
                WHERE dt.name = :doc_type 
                AND pt.status = 'active'
                ORDER BY pt.created_at DESC
                LIMIT 1
            '''), {"doc_type": document_type.title()})
            
            row = result.fetchone()
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'prompt_text': row[2],
                    'status': row[3]
                }
            return None
            
        except Exception as e:
            return None
    
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
