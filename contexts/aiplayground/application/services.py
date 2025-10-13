"""
AI Playground Service

Application Service - Orchestriert Use Cases und Provider Adapters.
"""

from typing import List, Dict, Optional, AsyncGenerator
import asyncio
import json

from contexts.aiplayground.domain.entities import TestResult, ConnectionTest, StreamingChunk
from contexts.aiplayground.domain.value_objects import (
    ModelConfig,
    ModelDefinition,
    AVAILABLE_MODELS,
    OPENAI_PROVIDER,
    OPENAI_GPT5_PROVIDER,
    GOOGLE_PROVIDER
)
from contexts.aiplayground.infrastructure.ai_providers.base import AIProviderAdapter
from contexts.aiplayground.infrastructure.ai_providers.openai_adapter import OpenAIAdapter
from contexts.aiplayground.infrastructure.ai_providers.google_adapter import GoogleAIAdapter


class AIPlaygroundService:
    """
    Application Service: AI Playground
    
    Orchestriert AI Provider Adapters und Use Cases.
    Keine Business Logic hier - nur Koordination!
    
    Beispiel:
        service = AIPlaygroundService()
        models = service.get_available_models()
        result = await service.test_model("gpt-4", "Hello World")
    """
    
    def __init__(self):
        """Initialize Service mit Provider Adapters"""
        self._adapters: Dict[str, AIProviderAdapter] = {
            "openai": OpenAIAdapter(),
            "openai_gpt5": OpenAIAdapter(api_key_env_var="OPENAI_GPT5_MINI_API_KEY"),
            "google": GoogleAIAdapter()
        }
    
    def get_available_models(self) -> List[Dict]:
        """
        Use Case: Get Available Models
        
        Liefert alle verfügbaren AI-Modelle mit Status.
        
        Returns:
            Liste von Model-Dictionaries mit is_configured Flag
        """
        models = []
        
        for model in AVAILABLE_MODELS:
            adapter = self._get_adapter_for_provider(model.provider.name)
            
            model_dict = model.to_dict()
            model_dict["is_configured"] = adapter.is_configured if adapter else False
            
            models.append(model_dict)
        
        return models
    
    def get_model_by_id(self, model_id: str) -> Optional[ModelDefinition]:
        """
        Get Model Definition by ID
        
        Args:
            model_id: Model ID (z.B. "gpt-4")
            
        Returns:
            ModelDefinition oder None
        """
        for model in AVAILABLE_MODELS:
            if model.id == model_id:
                return model
        return None
    
    async def test_connection(self, model_id: str) -> ConnectionTest:
        """
        Use Case: Test Model Connection
        
        Testet ob die Verbindung zum AI-Provider funktioniert.
        
        Args:
            model_id: Model ID (z.B. "gpt-4")
            
        Returns:
            ConnectionTest Entity
            
        Raises:
            ValueError: Wenn Model nicht gefunden
        """
        model = self.get_model_by_id(model_id)
        
        if not model:
            return ConnectionTest(
                provider="Unknown",
                model_name=model_id,
                success=False,
                error_message=f"Model '{model_id}' nicht gefunden"
            )
        
        adapter = self._get_adapter_for_provider(model.provider.name)
        
        if not adapter:
            return ConnectionTest(
                provider=model.provider.display_name,
                model_name=model.name,
                success=False,
                error_message=f"Adapter für Provider '{model.provider.name}' nicht gefunden"
            )
        
        return await adapter.test_connection(model.model_id)
    
    def _find_model_by_id(self, model_id: str) -> Optional[ModelDefinition]:
        """
        Private Helper: Finde Model Definition by ID
        
        Args:
            model_id: Model ID (z.B. "gpt-4o-mini")
            
        Returns:
            ModelDefinition oder None wenn nicht gefunden
        """
        return self.get_model_by_id(model_id)
    
    async def test_model(
        self,
        model_id: str,
        prompt: str,
        config: Optional[ModelConfig] = None,
        image_data: Optional[str] = None
    ) -> TestResult:
        """
        Use Case: Test Model mit Prompt (und optional Bild)
        
        Sendet einen Prompt an ein AI-Model und liefert Ergebnis.
        
        Args:
            model_id: Model ID (z.B. "gpt-4")
            prompt: User Prompt
            config: Optional Model Configuration
            image_data: Optional Base64-encoded image
            
        Returns:
            TestResult Entity mit Response und Metrics
            
        Raises:
            ValueError: Wenn Model nicht gefunden
        """
        model = self.get_model_by_id(model_id)
        
        if not model:
            return TestResult(
                model_name=model_id,
                provider="Unknown",
                prompt=prompt,
                response="",
                tokens_sent=0,
                tokens_received=0,
                response_time=0.0,
                success=False,
                error_message=f"Model '{model_id}' nicht gefunden"
            )
        
        adapter = self._get_adapter_for_provider(model.provider.name)
        
        if not adapter:
            return TestResult(
                model_name=model.name,
                provider=model.provider.display_name,
                prompt=prompt,
                response="",
                tokens_sent=0,
                tokens_received=0,
                response_time=0.0,
                success=False,
                error_message=f"Adapter für Provider '{model.provider.name}' nicht gefunden"
            )
        
        # Use default config if not provided
        if config is None:
            config = ModelConfig()
        
        return await adapter.send_prompt(model.model_id, prompt, config, image_data=image_data)
    
    async def compare_models(
        self,
        model_ids: List[str],
        prompt: str,
        config: Optional[ModelConfig] = None,
        image_data: Optional[str] = None
    ) -> List[TestResult]:
        """
        Use Case: Compare Multiple Models
        
        Sendet denselben Prompt an mehrere Modelle parallel.
        Mit 180s Timeout pro Modell.
        
        Args:
            model_ids: Liste von Model IDs
            prompt: User Prompt
            config: Optional Model Configuration
            image_data: Optional Base64-encoded image
            
        Returns:
            Liste von TestResult Entities (eins pro Model)
        """
        # Run all tests in parallel with timeout per model
        async def test_with_timeout(model_id: str):
            try:
                return await asyncio.wait_for(
                    self.test_model(model_id, prompt, config, image_data),
                    timeout=240.0  # 4 minutes timeout per model (für komplexe Prompts + Bilder)
                )
            except asyncio.TimeoutError:
                model = self.get_model_by_id(model_id)
                return TestResult(
                    model_name=model.name if model else model_id,
                    provider=model.provider.display_name if model else "Unknown",
                    prompt=prompt,
                    response="",
                    tokens_sent=0,
                    tokens_received=0,
                    response_time=240.0,
                    success=False,
                    error_message="Timeout: Modell hat nach 4 Minuten nicht geantwortet"
                )
        
        tasks = [test_with_timeout(model_id) for model_id in model_ids]
        results = await asyncio.gather(*tasks)
        return results
    
    def _get_adapter_for_provider(self, provider_name: str) -> Optional[AIProviderAdapter]:
        """
        Get Adapter für Provider
        
        Args:
            provider_name: Provider Name (z.B. "openai")
            
        Returns:
            AIProviderAdapter oder None
        """
        return self._adapters.get(provider_name.lower())
    
    async def test_model_stream(
        self, 
        model_id: str, 
        prompt: str, 
        config: ModelConfig,
        image_data: Optional[str] = None
    ) -> AsyncGenerator[StreamingChunk, None]:
        """
        Use Case: Test Model with Streaming
        
        Testet ein AI-Modell mit Streaming-Response.
        Gibt Chunks zurück, sobald sie verfügbar sind.
        
        Args:
            model_id: Model ID (z.B. "gpt-4o-mini")
            prompt: Der Prompt-Text
            config: Model-Konfiguration
            image_data: Optional: Base64-encoded image
            
        Yields:
            StreamingChunk: Einzelne Chunks der Response
        """
        # Finde das Modell
        model_def = self._find_model_by_id(model_id)
        if not model_def:
            yield StreamingChunk(
                content=f"❌ Modell '{model_id}' nicht gefunden",
                is_final=True,
                model_name=model_id,
                provider="unknown"
            )
            return
        
        # Hole den Provider Adapter
        adapter = self._get_adapter_for_provider(model_def.provider.name)
        if not adapter:
            yield StreamingChunk(
                content=f"❌ Provider '{model_def.provider.name}' nicht verfügbar",
                is_final=True,
                model_name=model_def.name,
                provider=model_def.provider.name  # Convert to string
            )
            return
        
        try:
            print(f"[SERVICE] Starting streaming for model: {model_id}")
            # Starte Streaming
            chunk_index = 0
            async for chunk_content in adapter.test_model_stream(
                model_id=model_id,
                prompt=prompt,
                config=config,
                image_data=image_data
            ):
                print(f"[SERVICE] Received chunk {chunk_index}: '{chunk_content}'")
                yield StreamingChunk(
                    content=chunk_content,
                    is_final=False,
                    model_name=model_def.name,
                    provider=model_def.provider.name,  # Convert to string
                    chunk_index=chunk_index
                )
                chunk_index += 1
            
            print(f"[SERVICE] Streaming completed with {chunk_index} chunks")
            # Finaler Chunk mit Token-Metriken
            yield StreamingChunk(
                content="",
                is_final=True,
                model_name=model_def.name,
                provider=model_def.provider.name,  # Convert to string
                chunk_index=chunk_index
            )
            
        except Exception as e:
            yield StreamingChunk(
                content=f"❌ Fehler beim Streaming: {str(e)}",
                is_final=True,
                model_name=model_def.name,
                provider=model_def.provider.name  # Convert to string
            )
    
    async def evaluate_comparison_results(
        self,
        evaluator_prompt: str,
        test_results: List[TestResult],
        evaluator_model_id: str
    ) -> List[Dict]:
        """
        Use Case: Evaluate Comparison Results
        
        Bewertet alle Modell-Outputs mit einem Evaluator-Prompt.
        Jedes Modell wird einzeln nach den Kriterien bewertet.
        
        Args:
            evaluator_prompt: Der Evaluator-Prompt (z.B. aus PromptTemplate)
            test_results: Liste der zu bewertenden Results (alle Modelle)
            evaluator_model_id: Modell für die Evaluation
            
        Returns:
            Liste von Evaluation Results mit Scores und Begründungen
        """
        evaluation_results = []
        
        # Finde Evaluator-Model
        evaluator_model = self._find_model_by_id(evaluator_model_id)
        if not evaluator_model:
            raise ValueError(f"Evaluator Model '{evaluator_model_id}' nicht gefunden")
        
        # Hole Evaluator-Adapter
        evaluator_adapter = self._get_adapter_for_provider(evaluator_model.provider.name)
        if not evaluator_adapter.is_configured:
            raise ValueError(f"Evaluator Model '{evaluator_model_id}' nicht konfiguriert")
        
        # Erstelle Evaluator-Config (konservativ für objektive Bewertung)
        evaluator_config = ModelConfig(
            temperature=0.1,  # Niedrig für konsistente Bewertung
            max_tokens=evaluator_model.max_tokens_supported,  # Model-Maximum (statt fixer Wert)
            top_p=0.9,
            detail_level="high"
        )
        
        # Bewerte alle Modelle paarweise (Vergleich)
        evaluation_results = []
        
        # Bewerte jedes Modell einzeln (auch bei 2 Modellen)
        for test_result in test_results:
            try:
                print(f"[EVALUATION] Processing model: {test_result.model_name}")
                print(f"[EVALUATION] Response length: {len(test_result.response)} chars")
                print(f"[EVALUATION] Response preview: {test_result.response[:200]}...")
                
                # Erstelle Evaluation-Prompt für einzelnes Modell
                evaluation_prompt = self._build_single_model_evaluation_prompt(
                    evaluator_prompt,
                    test_result.response,
                    test_result.model_name
                )
                
                # Führe Evaluation durch
                evaluation_result = await evaluator_adapter.send_prompt(
                    model_id=evaluator_model_id,
                    prompt=evaluation_prompt,
                    config=evaluator_config
                )
                
                if evaluation_result.success:
                    # Parse Evaluation JSON
                    evaluation_data = self._parse_evaluation_result(evaluation_result.response)
                    print(f"[EVALUATION] Model: {test_result.model_name}, Raw Score: {evaluation_data.get('overall_score', 'N/A')}")
                    evaluation_data.update({
                        "test_model_name": test_result.model_name,
                        "test_model_provider": test_result.provider,
                        "evaluator_model_name": evaluator_model.name,
                        "evaluation_success": True
                    })
                    print(f"[EVALUATION] Final Result for {test_result.model_name}: {evaluation_data.get('overall_score', 'N/A')}")
                else:
                    # Fallback bei Evaluation-Fehler
                    evaluation_data = {
                        "test_model_name": test_result.model_name,
                        "test_model_provider": test_result.provider,
                        "evaluator_model_name": evaluator_model.name,
                        "evaluation_success": False,
                        "error": evaluation_result.error_message,
                        "overall_score": 0,
                        "detailed_scores": {},
                        "explanations": ["Evaluation fehlgeschlagen"]
                    }
                
                evaluation_results.append(evaluation_data)
                
            except Exception as e:
                # Fehler bei einzelner Evaluation
                evaluation_results.append({
                    "test_model_name": test_result.model_name,
                    "test_model_provider": test_result.provider,
                    "evaluator_model_name": evaluator_model.name,
                    "evaluation_success": False,
                    "error": str(e),
                    "overall_score": 0,
                    "detailed_scores": {},
                    "explanations": ["Evaluation fehlgeschlagen"]
                })
        
        return evaluation_results
    
    async def evaluate_single_model_result(
        self,
        test_result: TestResult,
        evaluator_prompt: str,
        evaluator_model_id: str
    ) -> Dict:
        """
        Use Case: Evaluate Single Model Result
        
        Bewertet ein einzelnes Modell-Result mit einem Evaluator-Prompt.
        
        Args:
            test_result: Das zu bewertende TestResult
            evaluator_prompt: Der Evaluator-Prompt
            evaluator_model_id: Modell für die Evaluation
            
        Returns:
            EvaluationResult mit Score und Begründungen
        """
        # Finde Evaluator-Model
        evaluator_model = self._find_model_by_id(evaluator_model_id)
        if not evaluator_model:
            raise ValueError(f"Evaluator Model '{evaluator_model_id}' nicht gefunden")
        
        # Hole Evaluator-Adapter
        evaluator_adapter = self._get_adapter_for_provider(evaluator_model.provider.name)
        if not evaluator_adapter:
            raise ValueError(f"Kein Adapter für Provider '{evaluator_model.provider.name}' gefunden")
        
        # Evaluator-Config: Nutze Model-Maximum für max_tokens
        evaluator_config = ModelConfig(
            temperature=0.3,  # Niedrig für konsistente Bewertungen
            max_tokens=evaluator_model.max_tokens_supported,  # Model-Maximum (statt fixer Wert)
            top_p=0.9,
            detail_level="high"
        )
        
        try:
            print(f"\n{'='*80}")
            print(f"[SINGLE-EVALUATION] Evaluator: {evaluator_model.name} (max_tokens: {evaluator_model.max_tokens_supported})")
            print(f"[SINGLE-EVALUATION] Processing model: {test_result.model_name}")
            print(f"[SINGLE-EVALUATION] Response length: {len(test_result.response)} chars")
            print(f"[SINGLE-EVALUATION] Input JSON Preview (first 500 chars):")
            print(test_result.response[:500])
            print(f"[SINGLE-EVALUATION] Checking critical_rules in response: {'critical_rules' in test_result.response}")
            print(f"[SINGLE-EVALUATION] Checking definitions in response: {'definitions' in test_result.response}")
            print(f"{'='*80}\n")
            
            # Nutze vollständige JSON (keine Truncation mehr nötig, da max_tokens = model maximum)
            model_json = test_result.response
            
            # Erstelle Evaluation-Prompt für einzelnes Modell
            evaluation_prompt = self._build_single_model_evaluation_prompt(
                evaluator_prompt,
                model_json,
                test_result.model_name
            )
            
            # Führe Evaluation durch
            evaluation_result = await evaluator_adapter.send_prompt(
                model_id=evaluator_model_id,
                prompt=evaluation_prompt,
                config=evaluator_config
            )
            
            if evaluation_result.success:
                # Parse Evaluation JSON
                evaluation_data = self._parse_evaluation_result(evaluation_result.response)
                print(f"[SINGLE-EVALUATION] Model: {test_result.model_name}, Raw Score: {evaluation_data.get('overall_score', 'N/A')}")
                
                evaluation_data.update({
                    "test_model_name": test_result.model_name,
                    "test_model_provider": test_result.provider,
                    "evaluator_model_name": evaluator_model.name,
                    "evaluation_success": True
                })
                
                return evaluation_data
            else:
                # Fallback bei Evaluation-Fehler
                return {
                    "test_model_name": test_result.model_name,
                    "test_model_provider": test_result.provider,
                    "evaluator_model_name": evaluator_model.name,
                    "evaluation_success": False,
                    "error": evaluation_result.error_message,
                    "overall_score": 0,
                    "detailed_scores": {},
                    "explanations": ["Evaluation fehlgeschlagen"]
                }
                
        except Exception as e:
            # Fehler bei Evaluation
            print(f"[SINGLE-EVALUATION] Error for {test_result.model_name}: {str(e)}")
            return {
                "test_model_name": test_result.model_name,
                "test_model_provider": test_result.provider,
                "evaluator_model_name": evaluator_model.name,
                "evaluation_success": False,
                "error": str(e),
                "overall_score": 0,
                "detailed_scores": {},
                "explanations": ["Evaluation fehlgeschlagen"]
            }
    
    def _build_comparison_evaluation_prompt(
        self,
        evaluator_prompt: str,
        reference_json: str,
        test_json: str,
        reference_model: str,
        test_model: str
    ) -> str:
        """
        Helper: Baue Evaluation-Prompt für direkten Vergleich
        
        Args:
            evaluator_prompt: Basis-Evaluator-Prompt
            reference_json: JSON-Output des Referenz-Modells
            test_json: JSON-Output des Test-Modells
            reference_model: Name des Referenz-Modells
            test_model: Name des Test-Modells
            
        Returns:
            Vollständiger Evaluation-Prompt für Vergleich
        """
        return f"""{evaluator_prompt}

⸻

📋 Eingabe:
{{
  "reference_json": {reference_json},
  "test_json": {test_json}
}}

⸻

📊 Ausgabe:
Gib ausschließlich folgendes JSON zurück:
{{
  "overall_score": 85,
  "category_scores": {{
    "structure": 9,
    "steps_completeness": 8,
    "articles_materials": 9,
    "consumables": 8,
    "tools": 7,
    "safety": 9,
    "visuals": 8,
    "quality_rules": 8,
    "text_accuracy": 9,
    "rag_ready": 8
  }},
  "strengths": [
    "Strukturkonformität: Alle Hauptfelder vorhanden, korrekte Typisierung",
    "Vollständigkeit: 8 von 10 Schritten erkannt, logische Reihenfolge stimmt",
    "Materialdaten: Artikelnummern korrekt, Mengen stimmen überein"
  ],
  "weaknesses": [
    "Werkzeuge-Sektion könnte detaillierter sein",
    "Sicherheitshinweise sind sehr gut erfasst"
  ],
  "summary": "Der Test-Output zeigt gute Übereinstimmung mit der Referenz, mit kleineren Abweichungen in der Werkzeug-Dokumentation."
}}"""
    
    def _build_single_model_evaluation_prompt(
        self,
        evaluator_prompt: str,
        model_json: str,
        model_name: str
    ) -> str:
        """
        Helper: Baue Evaluation-Prompt für einzelnes Modell
        
        Args:
            evaluator_prompt: Basis-Evaluator-Prompt (wird gekürzt wenn zu lang)
            model_json: JSON-Output des zu bewertenden Modells
            model_name: Name des Modells
            
        Returns:
            Vollständiger Evaluation-Prompt
        """
        return f"""{evaluator_prompt}

⸻

📋 ZU BEWERTENDE JSON ({model_name}):
{model_json}

⸻

📊 ANTWORT-FORMAT (NUR JSON):
{{
  "overall_score": 8.5,
  "category_scores": {{
    "structure": 9,
    "steps_completeness": 8,
    "articles_materials": 9,
    "consumables": 8,
    "tools": 7,
    "safety": 9,
    "visuals": 8,
    "quality_rules": 8,
    "text_accuracy": 9,
    "rag_ready": 8
  }},
  "strengths": [
    "✅ Strukturkonformität: Alle Hauptfelder vorhanden",
    "✅ Materialdaten: Artikelnummern vollständig (z.B. 26-10-204)",
    "✅ Sicherheitsangaben: Alle Warnungen erfasst"
  ],
  "weaknesses": [
    "❌ critical_rules: Feld leer",
    "❌ definitions: Feld leer",
    "⚠️ Werkzeuge: Nur generische Bezeichnungen"
  ],
  "summary": "Kurze Zusammenfassung mit Handlungsempfehlung (max. 2-3 Sätze)."
}}

ANTWORT (NUR JSON, KEINE ZUSÄTZLICHEN TEXTE):"""
    
    def _build_evaluation_prompt(
        self,
        evaluator_prompt: str,
        reference_json: str,
        test_json: str,
        reference_model: str,
        test_model: str
    ) -> str:
        """
        Helper: Baue Evaluation-Prompt zusammen
        
        Args:
            evaluator_prompt: Basis-Evaluator-Prompt
            reference_json: Referenz-JSON (Gold Standard)
            test_json: Zu bewertende JSON
            reference_model: Name des Referenz-Modells
            test_model: Name des Test-Modells
            
        Returns:
            Vollständiger Evaluation-Prompt
        """
        return f"""{evaluator_prompt}

⸻

📋 Eingabe:
• reference_json: {reference_model} (Gold Standard)
{reference_json}

• test_json: {test_model} (zu bewertend)
{test_json}

⸻

📊 Ausgabe:
Gib ausschließlich folgendes JSON zurück:
{{
  "overall_score": 85,
  "detailed_scores": {{
    "structure_compliance": 9,
    "completeness": 8,
    "material_accuracy": 9,
    "chemicals_consumables": 8,
    "tools_equipment": 7,
    "safety_instructions": 9,
    "visual_description": 8,
    "quality_checks": 8,
    "text_accuracy": 9,
    "rag_compatibility": 8
  }},
  "explanations": [
    "Strukturkonformität: Alle Hauptfelder vorhanden, korrekte Typisierung",
    "Vollständigkeit: 8 von 10 Schritten erkannt, logische Reihenfolge stimmt",
    "Materialdaten: Artikelnummern korrekt, Mengen stimmen überein"
  ],
  "recommendations": [
    "Werkzeuge-Sektion könnte detaillierter sein",
    "Sicherheitshinweise sind sehr gut erfasst"
  ]
}}"""
    
    def _parse_evaluation_result(self, evaluation_response: str) -> Dict:
        """
        Helper: Parse Evaluation JSON Response
        
        Args:
            evaluation_response: Raw Response vom Evaluator
            
        Returns:
            Parsed Evaluation Data
        """
        try:
            print(f"[EVALUATION] Raw response (full): {evaluation_response}")
            
            # Versuche JSON zu extrahieren
            json_match = None
            
            # Suche nach JSON in der Response
            if "{" in evaluation_response and "}" in evaluation_response:
                start = evaluation_response.find("{")
                end = evaluation_response.rfind("}") + 1
                json_str = evaluation_response[start:end]
                print(f"[EVALUATION] Extracted JSON: {json_str}")
                
                try:
                    json_match = json.loads(json_str)
                    print(f"[EVALUATION] Parsed JSON successfully: {json_match}")
                except json.JSONDecodeError as e:
                    print(f"[EVALUATION] JSON decode error: {e}")
                    pass
            
            if json_match:
                # Support both old and new format
                result = {
                    "overall_score": json_match.get("overall_score", 0),
                }
                
                # New format (category_scores, strengths, weaknesses, summary)
                if "category_scores" in json_match:
                    result.update({
                        "category_scores": json_match.get("category_scores", {}),
                        "strengths": json_match.get("strengths", []),
                        "weaknesses": json_match.get("weaknesses", []),
                        "summary": json_match.get("summary", "")
                    })
                
                # Legacy format (detailed_scores, explanations, recommendations)
                if "detailed_scores" in json_match:
                    result.update({
                        "detailed_scores": json_match.get("detailed_scores", {}),
                        "explanations": json_match.get("explanations", []),
                        "recommendations": json_match.get("recommendations", [])
                    })
                
                return result
            else:
                # Fallback: Einfache Score-Extraktion
                return {
                    "overall_score": 0,
                    "detailed_scores": {},
                    "explanations": [f"JSON-Parsing fehlgeschlagen: {evaluation_response[:200]}..."],
                    "recommendations": ["Evaluation-Response konnte nicht geparst werden"]
                }
                
        except Exception as e:
            return {
                "overall_score": 0,
                "detailed_scores": {},
                "explanations": [f"Evaluation-Parsing Fehler: {str(e)}"],
                "recommendations": ["Evaluation konnte nicht verarbeitet werden"]
            }

